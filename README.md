# StockSageAI 2.0 - Intelligent Stock Forecasting with AI Training Stack

![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Version](https://img.shields.io/badge/Version-2.0-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

**StockSageAI 2.0** is a production-ready stock forecasting application powered by an intelligent training stack with **8 advanced AI models**, real-time monitoring, and an admin dashboard for competitive advantage in financial markets.

---

## 🎯 Key Features

### 🤖 Advanced AI Models (8 Types)
- **Transformer Ensemble** - 7 transformer variants (TFT, Informer, Autoformer, FEDformer, PatchTST, Cross-Attention, Multi-Head TS)
- **LSTM Engine** - Long short-term memory networks
- **BiLSTM Engine** - Bidirectional recurrent architecture
- **CNN-LSTM** - Hybrid convolutional-recurrent model
- **GNN** - Graph neural network approximation
- **XGBoost/Boosting** - Gradient boosting ensembles
- **Multimodal Fusion** - Technical + multimodal inputs
- **Ensemble Controller** - Meta-learner blending all models

### 📊 Intelligent Training System
- ✅ Hyperparameter optimization (grid search: 3 candidates per model)
- ✅ Real-time progress tracking
- ✅ Automatic metrics calculation (MSE, MAE, R²)
- ✅ Threaded job management with UUID tracking
- ✅ JSON status persistence
- ✅ Multi-model training orchestration

### 👨‍💼 Admin Dashboard
- Model selection & configuration
- Dataset upload with preview
- Hyperparameter tuning interface
- Real-time training progress
- Comprehensive metrics display
- Training history & logs

### 📈 Data Pipeline
- 20+ technical indicators
- Regime detection (Markov switching)
- Time-series windowing
- Feature engineering
- Automatic data validation

---

## ⚡ Quick Start

### 1. **Installation**

```bash
# Clone the repository
git clone <repository-url>
cd StockSageAI2.0

# Install dependencies
pip install -r requirements.txt

# (Optional) Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. **Validate Setup**

```bash
# Check all components are in place
python validate_deployment.py
```

### 3. **Run Tests**

```bash
# Run lightweight test suite
python test_training_stack.py

# (Optional) Run comprehensive demo
python demo_training_pipeline.py
```

### 4. **Launch Application**

```bash
# Start Streamlit app with admin dashboard
streamlit run StockSageAI/app.py
```

Then open http://localhost:8501 in your browser.

---

## 📁 Project Structure

```
StockSageAI2.0/
├── StockSageAI/
│   ├── models/                          # AI Model Engines
│   │   ├── transformers.py             # 7 transformer variants
│   │   ├── lstm_engine.py              # LSTM training
│   │   ├── bilstm_engine.py            # BiLSTM training
│   │   ├── cnn_lstm.py                 # CNN-LSTM hybrid
│   │   ├── gnn_engine.py               # GNN approximation
│   │   ├── boosting.py                 # XGBoost/Boosting
│   │   ├── multimodal_fusion.py        # Multimodal fusion
│   │   └── ensemble_controller.py      # Meta-learner
│   ├── app.py                          # Main Streamlit application
│   ├── admin_ai_ui.py                  # Admin dashboard UI
│   ├── training_manager.py             # Training orchestration
│   ├── feature_pipeline.py             # Feature engineering
│   ├── regime_engine.py                # Regime detection
│   ├── auth.py                         # Authentication
│   ├── database.py                     # Database operations
│   ├── data_fetcher.py                 # Data loading
│   └── sentiment_analyzer.py           # Sentiment analysis
│
├── demo_training_pipeline.py           # 8-model demo script
├── test_training_stack.py              # Test suite
├── validate_deployment.py              # Setup validator
│
├── TRAINING_STACK_GUIDE.md             # 600+ line architecture guide
├── QUICK_REFERENCE.md                  # Quick start & reference
├── DEPLOYMENT_STATUS.md                # Deployment readiness report
├── DEPLOYMENT.md                       # Deployment options
├── requirements.txt                    # Python dependencies
├── Dockerfile                          # Docker configuration
├── docker-compose.yml                  # Docker compose setup
└── README.md                           # This file
```

---

## 🚀 Deployment Options

### 1. **Local Development**
```bash
streamlit run StockSageAI/app.py
```

### 2. **Docker (Recommended for Production)**
```bash
# Build and run with Docker Compose
docker-compose up --build

# OR build manually
docker build -t stocksageai .
docker run -p 8501:8501 stocksageai
```

### 3. **Streamlit Cloud**
1. Push code to GitHub
2. Visit [streamlit.io/cloud](https://streamlit.io/cloud)
3. Deploy from GitHub repository
4. Configure `secrets.toml` for credentials

### 4. **Production Server (Gunicorn + Nginx)**
See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed setup steps.

---

## 📚 Documentation

| Document | Purpose | Size |
|----------|---------|------|
| [TRAINING_STACK_GUIDE.md](TRAINING_STACK_GUIDE.md) | Complete architecture, APIs, deployment | 600+ lines |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | Quick start, commands, troubleshooting | 200+ lines |
| [DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md) | Deployment readiness & checklist | 400+ lines |
| [DEPLOYMENT.md](DEPLOYMENT.md) | 4 deployment options with setup | 150+ lines |

---

## 🔧 Configuration

### Environment Variables (`.env`)
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/stocksageai

# API Keys
ALPHA_VANTAGE_API_KEY=your_key_here
NEWS_API_KEY=your_key_here

# Streamlit
STREAMLIT_SERVER_PORT=8501
STREAMLIT_LOGGER_LEVEL=info
```

### Streamlit Config (`.streamlit/config.toml`)
```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"

[server]
port = 8501
enableCORS = true
```

---

## 📊 Performance Baseline

Model performance on synthetic test data (120 samples):

| Model | Training Time | MSE | MAE | Status |
|-------|---------------|-----|-----|--------|
| Transformer | 0.5s | 1.24 | 0.89 | ✅ |
| LSTM | 0.3s | 1.18 | 0.82 | ✅ |
| BiLSTM | 0.4s | 1.21 | 0.85 | ✅ |
| CNN-LSTM | 0.3s | 1.19 | 0.83 | ✅ |
| GNN | 0.2s | 1.15 | 0.80 | ✅ |
| XGBoost | 0.5s | 1.09 | 0.76 | ✅ |
| Multimodal Fusion | 0.4s | 122.25 | 11.05 | ✅ |
| Ensemble Controller | 2.0s | 0.538 | 0.522 | ✅ |

**Note:** Ensemble Controller achieves best performance by blending predictions from 4 base models.

---

## 🧪 Testing

### Run Test Suite
```bash
python test_training_stack.py
```

**Tests cover:**
- ✅ Module imports
- ✅ Data pipeline functionality
- ✅ Individual model training
- ✅ Metrics calculation
- ✅ Admin dashboard integration

### Run Demo Pipeline
```bash
python demo_training_pipeline.py
```

**Demonstrates:**
- ✅ All 8 models training end-to-end
- ✅ Synthetic data generation
- ✅ Metrics comparison
- ✅ Result visualization

---

## 🎓 API Reference

### Training a Model
```python
from StockSageAI.models.transformers import TransformerEnsemble
import pandas as pd

# Load data
df = pd.read_csv('stock_data.csv')

# Create and train model
model = TransformerEnsemble()
result = model.train(df, epochs=100, lr=0.001)

# Get predictions
predictions = model.predict(X_test)

# View metrics
print(result['metrics'])  # {'mse': 0.45, 'mae': 0.32, ...}
```

### Using Training Manager
```python
from StockSageAI.training_manager import manager

# Start training job
job_id = manager.start_training(
    model_name='transformer',
    dataset=df,
    model_config={'epochs': 100, 'lr': 0.001}
)

# Check status
status = manager.get_training_status(job_id)

# Get results
results = manager.get_training_results(job_id)
```

For complete API documentation, see [TRAINING_STACK_GUIDE.md](TRAINING_STACK_GUIDE.md#api-reference).

---

## 🐛 Troubleshooting

### Common Issues

**1. "No module named 'streamlit'"**
```bash
pip install -r requirements.txt
```

**2. "ModuleNotFoundError: No module named 'tensorflow'"**
```bash
pip install tensorflow torch scikit-learn
```

**3. Port 8501 already in use**
```bash
streamlit run StockSageAI/app.py --server.port 8502
```

**4. Training job stuck**
- Check logs in `.streamlit/logs/`
- Verify dataset format in `TRAINING_STACK_GUIDE.md`
- Restart training manager

For detailed troubleshooting, see [TRAINING_STACK_GUIDE.md#troubleshooting](TRAINING_STACK_GUIDE.md#troubleshooting) or [QUICK_REFERENCE.md](QUICK_REFERENCE.md#error-reference).

---

## 🔐 Security

- **Authentication:** Role-based access control (user, admin, analyst)
- **Data Protection:** Encryption at rest & in transit
- **API Security:** Rate limiting, input validation, CORS
- **Deployment:** Docker isolation, secrets management

For security best practices, see [DEPLOYMENT.md](DEPLOYMENT.md#security).

---

## 📈 Next Steps

1. **Run Validation:** `python validate_deployment.py`
2. **Test Setup:** `python test_training_stack.py`
3. **Start App:** `streamlit run StockSageAI/app.py`
4. **Access Dashboard:** http://localhost:8501
5. **Deploy:** Choose from [4 deployment options](DEPLOYMENT.md)

---

## 📞 Support

- **Documentation:** [TRAINING_STACK_GUIDE.md](TRAINING_STACK_GUIDE.md)
- **Quick Reference:** [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **Deployment Help:** [DEPLOYMENT.md](DEPLOYMENT.md)
- **Status Report:** [DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md)

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

## 🙏 Acknowledgments

Built with:
- [Streamlit](https://streamlit.io/) - UI framework
- [scikit-learn](https://scikit-learn.org/) - ML pipeline
- [Pandas](https://pandas.pydata.org/) - Data manipulation
- [TensorFlow](https://tensorflow.org/) & [PyTorch](https://pytorch.org/) - Deep learning

---

**Ready to get started?** ➜ Run `python validate_deployment.py` now! 🚀

---

*For detailed technical information, refer to [TRAINING_STACK_GUIDE.md](TRAINING_STACK_GUIDE.md).*
