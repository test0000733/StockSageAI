"""
Risk Analytics Page
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from StockSageAI.risk_analytics import get_risk_analytics_engine
from StockSageAI.stocks_database import get_stocks_database, render_stock_selector, render_stock_multi_selector

st.set_page_config(page_title="Risk Analytics", layout="wide")

st.markdown("# ⚠️ Advanced Risk Analytics")
st.markdown("### VaR, correlation, volatility, beta, and alpha analysis")

risk_engine = get_risk_analytics_engine()
stocks_db = get_stocks_database()

# Sidebar
with st.sidebar:
    st.markdown("### 📊 Risk Analysis Control")
    st.divider()
    
    analysis_type = st.radio(
        "Select Analysis",
        ["Single Stock", "Portfolio Comparison", "Correlation Matrix"],
        captions=["📈 Individual", "⚖️ Multiple", "🔗 Correlation"]
    )

if analysis_type == "Single Stock":
    st.subheader("📈 Individual Stock Risk Analysis")
    
    col1, col2 = st.columns(2)
    with col1:
        symbol = render_stock_selector("Stock Symbol", default_value="AAPL", key="risk_single_symbol")
    with col2:
        portfolio_value = st.number_input("Portfolio Value (₹)", value=100000, min_value=1000, step=10000)
    
    if st.button("Analyze Risk", type="primary"):
        with st.spinner("💯 Fetching real-time data and analyzing risk..."):
            try:
                # Try to fetch real-time data first
                try:
                    import yfinance as yf
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="1y")
                    if not hist.empty:
                        st.info(f"✅ Real-time data fetched for {symbol}")
                except:
                    pass
                
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
                            st.dataframe(vol_df)
                    
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
                    st.error(f"❌ Unable to analyze risk for {symbol}. Try using NSE format (e.g., TCS.NS, INFY.NS)")
                    st.info("💡 Tip: Use .NS suffix for NSE stocks")
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)[:100]}")
                st.info("💡 Tip: Try entering a valid symbol like AAPL, GOOGL, TCS.NS, etc.")

elif analysis_type == "Portfolio Comparison":
    st.subheader("⚖️ Compare Risk Across Multiple Stocks")
    
    symbols = render_stock_multi_selector(
        "Select Stocks for Comparison",
        default_values=["AAPL", "GOOGL", "MSFT"],
        max_items=5,
        key="risk_compare_symbols"
    )
    
    if st.button("Compare Risk Profiles", type="primary"):
        with st.spinner("🔄 Fetching real-time data for all stocks..."):
            try:
                risk_data = []
                success_count = 0
                
                for symbol in symbols:
                    try:
                        report = risk_engine.generate_risk_report(symbol, 10000)
                        if report:
                            risk_data.append({
                                'Symbol': symbol,
                                'Volatility': report.get('volatility', {}).get('average', 0),
                                'Sharpe Ratio': report.get('sharpe_ratio', 0),
                                'VaR (95%)': report.get('var_95', 0),
                                'Risk Level': report.get('risk_level', 'N/A')
                            })
                            success_count += 1
                    except Exception as se:
                        st.warning(f"⚠️ Failed to fetch {symbol}")
                        continue
                
                if risk_data:
                    risk_df = pd.DataFrame(risk_data)
                    st.dataframe(risk_df)
                    
                    # Volatility comparison
                    fig = px.bar(risk_df, x='Symbol', y='Volatility', title="Volatility Comparison")
                    st.plotly_chart(fig)
                    
                    # Risk level visualization
                    fig = px.scatter(risk_df, x='Volatility', y='Sharpe Ratio', text='Symbol', title="Risk-Return Profile")
                    st.plotly_chart(fig)
            
            except Exception as e:
                st.error(f"Error: {str(e)}")

elif analysis_type == "Correlation Matrix":
    st.subheader("Correlation Analysis")

    symbols = render_stock_multi_selector(
        "Stocks for Correlation Analysis",
        default_values=["AAPL", "GOOGL", "MSFT", "AMZN"],
        max_items=6,
        key="risk_corr_symbols"
    )

    if st.button("Run Correlation Analysis", type="primary"):
        with st.spinner("🔄 Calculating correlation matrix..."):
            try:
                corr_matrix = risk_engine.calculate_correlation_matrix(symbols, days=252)

                if corr_matrix is not None and not corr_matrix.empty:
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
                    st.plotly_chart(fig)

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
