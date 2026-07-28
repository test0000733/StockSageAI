"""
Real-Time Trading Signals Generator for SP 07 StockSageAI
Automatic Buy/Sell/Hold recommendations with confidence scores
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import yfinance as yf
import sqlite3
import logging

logger = logging.getLogger(__name__)


class TradingSignalsGenerator:
    """Generate real-time trading signals from ensemble predictions"""
    
    def __init__(self, db_path: str = 'users.db'):
        self.db_path = db_path
        self.init_signals_db()
    
    def init_signals_db(self):
        """Initialize signals database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trading_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                signal TEXT NOT NULL,
                confidence REAL NOT NULL,
                entry_price REAL,
                target_price REAL,
                stop_loss REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signal_accuracy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_id INTEGER NOT NULL,
                predicted_direction TEXT NOT NULL,
                actual_direction TEXT,
                accuracy REAL,
                outcome TEXT,
                closed_at TIMESTAMP,
                FOREIGN KEY(signal_id) REFERENCES trading_signals(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_signal(self, symbol: str, models_predictions: Dict[str, float],
                       current_price: float) -> Dict:
        """Generate trading signal from ensemble predictions"""
        
        try:
            # Aggregate predictions
            predictions = list(models_predictions.values())
            avg_prediction = np.mean(predictions)
            confidence = self._calculate_confidence(predictions)
            
            # Determine signal
            if avg_prediction > 0.05:
                signal = 'BUY'
            elif avg_prediction < -0.05:
                signal = 'SELL'
            else:
                signal = 'HOLD'
            
            # Calculate price targets
            target_price = current_price * (1 + avg_prediction * 0.02)
            stop_loss = current_price * (1 - confidence/100 * 0.01)
            
            # Get additional technical analysis
            hist = yf.download(symbol, period='3mo', progress_bar=False, quiet=True)
            
            rsi = self._calculate_rsi(hist['Close'])
            macd = self._calculate_macd(hist['Close'])
            volatility = hist['Close'].pct_change().std()
            
            return {
                'symbol': symbol,
                'signal': signal,
                'confidence': confidence,
                'entry_price': current_price,
                'target_price': target_price,
                'stop_loss': stop_loss,
                'avg_prediction': avg_prediction,
                'rsi': rsi,
                'macd': macd,
                'volatility': volatility,
                'model_votes': {
                    'buy': len([p for p in predictions if p > 0]),
                    'sell': len([p for p in predictions if p < 0]),
                    'hold': len([p for p in predictions if abs(p) <= 0.05])
                },
                'generated_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            return {}
    
    def _calculate_confidence(self, predictions: List[float]) -> float:
        """Calculate signal confidence"""
        if not predictions:
            return 0
        
        predictions = np.array(predictions)
        signs = np.sign(predictions)
        
        # Higher agreement = higher confidence
        agreement = np.sum(signs == signs[0]) / len(signs)
        
        # Higher deviation from 0 = higher confidence
        magnitude = np.mean(np.abs(predictions))
        
        confidence = agreement * 100 * 0.7 + magnitude * 0.3 * 100
        return min(max(confidence, 0), 100)
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])
    
    def _calculate_macd(self, prices: pd.Series) -> Dict:
        """Calculate MACD"""
        ema_12 = prices.ewm(span=12).mean()
        ema_26 = prices.ewm(span=26).mean()
        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9).mean()
        
        return {
            'macd': float(macd_line.iloc[-1]),
            'signal': float(signal_line.iloc[-1]),
            'histogram': float((macd_line - signal_line).iloc[-1])
        }
    
    def save_signal(self, user_id: str, signal_data: Dict) -> int:
        """Save signal to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO trading_signals
                (user_id, symbol, signal, confidence, entry_price, target_price, stop_loss, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                signal_data['symbol'],
                signal_data['signal'],
                signal_data['confidence'],
                signal_data['entry_price'],
                signal_data['target_price'],
                signal_data['stop_loss'],
                (datetime.now() + timedelta(days=7)).isoformat()
            ))
            
            signal_id = cursor.lastrowid
            conn.commit()
            return signal_id
        except Exception as e:
            logger.error(f"Error saving signal: {e}")
            return -1
        finally:
            conn.close()
    
    def get_active_signals(self, user_id: str) -> List[Dict]:
        """Get all active signals for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, symbol, signal, confidence, entry_price, target_price, stop_loss, created_at
                FROM trading_signals
                WHERE user_id = ? AND status = 'active' AND expires_at > datetime('now')
                ORDER BY confidence DESC
            ''', (user_id,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'symbol': row[1],
                    'signal': row[2],
                    'confidence': row[3],
                    'entry_price': row[4],
                    'target_price': row[5],
                    'stop_loss': row[6],
                    'created_at': row[7]
                })
            
            return results
        except:
            return []
        finally:
            conn.close()
    
    def track_signal_performance(self, signal_id: int, current_price: float) -> Dict:
        """Track signal performance"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'SELECT signal, entry_price, target_price, stop_loss FROM trading_signals WHERE id = ?',
                (signal_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                return {}
            
            signal_type, entry_price, target_price, stop_loss = row
            
            # Calculate performance
            pnl = current_price - entry_price
            pnl_pct = (pnl / entry_price) * 100
            
            # Determine outcome
            if signal_type == 'BUY':
                if current_price >= target_price:
                    outcome = 'PROFITABLE'
                elif current_price <= stop_loss:
                    outcome = 'STOPPED_OUT'
                else:
                    outcome = 'PENDING'
            elif signal_type == 'SELL':
                if current_price <= target_price:
                    outcome = 'PROFITABLE'
                elif current_price >= stop_loss:
                    outcome = 'STOPPED_OUT'
                else:
                    outcome = 'PENDING'
            else:
                outcome = 'PENDING'
            
            return {
                'signal_id': signal_id,
                'current_price': current_price,
                'entry_price': entry_price,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'outcome': outcome,
                'distance_to_target': abs((target_price - current_price) / entry_price) * 100
            }
        except:
            return {}
        finally:
            conn.close()
    
    def get_signal_accuracy_report(self, user_id: str, days: int = 30) -> Dict:
        """Generate signal accuracy report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            cursor.execute('''
                SELECT COUNT(*), 
                       SUM(CASE WHEN outcome = 'PROFITABLE' THEN 1 ELSE 0 END),
                       AVG(CASE WHEN accuracy IS NOT NULL THEN accuracy ELSE 0 END)
                FROM signal_accuracy
                WHERE user_id = ? AND closed_at > ?
            ''', (user_id, cutoff_date))
            
            row = cursor.fetchone()
            total_signals = row[0] if row[0] else 0
            profitable = row[1] if row[1] else 0
            avg_accuracy = row[2] if row[2] else 0
            
            accuracy_rate = (profitable / total_signals * 100) if total_signals > 0 else 0
            
            return {
                'total_signals': total_signals,
                'profitable': profitable,
                'win_rate': accuracy_rate,
                'avg_accuracy': avg_accuracy,
                'period_days': days
            }
        except:
            return {}
        finally:
            conn.close()


# Singleton instance
_signals_generator = None


def get_trading_signals_generator():
    global _signals_generator
    if _signals_generator is None:
        _signals_generator = TradingSignalsGenerator()
    return _signals_generator
