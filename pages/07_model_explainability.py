"""
Model Explainability Page
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from StockSageAI.model_explainer import get_model_explainer

st.set_page_config(page_title="Model Explainability", layout="wide")

st.markdown("# 🔬 Model Explainability Dashboard")
st.markdown("SHAP values and feature importance visualization")

explainer = get_model_explainer()

st.subheader("Feature Importance Analysis")

col1, col2, col3 = st.columns(3)

with col1:
    method = st.selectbox(
        "Importance Method",
        ["permutation", "gradient", "shap_approximation"],
        format_func=lambda x: x.replace("_", " ").title()
    )

with col2:
    st.info("ℹ️ Different methods for calculating feature importance")

if st.button("Calculate Importance", type="primary", use_container_width=True):
    with st.spinner("Calculating feature importance..."):
        try:
            # Create dummy model and data
            import numpy as np
            X_data = np.random.randn(100, 10)
            
            # Mock model
            class MockModel:
                def predict(self, X):
                    if len(X.shape) == 1:
                        X = X.reshape(1, -1)
                    return np.sum(X, axis=1) * 0.1
            
            model = MockModel()
            
            importance = explainer.calculate_feature_importance(model, X_data, method)
            
            if importance:
                st.success("✅ Importance calculated")
                
                # Display top features
                top_n = min(10, len(importance))
                top_features = dict(list(importance.items())[:top_n])
                
                # Feature importance chart
                features = list(top_features.keys())
                importance_values = list(top_features.values())
                
                fig = go.Figure(data=[
                    go.Bar(
                        y=features,
                        x=importance_values,
                        orientation='h',
                        marker=dict(color=importance_values, colorscale='Viridis')
                    )
                ])
                
                fig.update_layout(
                    title=f"Top {top_n} Important Features ({method.title()})",
                    xaxis_title="Importance Score",
                    yaxis_title="Features",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Feature importance table
                st.subheader("Feature Ranking")
                
                importance_df = pd.DataFrame([
                    {'Rank': i+1, 'Feature': f, 'Importance': v}
                    for i, (f, v) in enumerate(importance.items())
                ])
                
                st.dataframe(importance_df, use_container_width=True)
            
            else:
                st.error("Unable to calculate importance")
        
        except Exception as e:
            st.error(f"Error: {str(e)}")

st.divider()

# Prediction Explanation
st.subheader("Individual Prediction Explanation")

col1, col2 = st.columns(2)

with col1:
    st.write("Explain a single prediction")

with col2:
    if st.button("Generate Explanation"):
        try:
            # Dummy sample
            import numpy as np
            sample = np.array([0.5, -0.3, 1.2, 0.1, -0.5, 0.8, 0.2, -0.1, 0.9, 0.4])
            prediction = 0.25
            
            class MockModel:
                def predict(self, X):
                    if len(X.shape) == 1:
                        X = X.reshape(1, -1)
                    return np.sum(X, axis=1) * 0.1
            
            model = MockModel()
            explanation = explainer.explain_prediction(model, sample, prediction)
            
            if explanation:
                st.success("✅ Prediction explained")
                
                # Display explanation
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Prediction", f"{explanation['prediction']:.4f}")
                with col2:
                    st.metric("Direction", explanation['direction'])
                with col3:
                    st.metric("Confidence", f"{explanation['confidence']:.1f}%")
                
                st.divider()
                
                # Feature contributions
                st.write("**Feature Contributions:**")
                
                if explanation.get('top_features'):
                    contrib_df = pd.DataFrame([
                        {
                            'Feature': f,
                            'Value': f"{v['value']:.4f}",
                            'Contribution': f"{v['contribution']:.4f}"
                        }
                        for f, v in explanation['top_features']
                    ])
                    
                    st.dataframe(contrib_df, use_container_width=True)
        
        except Exception as e:
            st.error(f"Error: {str(e)}")

st.divider()

# Model Comparison
st.subheader("Compare Multiple Models")

if st.button("Compare Model Decisions"):
    try:
        import numpy as np
        sample = np.array([0.5, -0.3, 1.2, 0.1, -0.5, 0.8, 0.2, -0.1, 0.9, 0.4])
        
        class MockModel:
            def __init__(self, multiplier=1.0):
                self.multiplier = multiplier
            
            def predict(self, X):
                if len(X.shape) == 1:
                    X = X.reshape(1, -1)
                return np.sum(X, axis=1) * self.multiplier
        
        models = {
            'Transformer': MockModel(0.15),
            'LSTM': MockModel(0.12),
            'BiLSTM': MockModel(0.14),
            'CNN-LSTM': MockModel(0.13),
            'GNN': MockModel(0.11)
        }
        
        comparisons = explainer.compare_models_decisions(models, sample)
        
        if comparisons:
            st.success("✅ Models compared")
            
            comparison_df = pd.DataFrame([
                {
                    'Model': model,
                    'Prediction': f"{data['prediction']:.4f}",
                    'Direction': data['direction'],
                    'Confidence': f"{data['confidence']:.1f}%"
                }
                for model, data in comparisons.items()
            ])
            
            st.dataframe(comparison_df, use_container_width=True)
            
            st.write("**Consensus Analysis:**")
            
            directions = [d['direction'] for d in comparisons.values()]
            majority = max(set(directions), key=directions.count)
            
            st.write(f"Majority Direction: **{majority}**")
            st.write(f"Agreement: {(directions.count(majority) / len(directions)) * 100:.1f}%")
    
    except Exception as e:
        st.error(f"Error: {str(e)}")

st.caption("Model Explainability • SP 07 StockSageAI")
