"""
Unified Stock Database Module
Provides global access to stocks database with caching and real-time updates
"""

import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Optional, Tuple
import time

logger = logging.getLogger(__name__)

# Global stock lists
POPULAR_US_STOCKS = {
    "Technology": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "NFLX"],
    "Finance": ["JPM", "BAC", "WFC", "GS", "MS", "BLK", "AXP", "COF"],
    "Healthcare": ["JNJ", "UNH", "LLY", "MRK", "ABBV", "PFE", "TMO", "AMGN"],
    "Energy": ["XOM", "CVX", "COP", "SLB", "MPC", "PSX", "VLO", "KMI"],
    "Consumer": ["WMT", "COST", "MCD", "NKE", "SBUX", "PG", "KO", "PEP"],
    "Industrials": ["BA", "CAT", "GE", "MMM", "LMT", "RTX", "HON", "ITW"],
}

POPULAR_INDIAN_STOCKS = {
    "Banking": ["HDFC.NS", "ICICIBANK.NS", "AXISBANK.NS", "SBIN.NS", "INDUSIND.NS", "KOTAK.NS", "BPCL.NS"],
    "IT": ["TCS.NS", "INFY.NS", "WIPRO.NS", "HCL.NS", "TECHM.NS", "LT.NS", "DLF.NS"],
    "Energy": ["RELIANCE.NS", "ONGC.NS", "IOC.NS", "NTPC.NS", "POWER.NS", "ADANIGREEN.NS"],
    "Auto": ["MARUTI.NS", "BAJAJ-AUTO.NS", "TATAMOTORS.NS", "MAHINDRA.NS", "EICHER.NS"],
    "FMCG": ["NESTLEIND.NS", "BRITANNIA.NS", "ITC.NS", "MARICO.NS", "GODREJCP.NS"],
    "Pharma": ["CIPLA.NS", "DRREDDY.NS", "SUNPHARMA.NS", "LUPIN.NS", "DIVISLAB.NS"],
}

class StocksDatabase:
    """Unified global stocks database with caching"""
    
    def __init__(self):
        self.us_stocks = self._flatten_dict(POPULAR_US_STOCKS)
        self.indian_stocks = self._flatten_dict(POPULAR_INDIAN_STOCKS)
        self.all_stocks = self.us_stocks + self.indian_stocks
        self.stock_details_cache = {}
        self.last_update = {}
    
    @staticmethod
    def _flatten_dict(d: Dict) -> List[str]:
        """Flatten nested dictionary of stocks"""
        result = []
        for category, stocks in d.items():
            result.extend(stocks)
        return sorted(list(set(result)))
    
    def get_all_stocks(self, market: str = "all") -> List[str]:
        """Get all available stocks"""
        if market == "us":
            return self.us_stocks
        elif market == "india":
            return self.indian_stocks
        else:
            return self.all_stocks
    
    def get_stocks_by_category(self, market: str = "us") -> Dict[str, List[str]]:
        """Get stocks organized by category"""
        if market == "india":
            return POPULAR_INDIAN_STOCKS
        else:
            return POPULAR_US_STOCKS
    
    @st.cache_data(ttl=3600)
    def get_stock_info(_self, symbol: str) -> Optional[Dict]:
        """Get stock information with caching"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Extract key information
            stock_data = {
                'symbol': symbol,
                'name': info.get('longName', info.get('shortName', symbol)),
                'price': info.get('currentPrice', info.get('regularMarketPrice', 0)),
                'currency': info.get('currency', 'USD'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'dividend_yield': info.get('dividendYield', 0),
                '52_week_high': info.get('fiftyTwoWeekHigh', 0),
                '52_week_low': info.get('fiftyTwoWeekLow', 0),
            }
            
            return stock_data
        except Exception as e:
            logger.error(f"Error fetching info for {symbol}: {e}")
            return None
    
    @st.cache_data(ttl=300)
    def get_stock_price(_self, symbol: str) -> Optional[float]:
        """Get current stock price with caching"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d")
            if not data.empty:
                return float(data['Close'].iloc[-1])
            return None
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return None
    
    def search_stocks(self, query: str, market: str = "all", limit: int = 10) -> List[Tuple[str, str]]:
        """Search stocks by symbol or name"""
        query_lower = query.lower()
        stocks = self.get_all_stocks(market)
        
        results = []
        for stock in stocks:
            stock_info = self.get_stock_info(stock)
            if stock_info:
                name = stock_info.get('name', '')
                if query_lower in stock.lower() or query_lower in name.lower():
                    results.append((stock, name))
        
        return results[:limit]
    
    def get_popular_stocks(self, market: str = "all", limit: int = 20) -> List[str]:
        """Get most popular stocks"""
        stocks = self.get_all_stocks(market)
        return stocks[:limit]


