import numpy as np
import pandas as pd
from datetime import datetime, timedelta

class RecommendationEngine:
    """Generate BUY/SELL/HOLD recommendations based on predictions and sentiment"""
    
    def __init__(self):
        # Configurable thresholds
        self.price_thresholds = {
            'strong_buy': 0.08,    # 8% increase
            'buy': 0.05,           # 5% increase
            'hold_upper': 0.02,    # 2% increase
            'hold_lower': -0.02,   # -2% decrease
            'sell': -0.05,         # -5% decrease
            'strong_sell': -0.08   # -8% decrease
        }
        
        self.sentiment_weights = {
            'very_positive': 0.6,   # Strong positive sentiment
            'positive': 0.4,        # Mild positive sentiment
            'neutral': 0.0,         # Neutral sentiment
            'negative': -0.4,       # Mild negative sentiment
            'very_negative': -0.6   # Strong negative sentiment
        }
        
        self.volatility_penalty = 0.2  # Reduce confidence for high volatility
    
    def calculate_price_trend(self, stock_data, predictions):
        """Calculate price trend and expected return"""
        current_price = stock_data['Close'].iloc[-1]
        
        if len(predictions) == 0:
            return 0.0, 0.0
        
        predicted_price = predictions[-1]  # Final predicted price
        
        # Calculate percentage change
        price_change = (predicted_price - current_price) / current_price
        
        # Calculate trend strength (consistency of direction)
        if len(predictions) > 1:
            daily_changes = np.diff(predictions) / predictions[:-1]
            trend_consistency = np.mean(np.sign(daily_changes) == np.sign(price_change))
        else:
            trend_consistency = 0.5
        
        return price_change, trend_consistency
    
    def analyze_volatility(self, stock_data):
        """Analyze stock volatility for risk assessment"""
        # Calculate historical volatility (20-day)
        returns = stock_data['Close'].pct_change().dropna()
        volatility = returns.rolling(window=20).std().iloc[-1] * np.sqrt(252)  # Annualized
        
        # Volatility categories
        if volatility < 0.2:  # Low volatility
            risk_level = "Low"
            volatility_score = 0.8
        elif volatility < 0.4:  # Medium volatility
            risk_level = "Medium"
            volatility_score = 0.6
        else:  # High volatility
            risk_level = "High"
            volatility_score = 0.4
        
        return {
            'volatility': volatility,
            'risk_level': risk_level,
            'score': volatility_score
        }
    
    def analyze_technical_indicators(self, stock_data):
        """Analyze technical indicators for additional signals"""
        signals = {}
        
        # RSI analysis
        if 'RSI' in stock_data.columns:
            current_rsi = stock_data['RSI'].iloc[-1]
            if current_rsi > 70:
                signals['rsi'] = 'Overbought'
                signals['rsi_score'] = -0.3
            elif current_rsi < 30:
                signals['rsi'] = 'Oversold'
                signals['rsi_score'] = 0.3
            else:
                signals['rsi'] = 'Neutral'
                signals['rsi_score'] = 0.0
        else:
            signals['rsi_score'] = 0.0
        
        # Moving average analysis
        if 'MA_20' in stock_data.columns and 'MA_50' in stock_data.columns:
            current_price = stock_data['Close'].iloc[-1]
            ma_20 = stock_data['MA_20'].iloc[-1]
            ma_50 = stock_data['MA_50'].iloc[-1]
            
            if current_price > ma_20 > ma_50:
                signals['ma'] = 'Bullish'
                signals['ma_score'] = 0.2
            elif current_price < ma_20 < ma_50:
                signals['ma'] = 'Bearish'
                signals['ma_score'] = -0.2
            else:
                signals['ma'] = 'Mixed'
                signals['ma_score'] = 0.0
        else:
            signals['ma_score'] = 0.0
        
        return signals
    
    def sentiment_to_score(self, sentiment_scores):
        """Convert sentiment scores to recommendation score"""
        if not sentiment_scores:
            return 0.0, "Neutral"
        
        # Get overall sentiment
        overall_compounds = [s['compound'] for s in sentiment_scores]
        avg_compound = np.mean(overall_compounds)
        
        # Classify sentiment
        if avg_compound >= 0.3:
            sentiment_label = "Very Positive"
            sentiment_score = self.sentiment_weights['very_positive']
        elif avg_compound >= 0.1:
            sentiment_label = "Positive"
            sentiment_score = self.sentiment_weights['positive']
        elif avg_compound <= -0.3:
            sentiment_label = "Very Negative"
            sentiment_score = self.sentiment_weights['very_negative']
        elif avg_compound <= -0.1:
            sentiment_label = "Negative"
            sentiment_score = self.sentiment_weights['negative']
        else:
            sentiment_label = "Neutral"
            sentiment_score = self.sentiment_weights['neutral']
        
        return sentiment_score, sentiment_label
    
    def generate_recommendation(self, stock_data, predictions, sentiment_scores, forecast_days):
        """
        Generate final BUY/SELL/HOLD recommendation with error handling
        
        Args:
            stock_data: Historical stock data
            predictions: Price predictions
            sentiment_scores: News sentiment analysis
            forecast_days: Number of forecast days
        
        Returns:
            Dictionary with recommendation details
        """
        try:
            # Validate inputs
            if stock_data is None or stock_data.empty:
                raise ValueError("Stock data is empty")
            
            if predictions is None or len(predictions) == 0:
                raise ValueError("Predictions are empty")
            
            # Calculate price trend with error handling
            try:
                price_change, trend_consistency = self.calculate_price_trend(stock_data, predictions)
            except Exception as e:
                price_change, trend_consistency = 0.0, 0.5
            
            # Analyze volatility with error handling
            try:
                volatility_analysis = self.analyze_volatility(stock_data)
            except Exception as e:
                volatility_analysis = {
                    'volatility': 0.25,
                    'risk_level': 'Medium',
                    'score': 0.6
                }
            
            # Analyze technical indicators with error handling
            try:
                technical_signals = self.analyze_technical_indicators(stock_data)
            except Exception as e:
                technical_signals = {
                    'rsi': 'Neutral',
                    'rsi_score': 0.0,
                    'ma': 'Mixed',
                    'ma_score': 0.0
                }
            
            # Convert sentiment to score with error handling
            try:
                sentiment_score, sentiment_label = self.sentiment_to_score(sentiment_scores)
            except Exception as e:
                sentiment_score, sentiment_label = 0.0, "Neutral"
            
            # Calculate base recommendation score
            base_score = price_change
            
            # Apply sentiment adjustment
            sentiment_adjusted_score = base_score + sentiment_score
            
            # Apply technical indicator adjustments
            technical_adjustment = technical_signals.get('rsi_score', 0) + technical_signals.get('ma_score', 0)
            final_score = sentiment_adjusted_score + technical_adjustment
            
            # Determine action based on final score
            if final_score >= self.price_thresholds['strong_buy']:
                action = "BUY"
                action_strength = "Strong"
            elif final_score >= self.price_thresholds['buy']:
                action = "BUY"
                action_strength = "Moderate"
            elif final_score <= self.price_thresholds['strong_sell']:
                action = "SELL"
                action_strength = "Strong"
            elif final_score <= self.price_thresholds['sell']:
                action = "SELL"
                action_strength = "Moderate"
            else:
                action = "HOLD"
                action_strength = "Neutral"
            
            # Calculate confidence
            base_confidence = min(abs(final_score) * 10, 1.0)  # Scale to 0-1
            volatility_penalty = (1 - volatility_analysis.get('score', 0.6)) * self.volatility_penalty
            trend_bonus = trend_consistency * 0.2
            
            confidence = max(0.1, min(0.95, base_confidence - volatility_penalty + trend_bonus))
            
            # Generate reasoning
            reasoning = self._generate_reasoning(
                price_change, sentiment_label, volatility_analysis,
                technical_signals, action, forecast_days
            )
            
            return {
                'action': action,
                'confidence': confidence * 100,  # Convert to percentage
                'reasoning': reasoning,
                'details': {
                    'price_change_pct': price_change * 100,
                    'sentiment_score': sentiment_score,
                    'sentiment_label': sentiment_label,
                    'volatility': volatility_analysis,
                    'technical_signals': technical_signals,
                    'trend_consistency': trend_consistency,
                    'final_score': final_score
                }
            }
        
        except Exception as e:
            # Return safe default recommendation on error
            return {
                'action': 'HOLD',
                'confidence': 25.0,
                'reasoning': f'Unable to generate recommendation: {str(e)}. Please review market conditions manually.',
                'details': {
                    'price_change_pct': 0.0,
                    'sentiment_score': 0.0,
                    'sentiment_label': 'Unknown',
                    'volatility': {'volatility': 0, 'risk_level': 'Unknown', 'score': 0.5},
                    'technical_signals': {},
                    'trend_consistency': 0.5,
                    'final_score': 0.0
                }
            }
    
    def _generate_reasoning(self, price_change, sentiment_label, volatility_analysis, 
                          technical_signals, action, forecast_days):
        """Generate human-readable reasoning for the recommendation"""
        
        price_change_pct = price_change * 100
        
        reasoning_parts = []
        
        # Price trend reasoning
        if price_change_pct > 5:
            reasoning_parts.append(f"Strong upward price trend expected (+{price_change_pct:.1f}%)")
        elif price_change_pct > 2:
            reasoning_parts.append(f"Moderate upward price trend expected (+{price_change_pct:.1f}%)")
        elif price_change_pct < -5:
            reasoning_parts.append(f"Strong downward price trend expected ({price_change_pct:.1f}%)")
        elif price_change_pct < -2:
            reasoning_parts.append(f"Moderate downward price trend expected ({price_change_pct:.1f}%)")
        else:
            reasoning_parts.append(f"Sideways price movement expected ({price_change_pct:.1f}%)")
        
        # Sentiment reasoning
        if sentiment_label != "Neutral":
            reasoning_parts.append(f"{sentiment_label.lower()} news sentiment")
        
        # Volatility reasoning
        if volatility_analysis['risk_level'] == "High":
            reasoning_parts.append("high volatility indicates increased risk")
        elif volatility_analysis['risk_level'] == "Low":
            reasoning_parts.append("low volatility suggests stable movement")
        
        # Technical signals
        if 'rsi' in technical_signals:
            if technical_signals['rsi'] != 'Neutral':
                reasoning_parts.append(f"RSI indicates {technical_signals['rsi'].lower()} conditions")
        
        if 'ma' in technical_signals:
            if technical_signals['ma'] != 'Mixed':
                reasoning_parts.append(f"{technical_signals['ma'].lower()} moving average pattern")
        
        # Combine reasoning
        reasoning = ". ".join(reasoning_parts).capitalize()
        
        # Add time horizon
        reasoning += f" over {forecast_days}-day forecast period."
        
        return reasoning
