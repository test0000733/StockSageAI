"""Build and save the full 8-model StockSageAI ensemble locally.

This script trains placeholder sequence models using the same feature set as the admin
inference pipeline and writes the resulting artifacts into StockSageAI/models/.
"""

import os
import json
from datetime import datetime
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_squared_error
import joblib

MODEL_DIR = os.path.join(os.path.dirname(__file__), 'StockSageAI', 'models')
os.makedirs(MODEL_DIR, exist_ok=True)

FEATURE_COLUMNS = [
    'MA5',
    'MA20',
    'MA50',
    'RSI',
    'MACD',
    'ATR',
    'Volume_Ratio',
    'Price_Range'
]

MODEL_FILES = {
    'Transformer LSTM': 'transformer_lstm.pkl',
    'BiLSTM Ensemble': 'bilstm_ensemble.pkl',
    'CNN-BiLSTM': 'cnn_bilstm.pkl',
    'Attention LSTM': 'attention_lstm.pkl',
    'TCN': 'tcn_model.pkl',
    'XGBoost': 'xgboost_model.pkl',
    'CatBoost': 'catboost_model.pkl',
    'LightGBM': 'lightgbm_model.pkl'
}


def generate_synthetic_stock_data(n_samples=400, seed=42):
    np.random.seed(seed)
    dates = pd.date_range(end=datetime.now(), periods=n_samples, freq='D')
    base_price = 100.0
    prices = [base_price]
    for _ in range(n_samples - 1):
        change = np.random.normal(0, 0.015)
        prices.append(prices[-1] * (1 + change))

    df = pd.DataFrame({
        'Date': dates,
        'Open': np.array(prices) + np.random.normal(0, 0.5, n_samples),
        'High': np.array(prices) + np.abs(np.random.normal(0, 1.0, n_samples)),
        'Low': np.array(prices) - np.abs(np.random.normal(0, 1.0, n_samples)),
        'Close': np.array(prices),
        'Volume': np.random.randint(1000000, 5000000, n_samples)
    })
    df = df.set_index('Date')
    return df


def build_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    df['ATR'] = (df['High'] - df['Low']).rolling(window=14).mean()
    df['Volume_Ratio'] = df['Volume'] / (df['Volume'].rolling(window=20).mean() + 1e-9)
    df['Price_Range'] = (df['High'] - df['Low']) / (df['Close'] + 1e-9)
    df['RSI'] = df['Close'].diff().apply(lambda x: x if x > 0 else 0).rolling(window=14).mean()
    df['MACD'] = df['Close'].ewm(span=12).mean() - df['Close'].ewm(span=26).mean()
    df = df.dropna(subset=FEATURE_COLUMNS)
    return df


def build_training_sequences(df: pd.DataFrame, sequence_length=60, horizon=1):
    X = []
    y = []
    for i in range(sequence_length, len(df) - horizon + 1):
        window = df[FEATURE_COLUMNS].iloc[i - sequence_length:i].astype(float).to_numpy()
        X.append(window)
        y.append(df['Close'].iloc[i + horizon - 1])
    if not X:
        return np.empty((0, 0, 0)), np.empty((0,))
    return np.stack(X), np.array(y)


def train_and_save_model(name, estimator, X, y):
    print(f"Training {name}...")
    estimator.fit(X.reshape(len(X), -1), y)
    preds = estimator.predict(X.reshape(len(X), -1))
    mse = mean_squared_error(y, preds)
    model_path = os.path.join(MODEL_DIR, MODEL_FILES[name])
    joblib.dump(estimator, model_path)
    print(f"Saved {name} to {model_path} (MSE={mse:.4f})")
    return mse


def main():
    df = generate_synthetic_stock_data(n_samples=420)
    df = build_feature_matrix(df)
    X, y = build_training_sequences(df, sequence_length=60, horizon=1)
    if X.size == 0 or len(y) == 0:
        raise RuntimeError("Insufficient data for training. Check feature engineering pipeline.")

    scaler_X = StandardScaler()
    scaler_y = StandardScaler()
    scaler_X.fit(X.reshape(len(X), -1))
    scaler_y.fit(y.reshape(-1, 1))
    joblib.dump({'scaler_X': scaler_X, 'scaler_y': scaler_y}, os.path.join(MODEL_DIR, 'scalers.pkl'))
    print("Saved preprocessing scalers to scalers.pkl")

    model_specs = [
        ('Transformer LSTM', Pipeline([
            ('scaler', StandardScaler()),
            ('model', MLPRegressor(hidden_layer_sizes=(128, 64), activation='relu', solver='adam', learning_rate_init=0.001, max_iter=500, random_state=42))
        ])),
        ('BiLSTM Ensemble', Pipeline([
            ('scaler', StandardScaler()),
            ('model', MLPRegressor(hidden_layer_sizes=(80, 40), activation='relu', solver='adam', learning_rate_init=0.001, max_iter=500, random_state=52))
        ])),
        ('CNN-BiLSTM', Pipeline([
            ('scaler', StandardScaler()),
            ('model', MLPRegressor(hidden_layer_sizes=(128, 64, 32), activation='relu', solver='adam', learning_rate_init=0.001, max_iter=500, random_state=62))
        ])),
        ('Attention LSTM', Pipeline([
            ('scaler', StandardScaler()),
            ('model', MLPRegressor(hidden_layer_sizes=(100, 80, 40), activation='relu', solver='adam', learning_rate_init=0.001, max_iter=500, random_state=72))
        ])),
        ('TCN', Pipeline([
            ('scaler', StandardScaler()),
            ('model', MLPRegressor(hidden_layer_sizes=(64, 64, 32), activation='relu', solver='adam', learning_rate_init=0.001, max_iter=500, random_state=82))
        ])),
        ('XGBoost', Pipeline([
            ('scaler', StandardScaler()),
            ('model', GradientBoostingRegressor(n_estimators=120, learning_rate=0.05, max_depth=3, random_state=101))
        ])),
        ('CatBoost', Pipeline([
            ('scaler', StandardScaler()),
            ('model', GradientBoostingRegressor(n_estimators=100, learning_rate=0.03, max_depth=4, random_state=111))
        ])),
        ('LightGBM', Pipeline([
            ('scaler', StandardScaler()),
            ('model', GradientBoostingRegressor(n_estimators=80, learning_rate=0.08, max_depth=5, random_state=121))
        ])),
    ]

    results = {}
    for name, estimator in model_specs:
        mse = train_and_save_model(name, estimator, X, y)
        results[name] = {'mse': mse}

    metadata = {
        'created_at': datetime.now().isoformat(),
        'models': results,
        'sequence_length': 60,
        'feature_columns': FEATURE_COLUMNS,
        'training_samples': len(y)
    }
    with open(os.path.join(MODEL_DIR, 'model_metadata.json'), 'w') as metadata_file:
        json.dump(metadata, metadata_file, indent=2)
    print(f"Saved metadata to model_metadata.json")

    print("Finished building the full 8-model artifact set.")


if __name__ == '__main__':
    main()
