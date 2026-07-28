"""
Stock Comparison Page
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from StockSageAI.stock_comparator import get_stock_comparator

st.set_page_config(page_title="Stock Comparison", layout="wide")

st.markdown("# 📊 Multi-Stock Comparison Tool")
st.markdown("Compare stocks with side-by-side analysis and forecasts")

comparator = get_stock_comparator()

# Input section
st.subheader("Select Stocks to Compare")

symbols_input = st.text_input(
    "Enter Stock Symbols (comma-separated, max 5)",
    value="AAPL, GOOGL, MSFT, AMZN, TSLA",
    placeholder="e.g., AAPL, GOOGL, MSFT"
)

if st.button("Compare Stocks", type="primary", use_container_width=True):
    symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]
    
    if len(symbols) == 0:
        st.error("Please enter at least one symbol")
    elif len(symbols) > 5:
        st.error("Maximum 5 stocks to compare")
    else:
        with st.spinner("Comparing stocks..."):
            try:
                # Main comparison
                comparison_df = comparator.compare_stocks(symbols)
                
                if not comparison_df.empty:
                    st.subheader("Stock Metrics Comparison")
                    
                    # Display key metrics
                    display_cols = ['symbol', 'name', 'price', 'pe', 'dividend', 'volatility', 'sharpe_ratio', 'change_1y']
                    if 'name' in comparison_df.columns:
                        st.dataframe(
                            comparison_df[[c for c in display_cols if c in comparison_df.columns]],
                            use_container_width=True
                        )
                    
                    st.divider()
                    
                    # Performance comparison
                    st.subheader("Performance Metrics")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # 1-Year Return Comparison
                        fig = px.bar(
                            comparison_df,
                            x='symbol',
                            y='change_1y',
                            title="1-Year Returns",
                            color='change_1y',
                            color_continuous_scale='RdYlGn'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        # Volatility Comparison
                        fig = px.bar(
                            comparison_df,
                            x='symbol',
                            y='volatility',
                            title="Volatility",
                            color='volatility',
                            color_continuous_scale='Reds'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # P/E Ratio Comparison
                    fig = px.bar(
                        comparison_df,
                        x='symbol',
                        y='pe',
                        title="P/E Ratio Comparison",
                        color='pe',
                        color_continuous_scale='Blues'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.divider()
                    
                    # Relative Strength
                    st.subheader("Relative Strength Analysis")
                    strength = comparator.relative_strength_analysis(symbols)
                    
                    if strength:
                        strength_df = pd.DataFrame([
                            {
                                'Symbol': sym,
                                'Value': data.get('current_value', 0),
                                'Rank': data.get('rank', '-'),
                                'Momentum': data.get('momentum', 0),
                                'Status': '📈' if data.get('outperformer') else '📉'
                            }
                            for sym, data in strength.items()
                        ])
                        
                        st.dataframe(
                            strength_df.sort_values('Rank'),
                            use_container_width=True
                        )
                        
                        # Strength chart
                        fig = px.bar(
                            strength_df.sort_values('Rank'),
                            x='Symbol',
                            y='Value',
                            title="Relative Strength (Normalized to 100)",
                            color='Value',
                            color_continuous_scale='Viridis'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    st.divider()
                    
                    # Sector Analysis
                    st.subheader("Sector Analysis")
                    sector_analysis = comparator.sector_performance_comparison(symbols)
                    
                    if sector_analysis:
                        for sector, data in sector_analysis.items():
                            st.write(f"**{sector}** ({data['count']} stocks)")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Avg Return", f"{data['avg_return']:.1f}%")
                            with col2:
                                st.metric("Volatility", f"{data['volatility']:.1f}%")
                            with col3:
                                st.write(f"Stocks: {', '.join(data['stocks'])}")
                    
                    st.divider()
                    
                    # Correlation Heatmap
                    st.subheader("Correlation Heatmap")
                    heatmap_data = comparator.correlation_heatmap_data(symbols)
                    
                    if heatmap_data and 'values' in heatmap_data:
                        fig = go.Figure(data=go.Heatmap(
                            z=heatmap_data['values'],
                            x=heatmap_data['labels'],
                            y=heatmap_data['labels'],
                            colorscale='RdBu',
                            zmid=0
                        ))
                        fig.update_layout(title="Stock Correlation Matrix")
                        st.plotly_chart(fig, use_container_width=True)
                
                else:
                    st.error("Unable to fetch data for the selected stocks")
            
            except Exception as e:
                st.error(f"Error comparing stocks: {str(e)}")

st.caption("Stock Comparison Tool • SP 07 StockSageAI")
