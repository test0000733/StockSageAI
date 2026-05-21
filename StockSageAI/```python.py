
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import yfinance as yf

# Import custom modules
from data_fetcher import DataFetcher
from lstm_model import LSTMPredictor
from sentiment_analyzer import SentimentAnalyzer
from recommendation_engine import RecommendationEngine
from news_scraper import NewsScraper
from utils import format_currency, get_stock_symbol, get_indian_stock_list

# Page config
st.set_page_config(
    page_title="SP 07 🚀 AI-Powered Stock Forecasting",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced styling with animated background
st.markdown("""
<style>
    /* Animated gradient background */
    .stApp {
        background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
    }
    
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Main container styling */
    .main-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        border: 1px solid rgba(255, 255, 255, 0.18);
    }
    
    /* Title styling */
    .main-title {
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4, #45B7D1, #96CEB4);
        background-size: 400% 400%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gradientText 3s ease infinite;
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    @keyframes gradientText {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    /* Subtitle styling */
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
        font-style: italic;
    }
    
    /* Sidebar enhancements */
    .css-1d391kg {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px 0 rgba(31, 38, 135, 0.2);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px 0 rgba(31, 38, 135, 0.4);
    }
    
    /* Metric cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 20px 0 rgba(31, 38, 135, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.3);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    /* Chart containers */
    .chart-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 4px 20px 0 rgba(31, 38, 135, 0.15);
    }
    
    /* Loading animation */
    .loading {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 200px;
    }
    
    .spinner {
        width: 50px;
        height: 50px;
        border: 5px solid #f3f3f3;
        border-top: 5px solid #3498db;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Success/Error alerts */
    .success-alert {
        background: linear-gradient(135deg, #4ECDC4, #44A08D);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .error-alert {
        background: linear-gradient(135deg, #FF6B6B, #EE5A52);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* Floating particles animation */
    .particles {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        overflow: hidden;
        z-index: -1;
    }
    
    .particle {
        position: absolute;
        width: 4px;
        height: 4px;
        background: rgba(255, 255, 255, 0.5);
        border-radius: 50%;
        animation: float 6s ease-in-out infinite;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px) rotate(0deg); opacity: 1; }
        50% { transform: translateY(-20px) rotate(180deg); opacity: 0.5; }
    }
    
    /* Recommendation styling */
    .recommendation-buy {
        background: linear-gradient(135deg, #4CAF50, #45a049);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        font-weight: bold;
        font-size: 1.2rem;
        box-shadow: 0 4px 20px rgba(76, 175, 80, 0.3);
        animation: pulse 2s ease-in-out infinite;
    }
    
    .recommendation-sell {
        background: linear-gradient(135deg, #f44336, #d32f2f);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        font-weight: bold;
        font-size: 1.2rem;
        box-shadow: 0 4px 20px rgba(244, 67, 54, 0.3);
        animation: pulse 2s ease-in-out infinite;
    }
    
    .recommendation-hold {
        background: linear-gradient(135deg, #ff9800, #f57c00);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        font-weight: bold;
        font-size: 1.2rem;
        box-shadow: 0 4px 20px rgba(255, 152, 0, 0.3);
        animation: pulse 2s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }
</style>

<div class="particles">
    <div class="particle" style="left: 10%; animation-delay: 0s;"></div>
    <div class="particle" style="left: 20%; animation-delay: 1s;"></div>
    <div class="particle" style="left: 30%; animation-delay: 2s;"></div>
    <div class="particle" style="left: 40%; animation-delay: 3s;"></div>
    <div class="particle" style="left: 50%; animation-delay: 4s;"></div>
    <div class="particle" style="left: 60%; animation-delay: 5s;"></div>
    <div class="particle" style="left: 70%; animation-delay: 0.5s;"></div>
    <div class="particle" style="left: 80%; animation-delay: 1.5s;"></div>
    <div class="particle" style="left: 90%; animation-delay: 2.5s;"></div>
</div>

<div class="main-container">
    <h1 class="main-title">SP 07 🚀 AI-Powered Stock Forecasting</h1>
    <p class="subtitle">Predict Indian stock prices using advanced ML and news sentiment analysis</p>
</div>
""", unsafe_allow_html=True)

# --- Display market leaders section ---
def get_market_leaders():
    """Fetch most bought, top gainers, and top losers from popular NSE stocks."""
    stock_list = get_indian_stock_list()
    data = []
    for symbol in stock_list:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2d")
            if len(hist) < 2:
                continue
            prev_close = hist['Close'].iloc[-2]
            last_close = hist['Close'].iloc[-1]
            pct_change = ((last_close - prev_close) / prev_close) * 100
            volume = hist['Volume'].iloc[-1]
            data.append({
                'symbol': symbol,
                'name': ticker.info.get('shortName', symbol),
                'close': last_close,
                'pct_change': pct_change,
                'volume': volume
            })
        except Exception:
            continue
    if not data:
        return None, [], []
    most_bought = max(data, key=lambda x: x['volume'])
    sorted_by_change = sorted(data, key=lambda x: x['pct_change'], reverse=True)
    top_gainers = sorted_by_change[:3]
    top_losers = sorted_by_change[-3:][::-1]
    return most_bought, top_gainers, top_losers

# --- Place this block right after the main title/subtitle HTML ---
most_bought, top_gainers, top_losers = get_market_leaders()
st.markdown("""
<style>
.market-leader-card {
    background: linear-gradient(120deg, #f6d365 0%, #fda085 100%);
    border-radius: 14px;
    box-shadow: 0 2px 12px 0 rgba(31, 38, 135, 0.10);
    padding: 1.2rem 1.5rem 1.2rem 1.5rem;
    margin: 1rem 0 1.5rem 0;
    color: #222;
    display: flex;
    flex-wrap: wrap;
    gap: 1.5rem;
    justify-content: center;
}
.market-leader-section {
    min-width: 220px;
    flex: 1;
    text-align: center;
}
.market-leader-title {
    font-size: 1.1rem;
    font-weight: bold;
    margin-bottom: 0.5rem;
    color: #2E86C1;
}
.market-leader-symbol {
    font-size: 1.2rem;
    font-weight: bold;
    margin-bottom: 0.2rem;
}
.market-leader-pct {
    font-size: 1.1rem;
    font-weight: bold;
}
.gain { color: #27ae60; }
.loss { color: #c0392b; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="market-leader-card">', unsafe_allow_html=True)

if most_bought:
    st.markdown(f"""
    <div class="market-leader-section">
        <div class="market-leader-title">🔥 Most Bought Stock (Volume)</div>
        <div class="market-leader-symbol">{most_bought['symbol']}</div>
        <div>{most_bought['name']}</div>
        <div>Volume: <b>{int(most_bought['volume']):,}</b></div>
        <div>Price: {format_currency(most_bought['close'])}</div>
    </div>
    """, unsafe_allow_html=True)

if top_gainers:
    st.markdown(f"""
    <div class="market-leader-section">
        <div class="market-leader-title">🚀 Top 3 Gainers</div>
        {''.join([
            f"<div class='market-leader-symbol'>{g['symbol']}</div>"
            f"<div>{g['name']}</div>"
            f"<div class='market-leader-pct gain'>+{g['pct_change']:.2f}%</div>"
            for g in top_gainers
        ])}
    </div>
    """, unsafe_allow_html=True)

if top_losers:
    st.markdown(f"""
    <div class="market-leader-section">
        <div class="market-leader-title">📉 Top 3 Losers</div>
        {''.join([
            f"<div class='market-leader-symbol'>{l['symbol']}</div>"
            f"<div>{l['name']}</div>"
            f"<div class='market-leader-pct loss'>{l['pct_change']:.2f}%</div>"
            for l in top_losers
        ])}
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Sidebar inputs
st.sidebar.header("📊 Stock Analysis Parameters")

# Stock symbol input
company_input = st.sidebar.text_input(
    "Enter Company Symbol or Name",
    placeholder="e.g., TCS, RELIANCE, INFY, TCS.NS",
    help="Enter NSE stock symbol or company name"
)

# Remove forecast_days selection and button
analyze_button = st.sidebar.button("🔍 Analyze Stock", type="primary")

# Initialize session state
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False

if analyze_button and company_input:
    try:
        # Show progress
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Step 1: Get stock symbol
        status_text.text("🔍 Validating stock symbol...")
        progress_bar.progress(10)
        
        stock_symbol = get_stock_symbol(company_input)
        
        # Initialize components
        data_fetcher = DataFetcher()
        lstm_predictor = LSTMPredictor()
        sentiment_analyzer = SentimentAnalyzer()
        news_scraper = NewsScraper()
        recommendation_engine = RecommendationEngine()
        
        # Show the symbol being used
        st.info(f"📊 Analyzing: **{stock_symbol}**")
        
        # Step 2: Fetch stock data
        status_text.text("📈 Fetching historical stock data...")
        progress_bar.progress(25)
        
        stock_data = data_fetcher.get_stock_data(stock_symbol)
        if stock_data.empty:
            st.error(f"❌ Could not fetch data for {stock_symbol}")
            st.stop()
        
        # Step 3: Train LSTM model and make predictions for all durations
        status_text.text("🧠 Training LSTM model and generating predictions...")
        progress_bar.progress(50)
        
        forecast_days_list = [7, 14, 30]
        predictions_dict = {}
        recommendations_dict = {}
        for fd in forecast_days_list:
            preds = lstm_predictor.predict(stock_data, fd)
            predictions_dict[fd] = preds
        
        # Step 4: Fetch and analyze news
        status_text.text("📰 Fetching and analyzing news sentiment...")
        progress_bar.progress(75)
        
        company_name = stock_symbol.replace('.NS', '')
        news_headlines = news_scraper.get_news(company_name)
        sentiment_scores = sentiment_analyzer.analyze_sentiment(news_headlines)
        
        # Step 5: Generate recommendations for all durations
        status_text.text("🎯 Generating investment recommendations...")
        progress_bar.progress(90)
        
        for fd in forecast_days_list:
            recommendations_dict[fd] = recommendation_engine.generate_recommendation(
                stock_data, predictions_dict[fd], sentiment_scores, fd
            )
        
        # Store results in session state
        st.session_state.stock_symbol = stock_symbol
        st.session_state.stock_data = stock_data
        st.session_state.predictions_dict = predictions_dict
        st.session_state.sentiment_scores = sentiment_scores
        st.session_state.recommendations_dict = recommendations_dict
        st.session_state.news_headlines = news_headlines
        st.session_state.analysis_complete = True
        
        progress_bar.progress(100)
        status_text.text("✅ Analysis complete!")
        
    except Exception as e:
        st.error(f"❌ Error during analysis: {str(e)}")
        st.stop()

# Display results if analysis is complete
if st.session_state.analysis_complete:
    stock_data = st.session_state.stock_data
    predictions_dict = st.session_state.predictions_dict
    sentiment_scores = st.session_state.sentiment_scores
    recommendations_dict = st.session_state.recommendations_dict
    news_headlines = st.session_state.news_headlines
    stock_symbol = st.session_state.stock_symbol
    
    # Main content area
    st.subheader(f"📈 {stock_symbol} - Multi-Horizon Price Forecast & Recommendation")
    
    # Decorative combined forecast table
    st.markdown("""
    <style>
    .forecast-table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 2rem;
        background: rgba(255,255,255,0.95);
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 4px 20px 0 rgba(31, 38, 135, 0.15);
    }
    .forecast-table th, .forecast-table td {
        padding: 1rem;
        text-align: center;
        border-bottom: 1px solid #eee;
        font-size: 1.1rem;
    }
    .forecast-table th {
        background: linear-gradient(90deg, #23a6d5 0%, #23d5ab 100%);
        color: #fff;
        font-size: 1.2rem;
    }
    .forecast-table tr:last-child td {
        border-bottom: none;
    }
    .rec-buy { background: linear-gradient(90deg, #4CAF50 0%, #45a049 100%); color: #fff; font-weight: bold;}
    .rec-sell { background: linear-gradient(90deg, #f44336 0%, #d32f2f 100%); color: #fff; font-weight: bold;}
    .rec-hold { background: linear-gradient(90deg, #ff9800 0%, #f57c00 100%); color: #fff; font-weight: bold;}
    </style>
    """, unsafe_allow_html=True)
    
    current_price = stock_data['Close'].iloc[-1]
    table_html = """
    <table class="forecast-table">
        <tr>
            <th>Forecast Horizon</th>
            <th>Predicted Price</th>
            <th>Expected Change</th>
            <th>Recommendation</th>
            <th>Confidence</th>
        </tr>
    """
    for fd in [7, 14, 30]:
        preds = predictions_dict[fd]
        predicted_price = preds[-1]
        price_change_pct = (predicted_price - current_price) / current_price * 100
        rec = recommendations_dict[fd]
        rec_action = rec['action']
        rec_conf = rec['confidence']
        rec_class = "rec-buy" if rec_action == "BUY" else "rec-sell" if rec_action == "SELL" else "rec-hold"
        rec_emoji = "🟢" if rec_action == "BUY" else "🔴" if rec_action == "SELL" else "🟡"
        table_html += f"""
        <tr>
            <td><b>{fd} days</b></td>
            <td>{format_currency(predicted_price)}</td>
            <td style="color:{'green' if price_change_pct>=0 else 'red'}">{price_change_pct:+.2f}%</td>
            <td class="{rec_class}">{rec_emoji} {rec_action}</td>
            <td>{rec_conf:.1f}%</td>
        </tr>
        """
    table_html += "</table>"
    st.markdown(table_html, unsafe_allow_html=True)
    
    # Show price chart for all forecasts
    fig_price = go.Figure()
    fig_price.add_trace(go.Scatter(
        x=stock_data.index,
        y=stock_data['Close'],
        mode='lines',
        name='Historical Price',
        line=dict(color='blue', width=2)
    ))
    colors = {7: 'red', 14: 'orange', 30: 'green'}
    for fd in [7, 14, 30]:
        future_dates = pd.date_range(
            start=stock_data.index[-1] + timedelta(days=1),
            periods=fd,
            freq='D'
        )
        fig_price.add_trace(go.Scatter(
            x=future_dates,
            y=predictions_dict[fd],
            mode='lines+markers',
            name=f'{fd}-Day Forecast',
            line=dict(color=colors[fd], width=2, dash='dash'),
            marker=dict(size=6)
        ))
    fig_price.update_layout(
        title=f"{stock_symbol} - Historical vs Multi-Horizon Forecasted Prices",
        xaxis_title="Date",
        yaxis_title="Price (₹)",
        hovermode='x unified',
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#333333'),
        title_font_size=16,
        title_font_color='#2E86C1'
    )
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.plotly_chart(fig_price, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('---')
        st.subheader("📰 News Sentiment Analysis")
        
        if sentiment_scores:
            # Create sentiment chart
            sentiment_df = pd.DataFrame(sentiment_scores)
            
            fig_sentiment = px.bar(
                sentiment_df,
                x='date',
                y='compound',
                color='compound',
                color_continuous_scale=['red', 'yellow', 'green'],
                title="Daily Sentiment Scores",
                labels={'compound': 'Sentiment Score', 'date': 'Date'}
            )
            
            fig_sentiment.update_layout(height=300)
            st.plotly_chart(fig_sentiment, use_container_width=True)
            
            # Average sentiment
            avg_sentiment = np.mean([s['compound'] for s in sentiment_scores])
            sentiment_label = "Positive" if avg_sentiment > 0.1 else "Negative" if avg_sentiment < -0.1 else "Neutral"
            sentiment_color = "green" if avg_sentiment > 0.1 else "red" if avg_sentiment < -0.1 else "orange"
            
            st.markdown(f"""
            **Average Sentiment:** <span style="color: {sentiment_color};">{sentiment_label} ({avg_sentiment:.3f})</span>
            """, unsafe_allow_html=True)
        else:
            st.info("No recent news found for sentiment analysis")
    
    # Recent news headlines
    if news_headlines:
        st.subheader("📰 Recent News Headlines")
        
        for i, headline in enumerate(news_headlines[:5]):  # Show top 5 headlines
            sentiment_score = sentiment_scores[i]['compound'] if i < len(sentiment_scores) else 0
            sentiment_emoji = "🟢" if sentiment_score > 0.1 else "🔴" if sentiment_score < -0.1 else "🟡"
            
            st.markdown(f'''
            <div class="metric-card">
                <h4>{sentiment_emoji} {headline['title']}</h4>
                <p><em>Source: {headline.get('source', 'Unknown')} | {headline.get('date', 'Unknown date')}</em></p>
                <p><strong>Sentiment Score: {sentiment_score:.3f}</strong></p>
            </div>
            ''', unsafe_allow_html=True)
    
    # --- Decorative Investment Calculator ---
    st.markdown("""
    <style>
    .calc-container {
        background: linear-gradient(120deg, #f6d365 0%, #fda085 100%);
        border-radius: 18px;
        box-shadow: 0 4px 24px 0 rgba(31, 38, 135, 0.18);
        padding: 2rem 2rem 1.5rem 2rem;
        margin: 2rem 0 1rem 0;
        max-width: 600px;
        margin-left: auto;
        margin-right: auto;
        color: #333;
    }
    .calc-title {
        font-size: 1.6rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1.2rem;
        background: linear-gradient(90deg, #23a6d5 0%, #23d5ab 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .calc-label {
        font-weight: 600;
        margin-bottom: 0.3rem;
    }
    .calc-result {
        font-size: 1.2rem;
        font-weight: bold;
        margin-top: 0.7rem;
        padding: 0.7rem 1rem;
        border-radius: 10px;
        background: linear-gradient(90deg, #f8ffae 0%, #43c6ac 100%);
        color: #222;
        text-align: center;
        box-shadow: 0 2px 8px 0 rgba(31, 38, 135, 0.10);
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="calc-container">', unsafe_allow_html=True)
    st.markdown('<div class="calc-title">💹 Investment Calculator</div>', unsafe_allow_html=True)

    with st.form("investment_calc_form"):
        qty = st.number_input("Enter Quantity of Shares", min_value=1, value=10, step=1, key="calc_qty")
        current_price = stock_data['Close'].iloc[-1]
        pred_price_7 = predictions_dict[7][-1]
        pred_price_14 = predictions_dict[14][-1]
        pred_price_30 = predictions_dict[30][-1]
        pred_price = st.selectbox(
            "Select Future Predicted Price",
            options=[
                (f"7-Day: {format_currency(pred_price_7)}", pred_price_7),
                (f"14-Day: {format_currency(pred_price_14)}", pred_price_14),
                (f"30-Day: {format_currency(pred_price_30)}", pred_price_30)
            ],
            format_func=lambda x: x[0],
            index=0,
            key="calc_pred_price"
        )[1]
        submitted = st.form_submit_button("Calculate 💡")

    if qty and pred_price:
        invested = qty * current_price
        future_value = qty * pred_price
        profit = future_value - invested
        profit_pct = (profit / invested) * 100 if invested else 0

        st.markdown(f"""
        <div class="calc-result">
            <span class="calc-label">Invested Amount:</span> {format_currency(invested)}<br>
            <span class="calc-label">Future Value:</span> {format_currency(future_value)}<br>
            <span class="calc-label">Profit/Loss:</span> <span style="color:{'green' if profit>=0 else 'red'}">{format_currency(profit)} ({profit_pct:+.2f}%)</span>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Enhanced Risk disclaimer and credits
    st.markdown("---")
    st.markdown('''
    <div class="chart-container">
        <h3>⚠️ Risk Disclaimer & Credits</h3>
        <p><strong>Important Notice:</strong> This tool provides AI-generated predictions for educational purposes only. Stock market investments carry significant risk, and past performance does not guarantee future results. Always consult with qualified financial advisors before making investment decisions.</p>
        
        <div style="margin-top: 2rem;">
            <h4>💡 Built with Advanced Technology:</h4>
            <div style="display: flex; flex-wrap: wrap; gap: 1rem; margin-top: 1rem;">
                <div class="metric-card" style="flex: 1; min-width: 200px;">
                    <h5>🧠 Machine Learning</h5>
                    <p>Scikit-learn ensemble models with Random Forest & Linear Regression for realistic predictions</p>
                </div>
                <div class="metric-card" style="flex: 1; min-width: 200px;">
                    <h5>📊 Data Sources</h5>
                    <p>Yahoo Finance API for real-time stock data and financial news sentiment analysis</p>
                </div>
                <div class="metric-card" style="flex: 1; min-width: 200px;">
                    <h5>🚀 Technology Stack</h5>
                    <p>Streamlit, Plotly, VADER Sentiment, Python ML ecosystem</p>
                </div>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

else:
    # Enhanced Welcome screen with beautiful styling
    st.markdown('''
    <div class="chart-container">
        <h2>🎯 Welcome to SP 07 AI-Powered Stock Forecasting!</h2>
        <p style="font-size: 1.2rem; color: #666; text-align: center; margin-bottom: 2rem;">
            Harness the power of advanced AI to forecast Indian stock prices with realistic predictions and intelligent recommendations.
        </p>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; margin: 2rem 0;">
            <div class="metric-card">
                <h4>🧠 Smart Predictions</h4>
                <p>Advanced ensemble ML models with realistic volatility constraints ensure believable forecasts</p>
            </div>
            <div class="metric-card">
                <h4>📰 Sentiment Analysis</h4>
                <p>Real-time news analysis using VADER sentiment scoring for market mood assessment</p>
            </div>
            <div class="metric-card">
                <h4>📊 Interactive Charts</h4>
                <p>Beautiful visualizations showing historical data, predictions, and technical indicators</p>
            </div>
            <div class="metric-card">
                <h4>🎯 Investment Recommendations</h4>
                <p>Clear BUY/SELL/HOLD advice with confidence scores and detailed reasoning</p>
            </div>
        </div>
        
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; border-radius: 15px; margin: 2rem 0;">
            <h3>🚀 Quick Start Guide</h3>
            <ol style="font-size: 1.1rem; line-height: 1.8;">
                <li>Enter any Indian company name or symbol in the sidebar (TCS, RELIANCE, INFY)</li>
                <li>Choose your forecast duration: 7, 14, or 30 days</li>
                <li>Click "Analyze Stock" and watch the AI work its magic!</li>
            </ol>
        </div>
        
        <div class="success-alert">
            <h4>✨ Try These Popular Stocks:</h4>
            <p><strong>TCS</strong> | <strong>RELIANCE</strong> | <strong>INFY</strong> | <strong>HDFCBANK</strong> | <strong>ICICIBANK</strong> | <strong>SBIN</strong></p>
            <p>Or enter any NSE-listed company name - our universal symbol detection will find it automatically!</p>
        </div>
    </div>
    ''', unsafe_allow_html=True)