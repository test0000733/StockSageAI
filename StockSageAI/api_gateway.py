"""
REST API Gateway for SP 07 StockSageAI
External integration and data access via API
"""

from flask import Flask, request, jsonify
from functools import wraps
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, Optional, Callable
import hmac
import hashlib

logger = logging.getLogger(__name__)


class APIGateway:
    """REST API for external integrations"""
    
    def __init__(self, app: Optional[Flask] = None, secret_key: Optional[str] = None):
        self.app = app or Flask(__name__)
        self.secret_key = secret_key or 'stocksageai-secret-key'
        self.rate_limits = {}
        self.api_tokens = {}
        self.setup_routes()
    
    def setup_routes(self):
        """Setup API routes"""
        
        @self.app.route('/api/v1/health', methods=['GET'])
        def health_check():
            return jsonify({
                'status': 'operational',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0'
            })
        
        @self.app.route('/api/v1/predict', methods=['POST'])
        @self.require_auth
        def get_prediction():
            """Get stock price prediction"""
            data = request.json
            symbol = data.get('symbol')
            models = data.get('models', ['ensemble'])
            horizon = data.get('horizon', 1)
            
            if not symbol:
                return jsonify({'error': 'Symbol required'}), 400
            
            # Call prediction engine
            predictions = self._get_stock_prediction(symbol, models, horizon)
            
            return jsonify({
                'symbol': symbol,
                'predictions': predictions,
                'generated_at': datetime.now().isoformat()
            })
        
        @self.app.route('/api/v1/signals', methods=['GET'])
        @self.require_auth
        def get_signals():
            """Get trading signals"""
            symbol = request.args.get('symbol')
            
            if not symbol:
                return jsonify({'error': 'Symbol required'}), 400
            
            signals = self._get_trading_signals(symbol)
            
            return jsonify({
                'symbol': symbol,
                'signals': signals,
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/v1/portfolio', methods=['GET'])
        @self.require_auth
        def get_portfolio():
            """Get portfolio data"""
            user_id = request.headers.get('X-User-ID')
            
            if not user_id:
                return jsonify({'error': 'User ID required'}), 400
            
            portfolio = self._get_user_portfolio(user_id)
            
            return jsonify(portfolio)
        
        @self.app.route('/api/v1/portfolio', methods=['POST'])
        @self.require_auth
        def add_to_portfolio():
            """Add holding to portfolio"""
            data = request.json
            user_id = request.headers.get('X-User-ID')
            
            if not user_id:
                return jsonify({'error': 'User ID required'}), 400
            
            result = self._add_holding(
                user_id,
                data.get('symbol'),
                data.get('quantity'),
                data.get('purchase_price'),
                data.get('purchase_date')
            )
            
            return jsonify(result)
        
        @self.app.route('/api/v1/backtest', methods=['POST'])
        @self.require_auth
        def run_backtest():
            """Run backtesting"""
            data = request.json
            
            result = self._run_backtest(
                data.get('symbol'),
                data.get('strategy', 'ma_crossover'),
                data.get('start_date'),
                data.get('end_date'),
                data.get('initial_capital', 10000)
            )
            
            return jsonify(result)
        
        @self.app.route('/api/v1/risk-metrics', methods=['GET'])
        @self.require_auth
        def get_risk_metrics():
            """Get risk analytics"""
            symbol = request.args.get('symbol')
            
            if not symbol:
                return jsonify({'error': 'Symbol required'}), 400
            
            metrics = self._calculate_risk_metrics(symbol)
            
            return jsonify(metrics)
        
        @self.app.route('/api/v1/compare', methods=['POST'])
        @self.require_auth
        def compare_stocks():
            """Compare multiple stocks"""
            data = request.json
            symbols = data.get('symbols', [])
            
            if not symbols:
                return jsonify({'error': 'Symbols required'}), 400
            
            comparison = self._compare_stocks(symbols)
            
            return jsonify(comparison)
        
        @self.app.route('/api/v1/report', methods=['POST'])
        @self.require_auth
        def generate_report():
            """Generate analysis report"""
            data = request.json
            user_id = request.headers.get('X-User-ID')
            
            if not user_id:
                return jsonify({'error': 'User ID required'}), 400
            
            report = self._generate_report(
                user_id,
                data.get('symbols', []),
                data.get('type', 'daily')
            )
            
            return jsonify(report)
        
        @self.app.route('/api/v1/auth/token', methods=['POST'])
        def get_token():
            """Get API token"""
            data = request.json
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return jsonify({'error': 'Username and password required'}), 400
            
            token = self._authenticate_user(username, password)
            
            if not token:
                return jsonify({'error': 'Invalid credentials'}), 401
            
            return jsonify({
                'token': token,
                'expires_in': 3600,
                'token_type': 'Bearer'
            })
    
    def require_auth(self, f: Callable) -> Callable:
        """Authentication decorator"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            
            if not token or not self._verify_token(token):
                return jsonify({'error': 'Unauthorized'}), 401
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    def _verify_token(self, token: str) -> bool:
        """Verify API token"""
        # In production, validate against database
        return token in self.api_tokens
    
    def _authenticate_user(self, username: str, password: str) -> Optional[str]:
        """Authenticate user and return token"""
        # In production, validate against user database
        # For now, generate a dummy token
        token = hashlib.sha256(f"{username}{password}{datetime.now()}".encode()).hexdigest()
        self.api_tokens[token] = {'username': username, 'created_at': datetime.now().isoformat()}
        return token
    
    def _get_stock_prediction(self, symbol: str, models: list, horizon: int) -> Dict:
        """Get stock prediction"""
        return {
            'symbol': symbol,
            'horizon_days': horizon,
            'predictions': {
                model: {
                    'price_target': f"${100 + horizon * 2:.2f}",
                    'confidence': f"{80 + horizon}%",
                    'direction': 'UP'
                }
                for model in models
            },
            'ensemble_prediction': {
                'price_target': f"${100 + horizon * 2:.2f}",
                'confidence': f"{85 + horizon}%",
                'direction': 'UP'
            }
        }
    
    def _get_trading_signals(self, symbol: str) -> Dict:
        """Get trading signals"""
        return {
            'symbol': symbol,
            'current_signal': 'BUY',
            'confidence': 85.3,
            'entry_price': 150.50,
            'target_price': 165.00,
            'stop_loss': 145.00,
            'signal_generated_at': datetime.now().isoformat()
        }
    
    def _get_user_portfolio(self, user_id: str) -> Dict:
        """Get user portfolio"""
        return {
            'user_id': user_id,
            'portfolios': [
                {
                    'id': 1,
                    'name': 'Main Portfolio',
                    'total_value': 50000.00,
                    'total_gain': 5000.00,
                    'gain_percent': 10.0,
                    'holdings': [
                        {'symbol': 'AAPL', 'quantity': 10, 'current_value': 1500.00}
                    ]
                }
            ]
        }
    
    def _add_holding(self, user_id: str, symbol: str, quantity: float,
                    purchase_price: float, purchase_date: str) -> Dict:
        """Add holding to portfolio"""
        return {
            'success': True,
            'user_id': user_id,
            'holding': {
                'symbol': symbol,
                'quantity': quantity,
                'purchase_price': purchase_price,
                'purchase_date': purchase_date,
                'added_at': datetime.now().isoformat()
            }
        }
    
    def _run_backtest(self, symbol: str, strategy: str, start_date: str,
                     end_date: str, initial_capital: float) -> Dict:
        """Run backtest"""
        return {
            'symbol': symbol,
            'strategy': strategy,
            'period': f"{start_date} to {end_date}",
            'initial_capital': initial_capital,
            'final_value': initial_capital * 1.15,
            'total_return': 15.0,
            'sharpe_ratio': 1.25,
            'max_drawdown': 8.5,
            'trades': 12,
            'win_rate': 75.0
        }
    
    def _calculate_risk_metrics(self, symbol: str) -> Dict:
        """Calculate risk metrics"""
        return {
            'symbol': symbol,
            'var_95': 1250.00,
            'var_99': 1850.00,
            'cvar_95': 1500.00,
            'volatility': 0.185,
            'sharpe_ratio': 1.34,
            'sortino_ratio': 1.98,
            'max_drawdown': 12.5,
            'beta': 1.15,
            'alpha': 0.08
        }
    
    def _compare_stocks(self, symbols: list) -> Dict:
        """Compare stocks"""
        return {
            'symbols': symbols,
            'comparison': {
                symbol: {
                    'price': 150.00 + len(symbol),
                    'pe': 25.5,
                    'dividend_yield': 2.1,
                    'volatility': 0.18,
                    'recommendation': 'BUY'
                }
                for symbol in symbols
            }
        }
    
    def _generate_report(self, user_id: str, symbols: list, report_type: str) -> Dict:
        """Generate report"""
        return {
            'user_id': user_id,
            'report_type': report_type,
            'generated_at': datetime.now().isoformat(),
            'symbols_analyzed': symbols,
            'summary': 'Market looking bullish',
            'recommendations': [
                {'symbol': sym, 'action': 'BUY', 'confidence': 85}
                for sym in symbols[:2]
            ]
        }
    
    def get_app(self) -> Flask:
        """Get Flask app instance"""
        return self.app


# Create global API gateway instance
_api_gateway = None


def get_api_gateway(app: Optional[Flask] = None) -> APIGateway:
    global _api_gateway
    if _api_gateway is None:
        _api_gateway = APIGateway(app)
    return _api_gateway


def create_api_app() -> Flask:
    """Create and configure Flask app for API"""
    app = Flask(__name__)
    gateway = get_api_gateway(app)
    return gateway.get_app()
