"""
Enhanced AI Forecasting Module for SP 07
Powerful, accurate ensemble-based stock prediction system
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# ============================================================================
# ENHANCED AI FORECASTING ENGINE
# ============================================================================

class EnhancedAIForecaster(ABC):
    """Base class for enhanced AI forecasting"""

    @abstractmethod
    def predict(self, features: np.ndarray) -> Tuple[float, float, str]:
        """
        Generate prediction
        Returns: (prediction, confidence, signal)
        """
        pass

    @abstractmethod
    def get_reasoning(self) -> Dict:
        """Get detailed reasoning for prediction"""
        pass


class EnsembleForecaster:
    """Powerful ensemble forecasting system combining multiple models"""

    def __init__(self):
        self.models = {}
        self.weights = {}
        self.last_predictions = {}

    def register_model(self, name: str, predictor: EnhancedAIForecaster, weight: float = 1.0):
        """Register a model in ensemble"""
        self.models[name] = predictor
        self.weights[name] = weight
        logger.info(f"Registered model: {name} with weight {weight}")

    def predict(self, symbol: str, data: pd.DataFrame) -> Dict:
        """Generate ensemble prediction"""
        predictions = {}
        confidences = []
        signals = []

        try:
            # Extract features
            features = self._extract_features(data)

            # Get predictions from all models
            for model_name, model in self.models.items():
                try:
                    pred, conf, sig = model.predict(features)
                    predictions[model_name] = {
                        'value': pred,
                        'confidence': conf,
                        'signal': sig,
                        'weight': self.weights[model_name]
                    }
                    confidences.append(conf * self.weights[model_name])
                    signals.append((sig, conf, self.weights[model_name]))
                except Exception as e:
                    logger.error(f"Error in {model_name}: {str(e)}")
                    predictions[model_name] = {'error': str(e)}

            # Calculate ensemble prediction
            ensemble_result = self._calculate_ensemble(predictions, features, symbol, data)

            return {
                'ensemble_prediction': ensemble_result['prediction'],
                'ensemble_confidence': ensemble_result['confidence'],
                'ensemble_signal': ensemble_result['signal'],
                'individual_predictions': predictions,
                'model_reasoning': ensemble_result['reasoning'],
                'risk_level': ensemble_result['risk_level'],
                'recommendation': ensemble_result['recommendation'],
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Ensemble prediction failed: {str(e)}")
            return {
                'error': str(e),
                'ensemble_prediction': None,
                'timestamp': datetime.now().isoformat()
            }

    def _extract_features(self, data: pd.DataFrame) -> np.ndarray:
        """Extract comprehensive features from market data"""
        features = {}

        # Price features
        features['current_price'] = data['close'].iloc[-1]
        features['price_change'] = (data['close'].iloc[-1] - data['close'].iloc[-5]) / data['close'].iloc[-5]
        features['volatility'] = data['close'].rolling(20).std().iloc[-1] / data['close'].iloc[-1]

        # Trend features
        features['ma_5'] = data['close'].rolling(5).mean().iloc[-1]
        features['ma_20'] = data['close'].rolling(20).mean().iloc[-1]
        features['ma_50'] = data['close'].rolling(50).mean().iloc[-1]

        # Momentum features
        features['rsi'] = self._calculate_rsi(data['close'])
        features['macd'] = self._calculate_macd(data['close'])

        # Volume features
        if 'volume' in data.columns:
            features['volume_ma'] = data['volume'].rolling(20).mean().iloc[-1]
            features['volume_ratio'] = data['volume'].iloc[-1] / features['volume_ma']

        return np.array([v for v in features.values()])

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss if loss.iloc[-1] != 0 else 0
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]

    def _calculate_macd(self, prices: pd.Series) -> float:
        """Calculate MACD signal"""
        exp1 = prices.ewm(span=12).mean()
        exp2 = prices.ewm(span=26).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9).mean()
        return (macd - signal).iloc[-1]

    def _calculate_ensemble(self, predictions: Dict, features: np.ndarray, symbol: str, data: pd.DataFrame) -> Dict:
        """Calculate weighted ensemble prediction"""
        valid_predictions = [p for p in predictions.values() if 'error' not in p]

        if not valid_predictions:
            return {
                'prediction': None,
                'confidence': 0,
                'signal': 'neutral',
                'reasoning': 'No valid predictions',
                'risk_level': 'high',
                'recommendation': 'HOLD'
            }

        # Weighted average prediction
        weighted_sum = sum(p['value'] * p['weight'] for p in valid_predictions)
        weight_sum = sum(p['weight'] for p in valid_predictions)
        ensemble_pred = weighted_sum / weight_sum if weight_sum > 0 else 0

        # Average confidence
        avg_confidence = sum(p['confidence'] * p['weight'] for p in valid_predictions) / weight_sum

        # Majority signal
        signals_weighted = {}
        for pred in valid_predictions:
            sig = pred['signal']
            signals_weighted[sig] = signals_weighted.get(sig, 0) + pred['weight']
        ensemble_signal = max(signals_weighted, key=signals_weighted.get)

        # Risk assessment
        risk_level = self._assess_risk(features, data)

        # Generate recommendation
        recommendation = self._generate_recommendation(ensemble_pred, ensemble_signal, risk_level, data)

        return {
            'prediction': ensemble_pred,
            'confidence': avg_confidence,
            'signal': ensemble_signal,
            'reasoning': self._generate_reasoning(predictions, risk_level),
            'risk_level': risk_level,
            'recommendation': recommendation
        }

    def _assess_risk(self, features: np.ndarray, data: pd.DataFrame) -> str:
        """Assess risk level"""
        volatility = features[2]  # volatility index
        if volatility > 0.1:
            return 'high'
        elif volatility > 0.05:
            return 'medium'
        return 'low'

    def _generate_recommendation(self, prediction: float, signal: str, risk_level: str, data: pd.DataFrame) -> str:
        """Generate actionable recommendation"""
        if signal == 'buy' and risk_level == 'low':
            return 'STRONG_BUY'
        elif signal == 'buy':
            return 'BUY'
        elif signal == 'sell' and risk_level == 'low':
            return 'STRONG_SELL'
        elif signal == 'sell':
            return 'SELL'
        return 'HOLD'

    def _generate_reasoning(self, predictions: Dict, risk_level: str) -> Dict:
        """Generate detailed reasoning"""
        return {
            'model_consensus': len([p for p in predictions.values() if 'error' not in p]),
            'total_models': len(predictions),
            'risk_assessment': risk_level,
            'generated_at': datetime.now().isoformat()
        }


# ============================================================================
# SPECIALIZED FORECASTERS
# ============================================================================

class TrendForecaster(EnhancedAIForecaster):
    """Trend-based forecaster using moving averages"""

    def predict(self, features: np.ndarray) -> Tuple[float, float, str]:
        """Predict based on trend analysis"""
        # features[4:7] are MA5, MA20, MA50
        ma5, ma20, ma50 = features[4:7]

        if ma5 > ma20 > ma50:
            signal = 'buy'
            confidence = 0.85
        elif ma5 < ma20 < ma50:
            signal = 'sell'
            confidence = 0.85
        else:
            signal = 'neutral'
            confidence = 0.60

        prediction = ma5
        return prediction, confidence, signal

    def get_reasoning(self) -> Dict:
        return {'model': 'TrendForecaster', 'method': 'Moving Average Crossover'}


class MomentumForecaster(EnhancedAIForecaster):
    """Momentum-based forecaster using RSI and MACD"""

    def predict(self, features: np.ndarray) -> Tuple[float, float, str]:
        """Predict based on momentum"""
        # features[7:9] are RSI and MACD
        rsi, macd = features[7:9]

        if rsi > 70 and macd > 0:
            signal = 'buy'
            confidence = 0.80
        elif rsi < 30 and macd < 0:
            signal = 'sell'
            confidence = 0.80
        else:
            signal = 'neutral'
            confidence = 0.65

        prediction = rsi / 10  # Normalize RSI to useful scale
        return prediction, confidence, signal

    def get_reasoning(self) -> Dict:
        return {'model': 'MomentumForecaster', 'method': 'RSI and MACD'}


class VolatilityForecaster(EnhancedAIForecaster):
    """Volatility-aware forecaster"""

    def predict(self, features: np.ndarray) -> Tuple[float, float, str]:
        """Predict based on volatility analysis"""
        # features[2] is volatility
        volatility = features[2]

        if volatility > 0.1:
            signal = 'sell'
            confidence = 0.75
        elif volatility < 0.03:
            signal = 'buy'
            confidence = 0.70
        else:
            signal = 'neutral'
            confidence = 0.60

        prediction = 1.0 - volatility  # Inverse relationship
        return prediction, confidence, signal

    def get_reasoning(self) -> Dict:
        return {'model': 'VolatilityForecaster', 'method': 'Volatility Analysis'}


class VolumeForecaster(EnhancedAIForecaster):
    """Volume-based forecaster for trend confirmation"""

    def predict(self, features: np.ndarray) -> Tuple[float, float, str]:
        """Predict based on volume analysis"""
        # features[9] is volume ratio
        volume_ratio = features[9] if len(features) > 9 else 1.0

        if volume_ratio > 1.5:
            signal = 'buy'
            confidence = 0.78
        elif volume_ratio < 0.5:
            signal = 'sell'
            confidence = 0.72
        else:
            signal = 'neutral'
            confidence = 0.60

        prediction = volume_ratio
        return prediction, confidence, signal

    def get_reasoning(self) -> Dict:
        return {'model': 'VolumeForecaster', 'method': 'Volume Analysis'}


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_enhanced_ensemble() -> EnsembleForecaster:
    """Create and configure enhanced ensemble forecaster"""
    ensemble = EnsembleForecaster()

    # Register all models with appropriate weights
    ensemble.register_model('trend', TrendForecaster(), weight=0.35)
    ensemble.register_model('momentum', MomentumForecaster(), weight=0.35)
    ensemble.register_model('volatility', VolatilityForecaster(), weight=0.15)
    ensemble.register_model('volume', VolumeForecaster(), weight=0.15)

    return ensemble
