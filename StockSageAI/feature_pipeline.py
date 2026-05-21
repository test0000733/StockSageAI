import numpy as np
import pandas as pd

from StockSageAI.utils import calculate_technical_indicators


class FeaturePipeline:
    """Feature engineering pipeline for market regime detection and training."""

    def build_feature_matrix(self, df: pd.DataFrame) -> pd.DataFrame:
        """Build a cleaned feature DataFrame with technical and volatility signals."""
        if df is None or df.empty:
            return pd.DataFrame()

        df = calculate_technical_indicators(df.copy())
        df['returns'] = df['Close'].pct_change()
        df['volatility'] = df['returns'].rolling(window=10).std()
        df['momentum'] = df['Close'].diff(3)
        df['trend'] = df['Close'].diff(10)
        df['bb_width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']
        df['ma_gap'] = (df['EMA_12'] - df['EMA_26']) / df['Close']
        df['price_gap_20'] = (df['Close'] - df['SMA_20']) / df['SMA_20']
        df['volume_zscore'] = (df['Volume'] - df['Volume_MA']) / (df['Volume_MA'] + 1e-6)
        df['volatility_ma'] = df['volatility'].rolling(window=5).mean()

        for lag in [1, 2, 3, 5, 10]:
            df[f'returns_lag_{lag}'] = df['returns'].shift(lag)
            df[f'momentum_lag_{lag}'] = df['momentum'].shift(lag)

        df = df.dropna(
            subset=[
                'returns',
                'volatility',
                'RSI',
                'MACD',
                'MACD_Signal',
                'bb_width',
                'volume_zscore',
                'ma_gap',
                'price_gap_20'
            ]
        )

        return df

    def get_feature_columns(self):
        return [
            'returns',
            'volatility',
            'RSI',
            'MACD',
            'MACD_Signal',
            'bb_width',
            'volume_zscore',
            'ma_gap',
            'price_gap_20',
            'momentum',
            'trend'
        ]

    def build_time_series_dataset(self, df: pd.DataFrame, horizon: int = 1, sequence_length: int = 20, target_column: str = 'Close'):
        """Create sliding-window dataset for time-series training."""
        features = self.build_feature_matrix(df)
        if features is None or features.empty:
            return np.empty((0, 0, 0)), np.empty((0,)), []

        feature_columns = [col for col in self.get_feature_columns() if col in features.columns]
        if not feature_columns or target_column not in features.columns:
            return np.empty((0, 0, 0)), np.empty((0,)), []

        values = features[feature_columns].astype(float).to_numpy()
        target = features[target_column].astype(float).to_numpy()

        X = []
        y = []
        target_dates = []
        for idx in range(sequence_length, len(values) - horizon + 1):
            X.append(values[idx - sequence_length:idx])
            y.append(target[idx + horizon - 1])
            target_dates.append(features.index[idx + horizon - 1])

        if not X:
            return np.empty((0, 0, 0)), np.empty((0,)), []

        return np.stack(X), np.array(y), target_dates

    def calculate_anomaly_score(self, df: pd.DataFrame) -> float:
        if df is None or df.empty:
            return 0.0

        feature_columns = [col for col in self.get_feature_columns() if col in df.columns]
        matrix = df[feature_columns].dropna().astype(float)
        if matrix.shape[0] < 10 or matrix.shape[1] < 3:
            return 0.0

        matrix = (matrix - matrix.mean()) / (matrix.std(ddof=0) + 1e-9)
        cov = np.cov(matrix.T)
        eigvals, eigvecs = np.linalg.eigh(cov)
        topk = min(3, len(eigvals))
        components = eigvecs[:, -topk:]
        projection = matrix.values.dot(components).dot(components.T)
        reconstruction_error = np.mean((matrix.values - projection) ** 2, axis=1)
        anomaly_score = float(min(100.0, np.nanmean(reconstruction_error) * 200.0))
        return anomaly_score
