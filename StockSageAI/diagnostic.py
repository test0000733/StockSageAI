"""
StockSageAI Comprehensive Diagnostic Tool
Tests all modules and identifies issues
Usage: streamlit run diagnostic.py
"""
import streamlit as st
import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Set page config
st.set_page_config(
    page_title="StockSageAI Diagnostics",
    page_icon="🔧",
    layout="wide"
)

st.title("🔧 StockSageAI System Diagnostics")
st.write("Comprehensive system health check and module testing")
st.markdown("---")

# Dictionary to store test results
test_results = {}

# 1. Test Imports
st.header("1️⃣ Testing Imports")
import_col1, import_col2 = st.columns(2)

with import_col1:
    try:
        from StockSageAI.data_fetcher import DataFetcher
        st.success("✅ DataFetcher imported successfully")
        test_results['DataFetcher'] = 'pass'
    except Exception as e:
        st.error(f"❌ DataFetcher import failed: {str(e)}")
        test_results['DataFetcher'] = 'fail'
    
    try:
        from StockSageAI.lstm_model import LSTMPredictor
        st.success("✅ LSTMPredictor imported successfully")
        test_results['LSTMPredictor'] = 'pass'
    except Exception as e:
        st.error(f"❌ LSTMPredictor import failed: {str(e)}")
        test_results['LSTMPredictor'] = 'fail'

with import_col2:
    try:
        from StockSageAI.sentiment_analyzer import SentimentAnalyzer
        st.success("✅ SentimentAnalyzer imported successfully")
        test_results['SentimentAnalyzer'] = 'pass'
    except Exception as e:
        st.error(f"❌ SentimentAnalyzer import failed: {str(e)}")
        test_results['SentimentAnalyzer'] = 'fail'
    
    try:
        from StockSageAI.recommendation_engine import RecommendationEngine
        st.success("✅ RecommendationEngine imported successfully")
        test_results['RecommendationEngine'] = 'pass'
    except Exception as e:
        st.error(f"❌ RecommendationEngine import failed: {str(e)}")
        test_results['RecommendationEngine'] = 'fail'

st.markdown("---")

# 2. Test Data Fetcher
st.header("2️⃣ Testing Data Fetcher")

test_symbols = ['RELIANCE.NS', 'TCS.NS', 'INFY.NS']
selected_symbol = st.selectbox("Select symbol to test:", test_symbols)

