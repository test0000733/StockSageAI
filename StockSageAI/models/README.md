# Trained Models Directory

This directory contains the 8 trained ML models for SP 07 StockSageAI.

## Models to Download from Google Colab

After training models on Google Colab (see `GOOGLE_COLAB_TRAINING_GUIDE.md`), download these 8 files and place them in this directory:

### Deep Learning Models (Visible in Admin Panel)
1. `transformer_lstm.h5` - Transformer LSTM model
2. `bilstm_ensemble.h5` - Bidirectional LSTM ensemble
3. `cnn_bilstm.h5` - CNN-BiLSTM hybrid model
4. `attention_lstm.h5` - Multi-head attention LSTM
5. `tcn_model.h5` - Temporal Convolutional Network

### Gradient Boosting Models (Background Processing)
6. `xgboost_model.pkl` - XGBoost gradient boosting
7. `catboost_model.pkl` - CatBoost gradient boosting
8. `lightgbm_model.pkl` - LightGBM gradient boosting

### Supporting Files
9. `scalers.pkl` - Preprocessing scalers (MinMaxScaler for X and y)

## Expected File Sizes

| File | Size | Type |
|------|------|------|
| transformer_lstm.h5 | ~15-25 MB | Deep Learning |
| bilstm_ensemble.h5 | ~12-20 MB | Deep Learning |
| cnn_bilstm.h5 | ~10-18 MB | Deep Learning |
| attention_lstm.h5 | ~14-22 MB | Deep Learning |
| tcn_model.h5 | ~8-15 MB | Deep Learning |
| xgboost_model.pkl | ~5-10 MB | Gradient Boosting |
| catboost_model.pkl | ~8-15 MB | Gradient Boosting |
| lightgbm_model.pkl | ~3-8 MB | Gradient Boosting |
| scalers.pkl | ~1-2 MB | Preprocessing |

**Total Size**: ~75-135 MB

## How to Add Models

### Using Google Colab

1. Open Google Colab notebook with training code
2. Run all training cells
3. At the end, models are automatically saved to Colab instance
4. Download all 9 files (8 models + scalers)
5. Upload to this directory in the workspace

### Local Training (Optional)

If training locally instead of Colab:
```bash
python train_models.py
```

The training script will:
- Save models to `StockSageAI/models/`
- Save scalers to `StockSageAI/models/scalers.pkl`
- Generate model_metadata.json

## Verification

After placing models in this directory, verify they load correctly:

```python
from trained_model_manager import get_model_manager

manager = get_model_manager()
status = manager.get_model_status()

print(status)
# Should show all 8 models available
```

## Important Notes

- ✅ All models use the same feature set (8 features)
- ✅ All models use the same scalers
- ✅ All models are trained on 3+ years of historical data
- ✅ Admin panel automatically detects models on startup
- ✅ Missing models will be logged as warnings
- ⚠️ Do not delete or rename model files
- ⚠️ Keep scalers.pkl - it's required for predictions

## Training on Google Colab

See `GOOGLE_COLAB_TRAINING_GUIDE.md` for complete instructions with:
- Step-by-step setup
- Complete Python code for all 8 models
- Hyperparameter tuning
- Evaluation metrics
- Download instructions

## Storage Optimization

To reduce storage:
- Use `.png` compression for model visualizations (not stored here)
- Keep only the 9 essential files (8 models + scalers)
- Archive old model versions separately if needed

## Updates and Versions

Models should be updated:
- Weekly: When new training data becomes available
- When model performance degrades below threshold
- When new stocks are added to portfolio
- Quarterly: For seasonal adjustments

Keep version history if possible:
```
models/
├── transformer_lstm.h5 (current)
├── transformer_lstm_v1.h5 (backup)
├── transformer_lstm_v0.h5 (archive)
...
```

---

**Last Updated**: May 22, 2026  
**Models Needed**: 8 + scalers (9 total files)  
**Status**: Ready to receive trained models from Google Colab
