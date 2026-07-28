"""
Model Explainability Dashboard for SP 07 StockSageAI
SHAP values and feature importance visualization
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class ModelExplainer:
    """Explain model predictions with SHAP values and feature importance"""
    
    def __init__(self):
        self.feature_names = [
            'MA5', 'MA20', 'MA50', 'RSI', 'MACD', 'ATR',
            'Volume_Ratio', 'Price_Range', 'Volatility', 'Momentum'
        ]
    
    def calculate_feature_importance(self, model, X_data: np.ndarray,
                                    method: str = 'permutation') -> Dict:
        """Calculate feature importance using multiple methods"""
        
        if method == 'permutation':
            return self._permutation_importance(model, X_data)
        elif method == 'gradient':
            return self._gradient_importance(model, X_data)
        elif method == 'shap_approximation':
            return self._shap_approximation(model, X_data)
        
        return {}
    
    def _permutation_importance(self, model, X_data: np.ndarray) -> Dict:
        """Calculate permutation-based feature importance"""
        
        try:
            baseline_pred = model.predict(X_data)
            baseline_score = np.mean(baseline_pred)
            
            importances = {}
            
            for i, feature in enumerate(self.feature_names[:X_data.shape[1]]):
                X_permuted = X_data.copy()
                np.random.shuffle(X_permuted[:, i])
                
                permuted_pred = model.predict(X_permuted)
                permuted_score = np.mean(permuted_pred)
                
                importance = abs(baseline_score - permuted_score)
                importances[feature] = importance
            
            # Normalize
            total = sum(importances.values()) + 1e-10
            importances = {k: v/total * 100 for k, v in importances.items()}
            
            return dict(sorted(importances.items(), key=lambda x: x[1], reverse=True))
        except:
            return {}
    
    def _gradient_importance(self, model, X_data: np.ndarray) -> Dict:
        """Calculate gradient-based feature importance"""
        
        try:
            importances = {}
            n_samples = min(100, X_data.shape[0])
            
            for i, feature in enumerate(self.feature_names[:X_data.shape[1]]):
                X_plus = X_data[:n_samples].copy()
                X_minus = X_data[:n_samples].copy()
                
                epsilon = 0.01
                X_plus[:, i] += epsilon
                X_minus[:, i] -= epsilon
                
                pred_plus = model.predict(X_plus)
                pred_minus = model.predict(X_minus)
                
                gradient = np.mean(np.abs(pred_plus - pred_minus) / (2 * epsilon))
                importances[feature] = gradient
            
            total = sum(importances.values()) + 1e-10
            importances = {k: v/total * 100 for k, v in importances.items()}
            
            return dict(sorted(importances.items(), key=lambda x: x[1], reverse=True))
        except:
            return {}
    
    def _shap_approximation(self, model, X_data: np.ndarray) -> Dict:
        """SHAP-like approximation using coalition method"""
        
        try:
            n_features = X_data.shape[1]
            n_samples = min(50, X_data.shape[0])
            X_subset = X_data[:n_samples]
            
            feature_values = np.zeros(n_features)
            
            for feature_idx in range(n_features):
                predictions_with = []
                predictions_without = []
                
                for sample in X_subset:
                    pred_with = model.predict(sample.reshape(1, -1))
                    
                    sample_modified = sample.copy()
                    sample_modified[feature_idx] = X_subset[:, feature_idx].mean()
                    pred_without = model.predict(sample_modified.reshape(1, -1))
                    
                    predictions_with.append(pred_with[0])
                    predictions_without.append(pred_without[0])
                
                contribution = np.mean(
                    np.abs(np.array(predictions_with) - np.array(predictions_without))
                )
                feature_values[feature_idx] = contribution
            
            importances = {
                self.feature_names[i]: feature_values[i]
                for i in range(min(len(self.feature_names), n_features))
            }
            
            total = sum(importances.values()) + 1e-10
            importances = {k: v/total * 100 for k, v in importances.items()}
            
            return dict(sorted(importances.items(), key=lambda x: x[1], reverse=True))
        except:
            return {}
    
    def explain_prediction(self, model, sample: np.ndarray, prediction: float) -> Dict:
        """Explain individual prediction"""
        
        try:
            explanation = {
                'prediction': prediction,
                'features_used': min(10, len(sample)),
                'top_features': [],
                'feature_values': {},
                'direction': 'UP' if prediction > 0 else 'DOWN',
                'confidence': min(abs(prediction) * 100, 100)
            }
            
            # Feature-wise contributions (approximation)
            mean_value = np.mean(sample) if len(sample) > 0 else 0
            
            for i, feature in enumerate(self.feature_names[:len(sample)]):
                val = sample[i]
                contribution = (val - mean_value) * (prediction / (len(sample) + 1e-10))
                explanation['feature_values'][feature] = {
                    'value': val,
                    'contribution': contribution
                }
            
            # Sort by absolute contribution
            explanation['top_features'] = sorted(
                explanation['feature_values'].items(),
                key=lambda x: abs(x[1]['contribution']),
                reverse=True
            )[:5]
            
            return explanation
        except Exception as e:
            logger.error(f"Error explaining prediction: {e}")
            return {}
    
    def generate_explanation_report(self, model, X_data: np.ndarray,
                                   predictions: np.ndarray) -> Dict:
        """Generate comprehensive explanation report"""
        
        try:
            feature_importance = self.calculate_feature_importance(model, X_data)
            
            # Analyze prediction ranges
            pred_min = np.min(predictions)
            pred_max = np.max(predictions)
            pred_mean = np.mean(predictions)
            pred_std = np.std(predictions)
            
            # Distribution analysis
            positive_preds = np.sum(predictions > 0) / len(predictions) * 100
            negative_preds = np.sum(predictions < 0) / len(predictions) * 100
            neutral_preds = 100 - positive_preds - negative_preds
            
            return {
                'feature_importance': feature_importance,
                'prediction_stats': {
                    'min': float(pred_min),
                    'max': float(pred_max),
                    'mean': float(pred_mean),
                    'std': float(pred_std)
                },
                'prediction_distribution': {
                    'positive': positive_preds,
                    'negative': negative_preds,
                    'neutral': neutral_preds
                },
                'top_3_features': list(feature_importance.keys())[:3],
                'model_behavior': 'High variance' if pred_std > 0.5 else 'Stable'
            }
        except Exception as e:
            logger.error(f"Error generating explanation report: {e}")
            return {}
    
    def compare_models_decisions(self, models: Dict, sample: np.ndarray) -> Dict:
        """Compare different models' decisions on same sample"""
        
        comparisons = {}
        
        for model_name, model in models.items():
            try:
                prediction = model.predict(sample.reshape(1, -1))[0]
                explanation = self.explain_prediction(model, sample, prediction)
                
                comparisons[model_name] = {
                    'prediction': prediction,
                    'direction': explanation.get('direction', 'NEUTRAL'),
                    'confidence': explanation.get('confidence', 0),
                    'top_features': explanation.get('top_features', [])[:3]
                }
            except:
                pass
        
        return comparisons


# Singleton instance
_explainer = None


def get_model_explainer():
    global _explainer
    if _explainer is None:
        _explainer = ModelExplainer()
    return _explainer
