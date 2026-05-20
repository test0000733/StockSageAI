"""
Comprehensive System Health Check for StockSageAI 2.0

Tests:
1. All imports and dependencies
2. All 8 AI models
3. Training manager
4. Data pipeline
5. Admin dashboard
6. ML model training

Run with: python SYSTEM_HEALTH_CHECK.py
"""

import sys
import os
import traceback
from datetime import datetime
import logging

# Handle Windows encoding
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(__file__))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Color codes (disabled on Windows)
USE_COLORS = sys.platform != 'win32'
GREEN = '\033[92m' if USE_COLORS else ''
RED = '\033[91m' if USE_COLORS else ''
YELLOW = '\033[93m' if USE_COLORS else ''
BLUE = '\033[94m' if USE_COLORS else ''
RESET = '\033[0m' if USE_COLORS else ''

test_results = []
errors_found = []


def print_test(name, passed, message="", error_details=""):
    """Print test result."""
    status_text = "[PASS]" if passed else "[FAIL]"
    status = f"{GREEN}{status_text}{RESET}" if USE_COLORS else status_text
    print(f"  {status} {name}")
    if message:
        print(f"      {message}")
    if error_details:
        print(f"      {RED}Error: {error_details}{RESET}")
    test_results.append((name, passed))
    if not passed:
        errors_found.append({
            'test': name,
            'message': message,
            'error': error_details
        })


# Print header
print("\n" + "="*70)
print(f"{BLUE}StockSageAI 2.0 - System Health Check{RESET}")
print("="*70)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# ==================== SECTION 1: IMPORTS ====================
print(f"\n{BLUE}[1] Testing Core Imports{RESET}")
print("-" * 70)

try:
    import streamlit
    print_test("Streamlit", True, "v" + streamlit.__version__)
except Exception as e:
    print_test("Streamlit", False, "Required for dashboard", str(e))

try:
    import pandas as pd
    print_test("Pandas", True, f"v{pd.__version__}")
except Exception as e:
    print_test("Pandas", False, "Data manipulation required", str(e))

try:
    import numpy as np
    print_test("NumPy", True, f"v{np.__version__}")
except Exception as e:
    print_test("NumPy", False, "Numerical computing required", str(e))

try:
    from sklearn import __version__ as sklearn_version
    print_test("Scikit-learn", True, f"v{sklearn_version}")
except Exception as e:
    print_test("Scikit-learn", False, "ML pipeline required", str(e))

try:
    import yfinance
    print_test("yfinance", True, "Data fetching available")
except Exception as e:
    print_test("yfinance", False, "Data fetching library", str(e))

try:
    import plotly
    print_test("Plotly", True, "Visualization available")
except Exception as e:
    print_test("Plotly", False, "Visualization library", str(e))

# ==================== SECTION 2: DATA PIPELINE ====================
print(f"\n{BLUE}[2] Testing Data Pipeline{RESET}")
print("-" * 70)

try:
    from StockSageAI.feature_pipeline import FeaturePipeline
    print_test("Feature Pipeline import", True)
    
    # Test feature pipeline
    import pandas as pd
    np.random.seed(42)
    test_df = pd.DataFrame({
        'Date': pd.date_range(end=datetime.now(), periods=100, freq='D'),
        'Open': 100 + np.cumsum(np.random.normal(0, 0.5, 100)),
        'High': 102 + np.cumsum(np.random.normal(0, 0.5, 100)),
        'Low': 98 + np.cumsum(np.random.normal(0, 0.5, 100)),
        'Close': 100 + np.cumsum(np.random.normal(0, 0.5, 100)),
        'Volume': np.random.randint(1000000, 5000000, 100)
    })
    
    fp = FeaturePipeline()
    features = fp.build_feature_matrix(test_df)
    
    if not features.empty:
        print_test("Feature Pipeline Execution", True, f"Generated {len(features)} features")
    else:
        print_test("Feature Pipeline Execution", False, "Feature matrix is empty")
        
except Exception as e:
    print_test("Feature Pipeline", False, str(type(e).__name__), traceback.format_exc().split('\n')[-2])

try:
    from StockSageAI.regime_engine import RegimeEngine
    print_test("Regime Engine import", True)
    
    re = RegimeEngine()
    result = re.detect_regime(test_df)  # Fixed: singular "regime" not "regimes"
    
    if result is not None:
        regime_name = result.get('regime', 'Unknown')
        confidence = result.get('confidence', 0)
        print_test("Regime Detection", True, f"Detected: {regime_name} ({confidence}% confidence)")
    else:
        print_test("Regime Detection", False, "No regimes detected")
        
