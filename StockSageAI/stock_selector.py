"""
Stock Selector - Dynamically select Top 10 Indian stocks for forecasting
Based on market cap, volume, momentum, news sentiment and data quality
"""

import os
import logging
import pandas as pd
import numpy as np
import yfinance as yf
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import json
from functools import lru_cache

logger = logging.getLogger(__name__)

# Broader Indian equity universe seed used when live exchange listings are unavailable.
# This keeps the system functional while allowing future integration with a full NSE/BSE universe file.
INDIAN_UNIVERSE_SEED = [
    'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', 'SBIN', 'LTIM', 'ITC', 'SUNPHARMA', 'CIPLA',
    'HINDUNILVR', 'MARUTI', 'TATAMOTORS', 'BHARTIARTL', 'AXISBANK', 'KOTAKBANK', 'HCLTECH', 'TECHM',
    'WIPRO', 'TITAN', 'ASIANPAINT', 'ULTRACEMCO', 'NTPC', 'ONGC', 'POWERGRID', 'RECLTD', 'COALINDIA',
    'NESTLEIND', 'BRITANNIA', 'BAJAJ-AUTO', 'EICHERMOT', 'M&M', 'TATAPOWER', 'INDUSINDBK', 'GAIL',
    'ADANIGREEN', 'ADANIPORTS', 'JSWSTEEL', 'TATASTEEL', 'HINDALCO', 'VEDL', 'BPCL', 'IOC', 'DRREDDY',
    'DIVISLAB', 'LUPIN', 'APOLLOHOSP', 'TRENT', 'BEL', 'BHEL', 'BANKBARODA', 'PNB', 'CANBK', 'IDFCFIRSTB',
    'METROPOLIS', 'MRF', 'PIDILITIND', 'SHREECEM', 'ABB', 'ACC', 'AMBUJACEM', 'BAJAJFINANCE', 'BAJAJHLDNG',
    'DMART', 'GODREJCP', 'HDFCLIFE', 'ICICIPRULI', 'MUTHOOTFIN', 'PAYTM', 'PIDILITIND', 'SAIL', 'SYNGENE',
    'GRASIM', 'INDIGO', 'IRCTC', 'JINDALSTEL', 'SRF', 'NIFTYBEES', 'TATACONSUM', 'ZOMATO', 'WHIRLPOOL',
    'BANDHANBK', 'AUBANK', 'AUROPHARMA', 'COLPAL', 'MCDOWELL-N', 'GODREJPROP', 'KPITTECH', 'NATIONALUM',
    'PERSISTENT', 'DABUR', 'M&MFIN', 'RBLBANK', 'SUNDARMFIN', 'YESBANK', 'ZYDUSLIFE', 'IPCALAB', 'JUBLFOOD',
    'PVRINOX', 'TVSMOTOR', 'ASHOKLEY', 'EDELWEISS', 'BERGEPAINT', 'RAIN', 'SIEMENS', 'PAGEIND', 'HEROMOTOCO',
    'ATUL', 'CUMMINSIND', 'ESCORTS', 'GLENMARK', 'GODREJIND', 'MINDTREE', 'OMC', 'POLYCAB', 'REC', 'NHPC',
    'ZENSARTECH', 'AARTIIND', 'ALKEM', 'AUROPHARMA', 'CADILAHC', 'CHAMBLFERT', 'DEEPAKNTR', 'EMAMILTD',
    'INDHOTEL', 'JIOFIN', 'JSL', 'LALPATHLAB', 'MAHINDRA', 'MOTHERSON', 'NHPC', 'PETRONET', 'RITES', 'SOBHA',
    'SOLARINDS', 'SYNGENE', 'UNIPHOS', 'VOLTAS'
]

# Default Top 10 Indian stocks (NSE) - can be customized
DEFAULT_TOP_10_STOCKS = [
    'RELIANCE.NS',
    'TCS.NS',
    'INFY.NS',
    'HDFC.NS',
    'HINDUNILVR.NS',
    'ICICIBANK.NS',
    'WIPRO.NS',
    'MARUTI.NS',
    'BAJAJ-AUTO.NS',
    'LT.NS'
]

