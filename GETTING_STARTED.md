# 🚀 Getting Started with StockSageAI 2.0

Welcome to StockSageAI 2.0! This guide will have you up and running in **5 minutes**.

---

## ⚡ 5-Minute Quick Start

### Step 1: Validate Your Setup (30 seconds)
```bash
cd "d:\SP 07 Coding\StockSageAI2.0 -ready version"
python validate_deployment.py
```

**Expected output:** `✓ Deployment Checks PASSED`

If you see any ✗ marks, install dependencies:
```bash
pip install -r requirements.txt
```

---

### Step 2: Run the Test Suite (1 minute)
```bash
python test_training_stack.py
```

**Expected output:** All tests pass ✓

This verifies all 8 models are working correctly.

---

### Step 3: Run the Demo (2 minutes)
```bash
python demo_training_pipeline.py
```

**Expected output:** All 8 models training with metrics table

This shows all models in action with performance comparisons.

---

### Step 4: Launch the Application (1 minute)
```bash
streamlit run StockSageAI/app.py
```

**Expected output:**
```
Streamlit app is running on http://localhost:8501
```

Open http://localhost:8501 in your browser.

---

## 🎯 What You've Got

### 8 AI Models Ready to Use
1. **Transformer Ensemble** - State-of-the-art transformer with 7 variants
2. **LSTM** - Long short-term memory networks
3. **BiLSTM** - Bidirectional LSTM for context awareness
4. **CNN-LSTM** - Hybrid convolutional-recurrent
5. **GNN** - Graph neural network approximation
6. **XGBoost** - Gradient boosting power
7. **Multimodal Fusion** - Technical + multimodal inputs
8. **Ensemble Controller** - Best overall performance (MSE 0.538)

### Admin Dashboard Features
- ✅ Select from 8 models
- ✅ Upload stock data
- ✅ Configure hyperparameters
- ✅ Watch real-time training progress
- ✅ View detailed metrics
- ✅ Access training history

---

## 📖 Where to Find What

| I Want To... | Read This File |
|-------------|-----------------|
| Understand the architecture | [TRAINING_STACK_GUIDE.md](TRAINING_STACK_GUIDE.md) |
| Deploy to production | [DEPLOYMENT.md](DEPLOYMENT.md) |
| Look up a quick command | [QUICK_REFERENCE.md](QUICK_REFERENCE.md) |
| Check project status | [DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md) |
| See build summary | [BUILD_COMPLETE.md](BUILD_COMPLETE.md) |
| General info | [README.md](README.md) |

---

## 💡 Common Tasks

### Upload Your Own Data
1. Open http://localhost:8501
2. Go to "Admin Dashboard"
3. Click "Upload Dataset"
4. Select CSV file (must have: Date, Open, High, Low, Close, Volume)
5. Click "Preview to verify"

### Train a Model
1. Select model from dropdown (e.g., "Ensemble Controller")
2. Adjust hyperparameters (or use defaults)
3. Click "Start Training"
4. Watch progress bar in real-time
5. View results when complete

### Compare Models
```bash
python demo_training_pipeline.py
```
This runs all 8 models and shows comparison table.

### Deploy to Production
Choose one:

**Option 1: Docker (Recommended)**
```bash
docker-compose up
```

**Option 2: Streamlit Cloud**
1. Push to GitHub
2. Connect to Streamlit Cloud
3. Deploy in seconds

**Option 3: Production Server**
See [DEPLOYMENT.md](DEPLOYMENT.md) for setup

---

## 🔍 Available Commands

```bash
# Validation & Testing
python validate_deployment.py    # Check setup
python test_training_stack.py    # Run tests
python demo_training_pipeline.py # Run demo

# Run Application
streamlit run StockSageAI/app.py

# Docker
docker-compose up               # Run with Docker
docker-compose down             # Stop Docker

# View Logs
tail -f .streamlit/logs/2025-*.log
```

---

## 🎓 Training Your First Model

### Using Admin Dashboard (Easiest)
1. Start app: `streamlit run StockSageAI/app.py`
2. Load CSV dataset
3. Select "Transformer" model
4. Click "Start Training"
5. Wait for completion
6. View metrics

