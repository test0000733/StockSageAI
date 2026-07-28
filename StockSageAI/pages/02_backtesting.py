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
            # Fetch data
            df = backtest.fetch_historical_data(symbol, str(start_date), str(end_date))
            
            if df.empty:
                st.error("❌ No data available for this symbol and date range")
            else:
                # Run backtest
                result = backtest.backtest(df, strategy, commission)
                
                # Display results
                st.success("✅ Backtest completed!")
                
                # Key metrics
                metric_cols = st.columns(4)
                with metric_cols[0]:
                    st.metric("Total Return", f"{result['total_return']:.2f}%")
                with metric_cols[1]:
                    st.metric("Final Value", f"₹{result['final_value']:,.2f}")
                with metric_cols[2]:
                    st.metric("Sharpe Ratio", f"{result['sharpe_ratio']:.2f}")
                with metric_cols[3]:
                    st.metric("Max Drawdown", f"{result['max_drawdown']:.2f}%")
                
                st.divider()
                
                # Performance chart
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    y=result['portfolio_values'],
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
                if result['trades_history']:
                    trades_df = pd.DataFrame([
                        {
                            'Date': t['date'].strftime('%Y-%m-%d'),
                            'Type': t['type'],
                            'Price': f"₹{t['price']:.2f}",
                            'P&L': f"₹{t.get('pnl', 0):.2f}"
                        }
                        for t in result['trades_history']
                    ])
                    st.dataframe(trades_df, use_container_width=True)
                else:
                    st.info("No trades executed during this period")
                
                # Trade statistics
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Trades", result['trades'])
                with col2:
                    st.metric("Winning Trades", result['winning_trades'])
                
                if result['trades'] > 0:
                    with col1:
                        st.metric("Win Rate", f"{result['win_rate']:.1f}%")
        
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
