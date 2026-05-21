import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_squared_error

from StockSageAI.feature_pipeline import FeaturePipeline

class MultimodalFusionEngine:
    def __init__(self, config=None):
        self.config = config or {}
        self.feature_pipeline = FeaturePipeline()
        self.pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('model', GradientBoostingRegressor(
                n_estimators=self.config.get('n_estimators', 100),
                learning_rate=self.config.get('learning_rate', 0.05),
                max_depth=self.config.get('max_depth', 4),
                random_state=self.config.get('seed', 42)
            ))
        ])
        self.metrics = {}

    def _prepare_features(self, df: pd.DataFrame, extra_features: pd.DataFrame = None):
        features = self.feature_pipeline.build_feature_matrix(df)
        if features.empty:
            return pd.DataFrame(), pd.Series(dtype=float)

        if extra_features is not None and not extra_features.empty:
            extra_df = extra_features.copy()
            if 'Date' in extra_df.columns:
                extra_df['Date'] = pd.to_datetime(extra_df['Date'], errors='coerce')
                extra_df = extra_df.set_index('Date')
            extra_cols = [c for c in extra_df.columns if c not in features.columns]
            if extra_cols:
                features = features.join(extra_df[extra_cols], how='left')
        features = features.dropna()
        target = features['Close'].astype(float) if 'Close' in features.columns else pd.Series(dtype=float)
        return features, target

    def train(self, data, extra_features=None, sequence_length=20, horizon=1, lr=0.05, target_column='Close', epochs=10, y=None, **kwargs):
        if isinstance(data, pd.DataFrame):
            features, target = self._prepare_features(data, extra_features)
        elif isinstance(data, np.ndarray):
            if y is None:
                return {'status': 'failed', 'logs': ['Direct array input requires y labels for fusion training.'], 'metrics': {}}
            features = pd.DataFrame(data)
            target = pd.Series(y)
        else:
            return {'status': 'failed', 'logs': ['Unsupported training data type for multimodal fusion.'], 'metrics': {}}

        if features.empty or target.empty or len(target) < 10:
            return {'status': 'failed', 'logs': ['Not enough data to train multimodal fusion.'], 'metrics': {}}

        X = features.drop(columns=[target_column], errors='ignore')
        X = X.select_dtypes(include=[np.number])
        if X.empty:
            return {'status': 'failed', 'logs': ['No numeric multimodal features were available for training.'], 'metrics': {}}
        X = X.to_numpy()
        y = target.astype(float).to_numpy()
        self.pipeline.set_params(model__learning_rate=self.config.get('learning_rate', lr))
        self.pipeline.fit(X, y)
        preds = self.pipeline.predict(X)
        mse = float(mean_squared_error(y, preds))
        self.metrics = {'mse': mse}
        return {'status': 'ok', 'logs': [f'Multimodal fusion training complete: mse={mse:.4f}'], 'metrics': {'mse': mse}}

    def predict(self, data, extra_features=None):
        if isinstance(data, pd.DataFrame):
            features, _ = self._prepare_features(data, extra_features)
        elif isinstance(data, np.ndarray):
            features = pd.DataFrame(data)
        else:
            return np.array([])

        if features.empty:
            return np.array([])

        X = features.select_dtypes(include=[np.number]).to_numpy()
        if X.size == 0:
            return np.array([])
        return self.pipeline.predict(X)
