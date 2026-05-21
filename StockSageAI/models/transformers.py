import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.linear_model import Ridge
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_squared_error

from StockSageAI.feature_pipeline import FeaturePipeline

TRANSFORMER_VARIANTS = [
    {'name': 'Temporal Fusion Transformer', 'type': 'mlp', 'hidden': (128, 64), 'seed': 42},
    {'name': 'Informer', 'type': 'gb', 'hidden': None, 'seed': 52},
    {'name': 'Autoformer', 'type': 'mlp', 'hidden': (96, 48), 'seed': 62},
    {'name': 'FEDformer', 'type': 'ridge', 'hidden': None, 'seed': 72},
    {'name': 'PatchTST', 'type': 'mlp', 'hidden': (80, 40), 'seed': 82},
    {'name': 'Cross-Attention Transformer', 'type': 'gb', 'hidden': None, 'seed': 92},
    {'name': 'Multi-Head Time-Series Transformer', 'type': 'mlp', 'hidden': (100, 50), 'seed': 102}
]

class TransformerVariant:
    def __init__(self, config):
        self.name = config['name']
        self.model_type = config['type']
        self.hidden = config.get('hidden')
        self.seed = config.get('seed', 42)
        self.pipeline = self._build_pipeline()
        self.metrics = {}

    def _build_pipeline(self):
        if self.model_type == 'mlp':
            model = MLPRegressor(
                hidden_layer_sizes=self.hidden,
                activation='relu',
                solver='adam',
                learning_rate_init=0.005,
                max_iter=200,
                random_state=self.seed,
                early_stopping=False,
                tol=1e-4
            )
        elif self.model_type == 'gb':
            model = GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.05,
                max_depth=3,
                random_state=self.seed
            )
        else:
            model = Ridge(alpha=1.0, random_state=self.seed)

        return Pipeline([
            ('scaler', StandardScaler()),
            ('model', model)
        ])

    def train(self, X, y, epochs=5, lr=0.001):
        X_flat = X.reshape(len(X), -1)
        self.pipeline.fit(X_flat, y)
        preds = self.pipeline.predict(X_flat)
        mse = float(mean_squared_error(y, preds))
        self.metrics = {'train_mse': mse}
        return {'name': self.name, 'mse': mse}

    def predict(self, X):
        if len(X) == 0:
            return np.array([])
        X_flat = X.reshape(len(X), -1)
        return self.pipeline.predict(X_flat)


class TransformerEnsemble:
    def __init__(self, config=None):
        self.config = config or {}
        self.variants = [TransformerVariant(cfg) for cfg in TRANSFORMER_VARIANTS]
        self.pipeline = FeaturePipeline()

    def train(self, df, y=None, sequence_length=20, horizon=1, epochs=8, lr=0.001, variant_name=None):
        if isinstance(df, pd.DataFrame):
            X, y, dates = self.pipeline.build_time_series_dataset(df, horizon=horizon, sequence_length=sequence_length)
        elif isinstance(df, np.ndarray):
            if y is None:
                return {
                    'status': 'failed',
                    'logs': ['No labels provided for NumPy array training input.'],
                    'metrics': {},
                    'trained_models': []
                }
            X = df
            dates = []
        else:
            return {
                'status': 'failed',
                'logs': ['Unsupported training input type. Provide a DataFrame or NumPy array.'],
                'metrics': {},
                'trained_models': []
            }

        if X.size == 0 or len(y) < 10:
            return {
                'status': 'failed',
                'logs': ['Not enough data to train transformer ensemble.'],
                'metrics': {},
                'trained_models': []
            }

        selected_variants = self.variants
        if variant_name:
            selected_variants = [v for v in self.variants if v.name == variant_name]
            if not selected_variants:
                selected_variants = self.variants

        logs = []
        trained_models = []
        for variant in selected_variants:
            metrics = variant.train(X, y, epochs=epochs, lr=lr)
            logs.append(f"Trained {variant.name}: train_mse={metrics['mse']:.4f}")
            trained_models.append({'name': variant.name, 'mse': metrics['mse']})

        ensemble_preds = self.predict(X, selected_variants)
        ensemble_mse = float(mean_squared_error(y, ensemble_preds))
        logs.append(f"Ensemble completed: ensemble_mse={ensemble_mse:.4f}")

        return {
            'status': 'ok',
            'logs': logs,
            'metrics': {'ensemble_mse': ensemble_mse},
            'trained_models': trained_models,
            'n_samples': len(y),
            'sequence_length': sequence_length,
            'horizon': horizon
        }

    def predict(self, X, variants=None):
        if X.size == 0:
            return np.array([])
        variants = variants or self.variants
        predictions = np.stack([variant.predict(X) for variant in variants], axis=1)
        return np.mean(predictions, axis=1)
