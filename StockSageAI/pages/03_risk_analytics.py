"""
Risk Analytics Page
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from StockSageAI.risk_analytics import get_risk_analytics_engine

st.set_page_config(page_title="Risk Analytics", layout="wide")

st.markdown("# ⚠️ Advanced Risk Analytics")
st.markdown("VaR, correlation, volatility, beta, and alpha analysis")

risk_engine = get_risk_analytics_engine()

# Sidebar
with st.sidebar:
    st.subheader("Risk Analysis")
    analysis_type = st.radio(
        "Select Analysis",
        ["Single Stock", "Portfolio Comparison", "Correlation Matrix"]
    )

if analysis_type == "Single Stock":
    st.subheader("Individual Stock Risk Analysis")
    
    col1, col2 = st.columns(2)
    with col1:
        symbol = st.text_input("Stock Symbol", value="AAPL", max_chars=10).upper()
    with col2:
        portfolio_value = st.number_input("Portfolio Value (₹)", value=10000, min_value=1000)
    
    if st.button("Analyze Risk", type="primary", use_container_width=True):
        with st.spinner("Analyzing risk..."):
            try:
                report = risk_engine.generate_risk_report(symbol, portfolio_value)
                
                if report:
                    # Display metrics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("VaR (95%)", f"₹{report.get('var_95', 0):,.0f}")
                    with col2:
                        st.metric("VaR (99%)", f"₹{report.get('var_99', 0):,.0f}")
                    with col3:
                        st.metric("CVaR (95%)", f"₹{report.get('cvar_95', 0):,.0f}")
                    with col4:
                        st.metric("Sharpe Ratio", f"{report.get('sharpe_ratio', 0):.2f}")
                    
                    st.divider()
                    
                    # Volatility metrics
                    vol = report.get('volatility', {})
                    if vol:
                        st.subheader("Volatility Measures")
                        vol_df = pd.DataFrame({
                            'Volatility Type': list(vol.keys()),
                            'Value': list(vol.values())
                        })
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.dataframe(vol_df, use_container_width=True)
                    
                    # Beta & Alpha
                    ba = report.get('beta_alpha', {})
                    if ba:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Beta", f"{ba.get('beta', 0):.2f}")
                        with col2:
                            st.metric("Alpha", f"{ba.get('alpha', 0):.2f}")
                        with col3:
                            st.info(ba.get('interpretation', 'N/A'))
                    
                    # Max Drawdown
                    dd = report.get('max_drawdown', {})
                    if dd:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Max Drawdown", f"{dd.get('max_drawdown', 0):.2f}%")
                        with col2:
                            st.caption(f"Period: {dd.get('drawdown_start', 'N/A')} to {dd.get('drawdown_trough', 'N/A')}")
                        with col3:
                            st.caption(f"Recovery: {dd.get('recovery_days', 0)} days")
                
                else:
                    st.error("Unable to analyze risk for this symbol")
            
            except Exception as e:
                st.error(f"Error: {str(e)}")

elif analysis_type == "Portfolio Comparison":
    st.subheader("Compare Risk Across Stocks")
    
    symbols_input = st.text_input(
        "Enter Stock Symbols (comma-separated)",
        value="AAPL, GOOGL, MSFT",
        placeholder="e.g., AAPL, GOOGL, MSFT"
    )
    
    if st.button("Compare Risk", type="primary", use_container_width=True):
        symbols = [s.strip().upper() for s in symbols_input.split(",")]
        
        with st.spinner("Comparing risk metrics..."):
            try:
                risk_data = []
                for symbol in symbols:
                    report = risk_engine.generate_risk_report(symbol, 10000)
                    if report:
                        risk_data.append({
                            'Symbol': symbol,
                            'Volatility': report.get('volatility', {}).get('average', 0),
                            'Sharpe Ratio': report.get('sharpe_ratio', 0),
                            'VaR (95%)': report.get('var_95', 0),
                            'Risk Level': report.get('risk_level', 'N/A')
                        })
                
                if risk_data:
                    risk_df = pd.DataFrame(risk_data)
                    st.dataframe(risk_df, use_container_width=True)
                    
                    # Volatility comparison
                    fig = px.bar(risk_df, x='Symbol', y='Volatility', title="Volatility Comparison")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Risk level visualization
                    fig = px.scatter(risk_df, x='Volatility', y='Sharpe Ratio', text='Symbol', title="Risk-Return Profile")
                    st.plotly_chart(fig, use_container_width=True)
            
            except Exception as e:
                st.error(f"Error: {str(e)}")

elif analysis_type == "Correlation Matrix":
    st.subheader("Correlation Analysis")
    
    symbols_input = st.text_input(
        "Stocks for Correlation (comma-separated)",
        value="AAPL, GOOGL, MSFT, AMZN",
        placeholder="e.g., AAPL, GOOGL, MSFT, AMZN"
    )
    
    if st.button("Calculate Correlations", type="primary", use_container_width=True):
        symbols = [s.strip().upper() for s in symbols_input.split(",")]
        
        with st.spinner("Calculating correlations..."):
            try:
                corr_matrix = risk_engine.calculate_correlation_matrix(symbols, days=252)
                
                if not corr_matrix.empty:
                    # Display correlation matrix
                    st.subheader("Correlation Matrix")
                    
                    fig = go.Figure(data=go.Heatmap(
                        z=corr_matrix.values,
                        x=corr_matrix.columns,
                        y=corr_matrix.index,
                        colorscale='RdBu',
                        zmid=0,
                        zmin=-1,
                        zmax=1
                    ))
                    fig.update_layout(title="Stock Correlation Matrix (1-Year)")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Correlation insights
                    st.subheader("Correlation Insights")
                    
                    # Find highest correlations
                    corr_pairs = []
                    for i in range(len(corr_matrix.columns)):
                        for j in range(i+1, len(corr_matrix.columns)):
                            corr_pairs.append({
                                'Stock 1': corr_matrix.columns[i],
                                'Stock 2': corr_matrix.columns[j],
                                'Correlation': corr_matrix.iloc[i, j]
                            })
                    
                    corr_pairs = sorted(corr_pairs, key=lambda x: abs(x['Correlation']), reverse=True)
                    
                    st.write("**Strongest Correlations:**")
                    for pair in corr_pairs[:min(5, len(corr_pairs))]:
                        st.write(f"• {pair['Stock 1']} - {pair['Stock 2']}: {pair['Correlation']:.2f}")
            
            except Exception as e:
                st.error(f"Error: {str(e)}")

st.caption("Risk Analytics • SP 07 StockSageAI")
