"""
Demo training pipeline for StockSageAI training stack.

This script demonstrates how to train each model type and compare their performance.
Run this to test the full training pipeline with sample data.
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from StockSageAI.training_manager import manager
from StockSageAI.models.transformers import TransformerEnsemble
from StockSageAI.models.lstm_engine import LSTMEngine
from StockSageAI.models.bilstm_engine import BiLSTMEngine
from StockSageAI.models.cnn_lstm import CNNLSTMEngine
from StockSageAI.models.gnn_engine import GNNEngine
from StockSageAI.models.boosting import BoostingEnsemble
from StockSageAI.models.multimodal_fusion import MultimodalFusionEngine
from StockSageAI.models.ensemble_controller import EnsembleController


def generate_sample_dataset(n_samples=120, volatility=0.02):
    """Generate synthetic stock price data for demonstration."""
    dates = pd.date_range(end=datetime.now(), periods=n_samples, freq='D')
    base_price = 100.0
    prices = [base_price]
    
    for _ in range(n_samples - 1):
        change = np.random.normal(0, volatility)
        prices.append(prices[-1] * (1 + change))
    
    return pd.DataFrame({
        'Date': dates,
        'Open': prices + np.random.normal(0, 0.5, n_samples),
        'High': prices + np.abs(np.random.normal(0, 1.0, n_samples)),
        'Low': prices - np.abs(np.random.normal(0, 1.0, n_samples)),
        'Close': prices,
        'Volume': np.random.randint(1000000, 5000000, n_samples)
    })


def test_transformer_ensemble():
    """Test Transformer Ensemble training."""
    print("\n" + "="*60)
    print("Testing Transformer Ensemble")
    print("="*60)
    
    df = generate_sample_dataset()
    ensemble = TransformerEnsemble()
    result = ensemble.train(df, sequence_length=20, horizon=1, epochs=3, lr=0.001)
    
    print(f"Status: {result['status']}")
    print(f"MSE: {result['metrics'].get('ensemble_mse', 'N/A'):.4f}")
    print(f"Logs: {len(result['logs'])} entries")
    return result['metrics'].get('ensemble_mse', float('inf'))


def test_lstm():
    """Test LSTM training."""
    print("\n" + "="*60)
    print("Testing LSTM Engine")
    print("="*60)
    
    df = generate_sample_dataset()
    lstm = LSTMEngine()
    result = lstm.train(df, sequence_length=20, horizon=1, epochs=3, lr=0.001)
    
    print(f"Status: {result['status']}")
    print(f"MSE: {result['metrics'].get('mse', 'N/A'):.4f}")
    return result['metrics'].get('mse', float('inf'))


def test_bilstm():
    """Test BiLSTM training."""
    print("\n" + "="*60)
    print("Testing BiLSTM Engine")
    print("="*60)
    
    df = generate_sample_dataset()
    bilstm = BiLSTMEngine()
    result = bilstm.train(df, sequence_length=20, horizon=1, epochs=3, lr=0.001)
    
    print(f"Status: {result['status']}")
    print(f"MSE: {result['metrics'].get('mse', 'N/A'):.4f}")
    return result['metrics'].get('mse', float('inf'))


def test_cnn_lstm():
    """Test CNN-LSTM training."""
    print("\n" + "="*60)
    print("Testing CNN-LSTM Engine")
    print("="*60)
    
    df = generate_sample_dataset()
    cnn_lstm = CNNLSTMEngine()
    result = cnn_lstm.train(df, sequence_length=20, horizon=1, epochs=3, lr=0.001)
    
    print(f"Status: {result['status']}")
    print(f"MSE: {result['metrics'].get('mse', 'N/A'):.4f}")
    return result['metrics'].get('mse', float('inf'))


def test_gnn():
    """Test GNN Ensemble training."""
    print("\n" + "="*60)
    print("Testing GNN Ensemble")
    print("="*60)
    
    df = generate_sample_dataset()
    gnn = GNNEngine()
    result = gnn.train(df, sequence_length=20, horizon=1, epochs=3)
    
    print(f"Status: {result['status']}")
    print(f"MSE: {result['metrics'].get('mse', 'N/A'):.4f}")
    return result['metrics'].get('mse', float('inf'))


def test_xgboost():
    """Test XGBoost training."""
    print("\n" + "="*60)
    print("Testing XGBoost/Boosting Ensemble")
    print("="*60)
    
    df = generate_sample_dataset()
    boosting = BoostingEnsemble()
    result = boosting.train(df, sequence_length=20, horizon=1, epochs=3, rounds=50)
    
    print(f"Status: {result['status']}")
    print(f"MSE: {result['metrics'].get('mse', 'N/A'):.4f}")
    return result['metrics'].get('mse', float('inf'))


def test_multimodal_fusion():
    """Test Multimodal Fusion training."""
    print("\n" + "="*60)
    print("Testing Multimodal Fusion")
    print("="*60)
    
    df = generate_sample_dataset()
    fusion = MultimodalFusionEngine()
    result = fusion.train(df, epochs=3, lr=0.01)
    
    print(f"Status: {result['status']}")
    print(f"MSE: {result['metrics'].get('mse', 'N/A'):.4f}")
    return result['metrics'].get('mse', float('inf'))


def test_ensemble_controller():
    """Test Ensemble Intelligence Controller."""
    print("\n" + "="*60)
    print("Testing Ensemble Intelligence Controller")
    print("="*60)
    
    df = generate_sample_dataset()
    controller = EnsembleController()
    result = controller.train(df, sequence_length=20, horizon=1, epochs=3, lr=0.001)
    
    print(f"Status: {result['status']}")
    print(f"MSE: {result['metrics'].get('mse', 'N/A'):.4f}")
    print(f"Base models: {result['metrics'].get('base_models', [])}")
    return result['metrics'].get('mse', float('inf'))


def run_demo_pipeline():
    """Run demo training pipeline for all models."""
    print("\n" + "#"*60)
    print("# StockSageAI Training Stack Demo Pipeline")
    print("#"*60)
    print(f"Start time: {datetime.now().isoformat()}")
    
    results = {}
    
    try:
        results['Transformer Ensemble'] = test_transformer_ensemble()
    except Exception as e:
        print(f"Error: {e}")
        results['Transformer Ensemble'] = None
    
    try:
        results['LSTM'] = test_lstm()
    except Exception as e:
        print(f"Error: {e}")
        results['LSTM'] = None
    
    try:
        results['BiLSTM'] = test_bilstm()
    except Exception as e:
        print(f"Error: {e}")
        results['BiLSTM'] = None
    
    try:
        results['CNN-LSTM'] = test_cnn_lstm()
    except Exception as e:
        print(f"Error: {e}")
        results['CNN-LSTM'] = None
    
    try:
        results['GNN Ensemble'] = test_gnn()
    except Exception as e:
        print(f"Error: {e}")
        results['GNN Ensemble'] = None
    
    try:
        results['XGBoost'] = test_xgboost()
    except Exception as e:
        print(f"Error: {e}")
        results['XGBoost'] = None
    
    try:
        results['Multimodal Fusion'] = test_multimodal_fusion()
    except Exception as e:
        print(f"Error: {e}")
        results['Multimodal Fusion'] = None
    
    try:
        results['Ensemble Intelligence'] = test_ensemble_controller()
    except Exception as e:
        print(f"Error: {e}")
        results['Ensemble Intelligence'] = None
    
    print("\n" + "#"*60)
    print("# Summary of Results")
    print("#"*60)
    for model_name, mse in results.items():
        if mse is not None:
            print(f"{model_name:25s} - MSE: {mse:.4f}")
        else:
            print(f"{model_name:25s} - FAILED")
    
    best_model = min((k, v) for k, v in results.items() if v is not None)
    print(f"\nBest performing model: {best_model[0]} (MSE: {best_model[1]:.4f})")
    print(f"End time: {datetime.now().isoformat()}")


if __name__ == "__main__":
    run_demo_pipeline()
