import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import warnings
warnings.filterwarnings('ignore')

class LSTMPredictor:
    """Advanced stock price prediction model using Random Forest and Linear Regression ensemble"""
    
    def __init__(self, sequence_length=30, n_estimators=100, random_state=42):
        self.sequence_length = sequence_length
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.rf_model = RandomForestRegressor(n_estimators=n_estimators, random_state=random_state)
        self.lr_model = LinearRegression()
        self.is_trained = False
    
    def prepare_data(self, data):
        """Prepare data for ML training with feature engineering"""
        # Create features from price data
        features_df = data.copy()
        
        # Add technical indicators and lag features
        features_df['price_lag1'] = features_df['Close'].shift(1)
        features_df['price_lag2'] = features_df['Close'].shift(2)
        features_df['price_lag3'] = features_df['Close'].shift(3)
        features_df['price_change'] = features_df['Close'].pct_change()
        features_df['volume_ma'] = features_df['Volume'].rolling(window=5).mean()
        features_df['high_low_ratio'] = features_df['High'] / features_df['Low']
        features_df['open_close_ratio'] = features_df['Open'] / features_df['Close']
        
        # Add moving averages if not present
        if 'MA_20' not in features_df.columns:
            features_df['MA_20'] = features_df['Close'].rolling(window=20).mean()
        if 'MA_50' not in features_df.columns:
            features_df['MA_50'] = features_df['Close'].rolling(window=50).mean()
        
        # Create sequences for time series prediction
        X, y = [], []
        feature_cols = ['Close', 'Volume', 'price_lag1', 'price_lag2', 'price_lag3', 
                       'price_change', 'volume_ma', 'high_low_ratio', 'open_close_ratio', 'MA_20']
        
        # Clean data and select features
        features_df = features_df[feature_cols].dropna()
        
        if len(features_df) < self.sequence_length + 1:
            return np.array([]), np.array([]), features_df
        
        # Scale features
        scaled_features = self.scaler.fit_transform(features_df)
        
        # Create sequences
        for i in range(self.sequence_length, len(scaled_features)):
            X.append(scaled_features[i-self.sequence_length:i].flatten())
            y.append(scaled_features[i, 0])  # Predict Close price (first feature)
        
        return np.array(X), np.array(y), features_df
    
    def build_models(self):
        """Initialize the ensemble models"""
        self.rf_model = RandomForestRegressor(
            n_estimators=self.n_estimators,
            max_depth=10,
            min_samples_split=5,
            random_state=self.random_state
        )
        self.lr_model = LinearRegression()
    
    def train(self, X, y):
        """Train the ensemble models"""
        if len(X) == 0 or len(y) == 0:
            return None
            
        # Split data into train and validation
        train_size = int(len(X) * 0.8)
        X_train, X_val = X[:train_size], X[train_size:]
        y_train, y_val = y[:train_size], y[train_size:]
        
        # Train Random Forest
        self.rf_model.fit(X_train, y_train)
        
        # Train Linear Regression
        self.lr_model.fit(X_train, y_train)
        
        self.is_trained = True
        
        # Return validation scores
        rf_score = self.rf_model.score(X_val, y_val) if len(X_val) > 0 else 0
        lr_score = self.lr_model.score(X_val, y_val) if len(X_val) > 0 else 0
        
        return {
            'rf_score': rf_score,
            'lr_score': lr_score,
            'train_size': len(X_train),
            'val_size': len(X_val)
        }
    
    def predict_future(self, last_features, forecast_days, current_price, historical_volatility):
        """Predict future prices using ensemble models with realistic constraints"""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        predictions = []
        current_features = last_features.copy()
        
        # Calculate realistic daily change limits
        daily_volatility = historical_volatility if historical_volatility > 0 else 0.02
        max_daily_change = min(daily_volatility * 1.5, 0.04)  # Max 4% daily change, usually less
        
        previous_price = current_price
        
        for day_num in range(forecast_days):
            # Get ensemble prediction
            rf_pred = self.rf_model.predict(current_features.reshape(1, -1))[0]
            lr_pred = self.lr_model.predict(current_features.reshape(1, -1))[0]
            
            # Ensemble prediction (weighted average)
            ensemble_pred = 0.6 * rf_pred + 0.4 * lr_pred  # More conservative weighting
            
            # Convert scaled prediction back to price
            dummy_features = np.zeros((1, self.scaler.n_features_in_))
            dummy_features[0, 0] = ensemble_pred
            raw_price = self.scaler.inverse_transform(dummy_features)[0, 0]
            
            # Apply realistic constraints
            price_change_pct = (raw_price - previous_price) / previous_price
            
            # Limit daily price change to realistic bounds
            if price_change_pct > max_daily_change:
                price_change_pct = max_daily_change
            elif price_change_pct < -max_daily_change:
                price_change_pct = -max_daily_change
            
            # Apply decay factor for longer-term predictions (less confidence over time)
            confidence_decay = 0.95 ** day_num
            price_change_pct *= confidence_decay
            
            # Add some mean reversion tendency (stocks tend to revert to moving averages)
            mean_reversion_factor = 0.1 * (day_num / forecast_days)  # Stronger for longer predictions
            price_change_pct *= (1 - mean_reversion_factor)
            
            # Calculate final predicted price
            predicted_price = previous_price * (1 + price_change_pct)
            
            # Ensure price doesn't go below 50% or above 200% of current price for any prediction
            min_price = current_price * 0.5
            max_price = current_price * 2.0
            predicted_price = max(min_price, min(max_price, predicted_price))
            
            predictions.append(predicted_price)
            
            # Update for next iteration
            previous_price = predicted_price
            
            # Update features for next prediction (convert back to scaled form)
            scaled_price = self.scaler.transform([[predicted_price] + [0] * (self.scaler.n_features_in_ - 1)])[0, 0]
            current_features = np.roll(current_features, -1)
            current_features[-1] = scaled_price
        
        return np.array(predictions)
    
    def predict(self, stock_data, forecast_days):
        """Main prediction method with realistic constraints"""
        if len(stock_data) < self.sequence_length + 20:
            raise ValueError(f"Need at least {self.sequence_length + 20} days of data for training")
        
        # Prepare data
        X, y, features_df = self.prepare_data(stock_data)
        
        if len(X) == 0:
            # Fallback to simple trend-based prediction
            return self._simple_trend_prediction(stock_data, forecast_days)
        
        # Train models
        training_results = self.train(X, y)
        
        # Get current price and calculate historical volatility
        current_price = stock_data['Close'].iloc[-1]
        daily_returns = stock_data['Close'].pct_change().dropna()
        historical_volatility = daily_returns.std() if len(daily_returns) > 0 else 0.02
        
        # Get last features for prediction
        last_features = X[-1]  # Last sequence of features
        
        # Make realistic predictions
        future_predictions = self.predict_future(last_features, forecast_days, current_price, historical_volatility)
        
        return future_predictions
    
    def _simple_trend_prediction(self, stock_data, forecast_days):
        """Simple fallback prediction based on recent trend with realistic constraints"""
        recent_prices = stock_data['Close'].tail(20).values
        current_price = recent_prices[-1]
        
        # Calculate recent trend and volatility
        daily_changes = np.diff(recent_prices) / recent_prices[:-1]
        avg_daily_change = np.mean(daily_changes)
        daily_volatility = np.std(daily_changes)
        
        # Limit average daily change to realistic bounds
        max_avg_change = min(daily_volatility * 0.5, 0.02)  # Max 2% average daily change
        avg_daily_change = max(-max_avg_change, min(max_avg_change, avg_daily_change))
        
        # Generate conservative predictions
        predictions = []
        previous_price = current_price
        
        for i in range(forecast_days):
            # Apply trend with decreasing confidence over time
            confidence = 0.9 ** i  # Decay confidence for longer predictions
            daily_change = avg_daily_change * confidence
            
            # Add small random variation within realistic bounds
            noise = np.random.normal(0, daily_volatility * 0.3)
            daily_change += noise
            
            # Limit daily change
            daily_change = max(-0.03, min(0.03, daily_change))  # Max 3% daily change
            
            next_price = previous_price * (1 + daily_change)
            
            # Ensure price stays within reasonable bounds
            min_price = current_price * 0.7  # Max 30% decline from current
            max_price = current_price * 1.3  # Max 30% gain from current
            next_price = max(min_price, min(max_price, next_price))
            
            predictions.append(next_price)
            previous_price = next_price
        
        return np.array(predictions)
    
    def calculate_metrics(self, actual, predicted):
        """Calculate prediction accuracy metrics"""
        mse = mean_squared_error(actual, predicted)
        mae = mean_absolute_error(actual, predicted)
        rmse = np.sqrt(mse)
        
        # Calculate MAPE (Mean Absolute Percentage Error)
        mape = np.mean(np.abs((actual - predicted) / actual)) * 100
        
        return {
            'mse': mse,
            'mae': mae,
            'rmse': rmse,
            'mape': mape
        }
    
    def get_model_confidence(self, stock_data, predictions):
        """Calculate model confidence based on historical performance"""
        try:
            if not self.is_trained or len(predictions) == 0:
                return 0.6  # Default confidence
            
            # Use recent price volatility as confidence indicator
            recent_prices = stock_data['Close'].tail(20).values
            if len(recent_prices) < 10:
                return 0.6
                
            # Calculate volatility
            price_changes = np.diff(recent_prices) / recent_prices[:-1]
            volatility = np.std(price_changes)
            
            # Convert volatility to confidence (lower volatility = higher confidence)
            # Typical daily volatility ranges from 0.01 to 0.05 for stocks
            normalized_volatility = min(volatility / 0.05, 1.0)
            confidence = max(0.3, 0.9 - normalized_volatility)
            
            return confidence
            
        except Exception as e:
            print(f"Error calculating confidence: {e}")
            return 0.6
