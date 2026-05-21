import numpy as np
import pandas as pd
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

from StockSageAI.feature_pipeline import FeaturePipeline

MODEL_WEIGHT_MAP = {
    'Bullish Trend': {'Transformer Ensemble': 0.30, 'LSTM': 0.20, 'BiLSTM': 0.15, 'CNN-LSTM': 0.15, 'GNN Ensemble': 0.10, 'XGBoost': 0.10},
    'Bearish Trend': {'Transformer Ensemble': 0.20, 'LSTM': 0.10, 'BiLSTM': 0.10, 'CNN-LSTM': 0.15, 'GNN Ensemble': 0.20, 'XGBoost': 0.25},
    'Sideways Consolidation': {'Transformer Ensemble': 0.15, 'LSTM': 0.15, 'BiLSTM': 0.20, 'CNN-LSTM': 0.20, 'GNN Ensemble': 0.10, 'XGBoost': 0.20},
    'High Volatility': {'Transformer Ensemble': 0.25, 'LSTM': 0.10, 'BiLSTM': 0.10, 'CNN-LSTM': 0.20, 'GNN Ensemble': 0.20, 'XGBoost': 0.15},
    'Low Volatility': {'Transformer Ensemble': 0.20, 'LSTM': 0.20, 'BiLSTM': 0.15, 'CNN-LSTM': 0.20, 'GNN Ensemble': 0.10, 'XGBoost': 0.15},
    'Crash Regime': {'Transformer Ensemble': 0.20, 'LSTM': 0.05, 'BiLSTM': 0.05, 'CNN-LSTM': 0.10, 'GNN Ensemble': 0.35, 'XGBoost': 0.25},
    'Recovery Regime': {'Transformer Ensemble': 0.30, 'LSTM': 0.15, 'BiLSTM': 0.10, 'CNN-LSTM': 0.15, 'GNN Ensemble': 0.15, 'XGBoost': 0.15},
    'Institutional Accumulation': {'Transformer Ensemble': 0.25, 'LSTM': 0.15, 'BiLSTM': 0.20, 'CNN-LSTM': 0.20, 'GNN Ensemble': 0.10, 'XGBoost': 0.10},
    'Distribution Phase': {'Transformer Ensemble': 0.20, 'LSTM': 0.10, 'BiLSTM': 0.15, 'CNN-LSTM': 0.20, 'GNN Ensemble': 0.20, 'XGBoost': 0.15},
    'Momentum Breakout': {'Transformer Ensemble': 0.30, 'LSTM': 0.20, 'BiLSTM': 0.10, 'CNN-LSTM': 0.20, 'GNN Ensemble': 0.10, 'XGBoost': 0.10},
    'Mean Reversion Environment': {'Transformer Ensemble': 0.20, 'LSTM': 0.20, 'BiLSTM': 0.20, 'CNN-LSTM': 0.15, 'GNN Ensemble': 0.10, 'XGBoost': 0.15}
}

