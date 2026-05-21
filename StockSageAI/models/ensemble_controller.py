import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error

from StockSageAI.feature_pipeline import FeaturePipeline
from StockSageAI.models.transformers import TransformerEnsemble
from StockSageAI.models.lstm_engine import LSTMEngine
from StockSageAI.models.cnn_lstm import CNNLSTMEngine
from StockSageAI.models.boosting import BoostingEnsemble

class EnsembleController:
    def __init__(self, config=None):
        self.config = config or {}
        self.feature_pipeline = FeaturePipeline()
        self.base_models = {
            'TransformerEnsemble': TransformerEnsemble(),
            'LSTM': LSTMEngine({'lr': self.config.get('lr', 0.001)}),
            'CNN-LSTM': CNNLSTMEngine({'lr': self.config.get('lr', 0.001)}),
            'Boosting': BoostingEnsemble({'learning_rate': self.config.get('learning_rate', 0.05)})
        }
        self.meta_model = Pipeline([
            ('scaler', StandardScaler()),
            ('ridge', Ridge(alpha=self.config.get('alpha', 1.0), random_state=self.config.get('seed', 42)))
        ])
        self.metrics = {}

    def _build_dataset(self, df: pd.DataFrame, sequence_length=20, horizon=1, target_column='Close'):
        X, y, dates = self.feature_pipeline.build_time_series_dataset(df, horizon=horizon, sequence_length=sequence_length, target_column=target_column)
        return X, y, dates

    def train(self, data, sequence_length=20, horizon=1, epochs=8, lr=0.001, **kwargs):
        if not isinstance(data, pd.DataFrame):
            return {'status': 'failed', 'logs': ['Ensemble controller requires a DataFrame training set.'], 'metrics': {}}

        X, y, _ = self._build_dataset(data, sequence_length=sequence_length, horizon=horizon)
        if X.size == 0 or len(y) < 10:
            return {'status': 'failed', 'logs': ['Not enough data to train ensemble controller.'], 'metrics': {}}

        logs = []
        base_predictions = []
        for name, engine in self.base_models.items():
            if name == 'TransformerEnsemble':
                result = engine.train(data, sequence_length=sequence_length, horizon=horizon, epochs=epochs, lr=lr)
            elif name == 'Boosting':
                result = engine.train(data, sequence_length=sequence_length, horizon=horizon, y=None)
            else:
                result = engine.train(data, sequence_length=sequence_length, horizon=horizon, epochs=epochs, lr=lr)

            metric = result.get('metrics', {}).get('mse', None)
            logs.append(f"{name} base model trained: mse={metric if metric is not None else 'n/a'}")
            base_pred = engine.predict(X)
            base_predictions.append(base_pred)

        stack_features = np.vstack(base_predictions).T
        self.meta_model.fit(stack_features, y)
        final_preds = self.meta_model.predict(stack_features)
        mse = float(mean_squared_error(y, final_preds))
        self.metrics = {'mse': mse}
        logs.append(f'Ensemble intelligence blending completed: mse={mse:.4f}')

        return {
            'status': 'ok',
            'logs': logs,
            'metrics': {'mse': mse, 'base_models': list(self.base_models.keys())}
        }

    def predict(self, X):
        if isinstance(X, np.ndarray):
            stack_features = []
            for engine in self.base_models.values():
                stack_features.append(engine.predict(X))
            if not stack_features:
                return np.array([])
            stack_matrix = np.vstack(stack_features).T
            return self.meta_model.predict(stack_matrix)
        return np.array([])
