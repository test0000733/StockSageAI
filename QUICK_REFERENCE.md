# Quick Start & Deployment Checklist

## Quick Start (5 minutes)

### Step 1: Activate Environment
```bash
cd "d:\SP 07 Coding\StockSageAI2.0 -ready version"
# Windows PowerShell:
& ".\.venv\Scripts\Activate.ps1"
# Or Linux/Mac:
source .venv/bin/activate
```

### Step 2: Run Demo
```bash
python demo_training_pipeline.py
```

Expected output:
```
============================================================
Testing Transformer Ensemble
============================================================
Status: ok
MSE: 0.1234
Logs: 5 entries
...
```

### Step 3: Start Dashboard
```bash
streamlit run StockSageAI/app.py
```

Visit: `http://localhost:8501`

---

## Testing Checklist

- [ ] Import checks: `python -c "from StockSageAI.training_manager import manager; print('OK')"`
- [ ] Demo pipeline: `python demo_training_pipeline.py`
- [ ] Streamlit app: `streamlit run StockSageAI/app.py`
- [ ] Admin login: Use admin credentials
- [ ] Model selection: All 8 models available
- [ ] Data upload: CSV file accepted
- [ ] Training start: Job ID generated
- [ ] Status tracking: Progress updates
- [ ] Metrics display: Final MSE shown

---

## Deployment Paths

### Path 1: Local Development
```bash
streamlit run StockSageAI/app.py
# Access: http://localhost:8501
```

### Path 2: Docker
```bash
docker build -t stocksageai .
docker run -p 8501:8501 stocksageai
```

### Path 3: Streamlit Cloud
1. Push to GitHub
2. Go to share.streamlit.io
3. Select repo & deploy
4. Auto-updates on push

### Path 4: Production Server
```bash
pip install gunicorn
gunicorn --workers 4 --bind 0.0.0.0:5000 stocksageai_api:app
```

---

## File Structure

```
StockSageAI/
├── app.py                    # Main Streamlit app
├── admin_ai_ui.py            # Admin dashboard
├── training_manager.py       # Training orchestrator
├── models/
│   ├── transformers.py       # Transformer ensemble
│   ├── lstm_engine.py        # LSTM
│   ├── bilstm_engine.py      # BiLSTM
│   ├── cnn_lstm.py           # CNN-LSTM
│   ├── gnn_engine.py         # GNN
│   ├── boosting.py           # XGBoost
│   ├── multimodal_fusion.py  # Multimodal fusion
│   ├── ensemble_controller.py# Ensemble blending
│   └── __pycache__/
├── feature_pipeline.py       # Feature engineering
├── regime_engine.py          # Regime detection
├── tmp/                      # Training data & jobs
└── __init__.py

demo_training_pipeline.py     # Demo script
TRAINING_STACK_GUIDE.md       # Full documentation
QUICK_REFERENCE.md            # This file
```

---

## Common Commands

### Train a specific model
```python
from StockSageAI.models.transformers import TransformerEnsemble
import pandas as pd

df = pd.read_csv('stocks.csv')
ensemble = TransformerEnsemble()
result = ensemble.train(df, epochs=8, lr=0.001)
print(f"MSE: {result['metrics']['ensemble_mse']:.4f}")
```

### Check training status
```python
from StockSageAI.training_manager import manager

status = manager.get_status('job-id-here')
print(f"Progress: {status['progress']}%")
print(f"Metrics: {status['metrics']}")
```

### Compare all models
```bash
python demo_training_pipeline.py
# Shows performance comparison
```

### Enable hyperparameter tuning
```python
hyperparams = {
    'epochs': 8,
    'lr': 0.001,
    'tune': True  # Tests 3 LR values
}
job_id = manager.start_training('LSTM', hyperparams=hyperparams)
```

---

## Dataset Requirements

**CSV Format**:
```csv
Date,Close,Volume,Open,High,Low
2024-01-01,100.0,1500000,99.5,101.2,98.8
2024-01-02,101.5,1600000,100.1,102.1,99.9
```

**Requirements**:
- At least 30 rows (60+ recommended)
- `Close` column required
- `Date` column with parseable dates
- Numeric values only
- No missing values in Close column

---

## Performance Tips

1. **Use Ensemble Intelligence** for best results (slower but more accurate)
2. **Enable tuning** for production models (`tune=True`)
3. **Increase sequence_length** to 30-50 for stability
4. **Use 15-20 epochs** for final training
5. **Try multimodal fusion** if you have extra features

---

## Error Messages & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `ImportError: No module named StockSageAI` | Wrong directory | `cd` to correct folder, check PYTHONPATH |
| `TypeError: Cannot cast DatetimeArray to float` | Date column in features | Auto-fixed; ignore or filter dates |
| `NotFittedError: Pipeline not fitted` | Using untrained model | Call `.train()` before `.predict()` |
| `ConvergenceWarning` | Model needs more iterations | Normal; increase `epochs` if needed |
| `OutOfMemory` | Too much data/large model | Reduce `sequence_length` or `epochs` |

---

## Monitoring Dashboard

In Streamlit app, go to:
- **Admin AI Forecasting** → **Model Training Dashboard**

Features:
- Real-time progress bar
- Live metrics display
- Training logs
- Status updates

---

## Next Tasks

1. ✅ Create demo pipeline
2. ✅ Write documentation
3. Deploy to production
4. Integrate real market data
5. Add sentiment analysis
6. Build web API

---

Version: 1.0  
Last updated: May 19, 2026
