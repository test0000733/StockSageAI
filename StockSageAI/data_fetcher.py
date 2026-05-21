import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
import time

class DataFetcher:
    """Class to handle stock data fetching from Yahoo Finance"""
    
    def __init__(self):
        self.cache_duration = 300  # 5 minutes cache
        self.retry_count = 3
        self.retry_delay = 0.5
    
    @st.cache_data(ttl=300)
    def get_stock_data(_self, symbol, period="1y"):
        """
        Fetch historical stock data for given symbol with retry logic
        
        Args:
            symbol: Stock symbol (e.g., 'TCS.NS')
            period: Data period ('1y', '2y', '5y', 'max')
        
        Returns:
            DataFrame with OHLCV data
        """
        # Try different symbol formats
        symbols_to_try = []
        
        # Clean the input
        symbol_clean = symbol.strip().upper()
        
        # Add the original symbol first
        symbols_to_try.append(symbol_clean)
        
        # If no suffix, add NSE and BO variants
        if not symbol_clean.endswith('.NS') and not symbol_clean.endswith('.BO') and not symbol_clean.endswith('.BSE'):
            symbols_to_try.append(f"{symbol_clean}.NS")
            symbols_to_try.append(f"{symbol_clean}.BO")
        
        # Try each symbol format
        last_error = None
        for try_symbol in symbols_to_try:
            try:
                # Retry logic for network issues
                for attempt in range(_self.retry_count):
                    try:
                        ticker = yf.Ticker(try_symbol)
                        data = ticker.history(period=period)
                        
                        if not data.empty and len(data) > 10:
                            # Clean the data
                            data = data.dropna()
                            
                            # Add technical indicators
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
        
        # If all attempts failed, return empty with error message
        if last_error:
            return pd.DataFrame()
        return pd.DataFrame()
    
    def _calculate_rsi(self, prices, window=14):
        """Calculate Relative Strength Index (RSI)"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def get_company_info(self, symbol):
        """Get basic company information"""
        try:
            ticker = yf.Ticker(symbol)
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
        """Validate if the stock symbol exists and has data"""
        try:
            if not symbol or len(symbol.strip()) == 0:
                return False
            
            symbol = symbol.strip().upper()
            
            # Try the symbol as provided
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="30d")
            if not data.empty and len(data) > 5:
                return True
            
            # If no data, try with .NS suffix for Indian stocks
            if not symbol.endswith('.NS') and not symbol.endswith('.BO') and not symbol.endswith('.BSE'):
                ticker = yf.Ticker(symbol + '.NS')
                data = ticker.history(period="30d")
                if not data.empty and len(data) > 5:
                    return True
                
                # Also try .BO suffix
                ticker = yf.Ticker(symbol + '.BO')
                data = ticker.history(period="30d")
                if not data.empty and len(data) > 5:
                    return True
            
            return False
        except:
            return False

    def get_index_data(self, symbol, period="5d"):
        """Fetch index data such as NIFTY, SENSEX, BANKNIFTY"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            return data.dropna()
        except Exception as e:
            st.warning(f"Unable to fetch index data for {symbol}: {e}")
            return pd.DataFrame()
