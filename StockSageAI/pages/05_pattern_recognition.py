"""
Pattern Recognition Page
"""

import streamlit as st
import pandas as pd

from StockSageAI.pattern_recognition import get_pattern_recognizer
from StockSageAI.stocks_database import get_stocks_database, render_stock_selector
from StockSageAI.stocks_database import get_stocks_database, render_stock_selector

st.set_page_config(page_title="Pattern Recognition", layout="wide")

st.markdown("# 🔍 Candlestick Pattern Recognition")
st.markdown("### Automatic detection of 10+ technical patterns with probability scoring")

recognizer = get_pattern_recognizer()
stocks_db = get_stocks_database()
stocks_db = get_stocks_database()

# Enhanced layout
col1, col2, col3 = st.columns(3)

with col1:
    symbol = render_stock_selector("Stock Symbol", default_value="AAPL", key="pattern_symbol")

with col2:
    lookback = st.slider("📅 Lookback Period (days)", 30, 365, 100, 10)

with col3:
    confidence_threshold = st.slider("🎯 Confidence Threshold (%)", 50, 100, 75, 5)

if st.button("Scan for Patterns", type="primary"):
    with st.spinner("🔄 Fetching real-time data and scanning for patterns..."):
        try:
            # Fetch real-time data first
            try:
                import yfinance as yf
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=f"{lookback+30}d")
                if not hist.empty:
                    st.info(f"✅ Real-time data fetched for {symbol}")
            except:
                pass
            
            patterns = recognizer.detect_all_patterns(symbol, lookback)
            
            if patterns and 'patterns' in patterns:
                patterns_found = patterns['patterns']
                
                if patterns_found:
                    st.success(f"✅ Found {len(patterns_found)} patterns")
                    
                    st.divider()
                    
                    # Display patterns by signal
                    bullish_patterns = {k: v for k, v in patterns_found.items() if v.get('signal') == 'BULLISH'}
                    bearish_patterns = {k: v for k, v in patterns_found.items() if v.get('signal') == 'BEARISH'}
                    neutral_patterns = {k: v for k, v in patterns_found.items() if v.get('signal') == 'NEUTRAL'}
                    
                    if bullish_patterns:
                        st.subheader("📈 Bullish Patterns")
                        for pattern_name, pattern_data in bullish_patterns.items():
                            col1, col2, col3 = st.columns([2, 1, 1])
                            with col1:
                                st.write(f"**{pattern_data['pattern']}**")
                                st.caption(pattern_data.get('description', ''))
                            with col2:
                                st.metric("Probability", f"{pattern_data.get('probability', 0):.1f}%")
                            with col3:
                                st.metric("Strength", pattern_data.get('strength', 'N/A'))
                    
                    if bearish_patterns:
                        st.subheader("📉 Bearish Patterns")
                        for pattern_name, pattern_data in bearish_patterns.items():
                            col1, col2, col3 = st.columns([2, 1, 1])
                            with col1:
                                st.write(f"**{pattern_data['pattern']}**")
                                st.caption(pattern_data.get('description', ''))
                            with col2:
                                st.metric("Probability", f"{pattern_data.get('probability', 0):.1f}%")
                            with col3:
                                st.metric("Strength", pattern_data.get('strength', 'N/A'))
                    
                    if neutral_patterns:
                        st.subheader("⚪ Neutral Patterns")
                        for pattern_name, pattern_data in neutral_patterns.items():
                            col1, col2, col3 = st.columns([2, 1, 1])
                            with col1:
                                st.write(f"**{pattern_data['pattern']}**")
                                st.caption(pattern_data.get('description', ''))
                            with col2:
                                st.metric("Probability", f"{pattern_data.get('probability', 0):.1f}%")
                            with col3:
                                st.metric("Strength", pattern_data.get('strength', 'N/A'))
                else:
                    st.info("No patterns detected in the selected period")
            
            else:
                st.warning("⚠️ Unable to scan for patterns")
                st.info("💡 Tip: Try using valid symbols like AAPL, GOOGL, TCS.NS, INFY.NS")
        
        except Exception as e:
            st.error(f"❌ Error scanning patterns: {str(e)[:100]}")
            st.info("💡 Tip: Check if the symbol is valid and has sufficient data")

st.divider()

# Pattern Statistics
st.subheader("Pattern Statistics")

if st.button("Get Pattern Statistics", key="stats"):
    with st.spinner("Calculating statistics..."):
        try:
            stats = recognizer.get_pattern_statistics(symbol, 365)
            
            if stats and 'pattern_counts' in stats:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Patterns (1Y)", stats.get('total_patterns', 0))
                with col2:
                    st.metric("Bullish Patterns", stats.get('bullish_patterns', 0))
                with col3:
                    st.metric("Bearish Patterns", stats.get('bearish_patterns', 0))
                with col4:
                    st.metric("Bullish Ratio", f"{stats.get('bullish_ratio', 0)*100:.1f}%")
                
                st.divider()
                
                # Pattern frequency
                counted_patterns = stats.get('pattern_counts', {})
                top_patterns = sorted(
                    [(k, v) for k, v in counted_patterns.items() if v > 0],
                    key=lambda x: x[1],
                    reverse=True
                )
                
                if top_patterns:
                    st.write("**Most Frequent Patterns (12-Month Period):**")
                    
                    pattern_df = pd.DataFrame(top_patterns, columns=['Pattern', 'Occurrences'])
                    st.dataframe(pattern_df)
        
        except Exception as e:
            st.error(f"Error calculating statistics: {str(e)}")

st.caption("Pattern Recognition • SP 07 StockSageAI")
