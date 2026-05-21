import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_squared_error

from StockSageAI.feature_pipeline import FeaturePipeline

class LSTMEngine:
    def __init__(self, config=None):
        self.config = config or {}
        self.feature_pipeline = FeaturePipeline()
        self.pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('model', MLPRegressor(
                hidden_layer_sizes=(64, 32),
                activation='relu',
                solver='adam',
                learning_rate_init=self.config.get('lr', 0.001),
                max_iter=self.config.get('max_iter', 200),
                random_state=self.config.get('seed', 42)
            ))
        ])
        self.metrics = {}

    def train(self, data, epochs=5, sequence_length=20, horizon=1, lr=0.001, target_column='Close', y=None, **kwargs):
        if isinstance(data, pd.DataFrame):
            X, y, _ = self.feature_pipeline.build_time_series_dataset(
                data,
                horizon=horizon,
                sequence_length=sequence_length,
                target_column=target_column
            )
        elif isinstance(data, np.ndarray):
            if y is None:
                return {'status': 'failed', 'logs': ['Direct array input requires y labels.'], 'metrics': {}}
            X = data
        else:
            return {'status': 'failed', 'logs': ['Unsupported training data type for LSTM.'], 'metrics': {}}

        if X.size == 0 or len(y) < 10:
            return {'status': 'failed', 'logs': ['Not enough data to train LSTM engine.'], 'metrics': {}}

        X_flat = X.reshape(len(X), -1)
        self.pipeline.set_params(model__learning_rate_init=lr, model__max_iter=max(50, epochs * 20))
        self.pipeline.fit(X_flat, y)
        preds = self.pipeline.predict(X_flat)
        mse = float(mean_squared_error(y, preds))
        self.metrics = {'mse': mse}
        return {'status': 'ok', 'logs': [f'LSTM training complete: mse={mse:.4f}'], 'metrics': {'mse': mse}}

    def predict(self, X):
        if isinstance(X, np.ndarray) and X.size > 0:
            X_flat = X.reshape(len(X), -1)
            return self.pipeline.predict(X_flat)
        return np.array([])