except Exception as e:
    print_test("Regime Engine", False, str(type(e).__name__), traceback.format_exc().split('\n')[-2])

# ==================== SECTION 3: AI MODELS ====================
print(f"\n{BLUE}[3] Testing AI Models (8/8){RESET}")
print("-" * 70)

models_to_test = [
    ('transformers', 'TransformerEnsemble', 'Transformer Ensemble'),
    ('lstm_engine', 'LSTMEngine', 'LSTM Engine'),
    ('bilstm_engine', 'BiLSTMEngine', 'BiLSTM Engine'),
    ('cnn_lstm', 'CNNLSTMEngine', 'CNN-LSTM Hybrid'),
    ('gnn_engine', 'GNNEngine', 'GNN Ensemble'),
    ('boosting', 'BoostingEnsemble', 'XGBoost/Boosting'),
    ('multimodal_fusion', 'MultimodalFusionEngine', 'Multimodal Fusion'),
    ('ensemble_controller', 'EnsembleController', 'Ensemble Controller'),
]

model_results = {}

for module_name, class_name, display_name in models_to_test:
    try:
        module = __import__(f'StockSageAI.models.{module_name}', fromlist=[class_name])
        Model = getattr(module, class_name)
        model_results[display_name] = {'import': True, 'status': 'Ready'}
        print_test(f"{display_name} import", True)
        
        # Try instantiation
        try:
            model_instance = Model()
            model_results[display_name]['instance'] = True
            print_test(f"{display_name} instantiation", True, "Model created successfully")
        except Exception as e:
            model_results[display_name]['instance'] = False
            print_test(f"{display_name} instantiation", False, "Failed to create instance", str(e)[:80])
            
    except Exception as e:
        model_results[display_name] = {'import': False, 'status': 'Failed'}
        print_test(f"{display_name} import", False, f"Module not found", str(e)[:80])

# ==================== SECTION 4: MODEL TRAINING ====================
print(f"\n{BLUE}[4] Testing Model Training (With Synthetic Data){RESET}")
print("-" * 70)

# Generate synthetic training data
np.random.seed(42)
synthetic_df = pd.DataFrame({
    'Date': pd.date_range(end=datetime.now(), periods=80, freq='D'),
    'Open': 100 + np.cumsum(np.random.normal(0, 1, 80)),
    'High': 102 + np.cumsum(np.random.normal(0, 1, 80)),
    'Low': 98 + np.cumsum(np.random.normal(0, 1, 80)),
    'Close': 100 + np.cumsum(np.random.normal(0, 1, 80)),
    'Volume': np.random.randint(1000000, 5000000, 80)
})

training_tests = [
    ('transformers', 'TransformerEnsemble', 'Transformer', {'epochs': 1, 'lr': 0.001}),
    ('lstm_engine', 'LSTMEngine', 'LSTM', {'epochs': 1, 'lr': 0.001, 'sequence_length': 10, 'horizon': 1}),
    ('bilstm_engine', 'BiLSTMEngine', 'BiLSTM', {'epochs': 1, 'lr': 0.001, 'sequence_length': 10, 'horizon': 1}),
    ('cnn_lstm', 'CNNLSTMEngine', 'CNN-LSTM', {'epochs': 1, 'lr': 0.001, 'sequence_length': 10, 'horizon': 1}),
    ('gnn_engine', 'GNNEngine', 'GNN', {'epochs': 1, 'sequence_length': 10, 'horizon': 1}),
    ('boosting', 'BoostingEnsemble', 'XGBoost', {'epochs': 1, 'rounds': 20, 'sequence_length': 10, 'horizon': 1}),
    ('multimodal_fusion', 'MultimodalFusionEngine', 'Multimodal', {'epochs': 1, 'lr': 0.01}),
    ('ensemble_controller', 'EnsembleController', 'Ensemble', {'epochs': 1, 'lr': 0.001, 'sequence_length': 10, 'horizon': 1}),
]

for module_name, class_name, display_name, train_params in training_tests:
    try:
        module = __import__(f'StockSageAI.models.{module_name}', fromlist=[class_name])
        Model = getattr(module, class_name)
        
        model = Model()
        result = model.train(synthetic_df, **train_params)
        
        if result.get('status') == 'ok':
            metrics = result.get('metrics', {})
            mse = metrics.get('mse', 'N/A')
            print_test(f"{display_name} Training", True, f"MSE: {mse:.4f}" if isinstance(mse, (int, float)) else f"MSE: {mse}")
        else:
            print_test(f"{display_name} Training", False, result.get('error', 'Training failed'))
            
    except Exception as e:
        print_test(f"{display_name} Training", False, "Training error", str(e)[:100])

