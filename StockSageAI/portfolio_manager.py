"""
Portfolio Management System for SP 07 StockSageAI
Tracks multiple stocks with real-time P&L and analysis
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import yfinance as yf
import logging
from StockSageAI.utils import safe_download

logger = logging.getLogger(__name__)


class PortfolioManager:
    """Manage user stock portfolios with performance tracking"""
    
    def __init__(self, db_path: str = 'users.db'):
        self.db_path = db_path
        self.init_portfolio_db()
    
    def init_portfolio_db(self):
        """Initialize portfolio tables if not exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Portfolio table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                name TEXT DEFAULT 'My Portfolio',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Portfolio holdings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                quantity REAL NOT NULL,
                purchase_price REAL NOT NULL,
                purchase_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(portfolio_id) REFERENCES portfolios(id),
                UNIQUE(portfolio_id, symbol)
            )
        ''')
        
        # Portfolio history (for tracking)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER NOT NULL,
                date DATE NOT NULL,
                total_value REAL NOT NULL,
                cash_balance REAL DEFAULT 0,
                FOREIGN KEY(portfolio_id) REFERENCES portfolios(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_portfolio(self, user_id: str, name: str = 'My Portfolio') -> int:
        """Create new portfolio for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM portfolios WHERE user_id = ?', (user_id,))
        existing = cursor.fetchone()
        
        if existing:
            conn.close()
            return existing[0]
        
        cursor.execute(
            'INSERT INTO portfolios (user_id, name) VALUES (?, ?)',
            (user_id, name)
        )
        portfolio_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return portfolio_id
    
    def add_holding(self, portfolio_id: int, symbol: str, quantity: float,
                   purchase_price: float, purchase_date: str):
        """Add stock holding to portfolio"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO portfolio_holdings
                (portfolio_id, symbol, quantity, purchase_price, purchase_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (portfolio_id, symbol, quantity, purchase_price, purchase_date))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding holding: {e}")
            return False
        finally:
            conn.close()
    
    def get_holdings(self, portfolio_id: int) -> pd.DataFrame:
        """Get all holdings for portfolio"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(
            'SELECT * FROM portfolio_holdings WHERE portfolio_id = ?',
            conn,
            params=(portfolio_id,)
        )
        conn.close()
        return df
    
    def calculate_portfolio_metrics(self, portfolio_id: int) -> Dict:
        """Calculate comprehensive portfolio metrics"""
        holdings = self.get_holdings(portfolio_id)
        
        if holdings.empty:
            return {
                'total_value': 0,
                'total_invested': 0,
                'total_gain': 0,
                'total_gain_pct': 0,
                'diversification': [],
                'best_performer': None,
                'worst_performer': None
            }
        
        metrics = []
        total_invested = 0
        total_current_value = 0
        
        for _, row in holdings.iterrows():
            try:
                ticker = yf.Ticker(row['symbol'])
                current_price = ticker.info.get('currentPrice', row['purchase_price'])
                
                cost = row['quantity'] * row['purchase_price']
                current_value = row['quantity'] * current_price
                gain = current_value - cost
                gain_pct = (gain / cost * 100) if cost > 0 else 0
                
                total_invested += cost
                total_current_value += current_value
                
                metrics.append({
                    'symbol': row['symbol'],
                    'quantity': row['quantity'],
                    'purchase_price': row['purchase_price'],
                    'current_price': current_price,
                    'cost': cost,
                    'current_value': current_value,
                    'gain': gain,
                    'gain_pct': gain_pct,
                    'weight': current_value / (total_current_value + 0.001)
                })
            except Exception as e:
                logger.exception("Error computing holding metrics for %s", row['symbol'])
        
        if not metrics:
            return {
                'total_value': 0,
                'total_invested': 0,
                'total_gain': 0,
                'total_gain_pct': 0
            }
        
        total_gain = total_current_value - total_invested
        total_gain_pct = (total_gain / total_invested * 100) if total_invested > 0 else 0
        
        metrics = sorted(metrics, key=lambda x: x['gain_pct'], reverse=True)
        
        return {
            'total_value': total_current_value,
            'total_invested': total_invested,
            'total_gain': total_gain,
            'total_gain_pct': total_gain_pct,
            'holdings': metrics,
            'diversification': [
                {'symbol': m['symbol'], 'weight': m['weight']}
                for m in metrics
            ],
            'best_performer': metrics[0] if metrics else None,
            'worst_performer': metrics[-1] if metrics else None
        }
    
    def calculate_var(self, portfolio_id: int, days: int = 252, confidence: float = 0.95) -> float:
        """Calculate Value at Risk (VaR)"""
        holdings = self.get_holdings(portfolio_id)
        returns_list = []
        
        for _, row in holdings.iterrows():
            try:
                hist = safe_download(
                    row['symbol'],
                    start=datetime.now() - timedelta(days=days),
                    progress=False
                )
                
                if not hist.empty:
                    daily_returns = hist['Close'].pct_change().dropna()
                    returns_list.extend(daily_returns)
            except Exception as e:
                logger.exception("Error downloading data for %s in calculate_var", row['symbol'])
        
        if not returns_list:
            return 0
        
        returns_array = np.array(returns_list)
        var = np.percentile(returns_array, (1 - confidence) * 100)
        portfolio_value = self.calculate_portfolio_metrics(portfolio_id)['total_value']
        
        return abs(var * portfolio_value)
    
    def get_correlation_matrix(self, portfolio_id: int) -> pd.DataFrame:
        """Calculate correlation between holdings"""
        holdings = self.get_holdings(portfolio_id)
        
        if holdings.empty or len(holdings) < 2:
            return pd.DataFrame()
        
        prices_dict = {}
        
        for _, row in holdings.iterrows():
            try:
                hist = safe_download(
                    row['symbol'],
                    start=datetime.now() - timedelta(days=252),
                    progress=False
                )
                if not hist.empty:
                    prices_dict[row['symbol']] = hist['Close'].pct_change()
            except Exception as e:
                logger.exception("Error downloading data for %s in get_correlation_matrix", row['symbol'])
        
        if not prices_dict:
            return pd.DataFrame()
        
        df = pd.DataFrame(prices_dict)
        return df.corr()
        
    def delete_holding(self, portfolio_id: int, symbol: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'DELETE FROM portfolio_holdings WHERE portfolio_id = ? AND symbol = ?',
                (portfolio_id, symbol)
            )
            conn.commit()
            return True
        except Exception as e:
            logger.exception("Error deleting holding %s from portfolio %s", symbol, portfolio_id)
            return False
        finally:
            conn.close()


# Singleton instance
_portfolio_manager = None


def get_portfolio_manager():
    global _portfolio_manager
    if _portfolio_manager is None:
        _portfolio_manager = PortfolioManager()
    return _portfolio_manager