if st.button("Test Data Fetching for " + selected_symbol):
    try:
        from StockSageAI.data_fetcher import DataFetcher
        df = DataFetcher()
        
        st.info(f"Testing validation for {selected_symbol}...")
        is_valid = df.validate_symbol(selected_symbol)
        
        if is_valid:
            st.success(f"✅ Symbol {selected_symbol} validation passed")
            
            st.info(f"Fetching 1-year data for {selected_symbol}...")
            stock_data = df.get_stock_data(selected_symbol, period="1y")
            
            if stock_data.empty:
                st.error(f"❌ Could not fetch data for {selected_symbol}")
                test_results['DataFetch'] = 'fail'
            else:
                st.success(f"✅ Successfully fetched {len(stock_data)} days of data")
                
                # Display data info
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Records", len(stock_data))
                with col2:
                    st.metric("Current Price", f"₹{stock_data['Close'].iloc[-1]:.2f}")
                with col3:
                    st.metric("52W High", f"₹{stock_data['Close'].max():.2f}")
                
                # Show sample data
                st.write("**Sample Data (Last 5 days):**")
                st.dataframe(stock_data[['Open', 'High', 'Low', 'Close', 'Volume']].tail())
                
                test_results['DataFetch'] = 'pass'
        else:
            st.error(f"❌ Symbol {selected_symbol} validation failed")
            test_results['DataFetch'] = 'fail'
    
    except Exception as e:
        st.error(f"❌ Data Fetcher Error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        test_results['DataFetch'] = 'fail'

st.markdown("---")

# 3. Test LSTM Predictor
st.header("3️⃣ Testing LSTM Predictor")

if st.button("Test LSTM Model Prediction for " + selected_symbol):
    try:
        from StockSageAI.data_fetcher import DataFetcher
        from StockSageAI.lstm_model import LSTMPredictor
        
        st.info(f"Fetching data for {selected_symbol}...")
        df = DataFetcher()
        stock_data = df.get_stock_data(selected_symbol, period="1y")
        
        if stock_data.empty:
            st.error(f"Could not fetch data for {selected_symbol}")
        else:
            st.success("✅ Data fetched successfully")
            
            st.info("Training LSTM model...")
            predictor = LSTMPredictor()
            
            # Test 7, 14, 30 day predictions
            predictions_dict = {}
            for days in [7, 14, 30]:
                try:
                    preds = predictor.predict(stock_data, forecast_days=days)
                    if preds is not None and len(preds) > 0:
                        predictions_dict[days] = preds
                        st.success(f"✅ {days}-day forecast: {len(preds)} predictions generated")
                except Exception as e:
                    st.error(f"❌ {days}-day forecast failed: {str(e)}")
            
            if predictions_dict:
                # Display predictions
                current_price = stock_data['Close'].iloc[-1]
                
                pred_cols = st.columns(3)
                for idx, (days, preds) in enumerate(predictions_dict.items()):
                    with pred_cols[idx]:
                        final_price = preds[-1]
                        change_pct = ((final_price - current_price) / current_price) * 100
                        st.metric(
                            f"{days}-Day Target",
                            f"₹{final_price:.2f}",
                            f"{change_pct:+.2f}%"
                        )
                
                test_results['LSTM'] = 'pass'
            else:
                test_results['LSTM'] = 'fail'
    
    except Exception as e:
        st.error(f"❌ LSTM Predictor Error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        test_results['LSTM'] = 'fail'

st.markdown("---")

# 4. Test Sentiment Analyzer
st.header("4️⃣ Testing Sentiment Analyzer")

if st.button("Test Sentiment Analysis for " + selected_symbol):
    try:
        from StockSageAI.news_scraper import NewsScraper
        from StockSageAI.sentiment_analyzer import SentimentAnalyzer
        
        st.info(f"Fetching news for {selected_symbol}...")
        scraper = NewsScraper()
        news = scraper.get_news(selected_symbol, days_back=7, max_headlines=10)
        
        if news and len(news) > 0:
            st.success(f"✅ Fetched {len(news)} news headlines")
            
            st.info("Analyzing sentiment...")
            analyzer = SentimentAnalyzer()
            sentiments = analyzer.analyze_sentiment(news)
            
            if sentiments and len(sentiments) > 0:
                st.success(f"✅ Analyzed sentiment for {len(sentiments)} articles")
                
                overall = analyzer.get_overall_sentiment(sentiments)
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Overall Sentiment", overall['sentiment_label'])
                with col2:
                    st.metric("Compound Score", f"{overall['overall_compound']:.2f}")
                with col3:
                    st.metric("Confidence", f"{overall.get('confidence', 0):.1%}")
                
                test_results['Sentiment'] = 'pass'
            else:
                st.warning("⚠️ No sentiment data generated")
                test_results['Sentiment'] = 'fail'
        else:
            st.warning("⚠️ No news headlines found")
            test_results['Sentiment'] = 'fail'
    
    except Exception as e:
        st.error(f"❌ Sentiment Analyzer Error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        test_results['Sentiment'] = 'fail'

st.markdown("---")

# 5. Test Recommendation Engine
st.header("5️⃣ Testing Recommendation Engine")

if st.button("Test Recommendation Generation for " + selected_symbol):
    try:
        from StockSageAI.data_fetcher import DataFetcher
        from StockSageAI.lstm_model import LSTMPredictor
        from StockSageAI.recommendation_engine import RecommendationEngine
        
        st.info(f"Preparing data for {selected_symbol}...")
        df = DataFetcher()
        stock_data = df.get_stock_data(selected_symbol, period="1y")
        
        if stock_data.empty:
            st.error(f"Could not fetch data for {selected_symbol}")
        else:
            st.success("✅ Data fetched")
            
            st.info("Generating predictions...")
            predictor = LSTMPredictor()
            predictions = predictor.predict(stock_data, forecast_days=14)
            
            if predictions is not None and len(predictions) > 0:
                st.success("✅ Predictions generated")
                
                st.info("Generating recommendation...")
                engine = RecommendationEngine()
                rec = engine.generate_recommendation(stock_data, predictions, [], 14)
                
                st.success("✅ Recommendation generated")
                
                # Display recommendation
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Action", rec['action'])
                with col2:
                    st.metric("Confidence", f"{rec['confidence']:.0f}%")
                with col3:
                    st.metric("Reason", "See below")
                
                st.write(f"**Reasoning:** {rec['reasoning']}")
                
                test_results['Recommendation'] = 'pass'
            else:
                st.error("Could not generate predictions")
                test_results['Recommendation'] = 'fail'
    
    except Exception as e:
        st.error(f"❌ Recommendation Engine Error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        test_results['Recommendation'] = 'fail'

st.markdown("---")

# 6. Summary Report
st.header("📊 Diagnostic Summary")

summary_col1, summary_col2 = st.columns(2)

with summary_col1:
    st.subheader("Test Results")
    for test_name, result in test_results.items():
        if result == 'pass':
            st.success(f"✅ {test_name}")
        else:
            st.error(f"❌ {test_name}")

with summary_col2:
    st.subheader("Statistics")
    passed = sum(1 for r in test_results.values() if r == 'pass')
    total = len(test_results)
    st.metric("Tests Passed", f"{passed}/{total}")
    st.metric("Success Rate", f"{(passed/total * 100) if total > 0 else 0:.0f}%")

st.markdown("---")

st.info("💡 **Tip:** If any tests are failing, try:")
st.write("""
1. Check internet connection
2. Verify stock symbol is correct (use .NS for Indian stocks)
3. Clear Streamlit cache: `streamlit run app.py --logger.level=debug`
4. Try with: TCS.NS, RELIANCE.NS, or INFY.NS
5. Check if yfinance can fetch data: `python -c "import yfinance as yf; print(yf.Ticker('RELIANCE.NS').history(period='1d'))"`
""")
