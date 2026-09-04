# Telegram Daily Stock Forecast System - Complete Implementation Guide

**Status:** ✅ **PRODUCTION READY**  
**Version:** 1.0  
**Date:** September 4, 2026  
**Last Updated:** 2026-09-04

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Components](#components)
4. [Installation & Setup](#installation--setup)
5. [Configuration](#configuration)
6. [Usage](#usage)
7. [API Endpoints](#api-endpoints)
8. [Database Schema](#database-schema)
9. [Testing](#testing)
10. [Troubleshooting](#troubleshooting)
11. [Features & Capabilities](#features--capabilities)

---

## 🎯 Overview

The **Telegram Daily Stock Forecast System** is a production-ready solution that:

✅ Generates AI-powered price forecasts for India's Top 10 stocks  
✅ Sends beautiful, structured Telegram messages daily at **10:15 AM IST**  
✅ Integrates seamlessly with the existing StockSageAI forecasting pipeline  
✅ Validates data freshness and detects prediction anomalies  
✅ Tracks model performance metrics (MAE, RMSE, MAPE, Directional Accuracy)  
✅ Provides admin dashboard controls for manual forecasts and testing  
✅ Handles failures gracefully with retry logic and logging  
✅ Supports Indian market holidays and weekend skipping  
✅ Stores all forecasts in SQLite database for historical analysis  

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  TELEGRAM FORECAST SYSTEM                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            TELEGRAM MANAGER (Orchestrator)           │   │
│  │  - Coordinates all components                        │   │
│  │  - Manages forecast workflow                         │   │
│  └──────────────────────────────────────────────────────┘   │
│                         ⬇️                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │    FORECAST SCHEDULER (10:15 AM IST Daily)           │   │
│  │  - Validates trading day                            │   │
│  │  - Handles idempotency                              │   │
│  │  - Skips weekends & holidays                        │   │
│  └──────────────────────────────────────────────────────┘   │
│                         ⬇️                                    │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              FORECAST GENERATION PIPELINE              │ │
│  │                                                         │ │
│  │  ┌──────────────────┐  ┌──────────────────────────┐   │ │
│  │  │ Stock Selector   │→│ Forecast Generator       │   │ │
│  │  │ (Top 10)         │  │ (7D, 14D, 30D using ML)  │   │ │
│  │  └──────────────────┘  └──────────────────────────┘   │ │
│  │         ⬇️                         ⬇️                    │ │
│  │  ┌──────────────────────────────────────────────────┐  │ │
│  │  │  Validation Layer                               │  │ │
│  │  │  - Data freshness check                         │  │ │
│  │  │  - Anomaly detection                           │  │ │
│  │  │  - Confidence scoring                          │  │ │
│  │  └──────────────────────────────────────────────────┘  │ │
│  └─────────────────────────────────────────────────────────┘ │
│                         ⬇️                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │     TELEGRAM MESSAGE FORMATTING & DELIVERY            │   │
│  │                                                         │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │ Notifier     │→│ TG Service   │→│ Telegram API  │  │   │
│  │  │ (Format)     │  │ (Send)       │  │ (Send/Retry) │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
│                         ⬇️                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         DATABASE STORAGE & TRACKING                   │   │
│  │  - Forecast history                                  │   │
│  │  - Notification delivery status                     │   │
│  │  - Model performance metrics                        │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Components

### 1. **telegram_service.py**
Secure Telegram API wrapper with retry logic and error handling.

**Key Features:**
- Secure credential management (bot token, chat ID)
- Message sending with 3-attempt retry logic
- Connection testing and validation
- Chat ID verification
- Long message splitting (Telegram 4096 char limit)
- Rate limit handling with exponential backoff

```python
from StockSageAI.telegram_service import get_telegram_service

service = get_telegram_service()
success, msg_id = service.send_message("Your message")
```

---

### 2. **stock_selector.py**
Dynamic Top 10 Indian stock selection based on market factors.

**Selection Criteria:**
- Market capitalization
- Trading volume & liquidity
- Price momentum (7-day returns)
- Volatility (technical stability)
- Data quality & freshness
- NSE/BSE availability

**Methods:**
- `get_top_10_stocks(use_dynamic=True)` - Get selected stocks
- `validate_stocks(stocks)` - Validate stock accessibility
- `get_stock_metadata(symbol)` - Get stock information

---

### 3. **forecast_generator.py**
Integrated with existing LSTMPredictor pipeline.

**Workflow:**
1. Fetch validated market data (120 days)
2. Analyze sentiment from news headlines
3. Generate 7D, 14D, 30D forecasts using LSTM
4. Generate BUY/HOLD/SELL signals
5. Validate predictions for anomalies
6. Calculate confidence scores

**Methods:**
- `generate_forecast(symbol)` - Single stock forecast
- `generate_batch_forecasts(symbols)` - Multiple stocks

---

### 4. **forecast_scheduler.py**
Daily scheduling at 10:15 AM IST with trading day validation.

**Features:**
- Timezone-aware scheduling (Asia/Kolkata)
- Indian market holiday detection
- Weekend skipping
- Idempotency protection (once per day)
- Exponential backoff retry logic

**Trading Day Checks:**
- Excludes Saturdays & Sundays
- Excludes all Indian stock market holidays
- Validates actual trading day status

---

### 5. **telegram_notifier.py**
Beautiful message formatting for Telegram.

**Message Types:**
- Daily forecast report (structured format)
- Test message (connection verification)
- Preview message (non-delivery preview)
- Status message (system health)
- Error message (failure notifications)

**Example Output:**
```
📊 AI DAILY STOCK FORECAST

📅 Date: 04 Sep 2026
🕙 Generated: 10:15 AM IST
📡 Data: 2026-09-04T17:30:00

🏆 TOP 10 STOCK FORECASTS

1️⃣RELIANCE
Current: ₹2,850.50

📈 7D: ₹2,891.25 (+1.43%)
📈 14D: ₹2,945.60 (+3.33%)
📈 30D: ₹3,012.40 (+5.68%)

Signal: 🟢 BUY
Confidence: 78.5%

⚠️ DISCLAIMER
...
```

---

### 6. **telegram_api.py**
RESTful API endpoints for Telegram operations.

**Endpoints:**
```
POST /api/telegram/test          - Test connection
POST /api/telegram/send-forecast - Send daily forecast
GET  /api/telegram/status        - Get system status
POST /api/telegram/preview       - Preview forecast
POST /api/telegram/run-manual    - Trigger manual forecast
```

**Example Usage:**
```python
from StockSageAI.telegram_api import get_telegram_api

api = get_telegram_api()
result = api.test_telegram_connection()
print(result)  # {'success': True, 'message': '✅ Connected...'}
```

---

### 7. **forecast_scheduler.py**
Daily execution at 10:15 AM IST with idempotency.

**Key Features:**
- Background thread support
- Clean startup/shutdown
- Graceful error handling
- Detailed logging
- Manual trigger support

---

### 8. **telegram_manager.py**
Main orchestrator that coordinates all components.

**Key Methods:**
- `start_scheduler()` - Begin daily scheduling
- `generate_and_send_forecast()` - Execute forecast job
- `get_system_status()` - Get health status
- `test_telegram()` - Connection test
- `preview_forecast()` - Message preview

---

### 9. **telegram_dashboard.py**
Streamlit admin UI for forecast management.

**Features:**
- System status monitoring
- Telegram connection testing
- Manual forecast triggering
- Forecast preview without sending
- Forecast history viewing
- Model performance metrics
- Configuration display

---

## 🚀 Installation & Setup

### 1. Prerequisites

```bash
# Python 3.8+
python --version

# Required dependencies already installed via requirements.txt:
# - python-dotenv (environment variable management)
# - schedule (cron-like scheduling)
# - requests (HTTP library)
# - pytz (timezone support)
```

### 2. Install New Dependencies

```bash
cd "d:\SP 07 Coding\StockSageAI2.0 -ready version"
pip install -r requirements.txt
```

### 3. Configuration

Create/verify `.env` file in project root:

```bash
# .env
TELEGRAM_BOT_TOKEN=8738215622:AAHhD3wYHOUGD4r-yg3V8sX7OgmdpqBN1oU
TELEGRAM_CHAT_ID=5435787568

FORECAST_ENABLED=true
FORECAST_SCHEDULE_TIME=10:15
FORECAST_TIMEZONE=Asia/Kolkata
FORECAST_CONFIDENCE_THRESHOLD=60.0
USE_ENSEMBLE=true
TOP_10_UPDATE_FREQUENCY=daily
TOP_10_SELECTION_METHOD=dynamic
LOG_LEVEL=INFO
```

### 4. Verify Installation

```bash
python test_telegram_system.py
```

Expected output: **✅ 8/8 tests passed - System is ready!**

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | - | Telegram bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | - | Chat/Group/Channel ID for sending forecasts |
| `FORECAST_ENABLED` | true | Enable/disable forecast system |
| `FORECAST_SCHEDULE_TIME` | 10:15 | Daily run time (HH:MM format) |
| `FORECAST_TIMEZONE` | Asia/Kolkata | Timezone for scheduling |
| `FORECAST_CONFIDENCE_THRESHOLD` | 60.0 | Min confidence to send forecast |
| `USE_ENSEMBLE` | true | Use ensemble models for prediction |
| `TOP_10_UPDATE_FREQUENCY` | daily | Refresh Top 10 selection |
| `TOP_10_SELECTION_METHOD` | dynamic | dynamic or static |
| `LOG_LEVEL` | INFO | Logging level |

### Trading Days Configuration

The system automatically verifies trading days by:
1. Excluding weekends (Saturday-Sunday)
2. Checking 70+ pre-configured Indian market holidays
3. Supporting dynamic holiday updates

**To add a holiday:**

Edit `forecast_scheduler.py` and add to `INDIAN_MARKET_HOLIDAYS`:
```python
INDIAN_MARKET_HOLIDAYS = [
    ...
    (2026, 9, 14),  # New holiday
]
```

---

## 📖 Usage

### Option 1: Run Scheduler (Production)

```bash
python start_telegram_scheduler.py
```

This runs the scheduler indefinitely at 10:15 AM IST daily.

### Option 2: Run in Streamlit Admin Dashboard

1. Start Streamlit app:
```bash
streamlit run StockSageAI/app.py
```

2. Login as Admin
3. Navigate to Admin Dashboard
4. Click "📨 Telegram Daily Forecast System" tab
5. Use the controls to test, preview, or run forecasts manually

### Option 3: Programmatic Usage

```python
from StockSageAI.telegram_manager import get_telegram_forecast_manager

# Initialize manager
manager = get_telegram_forecast_manager()

# Test connection
status = manager.test_telegram()
print(status)

# Send test message
result = manager.send_test_message()
print(result)

# Generate and send forecast (manual)
success = manager.send_manual_forecast()
print(f"Forecast sent: {success}")

# Preview forecast (without sending)
preview = manager.preview_forecast()
print(preview['preview_message'])

# Get system status
status = manager.get_system_status()
print(f"Telegram: {status['telegram_connection']}")
print(f"Scheduler: {status['scheduler_status']}")
print(f"Next run: {status['next_scheduled_run']}")
```

---

## 🔌 API Endpoints

These endpoints can be integrated into your backend API framework (FastAPI, Flask, etc.):

### Test Telegram Connection

```python
POST /api/telegram/test

Response:
{
    "success": true,
    "message": "✅ Connected to bot @nexusglobalasset_bot",
    "timestamp": "2026-09-04T18:30:00",
    "bot_info": {
        "chat_id": 5435787568,
        "type": "private",
        "title": "Personal"
    }
}
```

### Send Test Message

```python
POST /api/telegram/send-test

Response:
{
    "success": true,
    "message_id": "123",
    "error": null,
    "timestamp": "2026-09-04T18:30:00"
}
```

### Send Daily Forecast

```python
POST /api/telegram/send-forecast
Body: {"forecasts": {...}}

Response:
{
    "success": true,
    "message_ids": ["123", "124"],
    "stocks_sent": 10,
    "stocks_failed": 0,
    "error": null,
    "timestamp": "2026-09-04T18:30:00"
}
```

### Get System Status

```python
GET /api/telegram/status

Response:
{
    "telegram_connection": "Connected",
    "scheduler_status": "Active",
    "next_scheduled_run": "2026-09-05 10:15 IST",
    "last_successful_run": "2026-09-04",
    "last_failed_run": null,
    "is_enabled": true,
    "schedule_time": "10:15",
    "timezone": "Asia/Kolkata",
    "trading_day_today": true
}
```

### Preview Forecast

```python
POST /api/telegram/preview
Body: {"forecasts": {...}}

Response:
{
    "success": true,
    "preview_message": "📊 AI DAILY STOCK FORECAST\n...",
    "message_length": 2541,
    "chunks_needed": 1,
    "stocks_previewed": 10
}
```

### Run Manual Forecast

```python
POST /api/telegram/run-manual

Response:
{
    "success": true,
    "message": "Forecast generated and sent",
    "timestamp": "2026-09-04T18:30:00"
}
```

---

## 📊 Database Schema

### telegram_forecast_history
Stores all generated forecasts for historical analysis.

```sql
CREATE TABLE telegram_forecast_history (
    id INTEGER PRIMARY KEY,
    forecast_date DATE NOT NULL,
    symbol TEXT NOT NULL,
    current_price REAL NOT NULL,
    forecast_7d REAL,
    forecast_14d REAL,
    forecast_30d REAL,
    signal_7d TEXT,
    signal_14d TEXT,
    signal_30d TEXT,
    confidence_7d REAL,
    confidence_14d REAL,
    confidence_30d REAL,
    sentiment_score REAL,
    model_version TEXT,
    data_timestamp DATETIME,
    actual_price_7d REAL,  -- Updated later for accuracy
    actual_price_14d REAL,
    actual_price_30d REAL,
    accuracy_7d REAL,
    accuracy_14d REAL,
    accuracy_30d REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(forecast_date, symbol)
);
```

### telegram_notification_history
Tracks all Telegram delivery attempts.

```sql
CREATE TABLE telegram_notification_history (
    id INTEGER PRIMARY KEY,
    notification_date DATE NOT NULL,
    notification_type TEXT DEFAULT 'daily_forecast',
    status TEXT NOT NULL,  -- 'sent', 'failed', 'retrying'
    stocks_sent INTEGER,
    stocks_failed INTEGER,
    message_ids TEXT,
    telegram_chat_id TEXT,
    sent_timestamp DATETIME,
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    created_at DATETIME,
    updated_at DATETIME,
    UNIQUE(notification_date, notification_type)
);
```

### telegram_model_performance
Historical model accuracy metrics by stock/horizon.

```sql
CREATE TABLE telegram_model_performance (
    id INTEGER PRIMARY KEY,
    model_name TEXT NOT NULL,
    symbol TEXT NOT NULL,
    forecast_horizon INTEGER NOT NULL,
    mae REAL,                    -- Mean Absolute Error
    rmse REAL,                   -- Root Mean Squared Error
    mape REAL,                   -- Mean Absolute Percentage Error
    directional_accuracy REAL,   -- % of correct direction predictions
    sample_count INTEGER,
    evaluation_date DATE,
    created_at DATETIME,
    UNIQUE(model_name, symbol, forecast_horizon, evaluation_date)
);
```

---

## 🧪 Testing

### Run Comprehensive Tests

```bash
python test_telegram_system.py
```

**Tests Include:**
- Environment configuration (✅)
- Module imports (✅)
- Telegram connection (✅)
- Telegram chat validation (✅)
- Test message sending (✅)
- Forecast generation (✅)
- Scheduler initialization (✅)
- Database operations (✅)

### Expected Output

```
✅ PASS - Environment
✅ PASS - Imports
✅ PASS - Telegram Connection
✅ PASS - Telegram Chat
✅ PASS - Test Message
✅ PASS - Forecast Generation
✅ PASS - Scheduler
✅ PASS - Database

Total: 8/8 tests passed
✅ ALL TESTS PASSED - System is ready!
```

### Manual Testing via Admin Dashboard

1. Go to Telegram section → **Status** tab
   - Verify all statuses show green checkmarks

2. Go to **Test** tab
   - Click "🧪 Test Connection" → Should show ✅ Connected
   - Click "📨 Send Test Message" → Should see message ID

3. Go to **Send** tab
   - Click "📊 Preview Forecast" → Should show formatted message
   - Click "🔄 Run Forecast Now" → Should send real forecast

---

##🐛 Troubleshooting

### Issue: "TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env"

**Solution:**
1. Create `.env` file in project root
2. Add your credentials:
```bash
TELEGRAM_BOT_TOKEN=xxxxxxxxxxxxx:xxxxxxxxxxxxxxxxxxx
TELEGRAM_CHAT_ID=123456789
```

### Issue: "❌ Unauthorized (401): Invalid bot token"

**Solution:**
1. Verify token from @BotFather
2. Check for typos/extra spaces in .env
3. Ensure token hasn't been revoked

### Issue: "❌ Bad request (400): Invalid chat ID"

**Solution:**
1. Double-check chat ID:
   - For groups: Add @RawDataBot, look for "chat"
   - For channels: Forward message to @userinfobot
   - For personal: Send message to @RawDataBot
2. Ensure negative sign (-) for groups
3. Don't include @username, use numeric ID only

### Issue: "⚠️ Data is N days old (may be stale)"

**Solution:**
- System detected data older than 2 days
- Check if market was closed (weekend/holiday)
- Manually refresh data source if needed

### Issue: "❌ No valid forecasts could be generated"

**Solution:**
1. Check stock validity:
   ```bash
   python -c "from StockSageAI.stock_selector import get_stock_selector; s = get_stock_selector(); print(s.validate_stocks(['INFY.NS', 'TCS.NS']))"
   ```
2. Check market data availability
3. Verify LSTM model can load

### Issue: "⏸️ Already executed today, skipping"

**Solution:**
- System has idempotency protection (once per day)
- Use admin "Run Forecast Now" button to trigger manual runs
- Wait until next trading day for automatic execution

### Common Error Logs

| Log | Meaning | Solution |
|-----|---------|----------|
| ⚠️ Data is N days old | Stale data detected | Wait for market data | 
| ⚠️ Stock not foundated | Invalid symbol | Check NSE/BSE format |
| ❌ Rate limited | API throttling | Wait and retry |
|❌ Forecast confidence too low | Model uncertainty | Check data quality |

---

## ✨ Features & Capabilities

### ✅ Implemented Features

- [x] Daily scheduling at 10:15 AM IST
- [x] Top 10 stock dynamic selection
- [x] 7/14/30-day forecasting using LSTMPredictor
- [x] BUY/HOLD/SELL signal generation
- [x] Confidence scoring with validation
- [x] Trading day detection + holiday skipping
- [x] Telegram message formatting & delivery
- [x] Retry logic with exponential backoff
- [x] Message idempotency (once per day)
- [x] Admin dashboard controls
- [x] Database storage (forecasts, notifications, metrics)
- [x] Sentiment analysis integration
- [x] Model performance tracking
- [x] Error handling & detailed logging
- [x] Comprehensive test suite
- [x] Production-ready code

### 🔮 Future Enhancements (Optional)

- [ ] Multi-language message support
- [ ] Customizable forecast horizons
- [ ] Portfolio-based recommendations
- [ ] Risk metrics in forecast messages
- [ ] Webhook integration for external alerts
- [ ] Email/SMS fallback notifications
- [ ] A/B testing framework for signals
- [ ] Real-time accuracy tracking
- [ ] Machine learning for message optimization
- [ ] Advanced charting in Telegram messages

---

## 📞 Support & Monitoring

### Log Files

Daily execution logs are saved to:
```
telegram_forecast.log
```

View recent logs:
```bash
tail -100 telegram_forecast.log
```

### Health Monitoring

Check system health:
```python
from StockSageAI.telegram_manager import get_telegram_forecast_manager

manager = get_telegram_forecast_manager()
status = manager.get_system_status()

print(f"Telegram: {status['telegram_connection']}")
print(f"Scheduler: {status['scheduler_status']}")
print(f"Next run: {status['next_scheduled_run']}")
```

### Database Inspection

```sql
-- View recent forecasts
SELECT * FROM telegram_forecast_history 
WHERE forecast_date = DATE('now') 
ORDER BY created_at DESC;

-- View notification history
SELECT * FROM telegram_notification_history 
ORDER BY notification_date DESC LIMIT 10;

-- View model performance
SELECT * FROM telegram_model_performance 
WHERE evaluation_date >= DATE('now', '-7 days');
```

---

## 📝 License & Attribution

**System:** StockSageAI 2.0  
**Component:** Telegram Daily Forecast System  
**Status:** Production Ready  
**Version:** 1.0  
**Last Updated:** September 4, 2026  

---

## ✅ Verification Checklist

Before deploying to production:

- [ ] .env file created with valid credentials
- [ ] All tests pass: `python test_telegram_system.py`
- [ ] Test message received in Telegram
- [ ] Admin dashboard shows all green
- [ ] Database tables created successfully
- [ ] Logs show no critical errors
- [ ] Top 10 stocks validating correctly
- [ ] Forecast generation completes < 2 minutes
- [ ] Telegram message sends successfully
- [ ] Scheduler starts without errors
- [ ] Documentation reviewed

---

## 🎉 You're All Set!

The Telegram Daily Stock Forecast System is now ready for production use.

**Next Steps:**
1. ✅ Verify .env configuration
2. ✅ Run test_telegram_system.py
3. ✅ Send test message via admin dashboard
4. ✅ Schedule daily execution: `python start_telegram_scheduler.py`
5. ✅ Monitor logs and performance

**Congratulations!** Your AI-powered stock forecasts will now be delivered to Telegram every trading day at 10:15 AM IST. 🚀

---

For support or questions, refer to the troubleshooting section above or review the inline code documentation in each module.

**Happy forecasting!** 📈
