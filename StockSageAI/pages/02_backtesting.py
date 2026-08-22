"""
Backtesting Engine Page
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

from StockSageAI.backtesting_engine import get_backtest_engine

st.set_page_config(page_title="Backtesting", layout="wide")

st.markdown("# 📊 Advanced Backtesting Engine")
st.markdown("Test trading strategies on historical data with comprehensive metrics")

backtest = get_backtest_engine()

st.subheader("Backtest Configuration")

col1, col2, col3 = st.columns(3)

with col1:
    symbol = st.text_input("Stock Symbol", value="AAPL", max_chars=10).upper()

with col2:
    strategy = st.selectbox(
        "Strategy",
        ["ma_crossover", "rsi", "bollinger_bands"],
        format_func=lambda x: x.replace("_", " ").title()
    )

with col3:
    initial_capital = st.number_input("Initial Capital (₹)", value=10000, min_value=1000)

col1, col2, col3 = st.columns(3)

with col1:
    start_date = st.date_input(
        "Start Date",
        value=datetime.now() - timedelta(days=365)
    )

with col2:
    end_date = st.date_input(
        "End Date",
        value=datetime.now()
    )

with col3:
    commission = st.slider("Commission (%)", 0.0, 1.0, 0.1) / 100

if st.button("Run Backtest", type="primary", use_container_width=True):
    with st.spinner("Running backtest..."):
        try:
            if start_date >= end_date:
                st.error("❌ Start date must be before end date")
            else:
                # Fetch data with real-time updates
                with st.spinner("Fetching real-time data for " + symbol + "..."):
                    df = backtest.fetch_historical_data(symbol, str(start_date), str(end_date))
                
                if df.empty or len(df) < 2:
                    st.error(f"❌ No data available for {symbol}. Try using NSE format (e.g., TCS.NS for Indian stocks) or US symbols.")
                    st.info("💡 Tip: Use .NS for NSE stocks (e.g., TCS.NS, INFY.NS, RELIANCE.NS)")
                else:
                    # Run backtest
                    result = backtest.backtest(df, strategy, commission)
                    
                    if result is None:
                        st.error("❌ Error running backtest. Please check the data and try again.")
                    else:
                        # Display results
                        st.success("✅ Backtest completed!")
                        
                        # Key metrics
                        metric_cols = st.columns(4)
                        with metric_cols[0]:
                            st.metric("Total Return", f"{result.get('total_return', 0):.2f}%")
                        with metric_cols[1]:
                            st.metric("Final Value", f"₹{result.get('final_value', 0):,.2f}")
                        with metric_cols[2]:
                            st.metric("Sharpe Ratio", f"{result.get('sharpe_ratio', 0):.2f}")
                        with metric_cols[3]:
                            st.metric("Max Drawdown", f"{result.get('max_drawdown', 0):.2f}%")
                
                        st.divider()
                        
                        # Performance chart
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            y=result.get('portfolio_values', []),
                            mode='lines',
                            name='Portfolio Value',
                            line=dict(color='#00CC96', width=2)
                        ))
                        fig.update_layout(
                            title="Portfolio Value Over Time",
                            xaxis_title="Days",
                            yaxis_title="Value (₹)",
                            hovermode='x unified'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Trade history
                        st.subheader("Trade History")
                        trades_history = result.get('trades_history', [])
                        if trades_history:
                            trades_df = pd.DataFrame([
                                {
                                    'Date': t.get('date', datetime.now()).strftime('%Y-%m-%d'),
                                    'Type': t.get('type', 'N/A'),
                                    'Price': f"₹{t.get('price', 0):.2f}",
                                    'P&L': f"₹{t.get('pnl', 0):.2f}"
                                }
                                for t in trades_history
                            ])
                            st.dataframe(trades_df, use_container_width=True)
                        else:
                            st.info("No trades executed during this period")
                        
                        # Trade statistics
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Total Trades", result.get('trades', 0))
                        with col2:
                            st.metric("Winning Trades", result.get('winning_trades', 0))
                        
                        if result.get('trades', 0) > 0:
                            with col1:
                                st.metric("Win Rate", f"{result.get('win_rate', 0):.1f}%")
        
        except Exception as e:
            st.error(f"❌ Error running backtest: {str(e)}")

st.divider()

# Compare strategies
st.subheader("Compare Multiple Strategies")

if st.button("Compare Strategies", key="compare"):
    with st.spinner("Comparing strategies..."):
        try:
            comparison = backtest.compare_strategies(symbol, str(start_date), str(end_date))
            
            if not comparison.empty:
                st.dataframe(comparison, use_container_width=True)
            else:
                st.warning("Unable to compare strategies")
        except Exception as e:
            st.error(f"Error: {str(e)}")

st.caption("Backtesting Engine • SP 07 StockSageAI")
