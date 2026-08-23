"""
Advanced Backtesting Engine for SP 07 StockSageAI
Test trading strategies on historical data with comprehensive metrics
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import yfinance as yf
from sklearn.metrics import mean_absolute_error, mean_squared_error
import logging
from StockSageAI.utils import safe_download

logger = logging.getLogger(__name__)


class BacktestingEngine:
    """Comprehensive backtesting for trading strategies"""
    
    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
        self.results = None
    
    def _download_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        try:
            df = safe_download(symbol, start=start_date, end=end_date, progress=False)
            if df.empty or 'Close' not in df.columns:
                ticker = yf.Ticker(symbol)
                df = ticker.history(start=start_date, end=end_date, interval='1d', actions=False)
            return df
        except Exception as e:
            logger.error(f"Error downloading data for {symbol}: {e}")
            return pd.DataFrame()

    def fetch_historical_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch historical OHLCV data"""
        try:
            df = self._download_data(symbol, start_date, end_date)
            if df.empty and start_date == end_date:
                # Try a one-day extension when same-day range was provided
                end_date = (pd.to_datetime(end_date) + timedelta(days=1)).strftime('%Y-%m-%d')
                df = self._download_data(symbol, start_date, end_date)
            if not df.empty and 'Close' in df.columns:
                df['Daily_Return'] = df['Close'].pct_change()
            return df
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def generate_signals(self, df: pd.DataFrame, strategy: str = 'ma_crossover') -> pd.DataFrame:
        """Generate buy/sell signals based on strategy"""
        df = df.copy()
        
        if strategy == 'ma_crossover':
            # Moving Average Crossover Strategy
            df['MA_20'] = df['Close'].rolling(window=20).mean()
            df['MA_50'] = df['Close'].rolling(window=50).mean()
            df['Signal'] = 0
            df.loc[df['MA_20'] > df['MA_50'], 'Signal'] = 1
            df.loc[df['MA_20'] < df['MA_50'], 'Signal'] = -1
            df['Position'] = df['Signal'].diff()
            
        elif strategy == 'rsi':
            # RSI Strategy
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            df['Signal'] = 0
            df.loc[df['RSI'] < 30, 'Signal'] = 1
            df.loc[df['RSI'] > 70, 'Signal'] = -1
            df['Position'] = df['Signal'].diff()
            
        elif strategy == 'bollinger_bands':
            # Bollinger Bands Strategy
            df['MA'] = df['Close'].rolling(window=20).mean()
            df['Std'] = df['Close'].rolling(window=20).std()
            df['Upper'] = df['MA'] + (df['Std'] * 2)
            df['Lower'] = df['MA'] - (df['Std'] * 2)
            df['Signal'] = 0
            df.loc[df['Close'] < df['Lower'], 'Signal'] = 1
            df.loc[df['Close'] > df['Upper'], 'Signal'] = -1
            df['Position'] = df['Signal'].diff()
        
        return df
    
    def backtest(self, df: pd.DataFrame, strategy: str = 'ma_crossover',
                commission: float = 0.001) -> Dict:
        """Run backtest simulation"""
        
        df = self.generate_signals(df, strategy)
        df['Returns'] = df['Daily_Return'].fillna(0)
        
        # Initialize portfolio
        capital = self.initial_capital
        position = 0
        trades = []
        portfolio_values = [capital]
        entry_price = 0
        
        for i in range(len(df)):
            # Extract scalar values to avoid Series comparison issues
            position_val = df.iloc[i]['Position']
            if pd.isna(position_val):
                continue
            
            # Ensure scalar comparison
            position_val = float(position_val) if not pd.isna(position_val) else 0
            close_price = float(df.iloc[i]['Close'])
            
            # Buy signal
            if position_val == 2 and position == 0:
                entry_price = close_price
                position = 1
                trades.append({
                    'date': df.index[i],
                    'type': 'BUY',
                    'price': entry_price
                })
            
            # Sell signal
            elif position_val == -2 and position == 1:
                exit_price = close_price
                pnl = (exit_price - entry_price) * 1 - (commission * capital)
                capital += pnl
                trades.append({
                    'date': df.index[i],
                    'type': 'SELL',
                    'price': exit_price,
                    'pnl': pnl
                })
                position = 0
            
            # Update portfolio value
            if position == 1:
                unrealized_pnl = (close_price - entry_price)
                portfolio_values.append(capital + unrealized_pnl)
            else:
                portfolio_values.append(capital)
        
        # Calculate metrics
        returns = np.array(portfolio_values[1:]) / np.array(portfolio_values[:-1]) - 1
        total_return = (portfolio_values[-1] - self.initial_capital) / self.initial_capital
        sharpe_ratio = np.mean(returns) / (np.std(returns) + 1e-10) * np.sqrt(252)
        
        drawdowns = np.maximum.accumulate(portfolio_values) - portfolio_values
        max_drawdown = np.max(drawdowns) / np.max(portfolio_values)
        
        winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
        win_rate = len(winning_trades) / max(len(trades), 1) * 100
        
        return {
            'total_return': total_return * 100,
            'final_value': portfolio_values[-1],
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown * 100,
            'win_rate': win_rate,
            'trades': len(trades),
            'winning_trades': len(winning_trades),
            'portfolio_values': portfolio_values,
            'trades_history': trades
        }
    
    def compare_strategies(self, symbol: str, start_date: str, end_date: str,
                          strategies: List[str] = None) -> pd.DataFrame:
        """Compare multiple strategies"""
        
        if strategies is None:
            strategies = ['ma_crossover', 'rsi', 'bollinger_bands']
        
        df = self.fetch_historical_data(symbol, start_date, end_date)
        
        if df.empty:
            return pd.DataFrame()
        
        results = []
        
        for strategy in strategies:
            try:
                result = self.backtest(df, strategy)
                results.append({
                    'Strategy': strategy.replace('_', ' ').title(),
                    'Total Return': f"{result['total_return']:.2f}%",
                    'Final Value': f"${result['final_value']:.2f}",
                    'Sharpe Ratio': f"{result['sharpe_ratio']:.2f}",
                    'Max Drawdown': f"{result['max_drawdown']:.2f}%",
                    'Win Rate': f"{result['win_rate']:.1f}%",
                    'Trades': result['trades']
                })
            except Exception as e:
                logger.error(f"Error backtesting {strategy}: {e}")
        
        return pd.DataFrame(results)
    
    def walk_forward_analysis(self, symbol: str, start_date: str, end_date: str,
                             window_size: int = 60, step_size: int = 30) -> Dict:
        """Perform walk-forward analysis"""
        
        df = self.fetch_historical_data(symbol, start_date, end_date)
        
        if df.empty:
            return {}
        
        results = []
        dates = df.index
        
        for i in range(0, len(df) - window_size, step_size):
            train_df = df.iloc[i:i + window_size]
            test_df = df.iloc[i + window_size:min(i + window_size + step_size, len(df))]
            
            if test_df.empty:
                break
            
            try:
                backtest_result = self.backtest(test_df, 'ma_crossover')
                results.append({
                    'period_start': str(train_df.index[0].date()),
                    'period_end': str(test_df.index[-1].date()),
                    'return': backtest_result['total_return'],
                    'sharpe': backtest_result['sharpe_ratio'],
                    'drawdown': backtest_result['max_drawdown']
                })
            except Exception as e:
                logger.exception("Error running backtest for period %s to %s", train_df.index[0], test_df.index[-1])
        
        return {
            'periods': results,
            'avg_return': np.mean([r['return'] for r in results]) if results else 0,
            'avg_sharpe': np.mean([r['sharpe'] for r in results]) if results else 0,
            'consistency': len([r for r in results if r['return'] > 0]) / max(len(results), 1) * 100
        }
    
    def calculate_model_accuracy(self, predictions: List[float], actual: List[float]) -> Dict:
        """Calculate model prediction accuracy metrics"""
        
        predictions = np.array(predictions)
        actual = np.array(actual)
        
        mae = mean_absolute_error(actual, predictions)
        rmse = np.sqrt(mean_squared_error(actual, predictions))
        mape = np.mean(np.abs((actual - predictions) / actual)) * 100
        
        direction_correct = np.sum(
            np.sign(np.diff(predictions)) == np.sign(np.diff(actual))
        ) / (len(actual) - 1)
        
        return {
            'mae': mae,
            'rmse': rmse,
            'mape': mape,
            'direction_accuracy': direction_correct * 100
        }


# Singleton instance
_backtest_engine = None


def get_backtest_engine():
    global _backtest_engine
    if _backtest_engine is None:
        _backtest_engine = BacktestingEngine()
    return _backtest_engine
