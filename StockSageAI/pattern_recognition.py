"""
Advanced Candlestick Pattern Recognition for SP 07 StockSageAI
Automatic pattern detection and probability scoring
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import yfinance as yf
from datetime import datetime, timedelta
import logging
from StockSageAI.utils import safe_download

logger = logging.getLogger(__name__)


class PatternRecognizer:
    """Recognize candlestick patterns and scoring"""
    
    def __init__(self):
        self.patterns = {
            'hammer': self.detect_hammer,
            'shooting_star': self.detect_shooting_star,
            'doji': self.detect_doji,
            'engulfing': self.detect_engulfing,
            'harami': self.detect_harami,
            'morning_star': self.detect_morning_star,
            'evening_star': self.detect_evening_star,
            'three_white_soldiers': self.detect_three_white_soldiers,
            'three_black_crows': self.detect_three_black_crows,
            'divergence': self.detect_divergence
        }
    
    def detect_all_patterns(self, symbol: str, lookback_days: int = 100) -> Dict:
        """Detect all patterns in recent data"""
        
        try:
            hist = safe_download(
                symbol,
                start=datetime.now() - timedelta(days=lookback_days),
                progress=False
            )
            
            if isinstance(hist.columns, pd.MultiIndex):
                try:
                    hist = hist.xs(symbol, axis=1, level='Ticker')
                except KeyError:
                    hist = hist.droplevel('Ticker', axis=1)
            
            if hist.empty or len(hist) < 3:
                return {}
            
            patterns_found = {}
            
            for pattern_name, detector in self.patterns.items():
                detected = detector(hist)
                if detected is None:
                    continue
                if isinstance(detected, pd.Series) and detected.empty:
                    continue
                patterns_found[pattern_name] = detected
            
            return {
                'symbol': symbol,
                'scan_date': datetime.now().isoformat(),
                'patterns': patterns_found,
                'total_patterns_found': len(patterns_found)
            }
        except Exception as e:
            logger.error(f"Error detecting patterns: {e}")
            return {}
    
    def detect_hammer(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect hammer pattern (bullish reversal)"""
        
        if len(df) < 2:
            return None
        
        # Hammer: small body, long lower shadow, little or no upper shadow
        body_height = abs(df['Close'].iloc[-1] - df['Open'].iloc[-1])
        total_height = df['High'].iloc[-1] - df['Low'].iloc[-1]
        lower_shadow = min(df['Open'].iloc[-1], df['Close'].iloc[-1]) - df['Low'].iloc[-1]
        upper_shadow = df['High'].iloc[-1] - max(df['Open'].iloc[-1], df['Close'].iloc[-1])
        
        if (body_height < total_height * 0.3 and
            lower_shadow > body_height * 2 and
            upper_shadow < body_height):
            
            return {
                'pattern': 'Hammer',
                'date': df.index[-1].strftime('%Y-%m-%d'),
                'probability': self._calculate_probability(body_height, lower_shadow, upper_shadow),
                'signal': 'BULLISH',
                'strength': 'MODERATE',
                'description': 'Potential reversal pattern indicating bullish pressure'
            }
        
        return None
    
    def detect_shooting_star(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect shooting star pattern (bearish reversal)"""
        
        if len(df) < 2:
            return None
        
        # Shooting star: small body, long upper shadow, little or no lower shadow
        body_height = abs(df['Close'].iloc[-1] - df['Open'].iloc[-1])
        total_height = df['High'].iloc[-1] - df['Low'].iloc[-1]
        upper_shadow = df['High'].iloc[-1] - max(df['Open'].iloc[-1], df['Close'].iloc[-1])
        lower_shadow = min(df['Open'].iloc[-1], df['Close'].iloc[-1]) - df['Low'].iloc[-1]
        
        if (body_height < total_height * 0.3 and
            upper_shadow > body_height * 2 and
            lower_shadow < body_height):
            
            return {
                'pattern': 'Shooting Star',
                'date': df.index[-1].strftime('%Y-%m-%d'),
                'probability': self._calculate_probability(body_height, upper_shadow, lower_shadow),
                'signal': 'BEARISH',
                'strength': 'MODERATE',
                'description': 'Potential reversal pattern indicating selling pressure'
            }
        
        return None
    
    def detect_doji(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect doji pattern (indecision)"""
        
        if len(df) < 1:
            return None
        
        # Doji: open and close nearly equal
        body_height = abs(df['Close'].iloc[-1] - df['Open'].iloc[-1])
        total_height = df['High'].iloc[-1] - df['Low'].iloc[-1]
        
        if body_height < total_height * 0.1:
            return {
                'pattern': 'Doji',
                'date': df.index[-1].strftime('%Y-%m-%d'),
                'probability': 70.0,
                'signal': 'NEUTRAL',
                'strength': 'WEAK',
                'description': 'Indecision pattern - price may continue trending'
            }
        
        return None
    
    def detect_engulfing(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect engulfing pattern"""
        
        if len(df) < 2:
            return None
        
        prev_open = df['Open'].iloc[-2]
        prev_close = df['Close'].iloc[-2]
        curr_open = df['Open'].iloc[-1]
        curr_close = df['Close'].iloc[-1]
        
        # Bullish engulfing
        if (prev_close > prev_open and
            curr_close > prev_open and
            curr_open < prev_close):
            
            return {
                'pattern': 'Bullish Engulfing',
                'date': df.index[-1].strftime('%Y-%m-%d'),
                'probability': 75.0,
                'signal': 'BULLISH',
                'strength': 'STRONG',
                'description': 'Strong bullish reversal pattern'
            }
        
        # Bearish engulfing
        elif (prev_close < prev_open and
              curr_close < prev_open and
              curr_open > prev_close):
            
            return {
                'pattern': 'Bearish Engulfing',
                'date': df.index[-1].strftime('%Y-%m-%d'),
                'probability': 75.0,
                'signal': 'BEARISH',
                'strength': 'STRONG',
                'description': 'Strong bearish reversal pattern'
            }
        
        return None
    
    def detect_harami(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect harami pattern"""
        
        if len(df) < 2:
            return None
        
        prev_open = df['Open'].iloc[-2]
        prev_close = df['Close'].iloc[-2]
        curr_open = df['Open'].iloc[-1]
        curr_close = df['Close'].iloc[-1]
        
        prev_body = abs(prev_close - prev_open)
        curr_body = abs(curr_close - curr_open)
        
        # Bullish harami
        if (prev_close > prev_open and
            curr_body < prev_body and
            curr_open > prev_close and
            curr_close < prev_open):
            
            return {
                'pattern': 'Bullish Harami',
                'date': df.index[-1].strftime('%Y-%m-%d'),
                'probability': 65.0,
                'signal': 'BULLISH',
                'strength': 'MODERATE',
                'description': 'Potential bullish reversal pattern'
            }
        
        return None
    
    def detect_morning_star(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect morning star pattern (3-day pattern)"""
        
        if len(df) < 3:
            return None
        
        # Three-day pattern for bullish reversal
        day1_body = abs(df['Close'].iloc[-3] - df['Open'].iloc[-3])
        day2_body = abs(df['Close'].iloc[-2] - df['Open'].iloc[-2])
        day3_close = df['Close'].iloc[-1]
        day1_close = df['Close'].iloc[-3]
        
        if (day1_body > 0 and
            day2_body < day1_body and
            day3_close > day1_close):
            
            return {
                'pattern': 'Morning Star',
                'date': df.index[-1].strftime('%Y-%m-%d'),
                'probability': 80.0,
                'signal': 'BULLISH',
                'strength': 'STRONG',
                'description': 'Strong 3-day bullish reversal pattern'
            }
        
        return None
    
    def detect_evening_star(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect evening star pattern (3-day pattern)"""
        
        if len(df) < 3:
            return None
        
        # Three-day pattern for bearish reversal
        day1_body = abs(df['Close'].iloc[-3] - df['Open'].iloc[-3])
        day2_body = abs(df['Close'].iloc[-2] - df['Open'].iloc[-2])
        day3_close = df['Close'].iloc[-1]
        day1_close = df['Close'].iloc[-3]
        
        if (day1_body > 0 and
            day2_body < day1_body and
            day3_close < day1_close):
            
            return {
                'pattern': 'Evening Star',
                'date': df.index[-1].strftime('%Y-%m-%d'),
                'probability': 80.0,
                'signal': 'BEARISH',
                'strength': 'STRONG',
                'description': 'Strong 3-day bearish reversal pattern'
            }
        
        return None
    
    def detect_three_white_soldiers(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect three white soldiers pattern"""
        
        if len(df) < 3:
            return None
        
        # Three consecutive up days
        if (df['Close'].iloc[-3] > df['Open'].iloc[-3] and
            df['Close'].iloc[-2] > df['Open'].iloc[-2] and
            df['Close'].iloc[-1] > df['Open'].iloc[-1] and
            df['Close'].iloc[-2] > df['Close'].iloc[-3] and
            df['Close'].iloc[-1] > df['Close'].iloc[-2]):
            
            return {
                'pattern': 'Three White Soldiers',
                'date': df.index[-1].strftime('%Y-%m-%d'),
                'probability': 85.0,
                'signal': 'BULLISH',
                'strength': 'VERY_STRONG',
                'description': 'Strong uptrend pattern with consecutive gains'
            }
        
        return None
    
    def detect_three_black_crows(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect three black crows pattern"""
        
        if len(df) < 3:
            return None
        
        # Three consecutive down days
        if (df['Close'].iloc[-3] < df['Open'].iloc[-3] and
            df['Close'].iloc[-2] < df['Open'].iloc[-2] and
            df['Close'].iloc[-1] < df['Open'].iloc[-1] and
            df['Close'].iloc[-2] < df['Close'].iloc[-3] and
            df['Close'].iloc[-1] < df['Close'].iloc[-2]):
            
            return {
                'pattern': 'Three Black Crows',
                'date': df.index[-1].strftime('%Y-%m-%d'),
                'probability': 85.0,
                'signal': 'BEARISH',
                'strength': 'VERY_STRONG',
                'description': 'Strong downtrend pattern with consecutive losses'
            }
        
        return None
    
    def detect_divergence(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect price/volume divergence"""
        
        if len(df) < 5:
            return None
        
        recent_prices = df['Close'].tail(5)
        recent_volumes = df['Volume'].tail(5)
        
        # Bullish divergence: lower lows in price, higher lows in volume
        price_trend = recent_prices.iloc[-1] < recent_prices.iloc[0]
        volume_trend = recent_volumes.iloc[-1] > recent_volumes.iloc[0]
        
        if price_trend and volume_trend:
            return {
                'pattern': 'Bullish Divergence',
                'date': df.index[-1].strftime('%Y-%m-%d'),
                'probability': 70.0,
                'signal': 'BULLISH',
                'strength': 'MODERATE',
                'description': 'Divergence suggests potential upside reversal'
            }
        
        elif not price_trend and not volume_trend:
            return {
                'pattern': 'Bearish Divergence',
                'date': df.index[-1].strftime('%Y-%m-%d'),
                'probability': 70.0,
                'signal': 'BEARISH',
                'strength': 'MODERATE',
                'description': 'Divergence suggests potential downside reversal'
            }
        
        return None
    
    def _calculate_probability(self, *values) -> float:
        """Calculate pattern probability based on shape metrics"""
        # Higher variance in metrics suggests stronger pattern
        prob = 60 + (np.std(values) * 5) if values else 60
        return min(max(prob, 50), 95)
    
    def get_pattern_statistics(self, symbol: str, days: int = 365) -> Dict:
        """Get statistics on pattern occurrences"""
        
        try:
            hist = safe_download(
                symbol,
                start=datetime.now() - timedelta(days=days),
                progress=False
            )
            
            if hist.empty:
                return {}
            
            pattern_counts = {name: 0 for name in self.patterns}
            bullish_count = 0
            bearish_count = 0
            
            # Scan each day for patterns
            for i in range(2, len(hist)):
                subset = hist.iloc[:i+1]
                
                for pattern_name, detector in self.patterns.items():
                    result = detector(subset)
                    if result:
                        pattern_counts[pattern_name] += 1
                        if result.get('signal') == 'BULLISH':
                            bullish_count += 1
                        elif result.get('signal') == 'BEARISH':
                            bearish_count += 1
            
            return {
                'symbol': symbol,
                'period_days': days,
                'scan_date': datetime.now().isoformat(),
                'pattern_counts': pattern_counts,
                'total_patterns': sum(pattern_counts.values()),
                'bullish_patterns': bullish_count,
                'bearish_patterns': bearish_count,
                'bullish_ratio': bullish_count / (sum(pattern_counts.values()) + 1)
            }
        except Exception as e:
            logger.error(f"Error getting pattern statistics: {e}")
            return {}


# Singleton instance
_pattern_recognizer = None


def get_pattern_recognizer():
    global _pattern_recognizer
    if _pattern_recognizer is None:
        _pattern_recognizer = PatternRecognizer()
    return _pattern_recognizer
