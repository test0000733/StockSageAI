"""
Lightweight test suite for StockSageAI training stack.

Run with: python test_training_stack.py
"""

import sys
import os
import traceback
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import pandas as pd

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

test_results = []


def print_test(name, passed, message=""):
    """Print test result."""
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"  {status} {name}")
    if message:
        print(f"      {message}")
    test_results.append((name, passed))


def generate_sample_data(n=80):
    """Generate synthetic stock data."""
    dates = pd.date_range(end=datetime.now(), periods=n, freq='D')
    prices = 100 + np.cumsum(np.random.normal(0, 1, n))
    return pd.DataFrame({
        'Date': dates,
        'Open': prices + np.random.normal(0, 0.5, n),
        'High': prices + np.abs(np.random.normal(0, 1, n)),
        'Low': prices - np.abs(np.random.normal(0, 1, n)),
        'Close': prices,
        'Volume': np.random.randint(1000000, 5000000, n)
    })


# Test 1: Imports
print("\n" + "="*60)
print("Test Suite: StockSageAI Training Stack")
print("="*60)

print("\n[1/9] Testing Imports")
try:
    from StockSageAI.models.transformers import TransformerEnsemble
    print_test("TransformerEnsemble import", True)
except Exception as e:
    print_test("TransformerEnsemble import", False, str(e))

try:
    from StockSageAI.models.lstm_engine import LSTMEngine
    print_test("LSTMEngine import", True)
except Exception as e:
    print_test("LSTMEngine import", False, str(e))

try:
    from StockSageAI.models.bilstm_engine import BiLSTMEngine
    print_test("BiLSTMEngine import", True)
except Exception as e:
    print_test("BiLSTMEngine import", False, str(e))

try:
    from StockSageAI.models.cnn_lstm import CNNLSTMEngine
    print_test("CNNLSTMEngine import", True)
except Exception as e:
    print_test("CNNLSTMEngine import", False, str(e))

try:
    from StockSageAI.models.gnn_engine import GNNEngine
    print_test("GNNEngine import", True)
except Exception as e:
    print_test("GNNEngine import", False, str(e))

try:
    from StockSageAI.models.boosting import BoostingEnsemble
    print_test("BoostingEnsemble import", True)
except Exception as e:
    print_test("BoostingEnsemble import", False, str(e))

try:
    from StockSageAI.models.multimodal_fusion import MultimodalFusionEngine
    print_test("MultimodalFusionEngine import", True)
except Exception as e:
    print_test("MultimodalFusionEngine import", False, str(e))

try:
    from StockSageAI.models.ensemble_controller import EnsembleController
    print_test("EnsembleController import", True)
except Exception as e:
    print_test("EnsembleController import", False, str(e))

try:
    from StockSageAI.training_manager import manager
    print_test("TrainingManager import", True)
except Exception as e:
    print_test("TrainingManager import", False, str(e))

# Test 2: Data Pipeline
print("\n[2/9] Testing Data Pipeline")
try:
    from StockSageAI.feature_pipeline import FeaturePipeline
    df = generate_sample_data()
    fp = FeaturePipeline()
    features = fp.build_feature_matrix(df)
    assert not features.empty, "Feature matrix is empty"
    print_test("Feature Pipeline", True, f"Generated {len(features)} feature rows")
except Exception as e:
    print_test("Feature Pipeline", False, str(e))

try:
    from StockSageAI.regime_engine import RegimeEngine
    df = generate_sample_data()
    regime = RegimeEngine()
    result = regime.detect_regimes(df)
    assert result is not None, "Regime detection failed"
    print_test("Regime Detection", True, f"Identified {result.get('n_regimes', 0)} regimes")
except Exception as e:
    print_test("Regime Detection", False, str(e))

# Test 3: Individual Models
print("\n[3/9] Testing LSTM Model")
try:
    df = generate_sample_data()
    lstm = LSTMEngine()
    result = lstm.train(df, sequence_length=10, horizon=1, epochs=1, lr=0.001)
    assert result['status'] == 'ok', f"Training failed: {result}"
    assert 'mse' in result['metrics'], "MSE not in metrics"
    print_test("LSTM Training", True, f"MSE: {result['metrics']['mse']:.4f}")
except Exception as e:
    print_test("LSTM Training", False, str(e))
    traceback.print_exc()

print("\n[4/9] Testing BiLSTM Model")
try:
    df = generate_sample_data()
    bilstm = BiLSTMEngine()
    result = bilstm.train(df, sequence_length=10, horizon=1, epochs=1, lr=0.001)
    assert result['status'] == 'ok', f"Training failed: {result}"
    print_test("BiLSTM Training", True, f"MSE: {result['metrics']['mse']:.4f}")
except Exception as e:
    print_test("BiLSTM Training", False, str(e))

print("\n[5/9] Testing CNN-LSTM Model")
try:
    df = generate_sample_data()
    cnn_lstm = CNNLSTMEngine()
    result = cnn_lstm.train(df, sequence_length=10, horizon=1, epochs=1, lr=0.001)
    assert result['status'] == 'ok', f"Training failed: {result}"
    print_test("CNN-LSTM Training", True, f"MSE: {result['metrics']['mse']:.4f}")
except Exception as e:
    print_test("CNN-LSTM Training", False, str(e))

print("\n[6/9] Testing GNN Model")
try:
    df = generate_sample_data()
    gnn = GNNEngine()
    result = gnn.train(df, sequence_length=10, horizon=1, epochs=1)
    assert result['status'] == 'ok', f"Training failed: {result}"
    print_test("GNN Training", True, f"MSE: {result['metrics']['mse']:.4f}")
except Exception as e:
    print_test("GNN Training", False, str(e))

print("\n[7/9] Testing Boosting Model")
try:
    df = generate_sample_data()
    boosting = BoostingEnsemble()
    result = boosting.train(df, sequence_length=10, horizon=1, epochs=1, rounds=20)
    assert result['status'] == 'ok', f"Training failed: {result}"
    print_test("Boosting Training", True, f"MSE: {result['metrics']['mse']:.4f}")
except Exception as e:
    print_test("Boosting Training", False, str(e))

print("\n[8/9] Testing Multimodal Fusion")
try:
    df = generate_sample_data()
    fusion = MultimodalFusionEngine()
    result = fusion.train(df, epochs=1, lr=0.01)
    assert result['status'] == 'ok', f"Training failed: {result}"
    print_test("Multimodal Fusion", True, f"MSE: {result['metrics']['mse']:.4f}")
except Exception as e:
    print_test("Multimodal Fusion", False, str(e))

print("\n[9/9] Testing Ensemble Intelligence Controller")
try:
    df = generate_sample_data()
    controller = EnsembleController()
    result = controller.train(df, sequence_length=10, horizon=1, epochs=1, lr=0.001)
    assert result['status'] == 'ok', f"Training failed: {result}"
    print_test("Ensemble Controller", True, f"MSE: {result['metrics']['mse']:.4f}")
except Exception as e:
    print_test("Ensemble Controller", False, str(e))

# Summary
print("\n" + "="*60)
print("Test Summary")
print("="*60)

passed = sum(1 for _, p in test_results if p)
total = len(test_results)

print(f"\nTotal: {total} tests")
print(f"Passed: {GREEN}{passed}{RESET}")
print(f"Failed: {RED}{total - passed}{RESET}")

if passed == total:
    print(f"\n{GREEN}All tests passed! Training stack is ready.{RESET}")
    sys.exit(0)
else:
    print(f"\n{RED}{total - passed} test(s) failed.{RESET}")
    sys.exit(1)