# Popular stocks for news and momentum consideration
POPULAR_STOCKS = [
    'RELIANCE.NS',
    'INFY.NS',
    'TCS.NS',
    'HDFC.NS',
    'HINDUNILVR.NS',
    'ICICIBANK.NS',
    'WIPRO.NS',
    'MARUTI.NS',
    'BAJAJ-AUTO.NS',
    'LT.NS',
    'HCLTECH.NS',
    'AXISBANK.NS',
    'SBIN.NS',
    'KOTAK.NS',
    'ADANIGREEN.NS'
]

class StockSelector:
    """Dynamic Top 10 stock selection based on multiple factors"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize stock selector
        
        Args:
            config: Optional configuration dict with selection parameters
        """
        self.config = config or {}
        self._stocks_cache = None
        self._cache_time = None
        self.cache_duration = timedelta(hours=24)  # Refresh daily
        self._universe = None
        
        logger.info("✅ Stock Selector initialized")
    
    def get_market_universe(self, max_symbols: int = 7500, refresh: bool = False) -> List[str]:
        """Return a broad, tradable NSE/BSE candidate universe.

        This is designed to support a full-market scan. In production, this should be fed from a
        real exchange or company master file; if unavailable, it falls back to a rich Indian seed list
        and validates symbols dynamically.
        """
        if self._universe is not None and not refresh:
            return self._universe[:max_symbols]

        universe = []
        for item in INDIAN_UNIVERSE_SEED:
            if item.endswith('.NS') or item.endswith('.BO'):
                universe.append(item)
            else:
                universe.extend([f"{item}.NS", f"{item}.BO"])

        deduped = []
        seen = set()
        for symbol in universe:
            if symbol not in seen:
                seen.add(symbol)
                deduped.append(symbol)

        self._universe = deduped
        logger.info(f"📊 Market universe seeded with {len(self._universe)} symbols")
        return self._universe[:max_symbols]

    def get_top_10_stocks(self, use_dynamic: bool = True, refresh: bool = False) -> List[str]:
        """
        Get Top 10 stocks for forecasting
        
        Args:
            use_dynamic: If True, select dynamically based on factors. If False, use defaults.
            refresh: Force refresh cache
            
        Returns:
            List of 10 stock symbols with .NS or .BO suffix
        """
        if not use_dynamic:
            logger.info(f"📊 Using default Top 10 stocks: {DEFAULT_TOP_10_STOCKS}")
            return DEFAULT_TOP_10_STOCKS
        
        # Check cache
        if not refresh and self._is_cache_valid():
            logger.info("📦 Using cached stock selection")
            return self._stocks_cache
        
        # Generate dynamic selection
        logger.info("🔄 Generating dynamic Top 10 stock selection...")
        
        try:
            selected = self._select_by_factors()
            
            if len(selected) >= 10:
                selected = selected[:10]
            elif len(selected) > 0:
                logger.warning(f"⚠️ Could only select {len(selected)} stocks, padding with defaults...")
                # Pad with defaults if needed
                for stock in DEFAULT_TOP_10_STOCKS:
                    if stock not in selected and len(selected) < 10:
                        selected.append(stock)
            else:
                logger.warning("❌ Dynamic selection failed, using defaults")
                selected = DEFAULT_TOP_10_STOCKS
            
            self._stocks_cache = selected[:10]
            self._cache_time = datetime.now()
            
            logger.info(f"✅ Selected Top 10 stocks: {self._stocks_cache}")
            return self._stocks_cache
            
        except Exception as e:
            logger.error(f"❌ Error in dynamic selection: {str(e)}")
            logger.info("📦 Falling back to default stocks")
            return DEFAULT_TOP_10_STOCKS
    
    def _is_cache_valid(self) -> bool:
        """Check if cached selection is still valid"""
        if self._stocks_cache is None or self._cache_time is None:
            return False
        
        age = datetime.now() - self._cache_time
        return age < self.cache_duration
    
    def _select_by_factors(self) -> List[str]:
        """
        Select stocks based on liquidity, quality, momentum, trend and risk-adjusted strength.
        """
        candidates = self.get_market_universe(max_symbols=200)
        scored = []
        
        for symbol in candidates:
            try:
                score = self._calculate_stock_score(symbol)
                if score is not None and score > 0:
                    scored.append((symbol, score))
                    
            except Exception as e:
                logger.warning(f"⚠️ Could not score {symbol}: {str(e)}")
                continue
        
        if not scored:
            return DEFAULT_TOP_10_STOCKS
        
        sorted_stocks = sorted(scored, key=lambda x: x[1], reverse=True)
        return [stock for stock, _ in sorted_stocks[:50]]
    
    def _calculate_stock_score(self, symbol: str) -> Optional[float]:
        """
        Composite score with real-world selection criteria.
        """
        try:
            df = yf.download(symbol, period='180d', progress=False, threads=False, auto_adjust=False)
            if df is None or df.empty or len(df) < 30:
                return None

            required_cols = {'Close', 'Volume'}
            if not required_cols.issubset(set(df.columns)):
                logger.debug(f"⚠️ Skipping {symbol}: missing required OHLCV columns")
                return None

            df = df.dropna(subset=['Close', 'Volume'])
            if df.empty or len(df) < 30:
                return None
            
            current = float(df['Close'].iloc[-1])
            if current <= 0:
                return None
            
            avg_volume = float(df['Volume'].mean())
            recent_volume = float(df['Volume'].iloc[-1])
            trend_up = (df['Close'].iloc[-1] / df['Close'].iloc[-20] - 1) * 100 if len(df) >= 20 else 0.0
            trend_90 = (df['Close'].iloc[-1] / df['Close'].iloc[0] - 1) * 100 if len(df) >= 10 else 0.0
            daily_returns = df['Close'].pct_change().dropna()
            volatility = float(daily_returns.std() * 100) if len(daily_returns) > 0 else 0.0
            liquidity_score = min(30.0, max(0.0, (recent_volume / max(avg_volume, 1)) * 15.0))
            momentum_score = min(25.0, max(0.0, 12.0 + trend_up * 0.8))
            trend_score = min(20.0, max(0.0, 10.0 + trend_90 * 0.5))
            volatility_score = min(15.0, max(0.0, 15.0 - volatility * 2.5))
            data_quality_score = 10.0
            if len(df) >= 120:
                data_quality_score += 5.0
            if recent_volume > avg_volume * 1.1:
                data_quality_score += 5.0

            total_score = liquidity_score + momentum_score + trend_score + volatility_score + data_quality_score
            
            logger.debug(f"  {symbol}: total={total_score:.2f} vol={volatility:.2f}% trend={trend_up:.2f}%")
            
            return total_score
            
        except Exception as e:
            logger.warning(f"⚠️ Error calculating score for {symbol}: {str(e)}")
            return None
    
    def validate_stocks(self, stocks: List[str]) -> Tuple[List[str], List[str]]:
        """
        Validate that stocks are accessible and have data
        
        Returns:
            Tuple of (valid_stocks: List[str], invalid_stocks: List[str])
        """
        valid = []
        invalid = []
        
        for symbol in stocks:
            try:
                # Try to fetch 1 day of data
                df = yf.download(symbol, period='1d', progress=False, threads=False)
                
                if df is not None and not df.empty:
                    valid.append(symbol)
                    logger.info(f"✅ {symbol} validated")
                else:
                    invalid.append(symbol)
                    logger.warning(f"⚠️ {symbol} has no data")
                    
            except Exception as e:
                invalid.append(symbol)
                logger.warning(f"⚠️ {symbol} validation failed: {str(e)}")
        
        return valid, invalid
    
    def get_stock_metadata(self, symbol: str) -> Optional[Dict]:
        """Get metadata about a stock"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'name': info.get('longName', info.get('shortName', 'Unknown')),
                'market_cap': info.get('marketCap'),
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'pe_ratio': info.get('trailingPE'),
                'dividend_yield': info.get('dividendYield'),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow'),
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Could not fetch metadata for {symbol}: {str(e)}")
            return None
    
    def export_stock_list(self, stocks: List[str], filepath: str = None) -> bool:
        """Export selected stocks to JSON file for reference"""
        try:
            if filepath is None:
                filepath = os.path.join(
                    os.path.dirname(__file__),
                    'config',
                    f'top_10_stocks_{datetime.now().strftime("%Y%m%d")}.json'
                )
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            data = {
                'generated_at': datetime.now().isoformat(),
                'count': len(stocks),
                'stocks': stocks,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"✅ Stock list exported to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error exporting stock list: {str(e)}")
            return False


# Singleton instance
_stock_selector = None

def get_stock_selector(config: Optional[Dict] = None) -> StockSelector:
    """Get or create singleton stock selector instance"""
    global _stock_selector
    if _stock_selector is None:
        _stock_selector = StockSelector(config)
    return _stock_selector
