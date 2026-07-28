"""
Trading Signals Page
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from StockSageAI.trading_signals import get_trading_signals_generator

st.set_page_config(page_title="Trading Signals", layout="wide")

st.markdown("# 📡 Real-Time Trading Signals")
st.markdown("Automatic Buy/Sell/Hold recommendations with confidence scores")

signals_gen = get_trading_signals_generator()

if "user" not in st.session_state or not st.session_state.user:
    st.warning("⚠️ Please log in to access trading signals")
    st.stop()

user_id = st.session_state.user.get("username", "guest")

# Sidebar
with st.sidebar:
    st.subheader("Signal Generation")
    section = st.radio("Select", ["Generate Signals", "Track Active", "Accuracy Report"])

# ============================================================================
# GENERATE SIGNALS
# ============================================================================
if section == "Generate Signals":
    st.subheader("Generate Trading Signal")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        symbol = st.text_input("Stock Symbol", value="AAPL", max_chars=10).upper()
    
    with col2:
        # Dummy model predictions
        pred_ensemble = st.slider("Ensemble Prediction", -1.0, 1.0, 0.15)
    
    with col3:
        current_price = st.number_input("Current Price (₹)", value=150.0, min_value=0.01)
    
    if st.button("Generate Signal", type="primary", use_container_width=True):
        with st.spinner("Generating signal..."):
            try:
                # Generate signal
                models_predictions = {
                    'Transformer': pred_ensemble + 0.05,
                    'LSTM': pred_ensemble - 0.02,
                    'BiLSTM': pred_ensemble + 0.03,
                    'CNN-LSTM': pred_ensemble,
                    'GNN': pred_ensemble - 0.01,
                    'XGBoost': pred_ensemble + 0.02,
                    'Multimodal': pred_ensemble - 0.03,
                    'Ensemble': pred_ensemble
                }
                
                signal_data = signals_gen.generate_signal(symbol, models_predictions, current_price)
                
                if signal_data:
                    # Display signal
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        signal_color = "green" if signal_data['signal'] == 'BUY' else "red" if signal_data['signal'] == 'SELL' else "gray"
                        st.metric("Signal", signal_data['signal'])
                    
                    with col2:
                        st.metric("Confidence", f"{signal_data['confidence']:.1f}%")
                    
                    with col3:
                        st.metric("Entry Price", f"₹{signal_data['entry_price']:.2f}")
                    
                    with col4:
                        st.metric("Target Price", f"₹{signal_data['target_price']:.2f}")
                    
                    st.divider()
                    
                    # Risk metrics
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Stop Loss", f"₹{signal_data['stop_loss']:.2f}")
                    
                    with col2:
                        risk_reward = (signal_data['target_price'] - signal_data['entry_price']) / (signal_data['entry_price'] - signal_data['stop_loss']) if signal_data['entry_price'] != signal_data['stop_loss'] else 0
                        st.metric("Risk/Reward", f"{risk_reward:.2f}")
                    
                    with col3:
                        st.metric("Volatility", f"{signal_data.get('volatility', 0):.2%}")
                    
                    st.divider()
                    
                    # Model votes
                    votes = signal_data.get('model_votes', {})
                    if votes:
                        st.subheader("Model Consensus")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Buy Votes", votes.get('buy', 0))
                        with col2:
                            st.metric("Sell Votes", votes.get('sell', 0))
                        with col3:
                            st.metric("Hold Votes", votes.get('hold', 0))
                    
                    # Save signal
                    if st.button("Save Signal", use_container_width=True):
                        signal_id = signals_gen.save_signal(user_id, signal_data)
                        if signal_id > 0:
                            st.success(f"✅ Signal saved (ID: {signal_id})")
                        else:
                            st.error("Failed to save signal")
            
            except Exception as e:
                st.error(f"Error generating signal: {str(e)}")

# ============================================================================
# TRACK ACTIVE SIGNALS
# ============================================================================
elif section == "Track Active":
    st.subheader("Active Trading Signals")
    
    try:
        signals = signals_gen.get_active_signals(user_id)
        
        if signals:
            for signal in signals:
                with st.container(border=True):
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.write(f"**{signal['symbol']}**")
                        st.caption(f"Signal: {signal['signal']}")
                    
                    with col2:
                        st.metric("Confidence", f"{signal['confidence']:.1f}%")
                    
                    with col3:
                        st.metric("Entry", f"₹{signal['entry_price']:.2f}")
                    
                    with col4:
                        st.metric("Target", f"₹{signal['target_price']:.2f}")
                    
                    # Track performance
                    if st.button(f"Track {signal['symbol']}", key=f"track_{signal['id']}"):
                        current_price = st.number_input(
                            f"Current price for {signal['symbol']}",
                            value=signal['entry_price'],
                            key=f"price_{signal['id']}"
                        )
                        
                        performance = signals_gen.track_signal_performance(signal['id'], current_price)
                        
                        if performance:
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("P&L", f"₹{performance.get('pnl', 0):.2f}")
                            with col2:
                                st.metric("P&L %", f"{performance.get('pnl_pct', 0):.2f}%")
                            with col3:
                                st.metric("Status", performance.get('outcome', 'PENDING'))
        else:
            st.info("No active signals. Generate one to get started!")
    
    except Exception as e:
        st.error(f"Error retrieving signals: {str(e)}")

# ============================================================================
# ACCURACY REPORT
# ============================================================================
elif section == "Accuracy Report":
    st.subheader("Signal Accuracy Report")
    
    try:
        accuracy = signals_gen.get_signal_accuracy_report(user_id, days=30)
        
        if accuracy and accuracy.get('total_signals', 0) > 0:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Signals", accuracy['total_signals'])
            with col2:
                st.metric("Profitable", accuracy['profitable'])
            with col3:
                st.metric("Win Rate", f"{accuracy['win_rate']:.1f}%")
            with col4:
                st.metric("Avg Accuracy", f"{accuracy['avg_accuracy']:.1f}%")
        
        else:
            st.info("No signals in the selected period")
    
    except Exception as e:
        st.error(f"Error: {str(e)}")

st.caption("Trading Signals • SP 07 StockSageAI")
