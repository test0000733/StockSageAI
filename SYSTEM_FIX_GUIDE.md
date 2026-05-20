"""
COMPREHENSIVE SYSTEM FIX & TROUBLESHOOTING GUIDE
================================================

## ERRORS FIXED

### 1. "No data found for symbol" Error ❌ → ✅
**Problem:** 
- get_stock_data() would return empty DataFrame when validation passed
- No retry logic with alternative symbol formats
- Cache issues preventing data reload

**Solutions Implemented:**
- ✅ Added retry logic with 3 attempts per symbol
- ✅ Automatic fallback to .NS and .BO formats
- ✅ Better network error handling with delays
- ✅ Minimum data requirement checks (>10 days)

### 2. "Could not fetch time series data for this symbol" Error ❌ → ✅
**Problem:**
- No automatic symbol conversion before fetching
- Limited error messages
- Generic error handling

**Solutions Implemented:**
- ✅ Integrated get_stock_symbol() utility function
- ✅ Detailed error messages with suggestions
- ✅ Multiple fallback strategies
- ✅ Better user feedback

### 3. News Scraper Failures ❌ → ✅
**Problem:**
- Missing error handling for failed news fetches
- Empty sentiment analysis on missing news
- No graceful degradation

**Solutions Implemented:**
- ✅ Try-catch blocks in sentiment analyzer
- ✅ Validation before processing empty data
- ✅ Graceful fallback when no news available

### 4. LSTM Prediction Errors ❌ → ✅
**Problem:**
- Model training on insufficient data
- No fallback prediction method
- Unhandled exceptions during prediction

**Solutions Implemented:**
- ✅ Simple trend prediction fallback
- ✅ Better data validation before training
- ✅ Error handling at each forecast period

### 5. Recommendation Engine Failures ❌ → ✅
**Problem:**
- Crashes on incomplete data
- No default recommendation
- Missing error handling

**Solutions Implemented:**
- ✅ Try-catch blocks around all operations
- ✅ Safe default recommendations
- ✅ Graceful degradation

---

## HOW TO USE FIXED SYSTEM

### Quick Start:
```bash
# 1. Run diagnostic first to test system
streamlit run StockSageAI/diagnostic.py

# 2. If diagnostics pass, run main app
streamlit run StockSageAI/app.py

# 3. Try these symbols:
# - Indian: RELIANCE, TCS, INFY, HDFC (converted to .NS format)
# - Format: SYMBOL or SYMBOL.NS
```

### Testing Valid Symbols:
```
✅ RELIANCE.NS (automatic conversion works)
✅ RELIANCE (gets converted to RELIANCE.NS)
✅ TCS
✅ INFY
✅ HDFC
✅ AAPL (US stocks)
✅ MSFT (US stocks)
```

---

## TROUBLESHOOTING GUIDE

### Issue: Still getting "Symbol not found"
**Solution:**
1. Open `StockSageAI/utils.py`
2. Search for `name_to_symbol` dictionary
3. Add your symbol:
   ```python
   'YOUR_SYMBOL': 'YOUR_SYMBOL.NS',
   'FULL NAME': 'YOUR_SYMBOL.NS',
   ```

### Issue: "No data found" even for valid symbol
**Solution:**
1. Internet might be slow - wait a bit
2. Try: `python -c "import yfinance as yf; print(yf.Ticker('RELIANCE.NS').history(period='1d'))"`
3. If that works, clear Streamlit cache:
   ```bash
   rm -r ~/.streamlit/cache
   streamlit run app.py --logger.level=debug
   ```

### Issue: Forecasts not generating
**Solution:**
1. Check if you have minimum 30 days of data (see diagnostic)
2. Try with another symbol
3. Increase data period: Check app.py line 398 change `period="1y"` to `period="2y"`

### Issue: News/Sentiment not working
**Solution:**
1. This is optional - app works without it
2. Check internet connection
3. Try: `python -c "from StockSageAI.news_scraper import NewsScraper; print(NewsScraper().get_news('RELIANCE.NS'))"`

---

## FILES MODIFIED

1. **data_fetcher.py**
   - Added retry logic with exponential backoff
   - Automatic symbol format conversion
   - Better error handling

2. **app.py**
   - Integrated get_stock_symbol() for conversion
   - Detailed error messages
   - Better error handling around forecasting

3. **sentiment_analyzer.py**
   - Added error handling in analyze_sentiment()
   - Validation for empty inputs
   - Graceful degradation

4. **recommendation_engine.py**
   - Error handling in generate_recommendation()
   - Safe default values
   - Comprehensive try-catch blocks

---

## NEW FILES CREATED

1. **diagnostic.py**
   - Comprehensive system testing tool
   - Tests all modules
   - Provides detailed diagnostics

---

## CORE FEATURES NOW WORKING

✅ Symbol Recognition (auto-converts TCS → TCS.NS)
✅ Data Fetching (with retry logic)
✅ Data Validation (ensures sufficient data)
✅ 7/14/30 Day Forecasting (all periods working)
✅ Multi-Period Comparison (charts showing all 3 periods)
✅ AI Recommendations (BUY/SELL/HOLD for each period)
✅ News Sentiment Analysis (gracefully handles missing news)
✅ Excel Report Export (all data included)
✅ AI Advisory Section (multiple insights)
✅ Error Handling (graceful degradation)

---

## RECOMMENDED SYMBOLS FOR TESTING

**Indian Stocks (NSE):**
- RELIANCE (Oil & Gas leader)
- TCS (IT services)
- INFY (IT services)
- HDFC (Banking)
- ICICI (Banking)
- MARUTI (Automobiles)
- WIPRO (IT services)

**US Stocks:**
- AAPL (Apple)
- MSFT (Microsoft)
- GOOGL (Google)
- AMZN (Amazon)
- TSLA (Tesla)

---

## PERFORMANCE TIPS

1. **First run is slower** (model training) - be patient
2. **Use .NS suffix for Indian stocks** for faster validation
3. **Clear cache if data doesn't update**: 
   ```bash
   streamlit run app.py --logger.level=debug
   ```
4. **Run diagnostic first** to verify system is working

---

## IF PROBLEMS PERSIST

1. Check Python version: `python --version` (should be 3.8+)
2. Check all imports: `python -c "from StockSageAI.data_fetcher import DataFetcher"`
3. Test yfinance directly: `python -c "import yfinance as yf; print(yf.download('RELIANCE.NS', period='1d'))"`
4. Update packages: `pip install --upgrade yfinance pandas numpy streamlit plotly`

---

**Created:** May 14, 2026
**System Status:** ✅ All Known Issues Resolved
**Last Updated:** Today
