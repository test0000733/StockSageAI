"""
Advanced Risk Analytics Dashboard for SP 07 StockSageAI
VaR, correlation, volatility, beta, alpha calculations
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import yfinance as yf
import logging
from StockSageAI.utils import safe_download

logger = logging.getLogger(__name__)


class RiskAnalyticsEngine:
    """Comprehensive risk analysis and metrics"""
    
    def __init__(self):
        self.risk_free_rate = 0.03  # 3% annual
    
    def _download_historical(self, symbol: str, start=None, end=None, days: int = None) -> pd.DataFrame:
        try:
            if days is not None:
                start = datetime.now() - timedelta(days=days)
                end = datetime.now()
            df = safe_download(symbol, start=start, end=end, progress=False)
            if df.empty or 'Close' not in df.columns:
                ticker = yf.Ticker(symbol)
                kwargs = {'interval': '1d', 'actions': False}
                if start is not None:
                    kwargs['start'] = start
                if end is not None:
                    kwargs['end'] = end
                df = ticker.history(**kwargs)
            if df.empty or 'Close' not in df.columns:
                raise ValueError(f"Downloaded market data is empty for {symbol}")
            return df
        except Exception as e:
            logger.error(f"Error downloading historical data for {symbol}: {e}")
            return pd.DataFrame()

    def calculate_var(self, returns: np.ndarray, confidence: float = 0.95,
                     method: str = 'historical') -> float:
        """Calculate Value at Risk"""
        
        if method == 'historical':
            var = np.percentile(returns, (1 - confidence) * 100)
        elif method == 'parametric':
            var = np.mean(returns) - np.std(returns) * np.sqrt(252) * 1.645
        elif method == 'monte_carlo':
            var = self._monte_carlo_var(returns, confidence)
        else:
            var = np.percentile(returns, (1 - confidence) * 100)
        
        return float(var)
    
    def _monte_carlo_var(self, returns: np.ndarray, confidence: float,
                        simulations: int = 1000) -> float:
        """Monte Carlo VaR calculation"""
        mu = np.mean(returns)
        sigma = np.std(returns)
        
        simulated_returns = np.random.normal(mu, sigma, simulations)
        var = np.percentile(simulated_returns, (1 - confidence) * 100)
        
        return float(var)
    
    def calculate_cvar(self, returns: np.ndarray, confidence: float = 0.95) -> float:
        """Calculate Conditional Value at Risk (Expected Shortfall)"""
        var = self.calculate_var(returns, confidence)
        cvar = np.mean(returns[returns <= var])
        return float(cvar)
    
    def calculate_correlation_matrix(self, symbols: List[str], days: int = 252) -> pd.DataFrame:
        """Calculate correlation matrix between assets"""
        
        data = {}
        
        for symbol in symbols:
            try:
                hist = self._download_historical(symbol, days=days)
                
                if not hist.empty:
                    data[symbol] = hist['Close'].pct_change()
            except Exception as e:
                logger.error(f"Error downloading correlation data for {symbol}: {e}")
                pass
        
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        return df.corr()
    
    def calculate_volatility(self, symbol: str, days: int = 252) -> Dict:
        """Calculate various volatility measures"""
        
        try:
            hist = self._download_historical(symbol, days=days)
            if hist.empty or 'Close' not in hist.columns:
                return {}
            
            returns = hist['Close'].pct_change().dropna()
            if returns.empty:
                return {}
            
            hist_vol = np.std(returns) * np.sqrt(252)
            highs = hist['High']
            lows = hist['Low']
            if highs.empty or lows.empty or len(highs) < 2:
                return {
                    'historical': float(hist_vol),
                    'parkinson': 0.0,
                    'garman_klass': 0.0,
                    'average': float(hist_vol)
                }
            parkinson_vol = np.sqrt(
                np.mean((np.log(highs / lows) ** 2) / (4 * np.log(2)))
            ) * np.sqrt(252)
            
            close_prices = hist['Close']
            open_prices = hist['Open'] if 'Open' in hist.columns else close_prices
            gk_values = (
                0.5 * np.log(highs / lows) ** 2 -
                (2 * np.log(2) - 1) * np.log(close_prices / open_prices) ** 2
            )
            garman_klass_vol = np.sqrt(np.mean(gk_values)) * np.sqrt(252)
            
            return {
                'historical': float(hist_vol),
                'parkinson': float(parkinson_vol),
                'garman_klass': float(garman_klass_vol),
                'average': float((hist_vol + parkinson_vol + garman_klass_vol) / 3)
            }
        except Exception as e:
            logger.error(f"Error calculating volatility: {e}")
            return {}
    
    def calculate_beta_alpha(self, symbol: str, benchmark: str = '^NSEI',
                            days: int = 252) -> Dict:
        """Calculate Beta and Alpha"""
        
        try:
            stock_data = self._download_historical(symbol, days=days)
            benchmark_data = self._download_historical(benchmark, days=days)
            if stock_data.empty or benchmark_data.empty:
                if benchmark != '^GSPC':
                    benchmark_data = self._download_historical('^GSPC', days=days)
                if stock_data.empty or benchmark_data.empty:
                    return {}
            
            stock_returns = stock_data['Close'].pct_change().dropna()
            benchmark_returns = benchmark_data['Close'].pct_change().dropna()
            
            dates = stock_returns.index.intersection(benchmark_returns.index)
            stock_returns = stock_returns.loc[dates]
            benchmark_returns = benchmark_returns.loc[dates]
            
            if stock_returns.empty or benchmark_returns.empty or len(stock_returns) < 2 or len(benchmark_returns) < 2:
                return {}
            
            covariance = np.cov(stock_returns, benchmark_returns, ddof=0)[0][1]
            benchmark_variance = np.var(benchmark_returns)
            if benchmark_variance == 0 or np.isnan(covariance):
                return {}
            
            beta = covariance / benchmark_variance
            stock_mean_return = np.mean(stock_returns) * 252
            benchmark_mean_return = np.mean(benchmark_returns) * 252
            alpha = stock_mean_return - (self.risk_free_rate + beta * (benchmark_mean_return - self.risk_free_rate))
            
            return {
                'beta': float(beta),
                'alpha': float(alpha),
                'interpretation': self._interpret_beta_alpha(beta, alpha)
            }
        except Exception as e:
            logger.error(f"Error calculating beta/alpha: {e}")
            return {}
    
    def _interpret_beta_alpha(self, beta: float, alpha: float) -> str:
        """Interpret beta and alpha values"""
        
        interpretations = []
        
        if beta > 1.5:
            interpretations.append("High volatility (aggressive)")
        elif beta > 1:
            interpretations.append("Above market volatility")
        elif beta > 0.5:
            interpretations.append("Below market volatility")
        else:
            interpretations.append("Low volatility (defensive)")
        
        if alpha > 0:
            interpretations.append("Outperforming market (positive alpha)")
        elif alpha < 0:
            interpretations.append("Underperforming market (negative alpha)")
        else:
            interpretations.append("In line with market")
        
        return ", ".join(interpretations)
    
    def calculate_max_drawdown(self, symbol: str, days: int = 252) -> Dict:
        """Calculate maximum drawdown"""
        
        try:
            hist = self._download_historical(symbol, days=days)
            if hist.empty or 'Close' not in hist.columns:
                return {}
            
            prices = hist['Close'].astype(float).values
            if len(prices) < 2:
                return {}
            
            running_max = np.maximum.accumulate(prices)
            drawdown = (prices - running_max) / running_max
            
            max_drawdown = np.min(drawdown)
            max_drawdown_idx = int(np.argmin(drawdown))
            peak_idx = int(np.argmax(prices[:max_drawdown_idx+1])) if max_drawdown_idx >= 0 else 0
            recovery_idx = np.where(prices[max_drawdown_idx:] >= prices[peak_idx])[0]
            recovery_days = int(len(recovery_idx) and recovery_idx[0] or len(hist) - max_drawdown_idx)
            
            return {
                'max_drawdown': float(max_drawdown) * 100,
                'drawdown_start': hist.index[peak_idx].strftime('%Y-%m-%d') if peak_idx < len(hist.index) else '',
                'drawdown_trough': hist.index[max_drawdown_idx].strftime('%Y-%m-%d') if max_drawdown_idx < len(hist.index) else '',
                'recovery_days': int(recovery_days)
            }
        except Exception as e:
            logger.error(f"Error calculating max drawdown: {e}")
            return {}
    
    def calculate_sharpe_ratio(self, returns: np.ndarray, risk_free_rate: float = None) -> float:
        """Calculate Sharpe Ratio"""
        
        if risk_free_rate is None:
            risk_free_rate = self.risk_free_rate
        
        excess_returns = (np.mean(returns) * 252) - risk_free_rate
        volatility = np.std(returns) * np.sqrt(252)
        
        sharpe = excess_returns / (volatility + 1e-10)
        return float(sharpe)
    
    def calculate_sortino_ratio(self, returns: np.ndarray, target_return: float = 0) -> float:
        """Calculate Sortino Ratio"""
        
        excess_returns = np.mean(returns) * 252 - target_return
        downside_returns = returns[returns < target_return]
        downside_volatility = np.std(downside_returns) * np.sqrt(252)
        
        sortino = excess_returns / (downside_volatility + 1e-10)
        return float(sortino)
    
    def generate_risk_report(self, symbol: str, portfolio_value: float = 10000) -> Dict:
        """Generate comprehensive risk report"""
        
        try:
            hist = self._download_historical(symbol, days=252)
            if hist.empty or 'Close' not in hist.columns:
                return {
                    'symbol': symbol,
                    'var_95': 0.0,
                    'var_99': 0.0,
                    'cvar_95': 0.0,
                    'volatility': {},
                    'max_drawdown': {},
                    'sharpe_ratio': 0.0,
                    'sortino_ratio': 0.0,
                    'beta_alpha': {},
                    'risk_level': 'UNKNOWN'
                }
            
            returns = hist['Close'].pct_change().dropna().values
            if len(returns) == 0:
                return {
                    'symbol': symbol,
                    'var_95': 0.0,
                    'var_99': 0.0,
                    'cvar_95': 0.0,
                    'volatility': {},
                    'max_drawdown': {},
                    'sharpe_ratio': 0.0,
                    'sortino_ratio': 0.0,
                    'beta_alpha': {},
                    'risk_level': 'UNKNOWN'
                }
            
            report = {
                'symbol': symbol,
                'var_95': self.calculate_var(returns, 0.95) * portfolio_value,
                'var_99': self.calculate_var(returns, 0.99) * portfolio_value,
                'cvar_95': self.calculate_cvar(returns, 0.95) * portfolio_value,
                'volatility': self.calculate_volatility(symbol),
                'max_drawdown': self.calculate_max_drawdown(symbol),
                'sharpe_ratio': self.calculate_sharpe_ratio(returns),
                'sortino_ratio': self.calculate_sortino_ratio(returns),
                'beta_alpha': self.calculate_beta_alpha(symbol),
                'risk_level': self._categorize_risk(returns)
            }
            
            return report
        except Exception as e:
            logger.error(f"Error generating risk report: {e}")
            return {
                'symbol': symbol,
                'var_95': 0.0,
                'var_99': 0.0,
                'cvar_95': 0.0,
                'volatility': {},
                'max_drawdown': {},
                'sharpe_ratio': 0.0,
                'sortino_ratio': 0.0,
                'beta_alpha': {},
                'risk_level': 'UNKNOWN'
            }
    
    def _categorize_risk(self, returns: np.ndarray) -> str:
        """Categorize risk level"""
        
        volatility = np.std(returns) * np.sqrt(252)
        
        if volatility > 0.4:
            return "VERY_HIGH"
        elif volatility > 0.25:
            return "HIGH"
        elif volatility > 0.15:
            return "MEDIUM"
        elif volatility > 0.08:
            return "LOW"
        else:
            return "VERY_LOW"


# Singleton instance
_risk_engine = None


def get_risk_analytics_engine():
    global _risk_engine
    if _risk_engine is None:
        _risk_engine = RiskAnalyticsEngine()
    return _risk_engine
