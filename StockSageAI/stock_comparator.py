"""
Multi-Stock Comparison Tool for SP 07 StockSageAI
Compare 3-5 stocks with side-by-side forecasts and analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import yfinance as yf
import logging
from StockSageAI.utils import safe_download

logger = logging.getLogger(__name__)


class StockComparator:
    """Compare multiple stocks simultaneously"""
    
    def _ensure_series(self, data):
        if isinstance(data, pd.DataFrame):
            return data.iloc[:, 0]
        return data

    def compare_stocks(self, symbols: List[str], metrics: List[str] = None) -> pd.DataFrame:
        """Compare stocks across various metrics"""
        
        if metrics is None:
            metrics = ['price', 'pe', 'dividend', 'volatility', 'change_1d', 'change_1y']
        
        results = []
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info if hasattr(ticker, 'info') else {}
                
                # Historical data for calculating metrics
                hist = safe_download(
                    symbol,
                    start=datetime.now() - timedelta(days=365),
                    progress=False
                )
                
                if hist.empty or 'Close' not in hist.columns:
                    hist = ticker.history(period='1y', interval='1d', actions=False)
                if hist.empty or 'Close' not in hist.columns:
                    continue
                
                close_data = self._ensure_series(hist['Close'])
                price = info.get('currentPrice') or close_data.iloc[-1]
                try:
                    price = float(price)
                except (TypeError, ValueError):
                    price = float(close_data.iloc[-1])
                pe = info.get('trailingPE') or 0
                dividend = info.get('dividendRate') or 0
                close_returns = close_data.pct_change().dropna()
                volatility = float(close_returns.std() * np.sqrt(252)) if not close_returns.empty else 0.0
                change_1d = float(close_returns.iloc[-1] * 100) if not close_returns.empty else 0.0
                change_1m = float((close_data.iloc[-1] / close_data.iloc[-22] - 1) * 100) if len(close_data) > 22 else 0.0
                change_1y = float((close_data.iloc[-1] / close_data.iloc[0] - 1) * 100) if len(close_data) > 1 else 0.0
                sharpe_ratio = float(np.mean(close_returns) / (np.std(close_returns) + 1e-10) * np.sqrt(252)) if not close_returns.empty else 0.0
                
                stock_data = {
                    'symbol': symbol,
                    'name': info.get('longName') or symbol,
                    'price': price,
                    'pe': pe,
                    'pb': info.get('priceToBook') or 0,
                    'dividend': dividend,
                    'revenue': info.get('totalRevenue') or 0,
                    'market_cap': info.get('marketCap') or 0,
                    'eps': info.get('trailingEps') or 0,
                    'profit_margin': info.get('profitMargins') or 0,
                    'roe': info.get('returnOnEquity') or 0,
                    'debt_to_equity': info.get('debtToEquity') or 0,
                    'volatility': volatility,
                    'change_1d': change_1d,
                    'change_1m': change_1m,
                    'change_1y': change_1y,
                    'sharpe_ratio': sharpe_ratio
                }
                
                results.append(stock_data)
            except Exception as e:
                logger.error(f"Error comparing {symbol}: {e}")
                continue
        
        return pd.DataFrame(results)
    
    def relative_strength_analysis(self, symbols: List[str], days: int = 252) -> Dict:
        """Analyze relative strength between stocks"""
        
        try:
            prices = {}
            
            for symbol in symbols:
                hist = safe_download(
                    symbol,
                    start=datetime.now() - timedelta(days=days),
                    progress=False
                )
                
                if not hist.empty:
                    close_data = self._ensure_series(hist['Close'])
                    # Normalize to 100
                    prices[symbol] = (close_data / close_data.iloc[0]) * 100
            
            if not prices:
                return {}
            
            df = pd.DataFrame(prices)
            
            # Calculate relative strength
            strength_analysis = {}
            for symbol in symbols:
                if symbol in df.columns:
                    current_value = df[symbol].iloc[-1]
                    strength_analysis[symbol] = {
                        'current_value': float(current_value),
                        'rank': None,
                        'outperformer': current_value > 100,
                        'momentum': float(df[symbol].iloc[-1] - df[symbol].iloc[-20])
                    }
            
            # Rank performance
            sorted_symbols = sorted(
                strength_analysis.items(),
                key=lambda x: x[1]['current_value'],
                reverse=True
            )
            
            for rank, (symbol, data) in enumerate(sorted_symbols, 1):
                strength_analysis[symbol]['rank'] = rank
            
            return strength_analysis
        except Exception as e:
            logger.error(f"Error in relative strength analysis: {e}")
            return {}
    
    def sector_performance_comparison(self, symbols: List[str]) -> Dict:
        """Compare sector performance"""
        
        try:
            sectors = {}
            
            for symbol in symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    sector = ticker.info.get('sector', 'Unknown')
                    
                    if sector not in sectors:
                        sectors[sector] = []
                    
                    sectors[sector].append(symbol)
                except Exception as e:
                    logger.exception("Error fetching ticker info for %s in sector_performance_comparison", symbol)
            
            sector_analysis = {}
            
            for sector, sector_symbols in sectors.items():
                returns_list = []
                
                for symbol in sector_symbols:
                    try:
                        hist = safe_download(
                            symbol,
                            start=datetime.now() - timedelta(days=252),
                            progress=False
                        )
                        if not hist.empty:
                            close_data = self._ensure_series(hist['Close'])
                            returns = close_data.pct_change()
                            returns_list.extend(returns)
                    except Exception as e:
                        logger.exception("Error downloading historical data for %s in sector_performance_comparison", symbol)
                
                if returns_list:
                    sector_analysis[sector] = {
                        'count': len(sector_symbols),
                        'avg_return': float(np.mean(returns_list) * 252 * 100),
                        'volatility': float(np.std(returns_list) * np.sqrt(252)),
                        'stocks': sector_symbols
                    }
            
            return sector_analysis
        except Exception as e:
            logger.error(f"Error in sector analysis: {e}")
            return {}
    
    def correlation_heatmap_data(self, symbols: List[str], days: int = 252) -> Dict:
        """Generate data for correlation heatmap"""
        
        try:
            data = {}
            
            for symbol in symbols:
                hist = safe_download(
                    symbol,
                    start=datetime.now() - timedelta(days=days),
                    progress=False
                )
                
                if not hist.empty:
                    close_data = self._ensure_series(hist['Close'])
                    data[symbol] = close_data.pct_change()
            
            if not data:
                return {}
            
            df = pd.DataFrame(data)
            corr_matrix = df.corr()
            
            # Format for heatmap
            heatmap_data = {
                'labels': corr_matrix.columns.tolist(),
                'values': corr_matrix.values.tolist(),
                'min': float(corr_matrix.values.min()),
                'max': float(corr_matrix.values.max()),
                'mean': float(corr_matrix.values.mean())
            }
            
            return heatmap_data
        except Exception as e:
            logger.error(f"Error generating heatmap data: {e}")
            return {}
    
    def dividend_analysis(self, symbols: List[str]) -> pd.DataFrame:
        """Analyze dividends across stocks"""
        
        results = []
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                # Get dividend history
                div_history = ticker.dividends
                
                avg_dividend = 0
                if not div_history.empty:
                    avg_dividend = div_history.mean()
                
                results.append({
                    'symbol': symbol,
                    'dividend_rate': info.get('dividendRate', 0),
                    'dividend_yield': info.get('dividendYield', 0),
                    'payout_ratio': info.get('payoutRatio', 0),
                    'avg_dividend': float(avg_dividend),
                    'last_dividend_date': str(div_history.index[-1]) if not div_history.empty else 'N/A'
                })
            except Exception as e:
                logger.exception("Error fetching dividend data for %s", symbol)
        
        return pd.DataFrame(results)
    
    def growth_metrics_comparison(self, symbols: List[str]) -> pd.DataFrame:
        """Compare growth metrics"""
        
        results = []
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                results.append({
                    'symbol': symbol,
                    'revenue_growth': info.get('revenueGrowth', 0),
                    'earnings_growth': info.get('earningsGrowth', 0),
                    'roe': info.get('returnOnEquity', 0),
                    'roa': info.get('returnOnAssets', 0),
                    'roic': info.get('returnOnCapital', 0),
                    'peg_ratio': info.get('pegRatio', 0)
                })
            except Exception as e:
                logger.exception("Error fetching growth metrics for %s", symbol)
        
        return pd.DataFrame(results)
    
    def generate_comparison_report(self, symbols: List[str]) -> Dict:
        """Generate comprehensive comparison report"""
        
        try:
            report = {
                'symbols': symbols,
                'comparison_date': datetime.now().isoformat(),
                'metrics': self.compare_stocks(symbols).to_dict('records'),
                'relative_strength': self.relative_strength_analysis(symbols),
                'sector_analysis': self.sector_performance_comparison(symbols),
                'correlation_data': self.correlation_heatmap_data(symbols),
                'dividend_analysis': self.dividend_analysis(symbols).to_dict('records'),
                'growth_metrics': self.growth_metrics_comparison(symbols).to_dict('records')
            }
            
            return report
        except Exception as e:
            logger.error(f"Error generating comparison report: {e}")
            return {}
    
    def find_similar_stocks(self, symbol: str, market_cap_range: float = 0.3) -> List[str]:
        """Find similar stocks based on market cap, sector, and volatility"""
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            base_market_cap = info.get('marketCap', 0)
            base_sector = info.get('sector', '')
            
            if not base_market_cap or not base_sector:
                return []
            
            # This is simplified - in production you'd use a broader database
            # For now, return empty list as we'd need stock list database
            return []
        except Exception as e:
            logger.exception("Error finding similar stocks for %s", symbol)
            return []


# Singleton instance
_comparator = None


def get_stock_comparator():
    global _comparator
    if _comparator is None:
        _comparator = StockComparator()
    return _comparator