# ==================== SECTION 5: TRAINING MANAGER ====================
print(f"\n{BLUE}[5] Testing Training Manager{RESET}")
print("-" * 70)

try:
    from StockSageAI.training_manager import manager
    print_test("Training Manager import", True)
    
    # Test job tracking - use correct parameters: path, progress, log, final=False, metrics=None
    test_job_id = "test_" + datetime.now().strftime('%Y%m%d_%H%M%S')
    test_path = f"StockSageAI/tmp/train_{test_job_id}.json"
    
    # Create tmp directory if needed
    import os
    os.makedirs("StockSageAI/tmp", exist_ok=True)
    
    manager._write_status(test_path, progress=50, log="Test progress message")
    
    # Try to read back
    import json
    if os.path.exists(test_path):
        with open(test_path, 'r') as f:
            status = json.load(f)
        print_test("Job Status Persistence", True, "Reading/writing job status works")
        # Clean up
        os.remove(test_path)
    else:
        print_test("Job Status Persistence", False, "Status file not created")
        
except Exception as e:
    print_test("Training Manager", False, "Manager test failed", str(e)[:100])

# ==================== SECTION 6: ADMIN DASHBOARD ====================
print(f"\n{BLUE}[6] Testing Admin Dashboard{RESET}")
print("-" * 70)

try:
    from StockSageAI.admin_ai_ui import render_admin_training_dashboard
    print_test("Admin UI import", True, "Dashboard component available")
except Exception as e:
    print_test("Admin UI import", False, "Dashboard component error", str(e)[:100])

# ==================== SECTION 7: AUTHENTICATION ====================
print(f"\n{BLUE}[7] Testing Authentication System{RESET}")
print("-" * 70)

try:
    from StockSageAI.auth import auth_manager
    print_test("Auth Manager import", True, "Authentication available")
except Exception as e:
    print_test("Auth Manager import", False, "Auth module error", str(e)[:100])

# ==================== SECTION 8: DATABASE ====================
print(f"\n{BLUE}[8] Testing Database Module{RESET}")
print("-" * 70)

try:
    from StockSageAI.database import Database
    print_test("Database import", True, "Database module available")
except Exception as e:
    print_test("Database import", False, "Database module error", str(e)[:100])

# ==================== SUMMARY ====================
print("\n" + "="*70)
print(f"{BLUE}Test Summary{RESET}")
print("="*70)

passed = sum(1 for _, p in test_results if p)
total = len(test_results)

print(f"\n{BLUE}Results:{RESET}")
print(f"  Passed: {GREEN}{passed}{RESET}/{total}")
print(f"  Failed: {RED}{total - passed}{RESET}/{total}")
print(f"  Success Rate: {GREEN}{(passed/total*100):.1f}%{RESET}")

if errors_found:
    print(f"\n{RED}Errors Found ({len(errors_found)}):{RESET}")
    for i, error in enumerate(errors_found, 1):
        print(f"\n  {i}. {error['test']}")
        if error['message']:
            print(f"     Message: {error['message']}")
        if error['error']:
            print(f"     Details: {error['error']}")
else:
    print(f"\n{GREEN}[OK] No errors found!{RESET}")

# ==================== MODEL TRAINING SUMMARY ====================
print(f"\n{BLUE}Model Training Summary:{RESET}")
print(f"  Total Models: 8")
passed_training = sum(1 for _, p in test_results if 'Training' in _ and p)
print(f"  Trained Successfully: {GREEN}{passed_training}{RESET}/8")

# Final status
print("\n" + "="*70)
if passed == total:
    print(f"{GREEN}[SUCCESS] ALL SYSTEMS OPERATIONAL{RESET}")
    print(f"{GREEN}[OK] All 8 models tested and working{RESET}")
    print(f"{GREEN}[OK] Training pipeline functional{RESET}")
    print(f"{GREEN}[OK] Website ready for deployment{RESET}")
    sys.exit(0)
else:
    print(f"{RED}[WARNING] Some tests failed - review errors above{RESET}")
    if total - passed <= 3:
        print(f"{YELLOW}[INFO] Minor issues may not affect core functionality{RESET}")
    sys.exit(1)

print("="*70 + "\n")
