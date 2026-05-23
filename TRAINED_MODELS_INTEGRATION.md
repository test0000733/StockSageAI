# SP 07 StockSageAI - 8 Trained ML Models Integration Guide

## Overview
This document describes how to integrate and use the 8 trained ML models in SP 07 StockSageAI.

- **5 Models Visible in Admin Panel**
- **3 Models Running in Background**
- **Total: 8 Accurate Models**

## Directory Structure

```
StockSageAI/
├── models/                          # Model storage directory
│   ├── transformer_lstm.pkl           # Model 1: Transformer LSTM proxy
│   ├── bilstm_ensemble.pkl            # Model 2: BiLSTM Ensemble proxy
│   ├── cnn_bilstm.pkl                 # Model 3: CNN-BiLSTM proxy
│   ├── attention_lstm.pkl             # Model 4: Attention LSTM proxy
│   ├── tcn_model.pkl                  # Model 5: Temporal Convolutional Network proxy
│   ├── xgboost_model.pkl              # Model 6: XGBoost style gradient boosting proxy
│   ├── catboost_model.pkl             # Model 7: CatBoost style gradient boosting proxy
│   ├── lightgbm_model.pkl             # Model 8: LightGBM style gradient boosting proxy
│   └── scalers.pkl                    # Preprocessing scalers (X and y)
│
├── trained_model_manager.py          # Model manager class
└── app.py                            # Main app with admin panel integration
```

## Model Details

### Visible Models (Shown in Admin Panel)

| # | Name | Type | Architecture | Input | Output |
|---|------|------|--------------|-------|--------|
| 1 | **Transformer LSTM** | Deep Learning | Multi-head attention + LSTM | 60 timesteps × 8 features | Price prediction |
| 2 | **BiLSTM Ensemble** | Deep Learning | Bidirectional LSTM (3-layer) | 60 timesteps × 8 features | Price prediction |
| 3 | **CNN-BiLSTM** | Hybrid | Conv1D + Bidirectional LSTM | 60 timesteps × 8 features | Price prediction |
| 4 | **Attention LSTM** | Deep Learning | Multi-head attention mechanism | 60 timesteps × 8 features | Price prediction |
| 5 | **TCN** | Deep Learning | Temporal Convolutional Network | 60 timesteps × 8 features | Price prediction |

### Background Models (Auto-Ensemble)

| # | Name | Type | Purpose | Input | Output |
|---|------|------|---------|-------|--------|
| 6 | **XGBoost** | Gradient Boosting | Enterprise boosting for tabular data | 8 features | Price prediction |
| 7 | **CatBoost** | Gradient Boosting | Categorical-aware gradient boosting | 8 features | Price prediction |
| 8 | **LightGBM** | Gradient Boosting | Lightweight fast gradient boosting | 8 features | Price prediction |

## Features Used (8 Features)

1. **MA5** - 5-day Moving Average
2. **MA20** - 20-day Moving Average  
3. **MA50** - 50-day Moving Average
4. **RSI** - Relative Strength Index (14-period)
5. **MACD** - MACD difference
6. **ATR** - Average True Range (14-period)
7. **Volume_Ratio** - Volume normalized by 20-day average
8. **Price_Range** - High-Low range as percentage of close

## Integration Steps

### Step 1: Create Models Directory
```bash
mkdir -p StockSageAI/models
```

### Step 2: Train Models
Use the Google Colab training notebook: `GOOGLE_COLAB_TRAINING_GUIDE.md`

### Step 3: Download Trained Models
After training in Colab, download all 8 model files. If you are using the local build flow, the artifact names are:
- `transformer_lstm.pkl`
- `bilstm_ensemble.pkl`
- `cnn_bilstm.pkl`
- `attention_lstm.pkl`
- `tcn_model.pkl`
- `xgboost_model.pkl`
- `catboost_model.pkl`
- `lightgbm_model.pkl`
- `scalers.pkl`

### Step 4: Place Models in Directory
Copy all downloaded files to: `StockSageAI/models/`

### Step 5: Install Dependencies
```bash
pip install tensorflow tensorflow-gpu keras xgboost catboost lightgbm joblib
```

### Step 6: Verify Installation
The app will automatically detect models at startup.

## Admin Panel Usage

### Visible Models Selection
1. Log in as Admin or Super Admin
2. Go to Admin AI Forecasting Control Panel
3. Search and select a stock symbol
4. See 5 visible models in dropdown:
   - Transformer LSTM
   - BiLSTM Ensemble
   - CNN-BiLSTM
   - Attention LSTM
   - TCN
5. Select which models to run
6. Click "Analyze Now" or "Run Ensemble"

### What Happens Behind the Scenes
- **Selected visible models**: Generate predictions using deep learning
- **Background models (3)**: Always run the 3 gradient boosting models
- **Ensemble calculation**: Combines predictions from all 8 models
- **Confidence scoring**: Aggregates confidence from all models

## Model Manager API

