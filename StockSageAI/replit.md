# SP 07 🚀 AI-Powered Stock Forecasting Application

## Overview

This is a comprehensive AI-powered stock forecasting application called "SP 07 🚀 AI-Powered Stock Forecasting" built with Streamlit that predicts Indian stock prices using machine learning and sentiment analysis. The application combines technical analysis with news sentiment to provide buy/sell/hold recommendations for both NSE and BSE-listed stocks.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes (January 31, 2025)

✓ Fixed critical symbol validation issues for both NSE and BSE stocks
✓ Implemented universal stock symbol lookup system  
✓ Replaced TensorFlow with scikit-learn ensemble models (Random Forest + Linear Regression)
✓ Fixed data fetching errors and self parameter issues
✓ Added automatic NSE/BSE format detection and validation
✓ Improved error handling and user feedback messages
✓ Fixed Streamlit caching issue with underscore prefix for 'self' parameter
✓ Updated app name to "SP 07 🚀 AI-Powered Stock Forecasting"
✓ App is now fully functional and tested successfully
✓ Implemented realistic prediction constraints with volatility-based limits
✓ Added confidence decay and mean reversion for longer-term forecasts
✓ Limited daily price changes to maximum 4% and total predictions within 50%-200% bounds
✓ Tested successfully: INFY predictions now show realistic +3.41% (7-day) vs previous 127%
✓ Enhanced UI with animated gradient background and floating particles
✓ Added professional glassmorphism design with backdrop blur effects
✓ Implemented pulsing recommendation cards with color-coded styling
✓ Added hover animations and smooth transitions throughout interface
✓ Created beautiful metric cards with enhanced visual hierarchy
✓ Added comprehensive credits section showcasing technology stack

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web application
- **Layout**: Wide layout with sidebar navigation
- **Visualization**: Plotly for interactive charts and graphs
- **Caching**: Streamlit's built-in caching for data persistence

### Backend Architecture
- **Modular Design**: Separated into specialized classes for different functionalities
- **Data Processing**: Pandas and NumPy for data manipulation
- **Machine Learning**: TensorFlow/Keras LSTM models for price prediction
- **External APIs**: Yahoo Finance (yfinance) for stock data, optional NewsAPI for news

### Key Components

1. **DataFetcher** (`data_fetcher.py`)
   - Fetches historical stock data from Yahoo Finance
   - Calculates technical indicators (Moving Averages, RSI, Volatility)
   - Implements caching to reduce API calls

2. **LSTMPredictor** (`lstm_model.py`)
   - Deep learning model using LSTM neural networks
   - Handles data preprocessing and normalization
   - Configurable sequence length, epochs, and batch size

3. **SentimentAnalyzer** (`sentiment_analyzer.py`)
   - Uses VADER sentiment analysis with financial domain enhancements
   - Processes news headlines for sentiment scoring
   - Custom financial vocabulary for improved accuracy

4. **NewsScraper** (`news_scraper.py`)
   - Scrapes financial news from multiple sources (MoneyControl, Economic Times, etc.)
   - Falls back to web scraping if NewsAPI unavailable
   - Implements rate limiting and caching

5. **RecommendationEngine** (`recommendation_engine.py`)
   - Combines price predictions with sentiment analysis
   - Generates BUY/SELL/HOLD recommendations
   - Configurable thresholds for different recommendation levels

6. **Utilities** (`utils.py`)
   - Helper functions for currency formatting
   - NSE symbol conversion and validation
   - Company name to stock symbol mapping

## Data Flow

1. **User Input**: User enters company symbol/name and forecast duration
2. **Data Acquisition**: 
   - Fetch historical stock data via Yahoo Finance
   - Scrape recent news headlines for the company
3. **Data Processing**:
   - Clean and normalize stock price data
   - Calculate technical indicators
   - Analyze news sentiment
4. **Prediction**:
   - Train LSTM model on historical data
   - Generate price forecasts
5. **Recommendation**:
   - Combine price predictions with sentiment scores
   - Generate final buy/sell recommendations
6. **Visualization**: Display results with interactive charts

## External Dependencies

### Core Libraries
- **streamlit**: Web application framework
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computing
- **plotly**: Interactive visualizations
- **yfinance**: Yahoo Finance API wrapper

### Machine Learning
- **tensorflow/keras**: Deep learning framework for LSTM models
- **scikit-learn**: Data preprocessing and metrics

### Sentiment Analysis
- **vaderSentiment**: Rule-based sentiment analysis
- **beautifulsoup4**: HTML parsing for web scraping
- **trafilatura**: Text extraction from web pages

### Web Scraping
- **requests**: HTTP library for API calls and web scraping

## Deployment Strategy

### Local Development
- Standard Python virtual environment
- Dependencies managed via requirements.txt
- Streamlit development server for testing

### Production Considerations
- **Caching Strategy**: Implemented at multiple levels (data fetching, model predictions)
- **Error Handling**: Comprehensive try-catch blocks for external API failures
- **Rate Limiting**: Built-in delays for web scraping to avoid blocking
- **Fallback Mechanisms**: Multiple news sources and graceful degradation

### Configuration
- Configurable model parameters (sequence length, epochs, batch size)
- Adjustable recommendation thresholds
- Flexible news source selection
- Optional NewsAPI integration with fallback to web scraping

### Performance Optimizations
- Data caching with TTL (Time To Live) expiration
- Batch processing for news sentiment analysis
- Efficient data structures for time series processing
- Modular architecture allowing for easy scaling

The application follows a clean architecture pattern with separation of concerns, making it maintainable and extensible for additional features like more sophisticated models, additional data sources, or enhanced visualization capabilities.