# Global instance
@st.cache_resource
def get_stocks_database() -> StocksDatabase:
    """Get or create global stocks database instance"""
    return StocksDatabase()


def render_stock_selector(
    label: str = "Select Stock",
    default_value: str = None,
    market: str = "all",
    key: str = None,
    help_text: str = None
) -> str:
    """Render a beautiful stock selector dropdown"""
    db = get_stocks_database()
    stocks = db.get_all_stocks(market)
    
    if default_value and default_value not in stocks:
        default_value = stocks[0] if stocks else "AAPL"
    elif not default_value and stocks:
        default_value = stocks[0]
    
    # Create a selectbox with search functionality
    selected = st.selectbox(
        label,
        options=stocks,
        index=stocks.index(default_value) if default_value in stocks else 0,
        key=key,
        help=help_text or "🔍 Search or select from popular stocks"
    )
    
    return selected.upper()


def render_stock_multi_selector(
    label: str = "Select Stocks",
    default_values: List[str] = None,
    market: str = "all",
    max_items: int = 5,
    key: str = None,
) -> List[str]:
    """Render a multi-stock selector"""
    db = get_stocks_database()
    stocks = db.get_all_stocks(market)
    
    if not default_values:
        default_values = stocks[:3]
    
    selected = st.multiselect(
        label,
        options=stocks,
        default=[s for s in default_values if s in stocks],
        max_selections=max_items,
        key=key,
        help=f"🔍 Select up to {max_items} stocks"
    )
    
    return [s.upper() for s in selected]


def display_stock_info_card(symbol: str, columns: int = 1):
    """Display stock information card"""
    db = get_stocks_database()
    stock_info = db.get_stock_info(symbol)
    
    if not stock_info:
        st.warning(f"⚠️ Unable to fetch info for {symbol}")
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "💰 Price",
            f"₹{stock_info.get('price', 0):,.2f}" if ".NS" in symbol else f"${stock_info.get('price', 0):,.2f}",
            f"Market Cap: {stock_info.get('market_cap', 'N/A')}"
        )
    
    with col2:
        st.metric(
            "📊 P/E Ratio",
            f"{stock_info.get('pe_ratio', 0):.2f}",
            f"Div Yield: {stock_info.get('dividend_yield', 0):.2%}"
        )
    
    with col3:
        st.metric(
            "📈 Sector",
            stock_info.get('sector', 'N/A'),
            stock_info.get('industry', 'N/A')
        )


def get_stock_category(symbol: str, market: str = "us") -> Optional[str]:
    """Get category of a stock"""
    categories = POPULAR_INDIAN_STOCKS if ".NS" in symbol else POPULAR_US_STOCKS
    
    for category, stocks in categories.items():
        if symbol in stocks:
            return category
    
    return None


def render_category_tabs(market: str = "us"):
    """Render stocks organized by category tabs"""
    categories = POPULAR_INDIAN_STOCKS if market == "india" else POPULAR_US_STOCKS
    
    tabs = st.tabs(list(categories.keys()))
    
    results = {}
    for tab, (category, stocks) in zip(tabs, categories.items()):
        with tab:
            st.write(f"**{category} Stocks** ({len(stocks)} available)")
            col1, col2, col3, col4 = st.columns(4)
            
            for idx, stock in enumerate(stocks):
                col = [col1, col2, col3, col4][idx % 4]
                with col:
                    if st.button(f"📍 {stock}", key=f"cat_{stock}"):
                        results[category] = stock
    
    return results
