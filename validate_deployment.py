"""
Deployment Validation Script for StockSageAI Training Stack

This script performs pre-deployment checks to ensure all components are ready.

Run with: python validate_deployment.py
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def check_file(path, description):
    """Check if a file exists."""
    exists = os.path.exists(path)
    status = f"{GREEN}✓{RESET}" if exists else f"{RED}✗{RESET}"
    print(f"  {status} {description}: {path}")
    return exists


def check_directory(path, description):
    """Check if a directory exists."""
    exists = os.path.isdir(path)
    status = f"{GREEN}✓{RESET}" if exists else f"{RED}✗{RESET}"
    print(f"  {status} {description}: {path}")
    return exists


def check_module(module_name):
    """Check if a Python module can be imported."""
    try:
        __import__(module_name)
        print(f"  {GREEN}✓{RESET} {module_name}")
        return True
    except ImportError as e:
        print(f"  {RED}✗{RESET} {module_name}: {e}")
        return False


print("\n" + "="*70)
print("StockSageAI Deployment Validation")
print("="*70)

workspace_root = os.path.dirname(__file__)
stocksage_dir = os.path.join(workspace_root, 'StockSageAI')

# 1. File Structure
print(f"\n{BLUE}[1] Core Files{RESET}")
core_files = [
    ('app.py', 'Main Streamlit application'),
    ('requirements.txt', 'Python dependencies'),
    ('package.json', 'Node.js configuration'),
    ('Dockerfile', 'Docker container definition'),
    ('docker-compose.yml', 'Docker composition for local dev'),
]

core_ok = all(check_file(os.path.join(workspace_root, f), desc) for f, desc in core_files)

# 2. StockSageAI Package
print(f"\n{BLUE}[2] StockSageAI Package Structure{RESET}")
pkg_check = check_directory(stocksage_dir, 'Package directory')

core_modules = [
    ('__init__.py', 'Package init'),
    ('app.py', 'Main app'),
    ('auth.py', 'Authentication module'),
    ('database.py', 'Database module'),
    ('feature_pipeline.py', 'Feature engineering pipeline'),
    ('regime_engine.py', 'Regime detection engine'),
    ('training_manager.py', 'Training orchestration'),
    ('admin_ai_ui.py', 'Admin dashboard UI'),
]

modules_ok = all(check_file(os.path.join(stocksage_dir, f), desc) for f, desc in core_modules)

# 3. Model Engines
print(f"\n{BLUE}[3] Model Training Engines{RESET}")
model_engines = [
    ('models/transformers.py', 'Transformer Ensemble (7 variants)'),
    ('models/lstm_engine.py', 'LSTM Engine'),
    ('models/bilstm_engine.py', 'BiLSTM Engine'),
    ('models/cnn_lstm.py', 'CNN-LSTM Hybrid'),
    ('models/gnn_engine.py', 'GNN Ensemble'),
    ('models/boosting.py', 'XGBoost/Boosting Engine'),
    ('models/multimodal_fusion.py', 'Multimodal Fusion Engine'),
    ('models/ensemble_controller.py', 'Ensemble Intelligence Controller'),
]

engines_ok = all(check_file(os.path.join(stocksage_dir, f), desc) for f, desc in model_engines)

# 4. Demo & Test Files
print(f"\n{BLUE}[4] Demo & Testing Infrastructure{RESET}")
demo_files = [
    ('demo_training_pipeline.py', 'Comprehensive demo with all 8 models'),
    ('test_training_stack.py', 'Lightweight test suite'),
    ('validate_deployment.py', 'This validation script'),
]

demo_ok = all(check_file(os.path.join(workspace_root, f), desc) for f, desc in demo_files)

# 5. Documentation
print(f"\n{BLUE}[5] Documentation{RESET}")
docs = [
    ('TRAINING_STACK_GUIDE.md', 'Comprehensive training stack guide (600+ lines)'),
    ('QUICK_REFERENCE.md', 'Quick reference & quick start (200+ lines)'),
    ('README.md', 'Project README'),
    ('DEPLOYMENT.md', 'Deployment options'),
]

docs_ok = all(check_file(os.path.join(workspace_root, f), desc) for f, desc in docs)

# 6. Dependencies Check
print(f"\n{BLUE}[6] Required Python Packages{RESET}")
required_packages = [
    'streamlit',
    'pandas',
    'numpy',
    'scikit-learn',
    'tensorflow',
    'torch',
    'requests',
]

packages_ok = all(check_module(pkg) for pkg in required_packages)

# 7. Configuration
print(f"\n{BLUE}[7] Configuration Files{RESET}")
config_files = [
    ('.streamlit/config.toml', 'Streamlit config (optional)'),
    ('.env', 'Environment variables (optional)'),
]

for f, desc in config_files:
    path = os.path.join(workspace_root, f)
    exists = os.path.exists(path)
    status = f"{GREEN}✓{RESET}" if exists else f"{YELLOW}⊘{RESET}"
    print(f"  {status} {desc}: {path} {'(optional)' if not exists else ''}")

# 8. Summary & Recommendations
print("\n" + "="*70)
print("Deployment Readiness Assessment")
print("="*70)

checks = {
    'Core Files': core_ok,
    'Package Structure': modules_ok and pkg_check,
    'Model Engines': engines_ok,
    'Demo & Tests': demo_ok,
    'Documentation': docs_ok,
    'Dependencies': packages_ok,
}

print()
for check_name, result in checks.items():
    status = f"{GREEN}✓ Ready{RESET}" if result else f"{RED}✗ Needs Attention{RESET}"
    print(f"  {check_name}: {status}")

all_ready = all(checks.values())

print("\n" + "-"*70)
if all_ready:
    print(f"{GREEN}✓ Deployment Checks PASSED{RESET}")
    print("\nNext Steps:")
    print("  1. Run test suite: python test_training_stack.py")
    print("  2. Run demo: python demo_training_pipeline.py")
    print("  3. Start Streamlit app: streamlit run StockSageAI/app.py")
    print("  4. Deploy using one of the options:")
    print("     - Local: streamlit run StockSageAI/app.py")
    print("     - Docker: docker-compose up")
    print("     - Cloud: see DEPLOYMENT.md")
    sys.exit(0)
else:
    print(f"{RED}✗ Deployment Checks FAILED{RESET}")
    print("\nReview the failed checks above and resolve issues before deployment.")
    sys.exit(1)
