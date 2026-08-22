"""
Portfolio Management Page
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# Import portfolio manager
from StockSageAI.portfolio_manager import get_portfolio_manager

st.set_page_config(page_title="Portfolio Manager", layout="wide")

st.markdown("# 💼 Portfolio Management System")
st.markdown("Track and manage your stock portfolio with real-time P&L and analysis")

portfolio_mgr = get_portfolio_manager()

# Sidebar for actions
with st.sidebar:
    st.subheader("Portfolio Actions")
    action = st.radio("Select Action", ["View Portfolio", "Add Holding", "Analytics"])

if "user" not in st.session_state or not st.session_state.user:
    st.warning("⚠️ Please log in to access portfolio features")
    st.stop()

user_id = st.session_state.user.get("username", "guest")
portfolio_id = portfolio_mgr.create_portfolio(user_id)

# ============================================================================
# VIEW PORTFOLIO
# ============================================================================
if action == "View Portfolio":
    st.subheader("Current Holdings")
    
    holdings = portfolio_mgr.get_holdings(portfolio_id)
    
    if holdings.empty:
        st.info("📊 No holdings yet. Add your first stock to get started!")
        
        with st.form("add_first_holding"):
            col1, col2, col3 = st.columns(3)
            with col1:
                symbol = st.text_input("Stock Symbol", value="AAPL")
            with col2:
                quantity = st.number_input("Quantity", value=10.0, min_value=0.1)
            with col3:
                price = st.number_input("Purchase Price", value=150.0, min_value=0.01)
            
            if st.form_submit_button("Add First Holding", use_container_width=True):
                portfolio_mgr.add_holding(
                    portfolio_id,
                    symbol,
                    quantity,
                    price,
                    datetime.now().strftime("%Y-%m-%d")
                )
                st.success(f"✅ Added {quantity} shares of {symbol}")
                st.rerun()
    else:
        # Display holdings
        metrics = portfolio_mgr.calculate_portfolio_metrics(portfolio_id)
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Value",
                f"₹{metrics.get('total_value', 0):,.2f}"
            )
        
        with col2:
            st.metric(
                "Total Invested",
                f"₹{metrics.get('total_invested', 0):,.2f}"
            )
        
        with col3:
            st.metric(
                "Total Gain/Loss",
                f"₹{metrics.get('total_gain', 0):,.2f}",
                f"{metrics.get('total_gain_pct', 0):.2f}%"
            )
        
        with col4:
            # Attempt VaR calculation with real-time update
            try:
                with st.spinner("💯 Updating real-time data..."):
                    var_95 = portfolio_mgr.calculate_var(portfolio_id)
                    st.metric("Value at Risk (95%)", f"₹{abs(var_95):,.2f}")
            except Exception as e:
                st.metric("Value at Risk (95%)", "N/A")
                st.caption(f"Error: {str(e)[:50]}")
        
        st.divider()
        
        # Holdings table
        if 'holdings' in metrics:
            holdings_data = []
            for h in metrics['holdings']:
                holdings_data.append({
                    'Symbol': h['symbol'],
                    'Quantity': h['quantity'],
                    'Purchase Price': f"₹{h['purchase_price']:.2f}",
                    'Current Price': f"₹{h['current_price']:.2f}",
                    'Current Value': f"₹{h['current_value']:,.2f}",
                    'Gain/Loss': f"₹{h['gain']:,.2f}",
                    'Return %': f"{h['gain_pct']:.2f}%"
                })
            
            st.dataframe(pd.DataFrame(holdings_data), use_container_width=True)
            
            # Pie chart of diversification
            if 'diversification' in metrics:
                fig = go.Figure(data=[go.Pie(
                    labels=[d['symbol'] for d in metrics['diversification']],
                    values=[d['weight'] * 100 for d in metrics['diversification']],
                    hole=0.3
                )])
                fig.update_layout(title="Portfolio Diversification")
                st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# ADD HOLDING
# ============================================================================
elif action == "Add Holding":
    st.subheader("Add New Holding")
    
    with st.form("add_holding_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            symbol = st.text_input("Stock Symbol", placeholder="e.g., AAPL", max_chars=10).upper()
            quantity = st.number_input("Number of Shares", value=10.0, min_value=0.1)
        
        with col2:
            price = st.number_input("Purchase Price per Share (₹)", value=100.0, min_value=0.01)
            date = st.date_input("Purchase Date")
        
        if st.form_submit_button("Add to Portfolio", use_container_width=True):
            if symbol:
                success = portfolio_mgr.add_holding(
                    portfolio_id,
                    symbol,
                    quantity,
                    price,
                    str(date)
                )
                
                if success:
                    st.success(f"✅ Successfully added {quantity} shares of {symbol}")
                    st.balloons()
                else:
                    st.error("❌ Failed to add holding")

# ============================================================================
# ANALYTICS
# ============================================================================
elif action == "Analytics":
    st.subheader("Portfolio Analytics")
    
    try:
        metrics = portfolio_mgr.calculate_portfolio_metrics(portfolio_id)
        
        if not metrics.get('holdings'):
            st.info("No holdings to analyze")
        else:
            # Correlation analysis
            st.write("#### Correlation Matrix")
            symbols = [h['symbol'] for h in metrics['holdings']]
            
            if len(symbols) > 1:
                try:
                    corr_matrix = portfolio_mgr.get_correlation_matrix(symbols)
                    
                    fig = go.Figure(data=go.Heatmap(
                        z=corr_matrix.values,
                        x=corr_matrix.columns,
                        y=corr_matrix.index,
                        colorscale='RdBu'
                    ))
                    fig.update_layout(title="Stock Correlation Matrix")
                    st.plotly_chart(fig, use_container_width=True)
                except:
                    st.warning("Unable to calculate correlations")
            
            # Risk metrics
            st.write("#### Risk Metrics")
            try:
                var_95 = portfolio_mgr.calculate_var(portfolio_id, confidence=0.95)
                var_99 = portfolio_mgr.calculate_var(portfolio_id, confidence=0.99)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Value at Risk (95%)", f"₹{abs(var_95):,.2f}")
                with col2:
                    st.metric("Value at Risk (99%)", f"₹{abs(var_99):,.2f}")
            except:
                st.warning("Unable to calculate VaR")
            
            # Performance
            st.write("#### Holdings Performance")
            perf_data = []
            for h in metrics.get('holdings', []):
                perf_data.append({
                    'Symbol': h['symbol'],
                    'Return %': h['gain_pct'],
                    'Absolute Gain': h['gain']
                })
            
            if perf_data:
                fig = px.bar(
                    pd.DataFrame(perf_data),
                    x='Symbol',
                    y='Return %',
                    title='Individual Stock Returns',
                    color='Return %',
                    color_continuous_scale='RdYlGn'
                )
                st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error generating analytics: {str(e)}")

st.divider()
st.caption("Portfolio Management System • SP 07 StockSageAI")