### Using Command Line
```python
from StockSageAI.models.transformers import TransformerEnsemble
import pandas as pd

# Load data
df = pd.read_csv('stock_data.csv')

# Create model
model = TransformerEnsemble()

# Train
result = model.train(df, epochs=100, lr=0.001)

# Predict
predictions = model.predict(X_test)

# Check metrics
print(result['metrics'])
```

### Using Training Manager
```python
from StockSageAI.training_manager import manager
import pandas as pd

df = pd.read_csv('stock_data.csv')

# Start job
job_id = manager.start_training(
    model_name='ensemble',
    dataset=df,
    model_config={'epochs': 100, 'lr': 0.001}
)

# Monitor
status = manager.get_training_status(job_id)
print(f"Progress: {status['progress']}%")

# Get results
results = manager.get_training_results(job_id)
print(results['metrics'])
```

---

## 📊 Understanding Results

When training completes, you'll see metrics:

| Metric | Meaning | Good Value |
|--------|---------|-----------|
| MSE | Mean Squared Error (lower is better) | < 1.0 |
| MAE | Mean Absolute Error (lower is better) | < 0.8 |
| R² | Coefficient of determination (higher is better) | > 0.8 |
| Correlation | Price correlation (higher is better) | > 0.9 |

**Best Model:** Ensemble Controller typically achieves MSE ~0.538

---

## 🆘 Troubleshooting

### "ModuleNotFoundError: No module named 'streamlit'"
```bash
pip install -r requirements.txt
```

### "Port 8501 already in use"
```bash
streamlit run StockSageAI/app.py --server.port 8502
```

### "Training is slow"
- Use smaller dataset (< 500 samples) for testing
- Reduce epochs (e.g., epochs=10)
- Try GNN model (fastest)

### "Memory error during training"
- Reduce batch size
- Use fewer samples
- Reduce model complexity (use LSTM instead of Transformer)

For more troubleshooting, see [QUICK_REFERENCE.md](QUICK_REFERENCE.md#error-reference).

---

## 📚 Learning Path

**Beginner (This Time)**
1. ✅ Run quick start (5 min)
2. ✅ Try dashboard (2 min)
3. ✅ Upload sample data (2 min)

**Intermediate (Next)**
1. Read [TRAINING_STACK_GUIDE.md](TRAINING_STACK_GUIDE.md)
2. Understand model architecture
3. Experiment with hyperparameters
4. Compare model performance

**Advanced (Mastery)**
1. Customize models
2. Add new model types
3. Integrate with live data
4. Deploy to production

---

## ✅ Deployment Options

### 1. **Local (Development)**
```bash
streamlit run StockSageAI/app.py
```
- Best for: Testing, development
- Access: http://localhost:8501

### 2. **Docker (Recommended)**
```bash
docker-compose up
```
- Best for: Consistent environment
- Deploy anywhere with Docker

### 3. **Streamlit Cloud (Free)**
- Push code to GitHub
- Connect Streamlit account
- Deploy with one click

### 4. **Production Server**
- Full control
- Scaling capabilities
- Advanced monitoring
- See [DEPLOYMENT.md](DEPLOYMENT.md) for setup

---

## 📞 Quick Help

| Problem | Solution |
|---------|----------|
| Tests failing | Run `pip install -r requirements.txt` |
| Can't import models | Check Python path with `python -c "import sys; print(sys.path)"` |
| Dashboard not loading | Restart with `streamlit run StockSageAI/app.py --logger.level=debug` |
| Training too slow | Reduce epochs or use GNN model |
| Out of memory | Use smaller dataset |

---

## 🎉 You're Ready!

**Next Step:** Run validation command now!

```bash
python validate_deployment.py
```

Then pick a deployment option from [4 choices](DEPLOYMENT.md).

---

## 📖 Full Documentation

- [TRAINING_STACK_GUIDE.md](TRAINING_STACK_GUIDE.md) - Complete technical guide
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Quick lookup
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment options
- [README.md](README.md) - Project overview
- [DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md) - Status report
- [BUILD_COMPLETE.md](BUILD_COMPLETE.md) - Build summary

---

**Happy forecasting! 📈**

*For detailed information, refer to the full documentation guides listed above.*
