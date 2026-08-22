import logging
import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st
from datetime import datetime, timedelta
import re

def format_currency(amount, currency_symbol="₹"):
    """Format currency amount with Indian rupee symbol"""
    if amount >= 10000000:  # 1 crore
        return f"{currency_symbol}{amount/10000000:.2f}Cr"
    elif amount >= 100000:  # 1 lakh
        return f"{currency_symbol}{amount/100000:.2f}L"
    elif amount >= 1000:  # 1 thousand
        return f"{currency_symbol}{amount/1000:.2f}K"
    else:
        return f"{currency_symbol}{amount:.2f}"

def get_stock_symbol(company_input):
    """
    Convert company name or symbol to proper stock exchange format (NSE/BSE)
    
    Args:
        company_input: Company name or symbol (e.g., 'TCS', 'RELIANCE', 'INFY')
    
    Returns:
        Valid stock symbol or None if not found
    """
    # Clean input
    company_input = company_input.strip().upper()
    
    # Remove any existing exchange suffixes
    if company_input.endswith('.NS'):
        company_input = company_input[:-3]
    elif company_input.endswith('.BSE'):
        company_input = company_input[:-4]
    elif company_input.endswith('.BO'):
        company_input = company_input[:-3]
    
    # Common company name to symbol mappings
    name_to_symbol = {
        'TCS': 'TCS.NS',
        'TATA CONSULTANCY SERVICES': 'TCS.NS',
        'INFOSYS': 'INFY.NS',
        'INFY': 'INFY.NS',
        'RELIANCE': 'RELIANCE.NS',
        'RELIANCE INDUSTRIES': 'RELIANCE.NS',
        'HDFC BANK': 'HDFCBANK.NS',
        'HDFCBANK': 'HDFCBANK.NS',
        'HDFC': 'HDFCBANK.NS',
        'ICICI BANK': 'ICICIBANK.NS',
        'ICICIBANK': 'ICICIBANK.NS',
        'ICICI': 'ICICIBANK.NS',
        'SBI': 'SBIN.NS',
        'STATE BANK OF INDIA': 'SBIN.NS',
        'BHARTI AIRTEL': 'BHARTIARTL.NS',
        'AIRTEL': 'BHARTIARTL.NS',
        'WIPRO': 'WIPRO.NS',
        'HCL TECH': 'HCLTECH.NS',
        'HCLTECH': 'HCLTECH.NS',
        'HCL': 'HCLTECH.NS',
        'ITC': 'ITC.NS',
        'HINDUSTAN UNILEVER': 'HINDUNILVR.NS',
        'HUL': 'HINDUNILVR.NS',
        'MARUTI': 'MARUTI.NS',
        'MARUTI SUZUKI': 'MARUTI.NS',
        'BAJAJ FINANCE': 'BAJFINANCE.NS',
        'BAJFINANCE': 'BAJFINANCE.NS',
        'AXIS BANK': 'AXISBANK.NS',
        'AXISBANK': 'AXISBANK.NS',
        'AXIS': 'AXISBANK.NS',
        'KOTAK MAHINDRA BANK': 'KOTAKBANK.NS',
        'KOTAKBANK': 'KOTAKBANK.NS',
        'KOTAK': 'KOTAKBANK.NS',
        'L&T': 'LT.NS',
        'LARSEN & TOUBRO': 'LT.NS',
        'LARSEN AND TOUBRO': 'LT.NS',
        'ASIAN PAINTS': 'ASIANPAINT.NS',
        'ASIANPAINT': 'ASIANPAINT.NS',
        'NESTLE': 'NESTLEIND.NS',
        'NESTLE INDIA': 'NESTLEIND.NS',
        'NESTLEIND': 'NESTLEIND.NS',
        'TITAN': 'TITAN.NS',
        'TITAN COMPANY': 'TITAN.NS',
        'ULTRATECH CEMENT': 'ULTRACEMCO.NS',
        'ULTRACEMCO': 'ULTRACEMCO.NS',
        'ULTRATECH': 'ULTRACEMCO.NS',
        'SUN PHARMA': 'SUNPHARMA.NS',
        'SUNPHARMA': 'SUNPHARMA.NS',
        'TECH MAHINDRA': 'TECHM.NS',
        'TECHM': 'TECHM.NS',
        'MAHINDRA': 'M&M.NS',
        'M&M': 'M&M.NS',
        'TATA STEEL': 'TATASTEEL.NS',
        'TATASTEEL': 'TATASTEEL.NS',
        'ONGC': 'ONGC.NS',
        'OIL AND NATURAL GAS CORPORATION': 'ONGC.NS',
        'BPCL': 'BPCL.NS',
        'BHARAT PETROLEUM': 'BPCL.NS',
        'IOC': 'IOC.NS',
        'INDIAN OIL': 'IOC.NS',
        'INDIAN OIL CORPORATION': 'IOC.NS',
        'NTPC': 'NTPC.NS',
        'POWER GRID': 'POWERGRID.NS',
        'POWERGRID': 'POWERGRID.NS',
        'HINDALCO': 'HINDALCO.NS',
        'HINDALCO INDUSTRIES': 'HINDALCO.NS',
        'JSW STEEL': 'JSWSTEEL.NS',
        'JSWSTEEL': 'JSWSTEEL.NS',
        'JSW': 'JSWSTEEL.NS',
        'TATA MOTORS': 'TATAMOTORS.NS',
        'TATAMOTORS': 'TATAMOTORS.NS',
        'BAJAJ AUTO': 'BAJAJ-AUTO.NS',
        'CIPLA': 'CIPLA.NS',
        'DR REDDY': 'DRREDDY.NS',
        'DRREDDY': 'DRREDDY.NS',
        'EICHER MOTORS': 'EICHERMOT.NS',
        'EICHERMOT': 'EICHERMOT.NS',
        'EICHER': 'EICHERMOT.NS',
        'BRITANNIA': 'BRITANNIA.NS',
        'BRITANNIA INDUSTRIES': 'BRITANNIA.NS',
        'GRASIM': 'GRASIM.NS',
        'GRASIM INDUSTRIES': 'GRASIM.NS',
        'SHREE CEMENT': 'SHREECEM.NS',
        'SHREECEM': 'SHREECEM.NS',
        'DIVIS LAB': 'DIVISLAB.NS',
        'DIVISLAB': 'DIVISLAB.NS',
        'DIVIS': 'DIVISLAB.NS',
        'HERO MOTOCORP': 'HEROMOTOCO.NS',
        'HEROMOTOCO': 'HEROMOTOCO.NS',
        'HERO': 'HEROMOTOCO.NS'
    }
    
    # Check direct mapping first
    if company_input in name_to_symbol:
        return name_to_symbol[company_input]
    
    # Try multiple exchange formats in order of preference
    potential_symbols = [
        f"{company_input}.NS",  # NSE first
        f"{company_input}.BO",  # BSE Bombay Stock Exchange
        company_input,          # Just the symbol without suffix
    ]
    
    # Test each potential symbol
    for symbol in potential_symbols:
        if validate_stock_symbol(symbol):
            return symbol
    
    # If nothing works, return NSE format as default
    return f"{company_input}.NS"