class RegimeEngine:
    def __init__(self):
        self.pipeline = FeaturePipeline()
        self.scaler = StandardScaler()

    def _ensure_features(self, df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            return pd.DataFrame()
        return self.pipeline.build_feature_matrix(df)

    def _estimate_transition_matrix(self, hidden_states: np.ndarray, n_states: int) -> np.ndarray:
        matrix = np.full((n_states, n_states), 1e-6)
        for current_state, next_state in zip(hidden_states[:-1], hidden_states[1:]):
            matrix[current_state, next_state] += 1.0
        matrix = matrix / matrix.sum(axis=1, keepdims=True)
        return matrix

    def _viterbi(self, log_emissions: np.ndarray, log_transition: np.ndarray, start_log: np.ndarray) -> np.ndarray:
        T, K = log_emissions.shape
        if start_log is None:
            start_log = np.zeros(K)
        delta = np.full((T, K), -np.inf)
        psi = np.zeros((T, K), dtype=int)
        delta[0] = start_log + log_emissions[0]

        for t in range(1, T):
            for j in range(K):
                transitions = delta[t - 1] + log_transition[:, j]
                psi[t, j] = int(np.argmax(transitions))
                delta[t, j] = np.max(transitions) + log_emissions[t, j]

        path = np.zeros(T, dtype=int)
        path[-1] = int(np.argmax(delta[-1]))
        for t in range(T - 2, -1, -1):
            path[t] = psi[t + 1, path[t + 1]]
        return path

    def _map_state_to_regime(self, df: pd.DataFrame, state_index: int, labels: np.ndarray) -> str:
        state_rows = df.loc[labels == state_index]
        if state_rows.empty:
            return 'Sideways Consolidation'

        avg_return = float(state_rows['returns'].mean())
        avg_vol = float(state_rows['volatility'].mean())
        avg_rsi = float(state_rows['RSI'].mean())
        avg_price_gap = float(state_rows['price_gap_20'].mean())

        if avg_vol > 0.045 and avg_return < -0.006:
            return 'Crash Regime'
        if avg_vol > 0.035 and avg_return > 0.004:
            return 'Recovery Regime'
        if avg_vol > 0.035 and abs(avg_return) < 0.002:
            return 'High Volatility'
        if abs(avg_return) < 0.002 and avg_vol < 0.015:
            return 'Sideways Consolidation'
        if avg_return > 0.003 and avg_vol < 0.02:
            return 'Bullish Trend'
        if avg_return < -0.003 and avg_vol < 0.02:
            return 'Bearish Trend'
        if avg_rsi > 70 and avg_return > 0:
            return 'Momentum Breakout'
        if avg_rsi < 30 and avg_return < 0:
            return 'Mean Reversion Environment'
        if avg_return > 0 and avg_price_gap > 0.01:
            return 'Institutional Accumulation'
        if avg_return < 0 and avg_price_gap < -0.01:
            return 'Distribution Phase'
        return 'Low Volatility' if avg_vol < 0.02 else 'High Volatility'

    def _build_history(self, df: pd.DataFrame, hidden_sequence: np.ndarray, regime_map: dict, proba: np.ndarray) -> list:
        history = []
        n_steps = min(20, len(hidden_sequence))
        start_index = len(hidden_sequence) - n_steps
        for offset in range(n_steps):
            position = start_index + offset
            state = int(hidden_sequence[position])
            regime = regime_map.get(state, 'Sideways Consolidation')
            confidence = float(round(np.max(proba[position]) * 100, 1))
            idx = df.index[position]
            date_key = idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx)
            history.append({
                'date': date_key,
                'regime': regime,
                'state': state,
                'confidence': confidence
            })
        return history

    def _recommend_model_weights(self, regime: str) -> dict:
        return MODEL_WEIGHT_MAP.get(regime, MODEL_WEIGHT_MAP['Bullish Trend'])

    def detect_regime(self, df: pd.DataFrame) -> dict:
        features = self._ensure_features(df)
        if features is None or features.empty or len(features) < 30:
            return {
                'regime': 'Sideways Consolidation',
                'confidence': 55.0,
                'history': [],
                'recommended_weights': self._recommend_model_weights('Sideways Consolidation'),
                'state_probabilities': {},
                'anomaly_score': 0.0
            }

        feature_columns = [
            'returns',
            'volatility',
            'RSI',
            'MACD',
            'MACD_Signal',
            'bb_width',
            'volume_zscore',
            'ma_gap',
            'price_gap_20',
            'momentum'
        ]
        available_columns = [col for col in feature_columns if col in features.columns]
        if not available_columns:
            return {
                'regime': 'Sideways Consolidation',
                'confidence': 55.0,
                'history': [],
                'recommended_weights': self._recommend_model_weights('Sideways Consolidation'),
                'state_probabilities': {},
                'anomaly_score': 0.0
            }

        observation_matrix = features[available_columns].astype(float).fillna(0.0)
        scaled = self.scaler.fit_transform(observation_matrix)
        n_components = min(5, max(2, len(scaled) // 20))

        gmm = GaussianMixture(n_components=n_components, covariance_type='full', random_state=42)
        gmm.fit(scaled)

        probabilities = gmm.predict_proba(scaled)
        raw_states = np.argmax(probabilities, axis=1)
        transition_matrix = self._estimate_transition_matrix(raw_states, n_components)
        log_transition = np.log(transition_matrix + 1e-9)

        start_probs = np.bincount(raw_states, minlength=n_components).astype(float)
        start_probs = start_probs / np.sum(start_probs)
        start_log = np.log(start_probs + 1e-9)

        smoothed_states = self._viterbi(np.log(probabilities + 1e-9), log_transition, start_log)
        regime_map = {state: self._map_state_to_regime(features, state, raw_states) for state in range(n_components)}

        final_state = int(smoothed_states[-1])
        final_regime = regime_map.get(final_state, 'Sideways Consolidation')
        final_confidence = float(min(99.9, 45.0 + np.max(probabilities[-1]) * 40.0 + np.mean(features['volatility'][-5:]) * 250.0))
        final_confidence = round(final_confidence, 1)

        history = self._build_history(features, smoothed_states, regime_map, probabilities)
        state_probabilities = {
            regime_map[i]: float(round(probabilities[-1, i] * 100, 1))
            for i in range(probabilities.shape[1])
        }
        anomaly_score = self.pipeline.calculate_anomaly_score(features)

        return {
            'regime': final_regime,
            'confidence': final_confidence,
            'history': history,
            'recommended_weights': self._recommend_model_weights(final_regime),
            'state_probabilities': state_probabilities,
            'anomaly_score': round(anomaly_score, 1)
        }
