import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
import time

class DataFetcher:
    """Class to handle stock data fetching from Yahoo Finance and market-universe helpers."""
    
    def __init__(self):
        self.cache_duration = 300
        self.retry_count = 3
        self.retry_delay = 0.5
        self.market_universe_seed = [
            'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', 'SBIN', 'LTIM', 'ITC', 'SUNPHARMA', 'CIPLA',
            'HINDUNILVR', 'MARUTI', 'TATAMOTORS', 'BHARTIARTL', 'AXISBANK', 'KOTAKBANK', 'HCLTECH', 'TECHM',
            'WIPRO', 'TITAN', 'ASIANPAINT', 'ULTRACEMCO', 'NTPC', 'ONGC', 'POWERGRID', 'RECLTD', 'COALINDIA',
            'NESTLEIND', 'BRITANNIA', 'BAJAJ-AUTO', 'EICHERMOT', 'M&M', 'TATAPOWER', 'INDUSINDBK', 'GAIL',
            'ADANIGREEN', 'ADANIPORTS', 'JSWSTEEL', 'TATASTEEL', 'HINDALCO', 'VEDL', 'BPCL', 'IOC', 'DRREDDY',
            'DIVISLAB', 'LUPIN', 'APOLLOHOSP', 'TRENT', 'BEL', 'BHEL', 'BANKBARODA', 'PNB', 'CANBK', 'IDFCFIRSTB',
            'METROPOLIS', 'MRF', 'PIDILITIND', 'SHREECEM', 'ABB', 'ACC', 'AMBUJACEM', 'BAJAJFINANCE', 'BAJAJHLDNG',
            'DMART', 'GODREJCP', 'HDFCLIFE', 'ICICIPRULI', 'MUTHOOTFIN', 'PAYTM', 'SAIL', 'SYNGENE', 'GRASIM',
            'INDIGO', 'IRCTC', 'JINDALSTEL', 'SRF', 'NIFTYBEES', 'TATACONSUM', 'ZOMATO', 'WHIRLPOOL', 'BANDHANBK',
            'AUBANK', 'AUROPHARMA', 'COLPAL', 'CUMMINSIND', 'GODREJPROP', 'KPITTECH', 'NATIONALUM', 'PERSISTENT',
            'DABUR', 'M&MFIN', 'RBLBANK', 'SUNDARMFIN', 'YESBANK', 'ZYDUSLIFE', 'IPCALAB', 'JUBLFOOD', 'PVRINOX',
            'TVSMOTOR', 'ASHOKLEY', 'BERGEPAINT', 'RAIN', 'SIEMENS', 'PAGEIND', 'HEROMOTOCO', 'ATUL', 'ESCORTS',
            'GLENMARK', 'GODREJIND', 'MINDTREE', 'OMC', 'POLYCAB', 'REC', 'NHPC', 'ZENSARTECH', 'AARTIIND', 'ALKEM',
            'AUROPHARMA', 'CADILAHC', 'CHAMBLFERT', 'DEEPAKNTR', 'EMAMILTD', 'INDHOTEL', 'JIOFIN', 'JSL',
            'LALPATHLAB', 'MAHINDRA', 'MOTHERSON', 'PETRONET', 'RITES', 'SOBHA', 'SOLARINDS', 'UNIPHOS', 'VOLTAS'
        ]

    def normalize_symbol(self, symbol: str) -> str:
        """Normalize a stock symbol to the NSE/BSE format used by the project."""
        if not symbol:
            return symbol
        symbol_clean = str(symbol).strip().upper()
        if symbol_clean.endswith('.NS') or symbol_clean.endswith('.BO') or symbol_clean.endswith('.BSE'):
            return symbol_clean
        if symbol_clean.endswith('.NSE'):
            return symbol_clean.replace('.NSE', '.NS')
        if not symbol_clean:
            return symbol_clean
        return f"{symbol_clean}.NS"

    def get_market_universe(self, market: str = 'india', max_symbols: int = 7500) -> list:
        """Return a broader candidate universe for NSE/BSE scanning.

        This acts as a production-ready seed layer for a larger exchange universe; it supports later
        replacement with a real export from NSE/BSE master files while retaining backward compatibility.
        """
        universe = []
        for item in self.market_universe_seed:
            symbol = self.normalize_symbol(item)
            if symbol not in universe:
                universe.append(symbol)
        if market.lower() == 'india':
            return universe[:max_symbols]
        return universe[:max_symbols]

    @st.cache_data(ttl=300)
    def get_stock_data(_self, symbol, period="1y"):
        """Fetch historical stock data for given symbol with retry logic."""
        symbol_clean = _self.normalize_symbol(symbol)
        symbols_to_try = []
        symbol_clean = symbol_clean.strip().upper()
        symbols_to_try.append(symbol_clean)

        if not symbol_clean.endswith('.NS') and not symbol_clean.endswith('.BO') and not symbol_clean.endswith('.BSE'):
            symbols_to_try.append(f"{symbol_clean}.NS")
            symbols_to_try.append(f"{symbol_clean}.BO")

        last_error = None
        for try_symbol in symbols_to_try:
            try:
                for attempt in range(_self.retry_count):
                    try:
                        ticker = yf.Ticker(try_symbol)
                        data = ticker.history(period=period)
                        if not data.empty and len(data) > 10:
                            data = data.dropna()
                            data['MA_20'] = data['Close'].rolling(window=20).mean()
                            data['MA_50'] = data['Close'].rolling(window=50).mean()
                            data['RSI'] = _self._calculate_rsi(data['Close'])
                            data['Volatility'] = data['Close'].pct_change().rolling(window=20).std()
                            return data
                    except Exception as e:
                        last_error = str(e)
                        if attempt < _self.retry_count - 1:
                            time.sleep(_self.retry_delay)
                        continue
            except Exception as e:
                last_error = str(e)
                continue

        if last_error:
            return pd.DataFrame()
        return pd.DataFrame()

    def _calculate_rsi(self, prices, window=14):
        """Calculate Relative Strength Index (RSI)."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def get_company_info(self, symbol):
        """Get basic company information."""
        try:
            ticker = yf.Ticker(self.normalize_symbol(symbol))
            info = ticker.info
            company_data = {
                'name': info.get('longName', 'Unknown'),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('forwardPE', 0),
                'dividend_yield': info.get('dividendYield', 0)
            }
            return company_data
        except Exception as e:
            st.warning(f"Could not fetch company info for {symbol}: {str(e)}")
            return {}

    def validate_symbol(self, symbol):
        """Validate if the stock symbol exists and has data."""
        try:
            if not symbol or len(symbol.strip()) == 0:
                return False
            normalized = self.normalize_symbol(symbol)
            ticker = yf.Ticker(normalized)
            data = ticker.history(period="30d")
            if not data.empty and len(data) > 5:
                return True
            if not normalized.endswith('.NS') and not normalized.endswith('.BO') and not normalized.endswith('.BSE'):
                ticker = yf.Ticker(normalized + '.NS')
                data = ticker.history(period="30d")
                if not data.empty and len(data) > 5:
                    return True
                ticker = yf.Ticker(normalized + '.BO')
                data = ticker.history(period="30d")
                if not data.empty and len(data) > 5:
                    return True
            return False
        except Exception:
            return False

    def get_index_data(self, symbol, period="5d"):
        """Fetch index data such as NIFTY, SENSEX, BANKNIFTY."""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            return data.dropna()
        except Exception as e:
            st.warning(f"Unable to fetch index data for {symbol}: {e}")
            return pd.DataFrame()