def validate_stock_symbol(symbol):
    """Validate if the stock symbol exists by checking with yfinance"""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="2d")  # Shorter period for faster validation
        return not data.empty
    except Exception:
        return False

# Keep the old function name for backward compatibility
validate_nse_symbol = validate_stock_symbol


def safe_download(*args, **kwargs):
    """Safely call yfinance.download while removing unsupported arguments."""
    kwargs.pop('quiet', None)
    kwargs.pop('progress_bar', None)
    return yf.download(*args, **kwargs)

def calculate_technical_indicators(df):
    """Calculate various technical indicators for the stock data"""
    if df.empty:
        return df
    
    # Simple Moving Averages
    df['SMA_10'] = df['Close'].rolling(window=10).mean()
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    
    # Exponential Moving Averages
    df['EMA_12'] = df['Close'].ewm(span=12).mean()
    df['EMA_26'] = df['Close'].ewm(span=26).mean()
    
    # MACD
    df['MACD'] = df['EMA_12'] - df['EMA_26']
    df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
    df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
    
    # Bollinger Bands
    df['BB_Middle'] = df['Close'].rolling(window=20).mean()
    bb_std = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
    df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
    
    # RSI
    df['RSI'] = calculate_rsi(df['Close'])
    
    # Volume indicators
    df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
    
    return df

