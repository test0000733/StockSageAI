"""
Portfolio Management Page - Enhanced UI/UX
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

from StockSageAI import ui_components as ui
from StockSageAI.portfolio_manager import get_portfolio_manager

st.set_page_config(page_title="Portfolio Manager", layout="wide")

st.markdown("""
<div style='text-align: center; margin-bottom: 2rem;'>
    <h1 style='margin: 0.5rem 0;'>💼 Portfolio Management System</h1>
    <p style='color: #cbd5e1; margin: 0.5rem 0; font-size: 0.95rem;'>Track and manage your stock portfolio with real-time P&L and analysis</p>
</div>
""", unsafe_allow_html=True)

portfolio_mgr = get_portfolio_manager()

with st.sidebar:
    st.markdown("### 🎯 Portfolio Actions")
    action = st.radio(
        "Select Action",
        ["View Portfolio", "Add Holding", "Analytics"],
        label_visibility="collapsed"
    )

if "user" not in st.session_state or not st.session_state.user:
    st.warning("⚠️ Please log in to access portfolio features")
    st.stop()

user_id = st.session_state.user.get("username", "guest")
portfolio_id = portfolio_mgr.create_portfolio(user_id)

if action == "View Portfolio":
    st.markdown("### 📊 Current Holdings", divider="blue")

    holdings = portfolio_mgr.get_holdings(portfolio_id)

    if holdings.empty:
        st.info("📊 No holdings yet. Add your first stock to get started!")
        st.markdown("")

        with st.form("add_first_holding"):
            col1, col2, col3 = st.columns(3, gap="medium")
            with col1:
                symbol = ui.input_text("Stock Symbol", key='first_symbol', placeholder="e.g., AAPL")
            with col2:
                quantity = ui.input_number("Quantity", key='first_qty', value=10.0, min_value=0.1)
            with col3:
                price = ui.input_number("Purchase Price (₹)", key='first_price', value=150.0, min_value=0.01)

            st.markdown("")

            if st.form_submit_button("✅ Add First Holding", use_container_width=True):
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
        metrics = portfolio_mgr.calculate_portfolio_metrics(portfolio_id)

        st.markdown("**📈 Portfolio Overview**")
        metric_cols = st.columns(4, gap="medium")

        with metric_cols[0]:
            ui.render_metric_card("Total Value", f"₹{metrics.get('total_value', 0):,.2f}")

        with metric_cols[1]:
            ui.render_metric_card("Total Invested", f"₹{metrics.get('total_invested', 0):,.2f}")

        with metric_cols[2]:
            gain = metrics.get('total_gain', 0)
            gain_pct = metrics.get('total_gain_pct', 0)
            ui.render_metric_card(
                "Total Gain/Loss",
                f"₹{gain:,.2f}",
                delta=f"{gain_pct:.2f}%",
                trend="up" if gain >= 0 else "down"
            )

        with metric_cols[3]:
            try:
                var_95 = portfolio_mgr.calculate_var(portfolio_id)
                ui.render_metric_card("Value at Risk (95%)", f"₹{abs(var_95):,.2f}")
            except Exception:
                ui.render_metric_card("Value at Risk (95%)", "N/A")

        st.markdown("")
        st.divider()
        st.markdown("")

        st.markdown("**📋 Holdings Details**")
        if 'holdings' in metrics:
            holdings_data = []
            for h in metrics['holdings']:
                holdings_data.append({
                    'Symbol': h['symbol'],
                    'Quantity': f"{h['quantity']:.2f}",
                    'Purchase Price': f"₹{h['purchase_price']:.2f}",
                    'Current Price': f"₹{h['current_price']:.2f}",
                    'Current Value': f"₹{h['current_value']:,.2f}",
                    'Gain/Loss': f"₹{h['gain']:,.2f}",
                    'Return %': f"{h['gain_pct']:.2f}%",
                    '% of Portfolio': f"{(h['current_value']/max(metrics.get('total_value', 1), 1)*100):.1f}%"
                })

            st.dataframe(pd.DataFrame(holdings_data), use_container_width=True)

            st.markdown("")

            if 'diversification' in metrics and len(metrics['diversification']) > 0:
                col1, col2 = st.columns([2, 3], gap="large")

                with col1:
                    st.markdown("**🎯 Diversification**")
                    div_data = pd.DataFrame([
                        {'Symbol': d['symbol'], 'Weight %': d['weight'] * 100}
                        for d in metrics['diversification']
                    ])
                    st.dataframe(div_data, use_container_width=True, hide_index=True)

                with col2:
                    fig = go.Figure(data=[go.Pie(
                        labels=[d['symbol'] for d in metrics['diversification']],
                        values=[d['weight'] * 100 for d in metrics['diversification']],
                        hole=0.35,
                        marker=dict(colors=['#38bdf8', '#a855f7', '#10b981', '#f59e0b', '#ef4444'])
                    )])
                    fig.update_layout(
                        title="Portfolio Composition",
                        height=400,
                        showlegend=True
                    )
                    st.plotly_chart(fig, use_container_width=True)

            st.markdown("")

elif action == "Add Holding":
    st.markdown("### ➕ Add New Holding", divider="green")
    st.markdown("")

    with st.form("add_holding_form"):
        col1, col2 = st.columns(2, gap="medium")

        with col1:
            symbol = st.text_input(
                "Stock Symbol",
                placeholder="e.g., AAPL, TCS, INFY",
                max_chars=10
            ).upper()
            quantity = st.number_input(
                "Number of Shares",
                value=10.0,
                min_value=0.1,
                step=0.1
            )

        with col2:
            price = st.number_input(
                "Purchase Price per Share (₹)",
                value=100.0,
                min_value=0.01,
                step=0.01
            )
            date = st.date_input("Purchase Date")

        st.markdown("")

        col_btn, col_info = st.columns([2, 3], gap="medium")
        with col_btn:
            if st.form_submit_button("✅ Add to Portfolio", use_container_width=True):
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
                        st.rerun()
                    else:
                        st.error("❌ Failed to add holding")
                else:
                    st.error("❌ Please enter a valid stock symbol")

        with col_info:
            st.info("ℹ️ Add holdings to start tracking your portfolio performance and risk profile.")

elif action == "Analytics":
    st.subheader("Portfolio Analytics")

    try:
        metrics = portfolio_mgr.calculate_portfolio_metrics(portfolio_id)

        if not metrics.get('holdings'):
            st.info("No holdings to analyze")
        else:
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
                except Exception:
                    st.warning("Unable to calculate correlations")

            st.write("#### Risk Metrics")
            try:
                var_95 = portfolio_mgr.calculate_var(portfolio_id, confidence=0.95)
                var_99 = portfolio_mgr.calculate_var(portfolio_id, confidence=0.99)

                c1, c2 = st.columns(2)
                with c1:
                    ui.render_metric_card("Value at Risk (95%)", f"₹{abs(var_95):,.2f}")
                with c2:
                    ui.render_metric_card("Value at Risk (99%)", f"₹{abs(var_99):,.2f}")
            except Exception:
                st.warning("Unable to calculate VaR")

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