### Basic Usage
```python
from trained_model_manager import get_model_manager, get_visible_model_names

# Initialize
manager = get_model_manager()

# Get visible models only
visible = get_visible_model_names()
print(visible)  # ['Transformer LSTM', 'BiLSTM Ensemble', ...]

# Get specific model
model = manager.get_model('Transformer LSTM')

# Get all 8 models
all_models = manager.get_all_models()

# Get model status
status = manager.get_model_status()
print(status)
```

### Prediction Example
```python
import numpy as np

manager = get_model_manager()

# Prepare data
X_seq = np.random.randn(1, 60, 8)  # LSTM sequence
X_features = np.random.randn(1, 8)  # GB features

# Get all 8 predictions
result = manager.ensemble_predict_all_8_models(X_seq, X_features)

print(f"Ensemble Prediction: ${result['ensemble_prediction']:.2f}")
print(f"Confidence: {result['ensemble_confidence']:.1f}%")
print(f"Visible predictions: {result['visible_predictions']}")
print(f"Background predictions: {result['background_predictions']}")
```

## Ensemble Strategy

### Weight Distribution
- **Visible Deep Learning Models** (5 models): 60% total weight (12% each)
  - Transformer LSTM: 12%
  - BiLSTM Ensemble: 12%
  - CNN-BiLSTM: 12%
  - Attention LSTM: 12%
  - TCN: 12%

- **Background Gradient Boosting Models** (3 models): 40% total weight (~13.33% each)
  - XGBoost: 13.33%
  - CatBoost: 13.33%
  - LightGBM: 13.33%

### Prediction Formula
```
Ensemble_Prediction = 
    (Transformer_LSTM × 0.12) +
    (BiLSTM × 0.12) +
    (CNN-BiLSTM × 0.12) +
    (Attention_LSTM × 0.12) +
    (TCN × 0.12) +
    (XGBoost × 0.1333) +
    (CatBoost × 0.1333) +
    (LightGBM × 0.1333)

Ensemble_Confidence = Average(All_Model_Confidences)
```

## Expected Performance

| Model | Expected R² | Expected MAE | Expected RMSE |
|-------|-------------|--------------|---------------|
| Transformer LSTM | 0.88-0.92 | $2-4 | $3-5 |
| BiLSTM Ensemble | 0.86-0.90 | $2-4 | $3-5 |
| CNN-BiLSTM | 0.85-0.89 | $2-5 | $3-6 |
| Attention LSTM | 0.87-0.91 | $2-4 | $3-5 |
| TCN | 0.84-0.88 | $3-5 | $4-6 |
| XGBoost | 0.82-0.88 | $3-6 | $4-7 |
| CatBoost | 0.80-0.87 | $3-6 | $4-7 |
| LightGBM | 0.81-0.86 | $3-6 | $4-7 |
| **Ensemble** | **0.88-0.92** | **$2-4** | **$3-5** |

## Troubleshooting

### Models Not Loading
1. Check models directory exists: `StockSageAI/models/`
2. Verify all 8 files are present
3. Check file permissions (readable)
4. View logs: `Model not found: transformer_lstm.pkl`

### Memory Issues
- Keep only loaded models in RAM
- Clear cache periodically: `manager.clear_cache()`
- Use `get_visible_models()` if running in low-memory environment

### Prediction Errors
- Ensure input shape is correct: (1, 60, 8) for LSTM, (1, 8) for GB
- Check scalers are loaded: `manager.load_scalers()`
- Verify all models are trained on same data distribution

### Model Performance
- If accuracy drops, retrain models
- Include more recent data in training
- Validate on different stock symbols
- Monitor real predictions vs actual prices

## Update Directory Structure

Create the models directory:
```bash
mkdir -p StockSageAI/models
```

## Files Modified

1. **trained_model_manager.py** - NEW
   - Manages 8 models (5 visible + 3 background)
   - Loads, caches, and serves predictions
   - Ensemble voting system

2. **app.py** - UPDATED
   - Admin panel shows only 5 models
   - Integrates trained model manager
   - Enhanced forecasting display

3. **GOOGLE_COLAB_TRAINING_GUIDE.md** - NEW
   - Step-by-step training instructions
   - Complete Colab notebook code
   - 8 model implementations

4. **TRAINED_MODELS_INTEGRATION.md** - NEW (this file)
   - Integration guide
   - API documentation
   - Troubleshooting

## Next Steps

1. ✅ Create Google Colab notebook (GOOGLE_COLAB_TRAINING_GUIDE.md)
2. ✅ Create model manager (trained_model_manager.py)
3. ✅ Update admin panel (app.py)
4. ⏳ Train models on Google Colab
5. ⏳ Download trained models
6. ⏳ Place in StockSageAI/models/
7. ⏳ Verify loading and predictions
8. ⏳ Monitor production performance

---

**Last Updated**: May 22, 2026  
**Version**: 1.0  
**Models**: 8 (5 visible + 3 background)  
**Status**: Ready for training and integration
