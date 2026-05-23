# Trained Models Directory

This directory contains the 8 trained ML models for SP 07 StockSageAI.

## Models to Add

The current artifact names are saved using lightweight pickle format for local model loading.

### Deep Learning / Sequence Models (Visible in Admin Panel)
1. `transformer_lstm.pkl` - Transformer LSTM model proxy
2. `bilstm_ensemble.pkl` - Bidirectional LSTM ensemble model proxy
3. `cnn_bilstm.pkl` - CNN-BiLSTM hybrid model proxy
4. `attention_lstm.pkl` - Attention LSTM model proxy
5. `tcn_model.pkl` - Temporal Convolutional Network model proxy

### Gradient Boosting Models (Background Processing)
6. `xgboost_model.pkl` - XGBoost-style gradient boosting model proxy
7. `catboost_model.pkl` - CatBoost-style gradient boosting model proxy
8. `lightgbm_model.pkl` - LightGBM-style gradient boosting model proxy

### Supporting Files
9. `scalers.pkl` - Preprocessing scalers (StandardScaler for X and y)

## Expected File Sizes

| File | Size | Type |
|------|------|------|
| transformer_lstm.pkl | ~1-3 MB | Sequence model proxy |
| bilstm_ensemble.pkl | ~1-2 MB | Sequence model proxy |
| cnn_bilstm.pkl | ~1-3 MB | Sequence model proxy |
| attention_lstm.pkl | ~1-2 MB | Sequence model proxy |
| tcn_model.pkl | ~1-2 MB | Sequence model proxy |
| xgboost_model.pkl | ~0.2-0.5 MB | Gradient boosting proxy |
| catboost_model.pkl | ~0.2-0.5 MB | Gradient boosting proxy |
| lightgbm_model.pkl | ~0.2-0.5 MB | Gradient boosting proxy |
| scalers.pkl | ~0.1-0.3 MB | Preprocessing |

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
python build_trained_models.py
```

The training script will:
- Save models to `StockSageAI/models/`
- Save scalers to `StockSageAI/models/scalers.pkl`
- Generate `model_metadata.json`

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
├── transformer_lstm.pkl (current)
├── transformer_lstm_v1.pkl (backup)
├── transformer_lstm_v0.pkl (archive)
...
```

---

**Last Updated**: May 22, 2026  
**Models Needed**: 8 + scalers (9 total files)  
**Status**: Ready to receive trained models from Google Colab
