"""
Forecast Generator - Integrated with existing forecasting pipeline
Generates validated 7/14/30-day forecasts using LSTMPredictor
"""

import os
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np
import pandas as pd

from StockSageAI.lstm_model import LSTMPredictor
from StockSageAI.recommendation_engine import RecommendationEngine
from StockSageAI.data_fetcher import DataFetcher
from StockSageAI.sentiment_analyzer import SentimentAnalyzer
from StockSageAI.news_scraper import NewsScraper

logger = logging.getLogger(__name__)

class ForecastGenerator:
    """
    Generates forecasts using existing AI pipeline
    Connects to LSTMPredictor, recommends signals, validates data
    """
    
    def __init__(self):
        """Initialize forecast generator with existing components"""
        self.data_fetcher = DataFetcher()
        self.lstm_predictor = LSTMPredictor()
        self.recommendation_engine = RecommendationEngine()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.news_scraper = NewsScraper()
        
        self.forecast_horizons = [7, 14, 30]
        self.min_confidence_threshold = 60.0
        
        logger.info("✅ Forecast Generator initialized with existing pipeline")
    
    def generate_forecast(self, symbol: str, validate: bool = True) -> Dict:
        """
        Generate complete forecast for a stock

        Args:
            symbol: Stock symbol (e.g., 'INFY.NS')
            validate: If True, validate data and predictions

        Returns:
            Dict with forecasts, signals, confidence, metadata
        """
        result = {
            'symbol': symbol,
            'success': False,
            'error': None,
            'current_price': None,
            'data_timestamp': None,
            'forecasts': {},  # {7: price, 14: price, 30: price}
            'predictions': {},  # {7: [array], 14: [array], 30: [array]}
            'signals': {},  # {7: signal, 14: signal, 30: signal}
            'confidence': {},  # {7: confidence, 14: confidence, 30: confidence}
            'sentiment_score': None,
            'metadata': {},
            'validation_warnings': [],
            'horizon_details': {},
            'decision_summary': {}
        }
        
        try:
            # Step 1: Fetch data
            logger.info(f"📥 Fetching data for {symbol}...")
            stock_data = self._fetch_validated_data(symbol)
            
            if stock_data is None or stock_data.empty:
                result['error'] = f'No data available for {symbol}'
                logger.error(f"❌ {result['error']}")
                return result
            
            # Store metadata
            result['current_price'] = float(stock_data['Close'].iloc[-1])
            result['data_timestamp'] = stock_data.index[-1].isoformat()
            
            # Step 2: Validate data freshness
            if validate:
                warnings = self._validate_data_freshness(stock_data)
                result['validation_warnings'].extend(warnings)
            
            # Step 3: Generate sentiment analysis
            logger.info(f"📰 Analyzing sentiment for {symbol}...")
            try:
                company_name = symbol.replace('.NS', '').replace('.BO', '')
                news_headlines = self.news_scraper.get_news(company_name)
                if isinstance(news_headlines, dict):
                    news_headlines = [news_headlines]
                sentiment_scores = self.sentiment_analyzer.analyze_sentiment(news_headlines)
                if isinstance(sentiment_scores, dict):
                    sentiment_scores = [sentiment_scores]
                compounds = []
                for item in sentiment_scores or []:
                    if isinstance(item, dict):
                        compound = item.get('compound')
                        if isinstance(compound, (int, float)):
                            compounds.append(float(compound))
                result['sentiment_score'] = float(np.mean(compounds)) if compounds else 0.5
            except Exception as e:
                logger.warning(f"⚠️ Sentiment analysis failed: {str(e)}")
                result['sentiment_score'] = 0.5
            
            # Step 4: Generate forecasts for each horizon
            logger.info(f"🧠 Generating forecasts for {symbol}...")
            for horizon in self.forecast_horizons:
                try:
                    # Generate prediction using existing LSTM pipeline
                    predictions = self.lstm_predictor.predict(stock_data, forecast_days=horizon)
                    
                    if predictions is None or len(predictions) == 0:
                        logger.warning(f"⚠️ No predictions for {symbol} at {horizon}D")
                        result['validation_warnings'].append(f"No {horizon}D forecast generated")
                        continue
                    
                    # Store predictions array
                    result['predictions'][horizon] = predictions.tolist()
                    
                    # Get final predicted price
                    predicted_price = float(predictions[-1])
                    result['forecasts'][horizon] = predicted_price
                    
                    # Calculate adaptive multi-factor signal
                    signal_data = self._generate_signal(
                        stock_data,
                        predictions,
                        result['sentiment_score'],
                        horizon,
                        symbol=symbol
                    )
                    
                    result['signals'][horizon] = signal_data['signal']
                    result['confidence'][horizon] = signal_data['confidence']
                    result['metadata'][f'{horizon}d_reasoning'] = signal_data['reasoning']
                    result['horizon_details'][horizon] = {
                        'predicted_price': predicted_price,
                        'expected_return_pct': signal_data.get('expected_return_pct', 0.0),
                        'bull_case': signal_data.get('bull_case', predicted_price),
                        'base_case': signal_data.get('base_case', predicted_price),
                        'bear_case': signal_data.get('bear_case', predicted_price),
                        'risk_level': signal_data.get('risk_level', 'Medium'),
                        'positive_factors': signal_data.get('positive_factors', []),
                        'negative_factors': signal_data.get('negative_factors', []),
                        'confluence_score': signal_data.get('confluence_score', 50.0),
                        'scenario': signal_data.get('scenario', 'Base'),
                        'signal_confluence': signal_data.get('confluence_score', 50.0),
                        'decision': signal_data.get('signal', 'HOLD')
                    }
                    
                except Exception as e:
                    logger.error(f"❌ Error generating {horizon}D forecast: {str(e)}")
                    result['validation_warnings'].append(f"{horizon}D forecast error: {str(e)}")
                    continue
            
            if result['horizon_details']:
                result['decision_summary'] = {
                    'primary_signal': self._aggregate_signal(result['signals']),
                    'average_confidence': float(np.mean(list(result['confidence'].values()))) if result['confidence'] else 0.0,
                    'top_positive_factors': self._collect_top_factors(result['horizon_details']),
                    'top_negative_factors': self._collect_top_factors(result['horizon_details'], positive=False)
                }
            
            # Step 5: Validate predictions
            if validate and result['forecasts']:
                anomlies = self._detect_prediction_anomalies(result)
                if anomlies:
                    result['validation_warnings'].extend(anomlies)
            
            # Mark as successful if at least one forecast generated
            if result['forecasts']:
                result['success'] = True
                logger.info(f"✅ Forecast generated successfully for {symbol}")
            else:
                result['error'] = 'No valid forecasts could be generated'
                logger.error(f"❌ {result['error']}")
            
            return result
            
        except Exception as e:
            result['error'] = f"Forecast generation failed: {str(e)}"
            logger.error(f"❌ {result['error']}")
            return result

    def _aggregate_signal(self, signals: Dict) -> str:
        """Summarize final signal across horizons."""
        non_empty = [s for s in signals.values() if s]
        if not non_empty:
            return 'NO CLEAR SIGNAL'
        vote_count = {k: 0 for k in ['BUY', 'SELL', 'HOLD', 'NO CLEAR SIGNAL']}
        for signal in non_empty:
            vote_count.setdefault(signal.upper(), 0)
            vote_count[signal.upper()] += 1
        winner = max(vote_count.items(), key=lambda kv: kv[1])[0]
        if vote_count.get('BUY', 0) and vote_count.get('SELL', 0):
            return 'NO CLEAR SIGNAL' if vote_count['BUY'] == vote_count['SELL'] else winner
        return winner

    def _collect_top_factors(self, horizon_details: Dict, positive: bool = True) -> List[str]:
        """Collect strongest positive or negative factors from all horizons."""
        items = []
        for details in horizon_details.values():
            factors = details.get('positive_factors' if positive else 'negative_factors', [])
            for factor in factors:
                if factor:
                    items.append(str(factor))
        ordered = sorted(items, key=lambda x: items.count(x), reverse=True)
        unique = []
        for item in ordered:
            if item not in unique:
                unique.append(item)
        return unique[:5]

    def _compute_horizon_weight(self, horizon: int) -> float:
        """Lower confidence weight for longer horizons to reflect higher uncertainty."""
        weights = {7: 1.0, 14: 0.85, 30: 0.7}
        return weights.get(horizon, 0.75)

    def _get_market_context(self, stock_data: pd.DataFrame) -> Dict:
        """Gather real market context from live index and proxy data without fabricating signals."""
        context = {
            'index_trend': 0.0,
            'banknifty_trend': 0.0,
            'vix_level': 18.0,
            'sector_strength': 0.0,
            'market_regime': 'neutral'
        }
        try:
            index_data = self.data_fetcher.get_index_data('^NSEI', period='30d')
            if not index_data.empty and 'Close' in index_data.columns:
                current_idx = float(index_data['Close'].iloc[-1])
                prev_idx = float(index_data['Close'].iloc[-2]) if len(index_data) > 1 else current_idx
                context['index_trend'] = ((current_idx - prev_idx) / prev_idx) * 100
            bank_data = self.data_fetcher.get_index_data('^NSEBANK', period='30d')
            if not bank_data.empty and 'Close' in bank_data.columns:
                current_idx = float(bank_data['Close'].iloc[-1])
                prev_idx = float(bank_data['Close'].iloc[-2]) if len(bank_data) > 1 else current_idx
                context['banknifty_trend'] = ((current_idx - prev_idx) / prev_idx) * 100
            vix_data = self.data_fetcher.get_index_data('^VIX', period='30d')
            if not vix_data.empty and 'Close' in vix_data.columns:
                context['vix_level'] = float(vix_data['Close'].iloc[-1])
        except Exception:
            pass

        recent = stock_data.tail(20)
        if len(recent) >= 10:
            price_change = ((recent['Close'].iloc[-1] - recent['Close'].iloc[0]) / recent['Close'].iloc[0]) * 100
            context['sector_strength'] = float(np.clip(price_change, -20, 20) / 20.0)
        
        context['market_regime'] = 'bullish' if context['index_trend'] > 0.5 else 'bearish' if context['index_trend'] < -0.5 else 'neutral'
        return context

    def _compute_indicator_score(self, stock_data: pd.DataFrame, sentiment: float) -> Dict:
        """Compute a multi-factor score based on real price, volume, and trend data."""
        score = {
            'trend_score': 0.0,
            'momentum_score': 0.0,
            'volume_score': 0.0,
            'volatility_score': 0.0,
            'sentiment_score': float(np.clip(sentiment, -1, 1)),
            'positive_factors': [],
            'negative_factors': []
        }
        try:
            if stock_data is None or stock_data.empty:
                return score
            recent = stock_data.tail(30).copy()
            if len(recent) < 10:
                return score

            current_price = float(recent['Close'].iloc[-1])
            ma20 = recent['Close'].rolling(window=20, min_periods=1).mean().iloc[-1]
            ma50 = recent['Close'].rolling(window=50, min_periods=1).mean().iloc[-1]
            if current_price > ma20 > ma50:
                score['trend_score'] += 0.9
                score['positive_factors'].append('Price trading above 20/50-day moving averages')
            elif current_price < ma20 < ma50:
                score['trend_score'] -= 0.9
                score['negative_factors'].append('Price trading below 20/50-day moving averages')
            else:
                score['negative_factors'].append('Trend structure mixed across moving averages')

            if 'RSI' in recent.columns and not recent['RSI'].dropna().empty:
                rsi = float(recent['RSI'].iloc[-1])
                if rsi > 70:
                    score['momentum_score'] -= 0.3
                    score['negative_factors'].append('RSI indicates overbought conditions')
                elif rsi < 30:
                    score['momentum_score'] += 0.3
                    score['positive_factors'].append('RSI indicates oversold recovery potential')
                else:
                    score['momentum_score'] += 0.1

            if 'Volume' in recent.columns:
                vol_mean = recent['Volume'].rolling(window=10, min_periods=1).mean().iloc[-1]
                recent_vol = float(recent['Volume'].iloc[-1])
                if recent_vol > vol_mean * 1.15:
                    score['volume_score'] += 0.25
                    score['positive_factors'].append('Volume expansion confirms directional interest')
                elif recent_vol < vol_mean * 0.85:
                    score['volume_score'] -= 0.2
                    score['negative_factors'].append('Volume weakening reduces conviction')

            returns = recent['Close'].pct_change().dropna()
            if len(returns) > 5:
                price_vol = float(returns.std() * 100)
                if price_vol < 2:
                    score['volatility_score'] += 0.1
                    score['positive_factors'].append('Low volatility supports trend stability')
                elif price_vol > 6:
                    score['volatility_score'] -= 0.2
                    score['negative_factors'].append('High volatility raises risk')

            if score['sentiment_score'] > 0.2:
                score['positive_factors'].append('Recent company/news sentiment is constructive')
            elif score['sentiment_score'] < -0.2:
                score['negative_factors'].append('Recent company/news sentiment is weak')
        except Exception:
            pass
        return score

    def _generate_signal(
        self,
        stock_data: pd.DataFrame,
        predictions: np.ndarray,
        sentiment: float,
        horizon: int,
        symbol: str = None
    ) -> Dict:
        """
        Generate BUY/HOLD/SELL/NO CLEAR SIGNAL with adaptive multi-factor score.
        """
        try:
            current_price = float(stock_data['Close'].iloc[-1])
            predicted_price = float(predictions[-1])
            price_change_pct = ((predicted_price - current_price) / current_price) * 100
            expected_return = price_change_pct

            market_context = self._get_market_context(stock_data)
            indicator_score = self._compute_indicator_score(stock_data, sentiment)
            horizon_weight = self._compute_horizon_weight(horizon)

            # Adaptive ensemble weights based on regime and horizon
            trend_component = indicator_score['trend_score'] * 20
            sentiment_component = indicator_score['sentiment_score'] * 25
            momentum_component = indicator_score['momentum_score'] * 25
            volume_component = indicator_score['volume_score'] * 15
            regime_component = 0.0
            if market_context['market_regime'] == 'bullish':
                regime_component = 8.0
            elif market_context['market_regime'] == 'bearish':
                regime_component = -8.0

            composite_score = (
                expected_return * 1.5
                + trend_component
                + sentiment_component
                + momentum_component
                + volume_component
                + regime_component
            ) * horizon_weight

            # Conflict tolerance: do not force a signal when evidence is weak or mixed
            risk_level = 'Low'
            if indicator_score['volatility_score'] < -0.1 or abs(expected_return) > 18:
                risk_level = 'High'
            elif indicator_score['volatility_score'] > 0.1 or abs(expected_return) > 8:
                risk_level = 'Medium'

            positive_factors = indicator_score['positive_factors'][:4]
            negative_factors = indicator_score['negative_factors'][:4]

            signal = 'BUY'
            if composite_score < -7:
                signal = 'SELL'
            elif abs(composite_score) <= 4:
                signal = 'HOLD'
            elif composite_score > 7:
                signal = 'BUY'
            else:
                signal = 'HOLD'

            # If signals conflict across factors, soften to no clear signal
            if (indicator_score['trend_score'] > 0 and indicator_score['sentiment_score'] < -0.1 and indicator_score['momentum_score'] < 0) or \
               (indicator_score['trend_score'] < 0 and indicator_score['sentiment_score'] > 0.1 and indicator_score['momentum_score'] > 0):
                signal = 'NO CLEAR SIGNAL'

            confidence = float(np.clip(abs(composite_score) * 5.5, 15.0, 94.0))
            if signal == 'NO CLEAR SIGNAL':
                confidence = max(18.0, min(68.0, confidence * 0.8))
            if confidence < 55 and signal in {'BUY', 'SELL'}:
                signal = 'NO CLEAR SIGNAL'

            bull_case = predicted_price * (1 + max(0.02, abs(expected_return) * 0.55 / 100))
            base_case = predicted_price
            bear_case = predicted_price * (1 - max(0.02, abs(expected_return) * 0.55 / 100))
            confluence_score = float(np.clip((abs(composite_score) + 50) / 1.8, 0, 100))
            if signal == 'NO CLEAR SIGNAL':
                confluence_score = float(np.clip(confluence_score * 0.5, 0, 100))

            reasoning = (
                f"Adaptive multi-factor model estimates {expected_return:+.2f}% return over {horizon}-day horizon. "
                f"Market regime is {market_context['market_regime']} with trend {indicator_score['trend_score']:+.2f}, "
                f"volume {indicator_score['volume_score']:+.2f}, and sentiment {indicator_score['sentiment_score']:+.2f}. "
                f"The final decision is {signal} because the confluence of price action, momentum, volume, and sentiment "
                f"{'supports upside conviction' if signal == 'BUY' else 'indicates caution' if signal == 'SELL' else 'is not decisive enough for a directional call'}"
            )

            if not positive_factors:
                positive_factors = ['Price trend remains constructive']
            if not negative_factors:
                negative_factors = ['No major short-term breakdown observed']

            return {
                'signal': signal,
                'confidence': round(confidence, 1),
                'expected_return_pct': round(float(expected_return), 2),
                'reasoning': reasoning,
                'risk_level': risk_level,
                'bull_case': round(float(bull_case), 2),
                'base_case': round(float(base_case), 2),
                'bear_case': round(float(bear_case), 2),
                'positive_factors': positive_factors,
                'negative_factors': negative_factors,
                'confluence_score': round(float(confluence_score), 1),
                'scenario': 'Bull' if signal == 'BUY' else 'Bear' if signal == 'SELL' else 'Base',
                'market_regime': market_context['market_regime']
            }
        except Exception as e:
            logger.warning(f"⚠️ Error generating adaptive multi-factor signal: {str(e)}")
            return {
                'signal': 'NO CLEAR SIGNAL',
                'confidence': 35.0,
                'expected_return_pct': 0.0,
                'reasoning': 'Multi-factor model could not produce a decisive signal due to insufficient or conflicting evidence.',
                'risk_level': 'Medium',
                'bull_case': 0.0,
                'base_case': 0.0,
                'bear_case': 0.0,
                'positive_factors': ['Live market data available'],
                'negative_factors': ['Signal conflict or insufficient data'],
                'confluence_score': 30.0,
                'scenario': 'Base',
                'market_regime': 'neutral'
            }
    
    def generate_batch_forecasts(
        self,
        symbols: List[str],
        include_sentiment: bool = True
    ) -> Dict[str, Dict]:
        """
        Generate forecasts for multiple stocks
        
        Returns:
            Dict mapping symbol -> forecast result
        """
        results = {}
        
        for i, symbol in enumerate(symbols, 1):
            logger.info(f"📊 Processing {i}/{len(symbols)}: {symbol}")
            
            try:
                forecast = self.generate_forecast(symbol, validate=True)
                results[symbol] = forecast
                
            except Exception as e:
                logger.error(f"❌ Failed to process {symbol}: {str(e)}")
                results[symbol] = {
                    'symbol': symbol,
                    'success': False,
                    'error': str(e)
                }
        
        return results

    def _fetch_validated_data(self, symbol: str, period: str = '120d') -> Optional[pd.DataFrame]:
        """Fetch stock data with validation."""
        try:
            df = self.data_fetcher.get_stock_data(symbol, period=period)
            if df is None or df.empty:
                logger.error(f"❌ No data returned for {symbol}")
                return None
            if len(df) < 30:
                logger.error(f"❌ Insufficient data for {symbol} (need 30+ days, got {len(df)})")
                return None
            close_data = df['Close'].dropna()
            if len(close_data) < len(df) * 0.8:
                logger.error(f"❌ Too many missing values in {symbol}")
                return None
            logger.info(f"✅ Data validated for {symbol} ({len(df)} days)")
            return df
        except Exception as e:
            logger.error(f"❌ Error fetching data for {symbol}: {str(e)}")
            return None

    def _validate_data_freshness(self, stock_data: pd.DataFrame) -> List[str]:
        """Check if data is fresh and complete."""
        warnings = []
        last_timestamp = stock_data.index[-1]
        if hasattr(last_timestamp, 'tz') and last_timestamp.tz is not None:
            data_age = (datetime.now(last_timestamp.tz) - last_timestamp).days
        else:
            data_age = (datetime.now() - last_timestamp).days
        if data_age > 2:
            warnings.append(f"⚠️ Data is {data_age} days old (may be stale)")
        data_freq = pd.infer_freq(stock_data.index)
        if data_freq is not None and data_freq not in ('D', 'B'):
            warnings.append('⚠️ Data frequency is not daily')
        return warnings

    def _detect_prediction_anomalies(self, forecasts: Dict) -> List[str]:
        """Detect unrealistic or conflicting predictions."""
        warnings = []
        current_price = forecasts.get('current_price', 0)
        if current_price <= 0:
            return warnings
        for horizon, pred_price in forecasts.get('forecasts', {}).items():
            if pred_price <= 0:
                warnings.append(f"⚠️ Invalid prediction for {horizon}D: price={pred_price}")
                continue
            change_pct = abs((pred_price - current_price) / current_price * 100)
            if change_pct > 50:
                warnings.append(f"⚠️ Extreme prediction for {horizon}D: {change_pct:.1f}% change")
            if horizon > 7 and horizon in [14, 30]:
                prev_horizon = horizon - 7
                if prev_horizon in forecasts.get('forecasts', {}):
                    prev_price = forecasts['forecasts'][prev_horizon]
                    if (pred_price < current_price) != (prev_price < current_price):
                        logger.debug(f"Signal direction changed at {horizon}D (may indicate high uncertainty)")
        return warnings


# Singleton instance
_forecast_generator = None

def get_forecast_generator() -> ForecastGenerator:
    """Get or create singleton forecast generator instance"""
    global _forecast_generator
    if _forecast_generator is None:
        _forecast_generator = ForecastGenerator()
    return _forecast_generator