def calculate_rsi(prices, window=14):
    """Calculate Relative Strength Index"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def get_market_status():
    """Get current Indian market status"""
    now = datetime.now()
    
    # Indian market hours: 9:15 AM to 3:30 PM IST (Monday to Friday)
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    
    # Check if it's a weekday
    if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return "Closed (Weekend)"
    
    # Check if market is open
    if market_open <= now <= market_close:
        return "Open"
    elif now < market_open:
        return "Pre-Market"
    else:
        return "Closed"

# Logger for StockSageAI
logger = logging.getLogger("StockSageAI")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

def setup_logging(level=logging.INFO):
    """Set up global logging for the application."""
    logger.setLevel(level)
    return logger


def clean_dataframe_for_export(df, convert_index=True):
    """Clean a DataFrame before exporting to Excel.

    This removes timezone metadata from datetime columns and index,
    converts invalid datetime values safely, and replaces NaN values with None.
    """
    if df is None:
        return pd.DataFrame()

    df = df.copy()

    try:
        if convert_index and df.index is not None:
            if pd.api.types.is_datetime64_any_dtype(df.index):
                try:
                    df.index = pd.to_datetime(df.index, errors='coerce')
                except Exception:
                    pass

            if pd.api.types.is_datetime64tz_dtype(getattr(df.index, 'dtype', None)):
                try:
                    df.index = df.index.tz_convert(None)
                except Exception:
                    pass
                try:
                    df.index = df.index.tz_localize(None)
                except Exception:
                    pass

        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]) or pd.api.types.is_datetime64tz_dtype(df[col]):
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                except Exception:
                    logger.warning(f"Could not parse datetime column '{col}' during export cleanup.")
                    continue

                if pd.api.types.is_datetime64tz_dtype(df[col]):
                    try:
                        df[col] = df[col].dt.tz_convert(None)
                    except Exception:
                        pass
                    try:
                        df[col] = df[col].dt.tz_localize(None)
                    except Exception:
                        pass
            elif df[col].dtype == object:
                # Convert object column datetimes if possible
                try:
                    converted = pd.to_datetime(df[col], errors='ignore')
                    if pd.api.types.is_datetime64_any_dtype(converted) or pd.api.types.is_datetime64tz_dtype(converted):
                        df[col] = converted
                except Exception:
                    pass

        df = df.replace({np.nan: None})
    except Exception as e:
        logger.error(f"Failed to clean dataframe for export: {e}")

    return df


def safe_df_columns(df):
    """Return valid dataframe columns, handling empty and malformed frames."""
    if df is None or not isinstance(df, pd.DataFrame):
        return []
    return [col for col in df.columns if isinstance(col, (str, int, float))]


def validate_dataframe(df):
    """Validate the dataframe is safe for display and export."""
    if df is None:
        return False
    if not isinstance(df, pd.DataFrame):
        return False
    if df.empty:
        return False
    return True


def format_percentage(value, decimal_places=2):
    """Format percentage with proper sign and color coding"""
    formatted = f"{value:+.{decimal_places}f}%"
    return formatted

def clean_text_for_sentiment(text):
    """Clean text for sentiment analysis"""
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove special characters but keep important punctuation
    text = re.sub(r'[^\w\s\.\!\?\,\-\%\$]', ' ', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Convert to lowercase
    text = text.lower()
    
    return text

def calculate_sharpe_ratio(returns, risk_free_rate=0.05):
    """Calculate Sharpe ratio for the returns"""
    if len(returns) == 0:
        return 0
    
    excess_returns = returns - risk_free_rate / 252  # Daily risk-free rate
    
    if excess_returns.std() == 0:
        return 0
    
    sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252)
    return sharpe_ratio

def get_support_resistance_levels(df, window=20):
    """Calculate support and resistance levels"""
    if len(df) < window * 2:
        return None, None
    
    # Rolling min and max for support and resistance
    support_levels = df['Low'].rolling(window=window).min()
    resistance_levels = df['High'].rolling(window=window).max()
    
    # Get recent levels
    recent_support = support_levels.iloc[-window:].min()
    recent_resistance = resistance_levels.iloc[-window:].max()
    
    return recent_support, recent_resistance

def validate_forecast_parameters(forecast_days, stock_data_length):
    """Validate if forecast parameters are reasonable"""
    if forecast_days < 1:
        return False, "Forecast days must be at least 1"
    
    if forecast_days > 90:
        return False, "Forecast days cannot exceed 90"
    
    if stock_data_length < 60:
        return False, "Need at least 60 days of historical data"
    
    return True, "Valid parameters"

def get_indian_stock_list():
    """Get a list of popular Indian stocks"""
    return [
        'TCS.NS', 'INFY.NS', 'RELIANCE.NS', 'HDFCBANK.NS', 'ICICIBANK.NS',
        'SBIN.NS', 'BHARTIARTL.NS', 'WIPRO.NS', 'HCLTECH.NS', 'ITC.NS',
        'HINDUNILVR.NS', 'MARUTI.NS', 'BAJFINANCE.NS', 'AXISBANK.NS',
        'KOTAKBANK.NS', 'LT.NS', 'ASIANPAINT.NS', 'NESTLEIND.NS', 'TITAN.NS',
        'ULTRACEMCO.NS', 'SUNPHARMA.NS', 'TECHM.NS', 'M&M.NS', 'TATASTEEL.NS',
        'ONGC.NS', 'BPCL.NS', 'IOC.NS', 'NTPC.NS', 'POWERGRID.NS',
        'HINDALCO.NS', 'JSWSTEEL.NS', 'TATAMOTORS.NS', 'BAJAJ-AUTO.NS',
        'CIPLA.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'BRITANNIA.NS',
        'GRASIM.NS', 'SHREECEM.NS', 'DIVISLAB.NS', 'HEROMOTOCO.NS'
    ]


def build_loader_styles():
    return """
