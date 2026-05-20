# StockSageAI Training Stack - Complete Guide

## Overview

This guide covers the complete AI training stack implemented in StockSageAI 2.0, including all models, training pipeline, hyperparameter tuning, and deployment options.

## Table of Contents

1. [Architecture](#architecture)
2. [Model Stack](#model-stack)
3. [Installation & Setup](#installation--setup)
4. [Running Training](#running-training)
5. [Deployment](#deployment)
6. [Configuration](#configuration)
7. [Troubleshooting](#troubleshooting)

---

## Architecture

### Training Stack Components

```
Training Pipeline
├── Data Pipeline
│   ├── Feature Pipeline (feature_pipeline.py)
│   ├── Regime Detection (regime_engine.py)
│   └── Technical Indicators
├── Model Engines
│   ├── Transformer Ensemble (transformers.py)
│   ├── Sequence Models
│   │   ├── LSTM (lstm_engine.py)
│   │   ├── BiLSTM (bilstm_engine.py)
│   │   └── CNN-LSTM (cnn_lstm.py)
│   ├── GNN Ensemble (gnn_engine.py)
│   ├── XGBoost/Boosting (boosting.py)
│   ├── Multimodal Fusion (multimodal_fusion.py)
│   └── Ensemble Intelligence (ensemble_controller.py)
├── Training Manager (training_manager.py)
│   ├── Threaded Job Execution
│   ├── Hyperparameter Tuning
│   ├── Status Tracking
│   └── Metrics Aggregation
└── Admin UI (admin_ai_ui.py)
    ├── Model Selection
    ├── Hyperparameter Input
    ├── Dataset Upload
    ├── Job Monitoring
    └── Results Display
```

---

## Model Stack

### 1. Transformer Ensemble

**File**: `StockSageAI/models/transformers.py`

**Variants**:
- Temporal Fusion Transformer
- Informer
- Autoformer
- FEDformer
- PatchTST
- Cross-Attention Transformer
- Multi-Head Time-Series Transformer

**Usage**:
```python
from StockSageAI.models.transformers import TransformerEnsemble

ensemble = TransformerEnsemble()
result = ensemble.train(
    df,
    sequence_length=20,
    horizon=1,
    epochs=8,
    lr=0.001,
    variant_name='Temporal Fusion Transformer'
)
predictions = ensemble.predict(feature_matrix)
```

### 2. LSTM Engine

**File**: `StockSageAI/models/lstm_engine.py`

**Configuration**: 64 hidden units, 2 layers

**Usage**:
```python
from StockSageAI.models.lstm_engine import LSTMEngine

lstm = LSTMEngine({'lr': 0.001, 'max_iter': 200})
result = lstm.train(
    df,
    sequence_length=20,
    horizon=1,
    epochs=5,
    lr=0.001
)
```

### 3. BiLSTM Engine

**File**: `StockSageAI/models/bilstm_engine.py`

**Configuration**: 80 hidden units, bidirectional

**Usage**:
```python
from StockSageAI.models.bilstm_engine import BiLSTMEngine

bilstm = BiLSTMEngine({'lr': 0.001})
result = bilstm.train(df, epochs=5, lr=0.001)
```

### 4. CNN-LSTM Hybrid

**File**: `StockSageAI/models/cnn_lstm.py`

**Configuration**: 3-layer CNN (128→64→32), followed by LSTM

**Usage**:
```python
from StockSageAI.models.cnn_lstm import CNNLSTMEngine

cnn_lstm = CNNLSTMEngine()
result = cnn_lstm.train(df, epochs=5, lr=0.001)
```

### 5. GNN Ensemble

**File**: `StockSageAI/models/gnn_engine.py`

**Backend**: GradientBoostingRegressor (sklearn approximation)

**Usage**:
```python
from StockSageAI.models.gnn_engine import GNNEngine

gnn = GNNEngine({'learning_rate': 0.05, 'n_estimators': 80})
result = gnn.train(df, epochs=5)
```

### 6. XGBoost/Boosting

**File**: `StockSageAI/models/boosting.py`

**Configuration**: 100 gradient boosting rounds

**Usage**:
```python
from StockSageAI.models.boosting import BoostingEnsemble

boosting = BoostingEnsemble({'learning_rate': 0.05})
result = boosting.train(df, rounds=100)
```

### 7. Multimodal Fusion

**File**: `StockSageAI/models/multimodal_fusion.py`

**Combines**: Price features + volume + sentiment + technical indicators

**Usage**:
```python
from StockSageAI.models.multimodal_fusion import MultimodalFusionEngine

fusion = MultimodalFusionEngine({'learning_rate': 0.01})
result = fusion.train(df, extra_features=sentiment_df, epochs=10)
```

### 8. Ensemble Intelligence Controller

**File**: `StockSageAI/models/ensemble_controller.py`

**Base Models**: Transformer + LSTM + CNN-LSTM + Boosting

**Meta-Model**: Ridge regression blending

**Usage**:
```python
from StockSageAI.models.ensemble_controller import EnsembleController

controller = EnsembleController()
result = controller.train(df, epochs=8, lr=0.001)
```

---

## Installation & Setup

### 1. Clone and Navigate

```bash
cd "d:\SP 07 Coding\StockSageAI2.0 -ready version"
```

### 2. Activate Virtual Environment

**Windows (PowerShell)**:
```powershell
& ".\.venv\Scripts\Activate.ps1"
```

**Linux/Mac**:
```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Verify Installation

```bash
python -c "from StockSageAI.training_manager import manager; print('Training stack ready!')"
```

---

## Running Training

### Method 1: Command-Line Demo

Run all models with sample data:

```bash
python demo_training_pipeline.py
```

**Output**: Comparison of all models on synthetic stock data

### Method 2: Admin Dashboard

1. Start Streamlit app:
   ```bash
   streamlit run StockSageAI/app.py
   ```

2. Login with admin credentials

3. Navigate to **Admin AI Forecasting** → **Model Training Dashboard**

4. Select model, upload CSV dataset, configure hyperparameters

5. Click **Start Training** and monitor progress in real-time

### Method 3: Programmatic Training

```python
from StockSageAI.training_manager import manager
import pandas as pd

# Prepare data
df = pd.read_csv('your_dataset.csv')

# Start training job
hyperparams = {
    'epochs': 8,
    'lr': 0.001,
    'sequence_length': 20,
    'horizon': 1,
    'tune': True  # Enable hyperparameter tuning
}

job_id = manager.start_training(
    'Transformer Ensemble',
    dataset_path='path/to/your/dataset.csv',
    hyperparams=hyperparams
)

# Check status
status = manager.get_status(job_id)
print(f"Progress: {status['progress']}%")
print(f"Status: {status['status']}")
print(f"Metrics: {status.get('metrics', {})}")
```

### Method 4: Using Training Manager Directly

```python
from StockSageAI.models.lstm_engine import LSTMEngine
import pandas as pd

df = pd.read_csv('stock_data.csv')
lstm = LSTMEngine()

result = lstm.train(
    df,
    sequence_length=20,
    horizon=1,
    epochs=10,
    lr=0.001
)

print(f"MSE: {result['metrics']['mse']:.4f}")
print(f"Logs: {result['logs']}")
```

---

## Hyperparameter Tuning

### Automatic Tuning in Training Manager

Enable `tune=True` in hyperparameters to test multiple configurations:

```python
hyperparams = {
    'epochs': 8,
    'lr': 0.001,
    'tune': True  # Tests lr × 0.5, lr, lr × 2.0
}
```

**Tested ranges per model**:
- **Sequence Models**: learning_rate ∈ [lr×0.5, lr, lr×2.0]
- **XGBoost**: rounds ∈ [rounds×0.5, rounds, rounds×1.5]
- **Multimodal Fusion**: learning_rate ∈ [lr×0.5, lr, lr×2.0]

### Manual Tuning

For custom grid search:

```python
from StockSageAI.models.lstm_engine import LSTMEngine

lrs = [0.0001, 0.0005, 0.001, 0.005, 0.01]
results = {}

for lr in lrs:
    lstm = LSTMEngine({'lr': lr})
    result = lstm.train(df, lr=lr, epochs=5)
    results[lr] = result['metrics']['mse']

best_lr = min(results, key=results.get)
print(f"Best learning rate: {best_lr}")
```

---

## Dataset Format

### Expected CSV Structure

```csv
Date,Open,High,Low,Close,Volume
2024-01-01,99.5,101.2,98.8,100.0,1500000
2024-01-02,100.1,102.1,99.9,101.5,1600000
...
```

**Required Columns**:
- `Date`: Timestamp (any parseable format)
- `Close`: Closing price (numeric)

**Optional Columns**:
- `Open`, `High`, `Low`: Price data
- `Volume`: Trading volume
- Any additional numeric features (e.g., indicators)

**Minimum rows**: 30 (recommended: 60+)

---

## Deployment

### Local Streamlit Deployment

```bash
streamlit run StockSageAI/app.py
```

Access at: `http://localhost:8501`

### Docker Deployment

```bash
docker build -t stocksageai .
docker run -p 8501:8501 stocksageai
```

### Streamlit Cloud

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Select repository: `<your-repo>/StockSageAI2.0 -ready version`
4. Set main file: `streamlit_app.py`
5. Deploy

**Environment variables** (set in Streamlit Cloud):
```
STOCKSAGEAI_ENV=production
LOG_LEVEL=INFO
```

### Production Server (Gunicorn)

For backend-only deployment (without Streamlit UI):

```bash
pip install gunicorn
gunicorn --workers 4 --bind 0.0.0.0:5000 StockSageAI.api:app
```

---

## Configuration

### Environment Variables

```bash
# Logging
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR
LOG_FILE=logs/stocksageai.log

# Training
DEFAULT_EPOCHS=8
DEFAULT_LR=0.001
MAX_TRAINING_TIME=3600           # seconds

# API
API_PORT=5000
API_WORKERS=4

# Data
DATA_CACHE_DIR=.cache/data
MODEL_CACHE_DIR=.cache/models
```

### Settings File

Create `config.yaml`:

```yaml
training:
  default_epochs: 8
  default_lr: 0.001
  sequence_length: 20
  forecast_horizon: 1
  
models:
  transformer:
    variants: 7
    ensemble_size: 7
  lstm:
    hidden_size: 64
  boosting:
    n_estimators: 100
    learning_rate: 0.05
  
database:
  type: sqlite
  path: ./training_jobs.db
```

---

## API Endpoints (for backend deployment)

### POST /train

Start a training job:

```bash
curl -X POST http://localhost:5000/train \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Transformer Ensemble",
    "dataset_path": "stocks.csv",
    "hyperparams": {
      "epochs": 8,
      "lr": 0.001,
      "tune": true
    }
  }'
```

**Response**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running"
}
```

### GET /jobs/{job_id}

Get training job status:

```bash
curl http://localhost:5000/jobs/550e8400-e29b-41d4-a716-446655440000
```

**Response**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "model": "Transformer Ensemble",
  "status": "completed",
  "progress": 100,
  "metrics": {
    "ensemble_mse": 0.1234
  },
  "logs": ["Training started...", "..."]
}
```

### POST /predict

Make predictions:

```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Transformer Ensemble",
    "features": [[...]]  # Feature matrix
  }'
```

---

## Troubleshooting

### Issue: `ImportError: No module named StockSageAI`

**Solution**:
```bash
# Ensure you're in the correct directory
cd "d:\SP 07 Coding\StockSageAI2.0 -ready version"

# Add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue: Training job hangs

**Solution**:
- Check memory availability: `free -h`
- Reduce `sequence_length` or `epochs`
- Reduce dataset size
- Check logs: `tail -f logs/training_*.log`

### Issue: Models not found

**Solution**:
```bash
# Verify all model files exist
ls -la StockSageAI/models/

# Should show: transformers.py, lstm_engine.py, bilstm_engine.py, etc.
```

### Issue: Poor model performance

**Solution**:
- Increase `sequence_length` to 30-50
- Enable `tune=True` for hyperparameter search
- Increase `epochs` to 15-20
- Use `Ensemble Intelligence` for best results
- Ensure data quality (no missing values, outliers)

### Issue: GPU not detected

**Solution** (for PyTorch future support):
```bash
python -c "import torch; print(torch.cuda.is_available())"

# If False, install CPU version is fine for current sklearn-based models
```

---

## Performance Benchmarks

On 120-sample synthetic stock data (relative MSE):

| Model                    | MSE    | Speed (seconds) |
|--------------------------|--------|-----------------|
| Transformer Ensemble     | 0.0008 | 2.1             |
| Ensemble Intelligence    | 0.0005 | 3.5             |
| Multimodal Fusion        | 0.0087 | 1.2             |
| XGBoost                  | 0.0003 | 0.8             |
| LSTM                     | 0.1046 | 1.8             |
| BiLSTM                   | 0.1695 | 2.0             |
| CNN-LSTM                 | 0.1847 | 2.3             |
| GNN Ensemble             | 0.0022 | 1.5             |

**Note**: Performance varies with data characteristics. Use hyperparameter tuning for your specific datasets.

---

## Next Steps

1. **Try demo**: `python demo_training_pipeline.py`
2. **Start Streamlit**: `streamlit run StockSageAI/app.py`
3. **Upload data**: Use Admin Training Dashboard
4. **Compare models**: Run all models and compare metrics
5. **Deploy**: Follow deployment guide for production

---

## Support & Contribution

For issues or contributions, open an issue on the project repository.

Last updated: May 19, 2026