<style>
.loader-screen { position: relative; min-height: 60vh; display: flex; align-items: center; justify-content: center; padding: 2rem; background: radial-gradient(circle at top left, rgba(56,189,248,0.16), transparent 25%), radial-gradient(circle at bottom right, rgba(168,85,247,0.22), transparent 20%), linear-gradient(180deg, rgba(12,23,43,0.98), rgba(5,10,20,0.99)); border-radius: 28px; overflow: hidden; }
.loader-glow { position: absolute; top: 40%; left: 50%; width: 500px; height: 500px; transform: translate(-50%, -50%); background: radial-gradient(circle, rgba(59,130,246,0.2), transparent 60%); filter: blur(42px); z-index: 1; }
.loader-panel { position: relative; z-index: 2; width: 100%; max-width: 960px; backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.08); box-shadow: 0 28px 110px rgba(0,0,0,0.44); border-radius: 32px; padding: 2.25rem; color: #e0f7ff; overflow: hidden; }
.loader-logo { width: 96px; height: 96px; margin: 0 auto 1.35rem; border-radius: 50%; border: 1px solid rgba(59,130,246,0.36); display: flex; align-items: center; justify-content: center; background: rgba(255,255,255,0.06); box-shadow: inset 0 0 24px rgba(59,130,246,0.16); font-size: 1rem; font-weight: 700; letter-spacing: 0.18em; text-transform: uppercase; color: #fff; }
.loader-title { font-size: clamp(1.95rem, 3vw, 2.8rem); font-weight: 800; letter-spacing: -0.03em; text-align: center; margin: 0.55rem 0 0.85rem; }
.loader-subtitle { max-width: 720px; margin: 0 auto 1.35rem; text-align: center; color: rgba(226,239,255,0.78); line-height: 1.75; }
.loader-stripe { display: flex; align-items: center; justify-content: center; gap: 0.9rem; margin: 1.45rem auto 0; width: fit-content; }
.loader-dot { width: 14px; height: 14px; border-radius: 999px; background: rgba(34,209,255,0.9); animation: pulse-dot 1.2s ease-in-out infinite; }
.loader-dot:nth-child(2) { animation-delay: 0.2s; }
.loader-dot:nth-child(3) { animation-delay: 0.4s; }
.loader-progress { position: relative; width: 100%; height: 14px; border-radius: 999px; background: rgba(255,255,255,0.08); overflow: hidden; margin-top: 1.45rem; }
.loader-progress-inner { width: 30%; height: 100%; background: linear-gradient(90deg, #22d3ee, #7c3aed); transform-origin: left center; animation: progress-slide 2.6s infinite ease-in-out; }
@keyframes pulse-dot { 0%, 100% { opacity: 0.35; transform: scale(0.8); } 50% { opacity: 1; transform: scale(1.1); } }
@keyframes progress-slide { 0%, 20% { width: 14%; } 50% { width: 68%; } 100% { width: 20%; } }
.loader-card-grid { display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); margin-top: 2rem; }
.skeleton-card, .skeleton-chart, .skeleton-table, .skeleton-sidebar { background: rgba(255,255,255,0.04); border-radius: 24px; border: 1px solid rgba(255,255,255,0.08); overflow: hidden; position: relative; }
.skeleton-shimmer { position: absolute; inset: 0; background: linear-gradient(90deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.16) 50%, rgba(255,255,255,0.04) 100%); animation: shimmer 1.8s infinite; }
.skeleton-content { padding: 1.6rem; opacity: 0.95; }
.skeleton-line { height: 12px; border-radius: 999px; margin-bottom: 1rem; background: rgba(255,255,255,0.08); }
.skeleton-line.short { width: 35%; }
.skeleton-line.medium { width: 65%; }
.skeleton-line.long { width: 90%; }
@keyframes shimmer { 0% { transform: translateX(-120%); } 100% { transform: translateX(120%); } }
</style>
"""


def render_ai_loader(message='Preparing AI analysis...'):
    st.markdown(build_loader_styles(), unsafe_allow_html=True)
    st.markdown(f"""
<div class='loader-screen'>
  <div class='loader-glow'></div>
  <div class='loader-panel'>
    <div class='loader-logo'>AI</div>
    <div class='loader-title'>Analyzing Market Signals</div>
    <div class='loader-subtitle'>{message} <span style='color:#7c3aed;'>Scanning price action, indicators, and pattern intelligence...</span></div>
    <div class='loader-stripe'>
      <div class='loader-dot'></div>
      <div class='loader-dot'></div>
      <div class='loader-dot'></div>
    </div>
    <div class='loader-progress'><div class='loader-progress-inner'></div></div>
  </div>
</div>
""", unsafe_allow_html=True)


def render_graph_loader(title='Loading Chart...'):
    st.markdown(build_loader_styles(), unsafe_allow_html=True)
    st.markdown(f"""
<div class='loader-screen' style='min-height: 320px; padding: 1.5rem;'>
  <div class='loader-panel' style='max-width: 850px;'>
    <div class='loader-title'>{title}</div>
    <div class='loader-subtitle'>Visualizing candlestick trends, moving averages, and market momentum.</div>
    <div class='loader-progress'><div class='loader-progress-inner'></div></div>
  </div>
</div>
""", unsafe_allow_html=True)


def render_skeleton_loader():
    st.markdown(build_loader_styles(), unsafe_allow_html=True)
    st.markdown("""
<div class='loader-screen' style='min-height: 420px;'>
  <div class='loader-panel'>
    <div class='loader-title'>Loading Dashboard</div>
    <div class='loader-subtitle'>Preparing analytics, stock charts, and system insights.</div>
    <div class='loader-progress'><div class='loader-progress-inner'></div></div>
    <div class='loader-card-grid'>
      <div class='skeleton-card'><div class='skeleton-shimmer'></div><div class='skeleton-content'><div class='skeleton-line long'></div><div class='skeleton-line medium'></div></div></div>
      <div class='skeleton-card'><div class='skeleton-shimmer'></div><div class='skeleton-content'><div class='skeleton-line medium'></div><div class='skeleton-line short'></div></div></div>
      <div class='skeleton-chart' style='height:220px;'><div class='skeleton-shimmer'></div></div>
      <div class='skeleton-table' style='height:180px;'><div class='skeleton-shimmer'></div></div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


def detect_candlestick_patterns(df):
    """Detect major candlestick patterns from the latest price action."""
    if not validate_dataframe(df) or len(df) < 2:
        return []

    patterns = []
    close = df['Close']
    open_price = df['Open']
    high = df['High']
    low = df['Low']

    last = len(df) - 1
    prev = last - 1

    body = abs(close.iloc[last] - open_price.iloc[last])
    range_high_low = high.iloc[last] - low.iloc[last]
    upper_shadow = high.iloc[last] - max(open_price.iloc[last], close.iloc[last])
    lower_shadow = min(open_price.iloc[last], close.iloc[last]) - low.iloc[last]

    # Doji
    if range_high_low > 0 and body / range_high_low < 0.1:
        patterns.append({'name': 'Doji', 'description': 'Indecision in the market with a near-equal open and close.'})

    # Hammer / Hanging man
    if body > 0 and lower_shadow >= 2 * body and upper_shadow <= body:
        if close.iloc[last] > open_price.iloc[last]:
            patterns.append({'name': 'Hammer', 'description': 'Bullish reversal pattern after a downward move.'})
        else:
            patterns.append({'name': 'Hanging Man', 'description': 'Potential bearish reversal after an uptrend.'})

    # Inverted Hammer / Shooting Star
    if body > 0 and upper_shadow >= 2 * body and lower_shadow <= body:
        if close.iloc[last] > open_price.iloc[last]:
            patterns.append({'name': 'Inverted Hammer', 'description': 'Possible bullish reversal during market weakness.'})
        else:
            patterns.append({'name': 'Shooting Star', 'description': 'Possible bearish reversal signal at the top of a move.'})

    # Engulfing patterns
    if len(df) > 1:
        prev_body = abs(close.iloc[prev] - open_price.iloc[prev])
        curr_body = abs(close.iloc[last] - open_price.iloc[last])
        if curr_body > prev_body * 1.2:
            if close.iloc[last] > open_price.iloc[last] and close.iloc[prev] < open_price.iloc[prev] and close.iloc[last] > open_price.iloc[prev] and open_price.iloc[last] < close.iloc[prev]:
                patterns.append({'name': 'Bullish Engulfing', 'description': 'Strong bullish reversal when the current candle engulfs the previous bearish candle.'})
            elif close.iloc[last] < open_price.iloc[last] and close.iloc[prev] > open_price.iloc[prev] and close.iloc[last] < close.iloc[prev] and open_price.iloc[last] > open_price.iloc[prev]:
                patterns.append({'name': 'Bearish Engulfing', 'description': 'Strong bearish reversal when the current candle engulfs the previous bullish candle.'})

    # Moving average crossovers
    if 'MA_20' in df.columns and 'MA_50' in df.columns and len(df) > 2:
        prev_ma20 = df['MA_20'].iloc[prev]
        prev_ma50 = df['MA_50'].iloc[prev]
        current_ma20 = df['MA_20'].iloc[last]
        current_ma50 = df['MA_50'].iloc[last]

        if prev_ma20 <= prev_ma50 and current_ma20 > current_ma50:
            patterns.append({'name': 'Golden Cross', 'description': 'Bullish signal when shorter-term average crosses above longer-term average.'})
        elif prev_ma20 >= prev_ma50 and current_ma20 < current_ma50:
            patterns.append({'name': 'Death Cross', 'description': 'Bearish signal when shorter-term average crosses below longer-term average.'})

    return patterns


def get_pattern_probabilities(df):
    """Estimate pattern strength and probability values for the latest data."""
    if not validate_dataframe(df) or len(df) < 5:
        return {
            'momentum': 'N/A',
            'reversal': 'N/A',
            'breakout': 'N/A',
            'confidence': 'N/A'
        }

    latest_rsi = df['RSI'].iloc[-1] if 'RSI' in df.columns else 50
    volume_ratio = df['Volume'].iloc[-1] / max(df['Volume'].tail(20).mean(), 1)
    recent_trend = (df['Close'].iloc[-1] - df['Close'].iloc[-5]) / max(df['Close'].iloc[-5], 1)

    momentum = 70 if recent_trend > 0 else 40
    reversal = 70 if latest_rsi < 30 or latest_rsi > 70 else 45
    breakout = 75 if volume_ratio > 1.5 else 55
    confidence = min(95, max(35, momentum * 0.4 + reversal * 0.3 + breakout * 0.3))

    return {
        'momentum': f"{momentum}%",
        'reversal': f"{reversal}%",
        'breakout': f"{breakout}%",
        'confidence': f"{confidence:.0f}%"
    }


def can_access_admin(user):
    return bool(user and user.get('role') in ['Super Admin', 'Admin'])


def can_access_super_admin(user):
    return bool(user and user.get('role') == 'Super Admin')
