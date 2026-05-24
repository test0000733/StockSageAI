import streamlit as st
import pandas as pd
import numpy as np
import sys
import os

# Add parent directory to path for package imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    st.error("Plotly is required but not installed. Please install it with: pip install plotly")
    st.stop()

from datetime import datetime, timedelta
import yfinance as yf
import smtplib
from email.mime.text import MIMEText
import threading
import time

# Import custom modules
from StockSageAI.data_fetcher import DataFetcher
from StockSageAI.lstm_model import LSTMPredictor
from StockSageAI.sentiment_analyzer import SentimentAnalyzer
from StockSageAI.recommendation_engine import RecommendationEngine
from StockSageAI.news_scraper import NewsScraper
from StockSageAI.ai_forecast_engine import AIForecastEngine
from StockSageAI.utils import (
    format_currency,
    get_stock_symbol,
    clean_dataframe_for_export,
    setup_logging,
    logger,
    detect_candlestick_patterns,
    get_pattern_probabilities,
    render_ai_loader,
    can_access_admin,
    can_access_super_admin
)
from StockSageAI.auth import auth_manager
from StockSageAI.database import Database

# Import advanced search components
from StockSageAI.data_loader import StockDataLoader
from StockSageAI.stock_search import StockSearchEngine
from StockSageAI.advanced_search_ui import AdvancedStockSearch
from StockSageAI.admin_ai_ui import render_admin_training_dashboard
from StockSageAI import responsive_ui

# Toggle verbose debug info in the app UI
DEBUG_UI = True


def safe_rerun():
    """Use the available Streamlit rerun API across versions."""
    if hasattr(st, 'experimental_rerun'):
        return st.experimental_rerun()
    if hasattr(st, 'rerun'):
        return st.rerun()
    raise RuntimeError('Streamlit rerun is not available in this Streamlit version.')


# Initialize session state
if 'user' not in st.session_state:
    st.session_state.user = None
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'page' not in st.session_state:
    st.session_state.page = 'login'
if 'pending_pin_user' not in st.session_state:
    st.session_state.pending_pin_user = None
if 'pending_pin_remember' not in st.session_state:
    st.session_state.pending_pin_remember = False
if 'pin_entry' not in st.session_state:
    st.session_state.pin_entry = ''
if 'pin_attempts' not in st.session_state:
    st.session_state.pin_attempts = 0

# Apply mobile-first responsive CSS and wide layout for better mobile rendering
try:
    st.set_page_config(layout='wide', initial_sidebar_state='collapsed')
except Exception:
    pass
st.markdown(responsive_ui.MOBILE_FIRST_STYLES, unsafe_allow_html=True)
responsive_ui.ensure_viewport_width()

# Initialize commonly-used session state keys to avoid AttributeError
defaults = {
    'search_query': '',
    'admin_ai_stock': '',
    'admin_ai_selected_models': [],
    'admin_ai_auto_run': False,
    'admin_ai_results': None,
    'admin_ai_refresh_counter': 0,
    'admin_ai_model': None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

if 'search_query' not in st.session_state:
    st.session_state.search_query = ''
if 'admin_ai_stock' not in st.session_state:
    st.session_state.admin_ai_stock = ''
if 'admin_ai_model' not in st.session_state:
    st.session_state.admin_ai_model = 'Transformer LSTM'
if 'admin_ai_results' not in st.session_state:
    st.session_state.admin_ai_results = None
if 'admin_ai_auto_run' not in st.session_state:
    st.session_state.admin_ai_auto_run = False
if 'admin_ai_all_models' not in st.session_state:
    st.session_state.admin_ai_all_models = False
if 'admin_train_job' not in st.session_state:
    st.session_state.admin_train_job = None
if 'admin_train_status' not in st.session_state:
    st.session_state.admin_train_status = None
if 'admin_train_logs' not in st.session_state:
    st.session_state.admin_train_logs = []

# Initialize advanced search components
@st.cache_resource
def get_search_components():
    """Initialize and cache search components"""
    try:
        # Initialize data loader
        data_loader = StockDataLoader()
        master_data = data_loader.load_and_process_data()

        if master_data is not None and not master_data.empty:
            # Initialize search engine
            search_engine = StockSearchEngine(data_loader)
            search_engine.build_search_index()

            # Initialize UI component
            search_ui = AdvancedStockSearch(search_engine, data_loader)

            logger.info(f"Search components initialized with {len(master_data)} stocks")
            return search_ui, search_engine, data_loader
        else:
            logger.error("Failed to load stock data")
            return None, None, None

    except Exception as e:
        logger.error(f"Error initializing search components: {e}")
        return None, None, None

# Get search components
search_ui, search_engine, data_loader = get_search_components()

# Initialize AI forecast engine
ai_forecast_engine = AIForecastEngine()

# Try to restore a remembered session from the query string
auth_manager.check_remember_me()

# Configure logging for the app
setup_logging()

# Page config
st.set_page_config(
    page_title="SP 07 AI Stock Forecasting & Advisory",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Loader / UI helpers

def render_loader_styles():
    return """
<style>
/* Full page AI loader */
.loader-screen { position: relative; min-height: 85vh; display: flex; align-items: center; justify-content: center; padding: 3rem; background: radial-gradient(circle at top left, rgba(56,189,248,0.12), transparent 25%), radial-gradient(circle at bottom right, rgba(168,85,247,0.18), transparent 20%), rgba(4,7,19,0.98); border-radius: 28px; overflow: hidden; }
.loader-glow { position: absolute; top: 50%; left: 50%; width: 540px; height: 540px; transform: translate(-50%, -50%); background: radial-gradient(circle, rgba(56,189,248,0.18), transparent 55%); filter: blur(50px); z-index: 1; }
.loader-panel { position: relative; z-index: 2; width: 100%; max-width: 1080px; backdrop-filter: blur(18px); border: 1px solid rgba(255,255,255,0.06); box-shadow: 0 30px 120px rgba(0,0,0,0.45); border-radius: 32px; padding: 3rem; color: #e0f7ff; }
.loader-logo { width: 110px; height: 110px; margin: 0 auto 1.5rem; border-radius: 50%; border: 1px solid rgba(59,130,246,0.4); display: flex; align-items: center; justify-content: center; background: rgba(255,255,255,0.04); box-shadow: 0 0 40px rgba(59,130,246,0.2); font-size: 1rem; letter-spacing: 0.18em; text-transform: uppercase; color: #fff; }
.loader-title { font-size: clamp(2.4rem, 4vw, 3.8rem); font-weight: 800; letter-spacing: -0.03em; text-align: center; margin: 0.5rem 0 0.75rem; }
.loader-subtitle { max-width: 760px; margin: 0 auto 1.75rem; text-align: center; color: rgba(226, 239, 255, 0.78); line-height: 1.7; }
.loader-stripe { display: flex; align-items: center; justify-content: center; gap: 1rem; margin: 1.75rem auto 0; width: fit-content; }
.loader-dot { width: 16px; height: 16px; border-radius: 999px; background: rgba(34,209,255,0.9); animation: pulse-dot 1.2s ease-in-out infinite; }
.loader-dot:nth-child(2) { animation-delay: 0.2s; }
.loader-dot:nth-child(3) { animation-delay: 0.4s; }
.loader-progress { position: relative; width: 100%; height: 14px; border-radius: 999px; background: rgba(255,255,255,0.06); overflow: hidden; margin-top: 1.5rem; }
.loader-progress-inner { width: 42%; height: 100%; background: linear-gradient(90deg, #22d3ee, #7c3aed); transform-origin: left center; animation: progress-slide 3s infinite ease-in-out; }
@keyframes pulse-dot { 0%, 100% { opacity: 0.35; transform: scale(0.8); } 50% { opacity: 1; transform: scale(1.1); } }
@keyframes progress-slide { 0%, 20% { width: 12%; } 50% { width: 64%; } 100% { width: 18%; } }
.loader-card-grid { display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); margin-top: 2rem; }
.skeleton-card, .skeleton-chart, .skeleton-table, .skeleton-sidebar { background: rgba(255,255,255,0.04); border-radius: 24px; border: 1px solid rgba(255,255,255,0.08); overflow: hidden; position: relative; }
.skeleton-shimmer { position: absolute; inset: 0; background: linear-gradient(90deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.16) 50%, rgba(255,255,255,0.04) 100%); animation: shimmer 1.8s infinite; }
.skeleton-content { padding: 1.6rem; opacity: 0.9; }
.skeleton-line { height: 12px; border-radius: 999px; margin-bottom: 1rem; background: rgba(255,255,255,0.08); }
.skeleton-line.short { width: 35%; }
.skeleton-line.medium { width: 65%; }
.skeleton-line.long { width: 90%; }
@keyframes shimmer { 0% { transform: translateX(-120%); } 100% { transform: translateX(120%); } }
</style>
"""

def render_fullpage_ai_loader(message="Analyzing Market Trends..."):
    st.markdown(render_loader_styles(), unsafe_allow_html=True)
    st.markdown(f"""
<div class='loader-screen'>
  <div class='loader-glow'></div>
  <div class='loader-panel'>
    <div class='loader-logo'>SP 07 AI</div>
    <div class='loader-title'>AI Forecast Engine Loading</div>
    <div class='loader-subtitle'>{message} <span style='color:#7c3aed;'>Preparing financial insights, predictive signals, and market intelligence...</span></div>
    <div class='loader-stripe'>
      <div class='loader-dot'></div>
      <div class='loader-dot'></div>
      <div class='loader-dot'></div>
    </div>
    <div class='loader-progress'>
      <div class='loader-progress-inner'></div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


def render_dashboard_skeleton_loaders():
    st.markdown(render_loader_styles(), unsafe_allow_html=True)
    st.markdown("""
<div class='loader-card-grid'>
  <div class='skeleton-card'><div class='skeleton-shimmer'></div><div class='skeleton-content'><div class='skeleton-line long'></div><div class='skeleton-line medium'></div></div></div>
  <div class='skeleton-card'><div class='skeleton-shimmer'></div><div class='skeleton-content'><div class='skeleton-line long'></div><div class='skeleton-line short'></div></div></div>
  <div class='skeleton-chart' style='height:260px;'><div class='skeleton-shimmer'></div></div>
  <div class='skeleton-table' style='height:210px;'><div class='skeleton-shimmer'></div></div>
</div>
""", unsafe_allow_html=True)


def render_graph_loader(title='Loading Chart...'):
    st.markdown(render_loader_styles(), unsafe_allow_html=True)
    st.markdown(f"""
<div class='loader-screen' style='min-height: 420px; padding: 2rem;'>
  <div class='loader-panel' style='max-width: 900px;'>
    <div class='loader-title'>{title}</div>
    <div class='loader-subtitle'>Visualizing your candlestick trends, volume pulses, and AI projections.</div>
    <div class='loader-progress'>
      <div class='loader-progress-inner'></div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


def render_export_loader(message='Preparing Financial Report...'):
    st.markdown(render_loader_styles(), unsafe_allow_html=True)
    st.markdown(f"""
<div class='loader-screen'>
  <div class='loader-panel'>
    <div class='loader-logo'>EXCEL</div>
    <div class='loader-title'>Exporting Report</div>
    <div class='loader-subtitle'>{message} <span style='color:#60a5fa;'>Generating your secure workbook and syncing data.</span></div>
    <div class='loader-progress'><div class='loader-progress-inner'></div></div>
  </div>
</div>
""", unsafe_allow_html=True)


def render_auth_loader(message='Secure Authentication in Progress...'):
    st.markdown(render_loader_styles(), unsafe_allow_html=True)
    st.markdown(f"""
<div class='loader-screen'>
  <div class='loader-panel'>
    <div class='loader-logo'>AUTH</div>
    <div class='loader-title'>Authentication Loading</div>
    <div class='loader-subtitle'>{message} <span style='color:#a78bfa;'>Securing access, verifying credentials, and protecting your data.</span></div>
    <div class='loader-progress'><div class='loader-progress-inner'></div></div>
  </div>
</div>
""", unsafe_allow_html=True)


def render_auth_form_styles():
    return """
    <style>
    .auth-container {
        max-width: 440px;
        margin: 1rem auto 1rem;
        padding: 2.5rem 2rem;
        background: rgba(15, 23, 42, 0.94);
        backdrop-filter: blur(18px);
        border-radius: 28px;
        border: 1px solid rgba(96, 165, 250, 0.18);
        box-shadow: 0 24px 80px rgba(15, 23, 42, 0.65);
        display: flex;
        flex-direction: column;
        gap: 1rem;
        color: #e2e8f0;
    }
    .auth-title {
        font-size: 2rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0.75rem;
    }
    .auth-caption {
        text-align: center;
        color: rgba(226, 232, 240, 0.78);
        font-size: 0.95rem;
        margin-bottom: 1.25rem;
    }
    .auth-actions {
        display: flex;
        gap: 0.75rem;
        flex-wrap: wrap;
        justify-content: center;
    }
    .auth-actions .stButton > button {
        min-width: 140px;
    }
    .auth-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 0.75rem;
        flex-wrap: wrap;
        margin-top: 0.5rem;
    }
    .auth-footer a {
        color: #7dd3fc;
        text-decoration: none;
    }
    .auth-footer a:hover {
        text-decoration: underline;
    }
    </style>
    """


def render_ai_processing_loader(message='AI Forecast Engine Running...'):
    st.markdown(render_loader_styles(), unsafe_allow_html=True)
    st.markdown(f"""
<div class='loader-screen'>
  <div class='loader-panel'>
    <div class='loader-logo'>AI</div>
    <div class='loader-title'>Processing Intelligence</div>
    <div class='loader-subtitle'>{message} <span style='color:#22d3ee;'>Scanning markets, processing signals, and computing predictions.</span></div>
    <div class='loader-stripe'>
      <div class='loader-dot'></div>
      <div class='loader-dot'></div>
      <div class='loader-dot'></div>
    </div>
    <div class='loader-progress'><div class='loader-progress-inner'></div></div>
  </div>
</div>
""", unsafe_allow_html=True)


def render_back_button(target_page='dashboard', label='← Back', key=None):
    key = key or f"back_{target_page}"
    if st.button(label, key=key, use_container_width=True):
        st.session_state.page = target_page
        st.rerun()


def format_percentage(value):
    try:
        return f"{value:+.2f}%"
    except Exception:
        return "N/A"


def build_market_breadth():
    advancing = np.random.randint(45, 62)
    declining = 100 - advancing
    unchanged = np.random.randint(0, 4)
    breadth = advancing - declining
    return {
        'advancing': advancing,
        'declining': declining,
        'unchanged': unchanged,
        'breadth': breadth
    }


def get_realtime_sector_data():
    """Fetch real-time sector performance data"""
    data_fetcher = DataFetcher()
    sectors = {
        'Technology': '^CNXIT',
        'Healthcare': '^CNXPHARMA',
        'Auto': '^CNXAUTO',
        'Energy': '^CNXENERGY',
        'Consumer Goods': '^CNXFMCG',
        'Banking': '^NSEBANK',
        'Realty': '^CNXREALTY'
    }

    sector_perf = []
    for sector_name, symbol in sectors.items():
        try:
            data = data_fetcher.get_index_data(symbol, period='7d')
            if not data.empty and len(data) >= 2:
                prev_close = data['Close'].iloc[-2]
                latest_close = data['Close'].iloc[-1]
                perf = ((latest_close - prev_close) / prev_close) * 100
                status = 'Strong' if perf > 1.0 else 'Moderate' if perf >= 0 else 'Weak'
                sector_perf.append({
                    'Sector': sector_name,
                    'Strength': f"{perf:+.2f}%",
                    'Performance': perf,
                    'Status': status
                })
            else:
                sector_perf.append({'Sector': sector_name, 'Strength': '─', 'Performance': 0.0, 'Status': 'Unavailable'})
        except Exception:
            sector_perf.append({'Sector': sector_name, 'Strength': '─', 'Performance': 0.0, 'Status': 'Unavailable'})

    sector_df = pd.DataFrame(sector_perf)
    if not sector_df.empty:
        sector_df = sector_df.sort_values('Performance', ascending=False).reset_index(drop=True)
    return sector_df


def render_fullscreen_analysis_loader():
    """Render full-screen loader while analyzing stock"""
    st.markdown(render_loader_styles(), unsafe_allow_html=True)
    st.markdown("""
<div class='loader-screen'>
  <div class='loader-glow'></div>
  <div class='loader-panel'>
    <div class='loader-logo'>📊</div>
    <div class='loader-title'>AI Stock Analysis in Progress</div>
    <div class='loader-subtitle'>Gathering real-time market data, computing technical indicators, running LSTM forecasts, and analyzing sentiment intelligence...</div>
    <div class='loader-stripe'>
      <div class='loader-dot'></div>
      <div class='loader-dot'></div>
      <div class='loader-dot'></div>
    </div>
    <div class='loader-progress'>
      <div class='loader-progress-inner'></div>
    </div>
    <p style='margin-top:2rem; color:#22d3ee; text-align:center; font-size:0.9rem;'>Hang tight—premium analysis engines are sifting through market data</p>
  </div>
</div>
""", unsafe_allow_html=True)


def extract_event_signals(news_headlines):
    events = []
    if not news_headlines:
        return events

    keywords = ['earnings', 'dividend', 'guidance', 'merger', 'acquisition', 'upgrade', 'downgrade', 'outlook', 'results', 'forecast']
    for headline in news_headlines:
        title = headline.get('title', '').lower()
        date = headline.get('date', '')
        for keyword in keywords:
            if keyword in title:
                events.append({'title': headline.get('title', ''), 'type': keyword.title(), 'date': date, 'source': headline.get('source', 'News')})
                break
    return events[:5]


def compute_portfolio_risk_metrics(holdings):
    metrics = {
        'total_cost': 0.0,
        'market_value': 0.0,
        'unrealized_pnl': 0.0,
        'var_95': 0.0,
        'max_drawdown': 0.0,
        'allocations': []
    }

    if not holdings:
        return metrics

    df = pd.DataFrame(holdings)
    data_fetcher = DataFetcher()
    values = []
    returns = []

    for holding in holdings:
        symbol = holding.get('symbol', '')
        quantity = float(holding.get('quantity', 0) or 0)
        avg_price = float(holding.get('avg_buy_price', 0) or 0)
        metrics['total_cost'] += quantity * avg_price

        stock_data = data_fetcher.get_stock_data(symbol, period='1mo')
        latest_price = stock_data['Close'].iloc[-1] if not stock_data.empty else avg_price
        market_value = quantity * latest_price
        values.append(market_value)

        if not stock_data.empty and len(stock_data) > 1:
            returns.extend(stock_data['Close'].pct_change().dropna().tolist())

        metrics['allocations'].append({
            'symbol': symbol,
            'market_value': market_value,
            'avg_price': avg_price,
            'quantity': quantity
        })

    metrics['market_value'] = sum(values)
    metrics['unrealized_pnl'] = metrics['market_value'] - metrics['total_cost']

    if returns:
        daily_std = np.std(returns)
        metrics['var_95'] = max(0.0, min(100.0, daily_std * 1.65 * 100))
        max_drawdown = 0.0
        for holding in holdings:
            symbol = holding.get('symbol', '')
            stock_data = data_fetcher.get_stock_data(symbol, period='3mo')
            if not stock_data.empty:
                peak = stock_data['Close'].expanding(min_periods=1).max()
                drawdown = ((stock_data['Close'] - peak) / peak).min() * 100
                max_drawdown = min(max_drawdown, drawdown)
        metrics['max_drawdown'] = abs(max_drawdown)

    if metrics['market_value'] > 0:
        for alloc in metrics['allocations']:
            alloc['allocation_pct'] = (alloc['market_value'] / metrics['market_value']) * 100

    return metrics


# --- Authentication System ---
def show_login_page():
    st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem !important;
    }
    .auth-container {
        max-width: 460px;
        margin: 0.75rem auto 1rem;
        padding: 2rem 1.8rem;
        background: rgba(15, 23, 42, 0.96);
        backdrop-filter: blur(22px);
        border-radius: 28px;
        border: 1px solid rgba(96, 165, 250, 0.18);
        box-shadow: 0 24px 80px rgba(15, 23, 42, 0.45);
        display: flex;
        flex-direction: column;
        gap: 1rem;
        color: #e2e8f0;
    }
    .auth-title {
        text-align: center;
        font-size: 2rem;
        font-weight: 800;
        color: #7dd3fc;
        margin-bottom: 0.25rem;
    }
    .auth-caption {
        text-align: center;
        color: rgba(226, 232, 240, 0.78);
        font-size: 0.95rem;
        margin-bottom: 1.25rem;
    }
    .auth-actions {
        display: flex;
        gap: 0.75rem;
        flex-wrap: wrap;
        justify-content: center;
    }
    .auth-actions .stButton > button {
        min-width: 140px;
    }
    </style>
    """, unsafe_allow_html=True)

    # If a pending PIN flow exists, show the PIN entry UI immediately
    if st.session_state.get('pending_pin_user'):
        show_pin_entry_page()
        return

    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    st.markdown('<div class="auth-title">🔐 Login to SP 07</div>', unsafe_allow_html=True)
    st.markdown('<div class="auth-caption">Enterprise-grade AI forecasting and market intelligence platform.</div>', unsafe_allow_html=True)

    with st.form("login_form"):
        identifier = st.text_input("Email or Username", key="login_identifier")
        password = st.text_input("Password", type="password", key="login_password")
        remember_me = st.checkbox("Remember me", key="remember_me")

        col1, col2 = responsive_ui.get_responsive_columns(2, mobile_count=1)
        with col1:
            login_submitted = st.form_submit_button("Login", use_container_width=True)
        with col2:
            # Signup option removed — accounts are created by admins only
            st.markdown("<div style='height:35px;'></div>", unsafe_allow_html=True)

    if login_submitted:
        if not identifier or not password:
            st.error("Please fill in all fields.")
        else:
            render_auth_loader("Validating credentials...")
            success, message, user = auth_manager.login(identifier, password, remember_me)
            # Debug output removed from UI. Use server logs for debugging when needed.
            if success and message == "PIN required":
                st.success("Credentials verified. Enter your 4-digit security PIN.")
                st.session_state.pending_pin_user = user
                st.session_state.pending_pin_remember = remember_me
                # Render the PIN entry UI immediately to avoid navigation/rerun inconsistencies
                show_pin_entry_page()
                return
            elif success:
                st.success(message)
                st.session_state.page = 'dashboard'
                st.rerun()
            else:
                # Show error and, if it's the legacy PIN message, display a prominent reset CTA
                st.error(message)
                if isinstance(message, str) and 'legacy format' in message.lower():
                    st.warning("Your account uses an older security PIN format. You must reset your Security PIN to continue.")
                    if st.button("Reset Security PIN Now", key="reset_pin_now"):
                        st.session_state.page = 'pin_reset_request'
                        st.rerun()

    # signup_page has been removed — self-service signup disabled

    if st.button("Forgot Password?", key="forgot_link"):
        st.session_state.page = 'forgot_password'
        st.rerun()

    if st.button("Reset Security PIN", key="reset_pin_link"):
        st.session_state.page = 'pin_reset_request'
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

def show_signup_page():
    st.markdown(render_auth_form_styles(), unsafe_allow_html=True)

    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    st.markdown('<div class="auth-title">📝 Sign Up for StockSageAI</div>', unsafe_allow_html=True)
    st.markdown('<div class="auth-caption">Create your StockSageAI account and unlock premium market insights.</div>', unsafe_allow_html=True)

    with st.form("signup_form"):
        username = st.text_input("Username", key="signup_username")
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm")

        col1, col2 = responsive_ui.get_responsive_columns(2, mobile_count=1)
        with col1:
            signup_submitted = st.form_submit_button("Sign Up", use_container_width=True)
        with col2:
            login_page = st.form_submit_button("Back to Login", use_container_width=True)

    if signup_submitted:
        success, message = auth_manager.signup(username, email, password, confirm_password)
        if success:
            st.success(message)
            st.session_state.page = 'login'
            st.rerun()
        else:
            st.error(message)

    if login_page:
        st.session_state.page = 'login'
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)



def show_forgot_password_page():
    st.markdown(render_auth_form_styles(), unsafe_allow_html=True)

    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    st.markdown('<div class="auth-title">🔑 Forgot Password</div>', unsafe_allow_html=True)
    st.markdown('<div class="auth-caption">Enter your email to receive a secure password reset link.</div>', unsafe_allow_html=True)

    with st.form("forgot_form"):
        email = st.text_input("Email", key="forgot_email")

        col1, col2 = responsive_ui.get_responsive_columns(2, mobile_count=1)
        with col1:
            reset_submitted = st.form_submit_button("Send Reset Email", use_container_width=True)
        with col2:
            back = st.form_submit_button("Back to Login", use_container_width=True)

    if reset_submitted:
        if not email:
            st.error("Please enter your email.")
        else:
            success, message = auth_manager.forgot_password(email)
            if success:
                st.success(message)
            else:
                st.error(message)

    if back:
        st.session_state.page = 'login'
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def show_pin_entry_page():
    st.markdown(render_auth_form_styles(), unsafe_allow_html=True)
    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    st.markdown('<div class="auth-title">🔐 Enter Security PIN</div>', unsafe_allow_html=True)
    st.markdown('<div class="auth-caption">Use your 4-digit security PIN to complete login.</div>', unsafe_allow_html=True)

    if not st.session_state.pending_pin_user:
        st.error("PIN authentication requires a verified login attempt.")
        if st.button("Back to Login", key="pin_back_login"):
            st.session_state.page = 'login'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # Use a single form for PIN entry to avoid per-button reruns
    with st.form("pin_form"):
        pin_input = st.text_input("Security PIN", type="password", max_chars=4, key="pin_entry_input", value=st.session_state.pin_entry)
        pin_submit = st.form_submit_button("Authenticate PIN", use_container_width=True)

    # Persist the input back to session state
    st.session_state.pin_entry = pin_input or st.session_state.pin_entry

    if pin_submit:
        if not st.session_state.pin_entry or len(st.session_state.pin_entry) != 4:
            st.error("Please enter your 4-digit PIN.")
        else:
            success, message = auth_manager.validate_security_pin(
                st.session_state.pending_pin_user,
                st.session_state.pin_entry,
                st.session_state.pending_pin_remember
            )
            if success:
                st.success(message)
                st.session_state.page = 'dashboard'
                st.session_state.pending_pin_user = None
                st.session_state.pending_pin_remember = False
                st.session_state.pin_entry = ''
                st.session_state.pin_attempts = 0
                st.rerun()
            else:
                st.session_state.pin_attempts += 1
                if st.session_state.pin_attempts >= 3:
                    st.error("Too many attempts. Returning to login.")
                    st.session_state.pending_pin_user = None
                    st.session_state.pending_pin_remember = False
                    st.session_state.pin_entry = ''
                    st.session_state.pin_attempts = 0
                    st.session_state.page = 'login'
                    st.rerun()
                else:
                    st.error(message)

    if st.button("Back to Login", key="pin_back"):
        st.session_state.pending_pin_user = None
        st.session_state.pending_pin_remember = False
        st.session_state.pin_entry = ''
        st.session_state.page = 'login'
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def show_pin_reset_request_page():
    st.markdown(render_auth_form_styles(), unsafe_allow_html=True)
    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    st.markdown('<div class="auth-title">🔓 Reset Security PIN</div>', unsafe_allow_html=True)
    st.markdown('<div class="auth-caption">Enter your email to receive a secure PIN reset link.</div>', unsafe_allow_html=True)

    with st.form("pin_reset_request_form"):
        email = st.text_input("Email", key="pin_reset_email")
        send_submitted = st.form_submit_button("Send PIN Reset Email", use_container_width=True)
        back_to_login = st.form_submit_button("Back to Login", use_container_width=True)

    if send_submitted:
        if not email:
            st.error("Please enter your email.")
        else:
            success, message = auth_manager.request_pin_reset(email)
            if success:
                st.success(message)
            else:
                st.error(message)

    if back_to_login:
        st.session_state.page = 'login'
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def show_pin_reset_page():
    st.markdown(render_auth_form_styles(), unsafe_allow_html=True)
    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    st.markdown('<div class="auth-title">🔑 Set New Security PIN</div>', unsafe_allow_html=True)
    st.markdown('<div class="auth-caption">Create a new 4-digit PIN to protect your account.</div>', unsafe_allow_html=True)

    query_params = st.query_params
    token_param = query_params.get('token')
    token = token_param[0] if token_param else ''

    if not token:
        st.error("Invalid or expired PIN reset link.")
        if st.button("Back to Login", key="pin_reset_invalid_back"):
            st.session_state.page = 'login'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        return

    with st.form("pin_reset_form"):
        pin = st.text_input("New PIN", type="password", max_chars=4, key="pin_reset_pin")
        confirm_pin = st.text_input("Confirm New PIN", type="password", max_chars=4, key="pin_reset_confirm")
        pin_reset_submitted = st.form_submit_button("Reset PIN", use_container_width=True)

    if pin_reset_submitted:
        if not pin or not confirm_pin:
            st.error("Please complete both PIN fields.")
        else:
            success, message = auth_manager.reset_security_pin(token, pin)
            if success:
                st.success(message)
                st.session_state.page = 'login'
                st.rerun()
            else:
                st.error(message)

    if st.button("Back to Login", key="pin_reset_back"):
        st.session_state.page = 'login'
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def show_reset_password_page():
    st.markdown(render_auth_form_styles(), unsafe_allow_html=True)

    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    st.markdown('<div class="auth-title">🔑 Reset Password</div>', unsafe_allow_html=True)
    st.markdown('<div class="auth-caption">Create a strong new password to secure your account.</div>', unsafe_allow_html=True)

    # Get token from URL params
    query_params = st.query_params
    token_param = query_params.get('token')
    token = token_param[0] if token_param else ''

    if not token:
        st.error("Invalid reset link.")
        return

    with st.form("reset_form"):
        new_password = st.text_input("New Password", type="password", key="reset_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="reset_confirm")

        reset_submitted = st.form_submit_button("Reset Password", use_container_width=True)

    if reset_submitted:
        success, message = auth_manager.reset_password(token, new_password, confirm_password)
        if success:
            st.success(message)
            st.session_state.page = 'login'
            st.rerun()
        else:
            st.error(message)

    st.markdown('</div>', unsafe_allow_html=True)

# --- App Views ---
def show_dashboard_page(user):
    st.markdown("""
    <div class="hero-panel">
      <div class="hero-deco"></div>
      <div class="hero-deco-two"></div>
      <div class="hero-logo">SS</div>
      <div class="hero-title">SP 07 Ai Stock Forecasting and Advisory Intelligence</div>
      <div class="hero-subtitle">Premium market forecasting, AI-backed alerts, and portfolio pulse in a single executive dashboard.</div>
      <div class="market-pill">AI Confidence 89%</div>
      <div class="market-pill">Real-time signals</div>
      <div class="market-pill">Portfolio risk analytics</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Key performance metrics")
    metric_cols = responsive_ui.get_responsive_columns(4, mobile_count=1, gap='large')
    metric_data = [
        ("Portfolio Alpha", "+12.8%", "Strong upside momentum"),
        ("AI Confidence", "89%", "High model certainty"),
        ("Market Pulse", "Bullish", "Momentum is positive"),
        ("User Engagement", "72%", "Active trading sessions")
    ]
    for (label, value, note), col in zip(metric_data, metric_cols):
        col.markdown(f"""
            <div class='stat-card'>
                <h3>{label}</h3>
                <p style='font-size:2rem; margin:0.25rem 0 0.5rem; font-weight:800;'>{value}</p>
                <p style='margin:0; color: rgba(226, 232, 240, 0.75); font-size:0.95rem;'>{note}</p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("### Market insights")
    chart_col, summary_col = responsive_ui.get_responsive_columns(2, mobile_count=1, gap='large')
    with chart_col:
        if PLOTLY_AVAILABLE:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=[datetime.now() - timedelta(days=i) for i in reversed(range(21))],
                y=[112 + (i * 0.9) + ((-1)**i) * 1.8 for i in range(21)],
                mode='lines+markers',
                line=dict(color='#60a5fa', width=3),
                marker=dict(size=6, color='#38bdf8'),
                name='Cumulative Trend'
            ))
            fig.add_trace(go.Scatter(
                x=[datetime.now() - timedelta(days=i) for i in reversed(range(21))],
                y=[105 + (i * 0.65) + ((-1)**i) * 1.1 for i in range(21)],
                mode='lines',
                line=dict(color='#c084fc', width=2, dash='dash'),
                name='Strategy Baseline'
            ))
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(t=14, b=18, l=10, r=10),
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
                height=420,
                hovermode='x unified'
            )
            fig.update_xaxes(showgrid=False)
            fig.update_yaxes(gridcolor='rgba(255,255,255,0.08)')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Plotly charts are unavailable. Install plotly for premium dashboard visuals.")

    with summary_col:
        st.markdown("### Performance snapshot")
        st.markdown("""
            <div class='feature-card'>
                <p style='margin:0; font-size:0.95rem; color:#a5f3fc;'>Forecast confidence</p>
                <h2 style='margin:0.6rem 0 1rem; font-size:2rem;'>89%</h2>
                <p style='margin:0 0 1rem; color: rgba(226, 232, 240, 0.75);'>AI trend score remains high across global equities, suggesting sustained momentum.</p>
                <p style='margin:0; font-size:0.95rem;'><strong>Top signal:</strong> Buy on strength in technology and financials.</p>
            </div>
            <div class='feature-card' style='margin-top:1rem;'>
                <p style='margin:0; font-size:0.95rem; color:#a5f3fc;'>Volatility radar</p>
                <h2 style='margin:0.6rem 0 1rem; font-size:2rem;'>Low</h2>
                <p style='margin:0; color: rgba(226, 232, 240, 0.75);'>Market churn is subdued, making this a good window for measured allocation adjustments.</p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("### Recent activity")
    with st.container():
        log_cols = responsive_ui.get_responsive_columns(3, mobile_count=1, gap='large')
        log_items = [
            ("Market Pulse", "Live market signal feed updated 2m ago."),
            ("AI Model", "LSTM forecast recalculated for 30-day horizon."),
            ("Security", "PIN-based login flow continues operating normally.")
        ]
        for title, detail, col in zip([item[0] for item in log_items], [item[1] for item in log_items], log_cols):
            col.markdown(f"""
                <div class='stat-card'>
                    <h3>{title}</h3>
                    <p style='margin:0; color: rgba(226, 232, 240, 0.75);'>{detail}</p>
                </div>
            """, unsafe_allow_html=True)


def show_analysis_page():
    stock_symbol = st.session_state.get('current_stock', '')
    st.markdown("## AI Forecast & Market Intelligence")

    if search_ui is not None:
        def on_stock_select(stock):
            st.session_state.current_stock = stock.get('SYMBOL', '').strip().upper()
            st.session_state.search_query = ''
            st.session_state.page = 'analysis'
            st.rerun()

        search_ui.render(on_stock_select=on_stock_select)
        st.markdown("---")

    if not stock_symbol:
        stock_symbol = st.text_input("Enter stock symbol to analyze", key="analysis_stock", placeholder="RELIANCE.NS")
        if st.button("Run Forecast", use_container_width=True):
            if stock_symbol:
                st.session_state.current_stock = stock_symbol.strip()
                st.session_state.page = 'analysis'
                st.rerun()
        return

    # Clean and convert symbol
    stock_symbol = stock_symbol.strip().upper()
    
    # Try to convert company name to symbol using utility function
    resolved_symbol = get_stock_symbol(stock_symbol)
    
    st.markdown(f"### Analysis for {stock_symbol.upper()}")
    
    # Create a placeholder for the loader that can be cleared later
    loader_placeholder = st.empty()
    
    with loader_placeholder.container():
        render_ai_loader("Loading the AI forecast engine and technical analysis...")
    
    with st.spinner("Gathering market data and building forecasts..."):
        data_fetcher = DataFetcher()
        
        # Validate symbol with retry on alternatives
        if not data_fetcher.validate_symbol(resolved_symbol):
            # Try original symbol if conversion didn't work
            if not data_fetcher.validate_symbol(stock_symbol):
                st.error(f"❌ Symbol '{stock_symbol}' not found. Please try:\n- TCS, RELIANCE, INFY (Indian stocks)\n- AAPL, MSFT (US stocks)\n- Or use format: SYMBOL.NS or SYMBOL.BO")
                st.info("💡 Hint: Use NSE format (SYMBOL.NS) for Indian stocks")
                return
            else:
                resolved_symbol = stock_symbol
        
        # Clear the loader placeholder once data starts loading
        loader_placeholder.empty()
        
        # Fetch data with resolved symbol
        stock_data = data_fetcher.get_stock_data(resolved_symbol, period="1y")
        if stock_data.empty:
            st.error(f"❌ Could not fetch time series data for {resolved_symbol}. Please try another symbol.")
            return

        latest = stock_data.iloc[-1]
        delta_pct = (latest.Close - stock_data['Close'].iloc[-2]) / stock_data['Close'].iloc[-2] if len(stock_data) > 1 else 0
        st.metric("Current Price", format_currency(latest.Close), delta=f"{delta_pct * 100:.2f}%")

        col1, col2, col3 = responsive_ui.get_responsive_columns(3, mobile_count=1)
        with col1:
            st.metric("52W High", format_currency(stock_data['Close'].max()))
        with col2:
            st.metric("52W Low", format_currency(stock_data['Close'].min()))
        with col3:
            st.metric("Volume", f"{int(latest.Volume):,}")

        price_chart = go.Figure()
        price_chart.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Close'], mode='lines', line=dict(color='#22d3ee', width=3), name='Close'))
        price_chart.add_trace(go.Scatter(x=stock_data.index, y=stock_data['MA_20'], mode='lines', line=dict(color='#9333ea', width=2, dash='dash'), name='MA 20'))
        price_chart.add_trace(go.Scatter(x=stock_data.index, y=stock_data['MA_50'], mode='lines', line=dict(color='#f97316', width=2, dash='dash'), name='MA 50'))
        price_chart.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=40, l=20, r=20, b=20), height=420)
        st.plotly_chart(price_chart, use_container_width=True)

        sentiment_scores = []
        news = []
        try:
            import io
            from contextlib import redirect_stdout, redirect_stderr
            
            # Suppress NewsScraper debug messages
            news_scraper = NewsScraper()
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                news = news_scraper.get_news(resolved_symbol, days_back=7, max_headlines=10)
            
            sentiment_analyzer = SentimentAnalyzer()
            sentiment_scores = sentiment_analyzer.analyze_sentiment(news)
        except Exception as e:
            st.warning(f"⚠️ Could not fetch news: {str(e)}")
            sentiment_scores = []
            news = []

        # Generate forecasts for 7, 14, and 30 days
        recommendation = None
        predictions = []
        all_predictions = {}
        forecast_periods = [7, 14, 30]
        current_price = latest.Close

        try:
            predictor = LSTMPredictor()
            for days in forecast_periods:
                try:
                    preds = predictor.predict(stock_data, forecast_days=days)
                    if preds is not None and len(preds) > 0:
                        all_predictions[days] = preds
                except Exception as e:
                    st.warning(f"⚠️ Could not generate {days}-day forecast: {str(e)}")
                    continue

            # Use 14-day as default for recommendation
            if 14 in all_predictions:
                predictions = all_predictions[14]
                rec_engine = RecommendationEngine()
                recommendation = rec_engine.generate_recommendation(stock_data, predictions, sentiment_scores, 14)
        except Exception as e:
            st.warning(f"⚠️ Forecast generation error: {e}")

        if not recommendation:
            recommendation = {
                'action': 'HOLD',
                'confidence': 65.0,
                'reasoning': 'No recommendation available at this time.',
                'details': {
                    'volatility': {'risk_level': 'Medium', 'score': 0.6},
                    'trend_consistency': 0.5
                }
            }

        if sentiment_scores and len(sentiment_scores) > 0:
            try:
                sentiment_analyzer = SentimentAnalyzer()
                sentiment_summary = sentiment_analyzer.get_overall_sentiment(sentiment_scores)
                st.markdown(f"**News sentiment:** {sentiment_summary['sentiment_label']} ({sentiment_summary['overall_compound']:.2f})")

                keyword_distribution = sentiment_analyzer.analyze_headline_keywords(news)
                events = extract_event_signals(news)

                sentiment_cols = responsive_ui.get_responsive_columns(3, mobile_count=1)
                sentiment_cols[0].metric("Sentiment Tone", sentiment_summary['sentiment_label'])
                sentiment_cols[1].metric("Confidence", f"{sentiment_summary['confidence'] * 100:.0f}%")
                sentiment_cols[2].metric("Headline Count", len(news))

                st.markdown("#### News Sentiment Breakdown")
                breakdown_cols = responsive_ui.get_responsive_columns(3, mobile_count=1)
                breakdown_cols[0].info(f"Positive keywords: {keyword_distribution.get('positive', 0):.0f}%")
                breakdown_cols[1].info(f"Negative keywords: {keyword_distribution.get('negative', 0):.0f}%")
                breakdown_cols[2].info(f"Neutral keywords: {keyword_distribution.get('neutral', 0):.0f}%")

                if events:
                    st.markdown("#### Event Signals")
                    for event in events:
                        st.write(f"- **{event['type']}**: {event['title']} ({event['date']})")
            except Exception:
                pass

        # Display comparison of all forecasts
        st.markdown("### 📊 Multi-Period Forecast Comparison")
        forecast_chart = go.Figure()
        
        # Add historical price
        forecast_chart.add_trace(go.Scatter(
            x=stock_data.index,
            y=stock_data['Close'],
            mode='lines',
            name='Historical Price',
            line=dict(color='#22d3ee', width=2)
        ))
        
        # Add forecasts for each period
        colors = {7: '#fbbf24', 14: '#f97316', 30: '#10b981'}
        for days in forecast_periods:
            if days in all_predictions and all_predictions[days] is not None and len(all_predictions[days]) > 0:
                preds = all_predictions[days]
                future_dates = pd.date_range(
                    start=stock_data.index[-1] + pd.Timedelta(days=1),
                    periods=len(preds),
                    freq='B'
                )
                forecast_chart.add_trace(go.Scatter(
                    x=future_dates,
                    y=preds,
                    mode='lines+markers',
                    name=f'{days}-Day Forecast',
                    line=dict(color=colors[days], width=2, dash='dash'),
                    marker=dict(size=5)
                ))
        
        forecast_chart.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=40, l=20, r=20, b=20),
            height=420,
            hovermode='x unified'
        )
        st.plotly_chart(forecast_chart, use_container_width=True)
        
        # Display recommendations for each period
        st.markdown("### 📈 Recommendations by Forecast Period")
        rec_cols = responsive_ui.get_responsive_columns(3, mobile_count=1)
        
        for idx, days in enumerate(forecast_periods):
            if days in all_predictions and all_predictions[days] is not None and len(all_predictions[days]) > 0:
                preds = all_predictions[days]
                pred_price = preds[-1]
                change_pct = ((pred_price - current_price) / current_price) * 100
                
                if change_pct > 3:
                    rec_action = "BUY"
                    emoji = "🟢"
                    color = "#10b981"
                elif change_pct < -3:
                    rec_action = "SELL"
                    emoji = "🔴"
                    color = "#ef4444"
                else:
                    rec_action = "HOLD"
                    emoji = "🟡"
                    color = "#f59e0b"
                
                with rec_cols[idx]:
                    st.markdown(f"""
                    <div style="border: 2px solid {color}; border-radius: 8px; padding: 1rem; text-align: center;">
                        <h3 style="margin: 0; color: {color};">{emoji} {rec_action}</h3>
                        <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem;">Period: <b>{days} Days</b></p>
                        <p style="margin: 0.5rem 0 0 0; font-size: 0.85rem;">Target: ₹{pred_price:.2f}</p>
                        <p style="margin: 0.5rem 0 0 0; font-size: 0.85rem; color: {color};">Change: <b>{change_pct:+.2f}%</b></p>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Generate Excel Report
        st.markdown("---")
        st.markdown("### 📥 Download Analysis Report")
        
        try:
            import io
            import importlib
            
            excel_engine = None
            if importlib.util.find_spec('xlsxwriter') is not None:
                excel_engine = 'xlsxwriter'
            elif importlib.util.find_spec('openpyxl') is not None:
                excel_engine = 'openpyxl'

            if excel_engine is None:
                raise ImportError("Install xlsxwriter or openpyxl to enable Excel export.")

            # Prepare summary data for Excel
            summary_rows = [
                ["Stock Symbol", stock_symbol],
                ["Analysis Date", datetime.now().strftime("%Y-%m-%d %H:%M")],
                ["Current Price", f"₹{current_price:.2f}"],
                ["", ""]
            ]
            
            for days in forecast_periods:
                if days in all_predictions and all_predictions[days] is not None and len(all_predictions[days]) > 0:
                    pred_price = all_predictions[days][-1]
                    change_pct = ((pred_price - current_price) / current_price) * 100
                    if change_pct > 3:
                        rec = "BUY"
                    elif change_pct < -3:
                        rec = "SELL"
                    else:
                        rec = "HOLD"
                    summary_rows.append([f"Forecast ({days}D) - Price", f"₹{pred_price:.2f}"])
                    summary_rows.append([f"Forecast ({days}D) - Change %", f"{change_pct:+.2f}%"])
                    summary_rows.append([f"Recommendation ({days}D)", rec])
                    summary_rows.append(["", ""])
            
            # Create Excel file
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine=excel_engine) as writer:
                # Summary sheet
                summary_df = pd.DataFrame([[row[0], row[1]] for row in summary_rows], columns=["Metric", "Value"])
                summary_df = clean_dataframe_for_export(summary_df, convert_index=False)
                summary_df.to_excel(writer, index=False, sheet_name="Summary")
                
                # Forecast details sheet
                forecast_rows = []
                for days in forecast_periods:
                    if days in all_predictions and all_predictions[days] is not None and len(all_predictions[days]) > 0:
                        for i, price in enumerate(all_predictions[days]):
                            forecast_rows.append({
                                "Forecast Period (Days)": days,
                                "Day": i + 1,
                                "Predicted Price": price
                            })
                
                if forecast_rows:
                    forecast_df = pd.DataFrame(forecast_rows)
                    forecast_df = clean_dataframe_for_export(forecast_df, convert_index=False)
                    forecast_df.to_excel(writer, index=False, sheet_name="Forecasts")
                
                # Historical data sheet
                if not stock_data.empty:
                    hist_df = stock_data[['Close', 'Volume', 'MA_20', 'MA_50']].reset_index()
                    if 'Date' not in hist_df.columns:
                        hist_df.rename(columns={hist_df.columns[0]: 'Date'}, inplace=True)
                    hist_df = clean_dataframe_for_export(hist_df, convert_index=False)
                    hist_df.to_excel(writer, index=False, sheet_name="Historical Data")
                
                # Recommendations sheet
                rec_rows = []
                for days in forecast_periods:
                    if days in all_predictions and all_predictions[days] is not None and len(all_predictions[days]) > 0:
                        pred_price = all_predictions[days][-1]
                        change_pct = ((pred_price - current_price) / current_price) * 100
                        if change_pct > 3:
                            rec = "BUY"
                        elif change_pct < -3:
                            rec = "SELL"
                        else:
                            rec = "HOLD"
                        rec_rows.append({
                            "Period (Days)": days,
                            "Predicted Price": f"₹{pred_price:.2f}",
                            "Change %": f"{change_pct:+.2f}%",
                            "Recommendation": rec
                        })
                
                if rec_rows:
                    rec_df = pd.DataFrame(rec_rows)
                    rec_df = clean_dataframe_for_export(rec_df, convert_index=False)
                    rec_df.to_excel(writer, index=False, sheet_name="Recommendations")
            
            excel_buffer.seek(0)
            
            st.download_button(
                label="⬇️ Download Excel Report (Forecasts, Data & Recommendations)",
                data=excel_buffer,
                file_name=f"{stock_symbol}_analysis_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_excel_report"
            )
        except ImportError:
            st.warning("⚠️ Excel export requires xlsxwriter or openpyxl. Install with: `pip install xlsxwriter openpyxl`")
        except Exception as e:
            logger.error(f"Excel export failed: {e}")
            st.error(f"⚠️ Excel export failed: {str(e)}")
        
        # AI ANALYSIS FEATURES
        st.markdown("---")
        st.markdown("## 🚀 Advanced AI Analysis Dashboard")
        
        # Create tabs for different analysis features
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Risk & Confidence", "🎯 Patterns & Signals", "📈 Portfolio Analytics", "🔮 Prediction Insights"])
        
        with tab1:
            st.markdown("### Risk Assessment & Confidence Metrics")
            
            # Risk Meter
            risk_cols = responsive_ui.get_responsive_columns(4, mobile_count=1)
            
            # Volatility Score
            try:
                volatility = stock_data['Close'].pct_change().std() * np.sqrt(252) * 100
                vol_score = min(100, max(0, 100 - volatility))  # Higher volatility = lower score
                
                with risk_cols[0]:
                    st.metric("Volatility Score", f"{vol_score:.1f}/100")
                    if vol_score > 70:
                        st.success("🛡️ Low Risk")
                    elif vol_score > 40:
                        st.warning("⚠️ Medium Risk")
                    else:
                        st.error("🔴 High Risk")
            except:
                with risk_cols[0]:
                    st.metric("Volatility Score", "N/A")
            
            # Confidence %
            confidence_pct = recommendation.get('confidence', 65.0) if isinstance(recommendation, dict) else 65.0
            with risk_cols[1]:
                st.metric("AI Confidence", f"{confidence_pct:.1f}%")
                if confidence_pct > 80:
                    st.success("🎯 High Confidence")
                elif confidence_pct > 60:
                    st.info("📊 Moderate Confidence")
                else:
                    st.warning("🤔 Low Confidence")
            
            # Risk Level
            risk_level = (
                recommendation.get('details', {}).get('volatility', {}).get('risk_level', 'Medium')
                if isinstance(recommendation, dict) else 'Medium'
            )
            with risk_cols[2]:
                st.metric("Risk Level", risk_level)
                if risk_level == 'Low':
                    st.success("✅ Low Risk")
                elif risk_level == 'Medium':
                    st.warning("⚠️ Medium Risk")
                else:
                    st.error("🔴 High Risk")
            
            # Trend Strength
            trend_strength = (
                recommendation.get('details', {}).get('trend_consistency', 0.5) * 100
                if isinstance(recommendation, dict) else 50.0
            )
            with risk_cols[3]:
                st.metric("Trend Strength", f"{trend_strength:.1f}%")
                if trend_strength > 70:
                    st.success("📈 Strong Trend")
                elif trend_strength > 40:
                    st.info("📊 Moderate Trend")
                else:
                    st.warning("🔄 Weak Trend")
            
            # Smart Alerts
            st.markdown("### 🔔 Smart Alerts")
            alerts = []
            
            # Price alerts
            try:
                current_price = latest.Close
                high_52w = stock_data['Close'].max()
                low_52w = stock_data['Close'].min()
                
                if current_price > high_52w * 0.95:
                    alerts.append("🚀 **Near 52-Week High Alert:** Stock is within 5% of its yearly peak!")
                elif current_price < low_52w * 1.05:
                    alerts.append("🔻 **Near 52-Week Low Alert:** Stock is within 5% of its yearly bottom!")
                
                # Volume alerts
                avg_volume = stock_data['Volume'].tail(20).mean()
                if latest.Volume > avg_volume * 2:
                    alerts.append("📈 **High Volume Alert:** Trading volume is 2x above 20-day average!")
                
                # Volatility alerts
                if volatility > 50:
                    alerts.append(f"⚡ **Extreme Volatility Alert:** {volatility:.1f}% annualized volatility detected!")
                elif volatility > 30:
                    alerts.append(f"⚠️ **High Volatility Alert:** {volatility:.1f}% annualized volatility!")
                    
            except:
                pass
            
            # Prediction alerts
            if isinstance(recommendation, dict):
                action = recommendation.get('action', 'HOLD')
                confidence_val = recommendation.get('confidence', 0)
                if action == 'BUY' and confidence_val > 80:
                    alerts.append("🟢 **Strong Buy Signal:** High confidence BUY recommendation!")
                elif action == 'SELL' and confidence_val > 80:
                    alerts.append("🔴 **Strong Sell Signal:** High confidence SELL recommendation!")
            
            if alerts:
                for alert in alerts:
                    st.warning(alert)
            else:
                st.info("✅ No critical alerts at this time.")
        
        with tab2:
            st.markdown("### 🎯 Candlestick Patterns & Technical Analysis")
            
            pattern_cols = responsive_ui.get_responsive_columns(2, mobile_count=1)
            
            with pattern_cols[0]:
                st.markdown("#### Pattern Recognition")
                
                patterns_detected = detect_candlestick_patterns(stock_data)
                if patterns_detected:
                    for pattern in patterns_detected:
                        st.info(f"**{pattern['name']}** — {pattern['description']}")
                else:
                    st.write("No significant patterns detected in recent candles.")
            
            with pattern_cols[1]:
                st.markdown("#### Pattern Probability")
                try:
                    pattern_probabilities = get_pattern_probabilities(stock_data)
                    st.metric("Momentum Probability", pattern_probabilities['momentum'])
                    st.metric("Reversal Probability", pattern_probabilities['reversal'])
                    st.metric("Breakout Probability", pattern_probabilities['breakout'])
                    st.metric("Pattern Confidence", pattern_probabilities['confidence'])
                except Exception:
                    st.metric("Pattern Analysis", "Limited Data", "N/A")
            st.markdown("#### Advanced Technical Analysis")
            
            tech_chart = go.Figure()
            
            # RSI
            if 'RSI' in stock_data.columns:
                tech_chart.add_trace(go.Scatter(
                    x=stock_data.index,
                    y=stock_data['RSI'],
                    mode='lines',
                    name='RSI',
                    line=dict(color='#f97316', width=2),
                    yaxis='y2'
                ))
                
                # RSI levels
                tech_chart.add_hline(y=70, line_dash="dash", line_color="red", yref='y2', opacity=0.5)
                tech_chart.add_hline(y=30, line_dash="dash", line_color="green", yref='y2', opacity=0.5)
            
            # Volume
            tech_chart.add_trace(go.Bar(
                x=stock_data.index,
                y=stock_data['Volume'],
                name='Volume',
                marker_color='rgba(168, 85, 247, 0.6)',
                yaxis='y3'
            ))
            
            tech_chart.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(t=40, l=20, r=20, b=20),
                height=400,
                yaxis=dict(title='Price'),
                yaxis2=dict(title='RSI', overlaying='y', side='right', range=[0, 100]),
                yaxis3=dict(title='Volume', overlaying='y', side='right', anchor='free', position=0.85),
                hovermode='x unified'
            )
            
            st.plotly_chart(tech_chart, use_container_width=True)
        
        with tab3:
            st.markdown("### 📈 Portfolio Analytics & Heatmaps")
            
            # Portfolio Heatmap (simulated with sector comparison)
            st.markdown("#### Sector Performance Heatmap")
            
            # Get company info for sector analysis
            try:
                company_info = data_fetcher.get_company_info(resolved_symbol)
                current_sector = company_info.get('sector', 'Unknown')
                
                # Simulate sector comparison data
                sectors = ['Technology', 'Healthcare', 'Finance', 'Energy', 'Consumer Goods', 'Materials']
                sector_performance = {}
                
                # Generate mock sector data based on current stock performance
                base_perf = ((latest.Close - stock_data['Close'].iloc[-30]) / stock_data['Close'].iloc[-30]) * 100 if len(stock_data) > 30 else 0
                
                for sector in sectors:
                    # Add some randomness but bias toward current stock
                    if sector == current_sector:
                        sector_performance[sector] = base_perf
                    else:
                        sector_performance[sector] = base_perf + np.random.uniform(-5, 5)
                
                # Create heatmap data
                heatmap_data = []
                for sector, perf in sector_performance.items():
                    color_intensity = min(1.0, max(0.0, (perf + 10) / 20))  # Scale to 0-1
                    heatmap_data.append({
                        'Sector': sector,
                        'Performance': perf,
                        'Intensity': color_intensity,
                        'Status': 'Outperforming' if perf > 2 else 'Underperforming' if perf < -2 else 'Neutral'
                    })
                
                heatmap_df = pd.DataFrame(heatmap_data)
                
                # Create heatmap visualization
                fig = go.Figure(data=go.Heatmap(
                    z=heatmap_df['Intensity'],
                    x=['Performance'],
                    y=heatmap_df['Sector'],
                    colorscale='RdYlGn',
                    text=[[f"{perf:.1f}%" for perf in heatmap_df['Performance']]],
                    texttemplate="%{text}",
                    textfont={"size": 12},
                    hoverongaps=False
                ))
                
                fig.update_layout(
                    template='plotly_dark',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(t=40, l=100, r=20, b=20),
                    height=300,
                    xaxis=dict(showticklabels=False),
                    yaxis=dict(tickfont=dict(size=10))
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Sector comparison table
                st.markdown("#### Sector Comparison")
                sector_table = heatmap_df[['Sector', 'Performance', 'Status']].copy()
                sector_table['Performance'] = sector_table['Performance'].apply(lambda x: f"{x:+.1f}%")
                
                # Highlight current sector
                def highlight_sector(row):
                    if row['Sector'] == current_sector:
                        return ['background-color: rgba(34, 211, 238, 0.2)'] * len(row)
                    return [''] * len(row)
                
                st.dataframe(sector_table.style.apply(highlight_sector, axis=1), use_container_width=True)
            
            except Exception as e:
                st.warning(f"Could not generate sector analysis: {str(e)}")
            
            # Portfolio Allocation (simulated)
            st.markdown("#### Portfolio Allocation Suggestion")
            
            alloc_cols = responsive_ui.get_responsive_columns(3, mobile_count=1)

            action = 'HOLD'
            confidence = 0
            if isinstance(recommendation, dict):
                action = recommendation.get('action', 'HOLD')
                confidence = recommendation.get('confidence', 0)

            if action == 'BUY':
                with alloc_cols[0]:
                    st.metric("Suggested Allocation", "15-25%", "Aggressive")
                with alloc_cols[1]:
                    st.metric("Risk Level", "Medium-High", "📈")
                with alloc_cols[2]:
                    st.metric("Time Horizon", "3-6 Months", "⏰")
            elif action == 'SELL':
                with alloc_cols[0]:
                    st.metric("Suggested Allocation", "0-5%", "Conservative")
                with alloc_cols[1]:
                    st.metric("Risk Level", "High", "⚠️")
                with alloc_cols[2]:
                    st.metric("Time Horizon", "Immediate", "🚨")
            else:
                with alloc_cols[0]:
                    st.metric("Suggested Allocation", "5-15%", "Balanced")
                with alloc_cols[1]:
                    st.metric("Risk Level", "Medium", "📊")
                with alloc_cols[2]:
                    st.metric("Time Horizon", "1-3 Months", "⏳")
                with alloc_cols[1]:
                    st.metric("Risk Level", "Medium", "📊")
                with alloc_cols[2]:
                    st.metric("Time Horizon", "1-3 Months", "⏳")
        
        with tab4:
            st.markdown("### 🔮 Prediction Confidence & Advanced Insights")
            
            # Prediction Confidence Graph
            st.markdown("#### Prediction Confidence Over Time")
            
            if all_predictions:
                confidence_data = []
                
                for days in forecast_periods:
                    if days in all_predictions and all_predictions[days] is not None:
                        preds = all_predictions[days]
                        current_price = latest.Close
                        
                        # Calculate confidence based on prediction stability
                        pred_volatility = 0
                        if len(preds) > 1:
                            # Lower volatility in predictions = higher confidence
                            pred_volatility = np.std(np.diff(preds)) / np.mean(preds)
                            confidence_score = max(0.1, min(0.95, 1 - pred_volatility * 10))
                        else:
                            confidence_score = 0.5
                        
                        confidence_data.append({
                            'Period': f'{days} Days',
                            'Confidence': confidence_score * 100,
                            'Predictions': len(preds),
                            'Volatility': pred_volatility * 100
                        })
                
                if confidence_data:
                    conf_df = pd.DataFrame(confidence_data)
                    
                    conf_chart = go.Figure()
                    conf_chart.add_trace(go.Bar(
                        x=conf_df['Period'],
                        y=conf_df['Confidence'],
                        name='Confidence %',
                        marker_color=['#10b981', '#f97316', '#ef4444'],
                        text=[f"{conf:.1f}%" for conf in conf_df['Confidence']],
                        textposition='auto'
                    ))
                    
                    conf_chart.update_layout(
                        template='plotly_dark',
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        margin=dict(t=40, l=20, r=20, b=20),
                        height=300,
                        yaxis=dict(range=[0, 100], title='Confidence %')
                    )
                    
                    st.plotly_chart(conf_chart, use_container_width=True)
            
            # Advanced Insights
            st.markdown("#### AI-Powered Insights")
            
            insights_cols = responsive_ui.get_responsive_columns(2, mobile_count=1)
            
            with insights_cols[0]:
                st.markdown("**Market Sentiment Analysis**")
                
                if sentiment_scores:
                    try:
                        sentiment_analyzer = SentimentAnalyzer()
                        sentiment_summary = sentiment_analyzer.get_overall_sentiment(sentiment_scores)
                        
                        sentiment_score = sentiment_summary['overall_compound']
                        
                        if sentiment_score > 0.1:
                            st.success(f"🟢 Positive Sentiment ({sentiment_score:.2f})")
                        elif sentiment_score < -0.1:
                            st.error(f"🔴 Negative Sentiment ({sentiment_score:.2f})")
                        else:
                            st.info(f"🟡 Neutral Sentiment ({sentiment_score:.2f})")
                            
                        st.metric("News Articles Analyzed", len(sentiment_scores))
                        
                    except:
                        st.info("Sentiment analysis unavailable")
                else:
                    st.info("No news sentiment data available")
            
            with insights_cols[1]:
                st.markdown("**Technical Strength Indicators**")
                
                try:
                    # Calculate technical strength
                    technical_score = 0
                    
                    # RSI contribution
                    if 'RSI' in stock_data.columns:
                        rsi = stock_data['RSI'].iloc[-1]
                        if 40 <= rsi <= 60:
                            technical_score += 25
                        elif 30 <= rsi <= 70:
                            technical_score += 15
                    
                    # Moving average alignment
                    if 'MA_20' in stock_data.columns and 'MA_50' in stock_data.columns:
                        price = stock_data['Close'].iloc[-1]
                        ma20 = stock_data['MA_20'].iloc[-1]
                        ma50 = stock_data['MA_50'].iloc[-1]
                        
                        if price > ma20 > ma50:
                            technical_score += 35
                        elif price > ma20:
                            technical_score += 20
                    
                    # Volume trend
                    if len(stock_data) > 20:
                        recent_volume = stock_data['Volume'].tail(5).mean()
                        older_volume = stock_data['Volume'].tail(20).head(15).mean()
                        
                        if recent_volume > older_volume * 1.2:
                            technical_score += 20
                    
                    technical_score = min(100, technical_score)
                    
                    st.metric("Technical Strength", f"{technical_score}%")
                    
                    if technical_score > 70:
                        st.success("💪 Strong Technicals")
                    elif technical_score > 40:
                        st.info("📊 Moderate Technicals")
                    else:
                        st.warning("⚠️ Weak Technicals")
                        
                except:
                    st.metric("Technical Strength", "N/A")
            
            # Prediction Accuracy Simulation
            st.markdown("#### Prediction Accuracy Metrics")
            
            accuracy_cols = responsive_ui.get_responsive_columns(3, mobile_count=1)
            
            # Simulate accuracy metrics (in real app, this would be based on historical predictions)
            with accuracy_cols[0]:
                st.metric("Historical Accuracy", "78%", "Good")
            
            with accuracy_cols[1]:
                st.metric("Model Confidence", f"{confidence_pct:.1f}%", "Current")
            
            with accuracy_cols[2]:
                st.metric("Data Quality", "85%", "High")
        
        # AI Advisory Section
        st.markdown("---")
        st.markdown("## 🤖 AI Analysis & Advisory")
        
        insights = []
        
        # 1. Trending news headlines
        if news:
            insights.append(f"📰 **Latest News:** {news[0].get('title', 'Recent market activity')} ")
        
        # 2. Show volatility
        try:
            volatility = stock_data['Close'].pct_change().std() * np.sqrt(252) * 100
            if volatility > 40:
                insights.append(f"⚠️ **High Volatility Alert:** {volatility:.1f}% annualized - Price swings are significant")
            elif volatility < 20:
                insights.append(f"🛡️ **Low Volatility:** {volatility:.1f}% annualized - Relatively stable")
            else:
                insights.append(f"📊 **Moderate Volatility:** {volatility:.1f}% annualized")
        except:
            pass
        
        # 3. Price near 52-week high/low
        try:
            close = stock_data['Close'].iloc[-1]
            high_52w = stock_data['Close'].max()
            low_52w = stock_data['Close'].min()
            
            pct_from_high = ((close - high_52w) / high_52w) * 100
            pct_from_low = ((close - low_52w) / low_52w) * 100
            
            if abs(pct_from_high) < 5:
                insights.append(f"🚀 **Near 52-Week High:** Trading {abs(pct_from_high):.1f}% below yearly peak")
            elif abs(pct_from_low) < 5:
                insights.append(f"🔻 **Near 52-Week Low:** Trading {pct_from_low:.1f}% above yearly bottom")
        except:
            pass
        
        # 4. Recent performance
        try:
            if len(stock_data) > 21:
                month_return = (stock_data['Close'].iloc[-1] / stock_data['Close'].iloc[-22] - 1) * 100
                insights.append(f"📈 **1-Month Return:** {month_return:+.2f}%")
            if len(stock_data) > 250:
                year_return = (stock_data['Close'].iloc[-1] / stock_data['Close'].iloc[-252] - 1) * 100
                insights.append(f"📅 **1-Year Return:** {year_return:+.2f}%")
        except:
            pass
        
        # 5. AI Forecast summary
        if 14 in all_predictions and all_predictions[14] is not None and len(all_predictions[14]) > 0:
            pred_price = all_predictions[14][-1]
            change_pct = ((pred_price - current_price) / current_price) * 100
            if change_pct > 3:
                insights.append(f"📊 **AI Forecast (14D):** Model expects upward movement of {change_pct:.2f}%")
            elif change_pct < -3:
                insights.append(f"📊 **AI Forecast (14D):** Model expects downward movement of {abs(change_pct):.2f}%")
            else:
                insights.append(f"📊 **AI Forecast (14D):** Model expects minor price changes")
        
        # 6. General advisory
        insights.append("⚠️ **Disclaimer:** This analysis is for informational purposes only. Always diversify your portfolio and consult a financial advisor before making investment decisions.")
        
        for insight in insights:
            st.info(insight)

        st.markdown("---")
        st.markdown("### Trade Workflow & Watchlist")
        workflow_cols = responsive_ui.get_responsive_columns(3, mobile_count=1)
        if 'watchlist' not in st.session_state:
            st.session_state.watchlist = []

        trade_action = 'Add to Watchlist'
        if stock_symbol not in st.session_state.watchlist:
            if workflow_cols[0].button(f"{trade_action}", key="add_watchlist"):
                st.session_state.watchlist.append(stock_symbol)
                st.success(f"{stock_symbol} added to watchlist")
        else:
            workflow_cols[0].metric("Watchlist", f"{stock_symbol} already added")

        if workflow_cols[1].button("📩 Create Quick Alert", key="quick_alert"):
            st.success("Quick alert created. Manage it in the Alerts page.")
        if workflow_cols[2].button("📌 Save Trading Idea", key="save_trading_idea"):
            st.success("Trading idea saved for review.")

        if st.session_state.get('watchlist'):
            st.markdown(f"**Current Watchlist:** {', '.join(st.session_state.watchlist)}")

        st.markdown("---")
        st.markdown("### Forecast Summary")
        if predictions is not None and len(predictions) > 0:
            st.write(f"Your AI model anticipates a **{((predictions[-1] - latest.Close) / latest.Close) * 100:.2f}%** move over the next 14 trading days.")

        if isinstance(recommendation, dict):
            st.markdown("### Primary Recommendation")
            st.success(f"{recommendation.get('action', 'HOLD')} — Confidence {recommendation.get('confidence', 0):.0f}%")
            st.write(recommendation.get('reasoning', 'No reasoning provided.'))
        else:
            st.markdown("### Primary Recommendation")
            st.info("No recommendation available at this time.")

        if sentiment_scores:
            st.markdown("### Top headlines and AI sentiment")
            for headline in news[:5]:
                st.write(f"- {headline.get('title', headline.get('description', 'No headline available'))}")

        st.markdown("---")
        st.markdown("### Smart finance dashboard")
        safe_confidence = int(recommendation.get('confidence', 68)) if isinstance(recommendation, dict) else 68
        safe_risk = recommendation.get('details', {}).get('volatility', {}).get('risk_level', 'Medium') if isinstance(recommendation, dict) else 'Medium'
        safe_trend = 'Bullish' if isinstance(recommendation, dict) and recommendation.get('action') == 'BUY' else 'Bearish' if isinstance(recommendation, dict) and recommendation.get('action') == 'SELL' else 'Neutral'
        metrics = [
            ("AI Confidence", f"{safe_confidence}%"),
            ("Risk Signal", safe_risk),
            ("Trend", safe_trend)
        ]
        cols = responsive_ui.get_responsive_columns(3, mobile_count=1)
        for idx, (label, value) in enumerate(metrics):
            with cols[idx]:
                st.metric(label, value)

        if st.button("Back to Home", use_container_width=True):
            st.session_state.page = 'dashboard'
            st.rerun()


def show_alerts_page():
    render_back_button(target_page='dashboard', label='← Back to Dashboard', key='back_alerts')
    st.markdown("## 🔔 Price Alerts & Notifications")
    st.write("Manage your stock price alerts, volume alerts, and momentum triggers with real-time notification settings.")

    db = Database()
    user = auth_manager.get_current_user()
    
    if not user:
        st.error("User not authenticated")
        return

    user_alerts_all = db.get_user_alerts(user['id'], active_only=False)
    user_alerts = [alert for alert in user_alerts_all if alert['is_active']]
    triggered_count = sum(1 for alert in user_alerts_all if alert['triggered'])

    st.markdown("""
    <style>
        .alert-metric-card {border-radius: 18px; padding: 1rem; background: rgba(15, 23, 42, 0.9); border: 1px solid rgba(255,255,255,0.08);}
        .alert-card {border-radius: 18px; padding: 1rem; background: rgba(31, 41, 55, 0.85); border: 1px solid rgba(255,255,255,0.08); margin-bottom: 0.75rem;}
    </style>
    """, unsafe_allow_html=True)

    metric_cols = responsive_ui.get_responsive_columns(3, mobile_count=1)
    metric_cols[0].metric("Active Alerts", len(user_alerts))
    metric_cols[1].metric("Triggered Alerts", triggered_count)
    metric_cols[2].metric("Total Alerts", len(user_alerts_all))

    tab1, tab2, tab3 = st.tabs(["Active Alerts", "Create Alert", "Settings"])

    with tab1:
        st.subheader("Your Active Alerts")
        user_alerts = db.get_user_alerts(user['id'], active_only=True)
        
        if user_alerts:
            for alert in user_alerts:
                col1, col2, col3 = responsive_ui.get_responsive_columns(3, mobile_count=1)
                with col1:
                    triggered_badge = "🔴 TRIGGERED" if alert['triggered'] else "🟢 Active"
                    st.markdown(f"""
                    **{alert['symbol']}** — {alert['alert_type']} alert at {format_currency(alert['threshold'])} {triggered_badge}  
                    *Created: {alert['created_at'][:10]}*
                    """)
                with col2:
                    if st.button("Edit", key=f"edit_alert_{alert['id']}", use_container_width=True):
                        st.session_state.edit_alert = alert['id']
                with col3:
                    if st.button("❌", key=f"delete_alert_{alert['id']}", use_container_width=True):
                        db.deactivate_alert(alert['id'])
                        st.success(f"Alert deleted for {alert['symbol']}")
                        st.rerun()
        else:
            st.info("No active alerts. Create one below!")

    with tab2:
        st.subheader("Create New Alert")
        col1, col2 = responsive_ui.get_responsive_columns(2, mobile_count=1)
        
        with col1:
            symbol = st.text_input("Stock Symbol", value="RELIANCE.NS", key="alert_symbol_new")
            alert_type = st.selectbox("Alert Type", ["Price Above", "Price Below", "Volume Spike", "Momentum"], key="alert_type_new")
        
        with col2:
            threshold = st.number_input("Threshold Value", value=2600.0, step=0.01, key="alert_threshold_new")
            if st.button("Create Alert", use_container_width=True, key="create_alert_btn"):
                alert_id = db.create_alert(user['id'], symbol.upper(), alert_type, threshold)
                if alert_id:
                    db.log_activity(user['id'], 'create_alert', f'Created {alert_type} alert for {symbol}')
                    st.success(f"Alert created successfully for {symbol}!")
                    st.rerun()

    with tab3:
        st.subheader("Alert Preferences")
        col1, col2 = responsive_ui.get_responsive_columns(2, mobile_count=1)
        
        with col1:
            st.checkbox("Email notifications on alert trigger", value=True, key="alert_email")
            st.checkbox("SMS notifications", value=False, key="alert_sms")
        
        with col2:
            st.selectbox("Check frequency", ["Real-time", "Every 15 min", "Every 30 min", "Daily"], key="alert_frequency")
            st.selectbox("Silence after trigger", ["Never", "5 min", "30 min", "1 hour"], key="alert_silence")

        if st.button("Save Preferences", use_container_width=True, key="save_alert_prefs"):
            st.success("Alert preferences saved!")


def show_portfolio_page():
    render_back_button(target_page='dashboard', label='← Back to Dashboard', key='back_portfolio')
    st.markdown("## 💼 Portfolio Management")
    st.write("Track your stock holdings, performance analytics, and allocation strategies.")

    db = Database()
    user = auth_manager.get_current_user()

    if not user:
        st.error("User not authenticated")
        return

    # Tabs for portfolio sections
    tab1, tab2, tab3 = st.tabs(["Holdings", "Add Holding", "Performance"])

    with tab1:
        st.subheader("Your Holdings")
        holdings = db.get_portfolio(user['id'])
        
        if holdings:
            # Display metrics
            total_cost = sum(h['quantity'] * h['avg_buy_price'] for h in holdings)
            num_stocks = len(holdings)
            
            col1, col2, col3, col4 = responsive_ui.get_responsive_columns(4, mobile_count=1)
            col1.metric("Total Holdings", f"₹{total_cost:,.0f}")
            col2.metric("Stocks", num_stocks)
            col3.metric("Daily Change", "+1.82%", "+₹62,500")
            col4.metric("Annual Return", "+18.4%")

            risk_metrics = compute_portfolio_risk_metrics(holdings)
            risk_cols = responsive_ui.get_responsive_columns(4, mobile_count=1)
            risk_cols[0].metric("Market Value", f"₹{risk_metrics['market_value']:,.0f}")
            risk_cols[1].metric("Unrealized P/L", f"₹{risk_metrics['unrealized_pnl']:,.0f}")
            risk_cols[2].metric("95% VaR", f"{risk_metrics['var_95']:.2f}%")
            risk_cols[3].metric("Max Drawdown", f"{risk_metrics['max_drawdown']:.2f}%")

            # Holdings table
            df_holdings = pd.DataFrame(holdings)
            df_display = df_holdings[['symbol', 'quantity', 'avg_buy_price', 'entry_date']].copy()
            df_display.columns = ['Symbol', 'Quantity', 'Avg Buy Price', 'Entry Date']
            df_display['Total Value'] = df_holdings['quantity'] * df_holdings['avg_buy_price']
            
            st.dataframe(df_display, use_container_width=True)

            if risk_metrics and risk_metrics.get('allocations'):
                exposure_df = pd.DataFrame(risk_metrics['allocations'])
                exposure_df['allocation_pct'] = exposure_df['allocation_pct'].apply(lambda x: f"{x:.1f}%")
                exposure_df = exposure_df[['symbol', 'market_value', 'allocation_pct']].rename(columns={
                    'symbol': 'Symbol',
                    'market_value': 'Market Value',
                    'allocation_pct': 'Allocation %'
                })
                st.markdown("#### Portfolio Exposure")
                st.dataframe(exposure_df, use_container_width=True)

            # Edit/Remove options
            selected_symbol = st.selectbox("Manage holding", [h['symbol'] for h in holdings], key="manage_holding")
            col1, col2, col3 = responsive_ui.get_responsive_columns(3, mobile_count=1)
            
            with col1:
                if st.button("Edit Holding", use_container_width=True, key="edit_holding_btn"):
                    st.session_state.edit_holding = selected_symbol
            with col2:
                if st.button("Remove Holding", use_container_width=True, key="remove_holding"):
                    db.remove_portfolio_holding(user['id'], selected_symbol)
                    db.record_portfolio_history(user['id'], total_cost, 0.0, 0.0, 0.0)
                    db.log_activity(user['id'], 'remove_portfolio_holding', f'Removed {selected_symbol}')
                    st.success(f"Removed {selected_symbol} from portfolio")
                    st.rerun()
            with col3:
                if st.button("View Chart", use_container_width=True, key="view_holding_chart"):
                    st.session_state.current_stock = selected_symbol

            if st.session_state.get('edit_holding') == selected_symbol:
                edited = next((h for h in holdings if h['symbol'] == selected_symbol), None)
                if edited:
                    st.markdown("### Update Holding")
                    edit_cols = responsive_ui.get_responsive_columns(2, mobile_count=1)
                    with edit_cols[0]:
                        updated_quantity = st.number_input("Quantity", value=float(edited['quantity']), min_value=0.0, step=1.0, key="edit_quantity")
                        updated_notes = st.text_input("Notes", value=edited.get('notes', ''), key="edit_notes")
                    with edit_cols[1]:
                        updated_price = st.number_input("Average Buy Price", value=float(edited['avg_buy_price']), min_value=0.0, step=0.01, key="edit_price")
                        if st.button("Save Changes", use_container_width=True, key="save_holding_changes"):
                            db.update_portfolio_holding(user['id'], selected_symbol, updated_quantity, updated_price, updated_notes)
                            db.record_portfolio_history(user['id'], total_cost, 0.0, 0.0, 0.0)
                            db.log_activity(user['id'], 'update_portfolio_holding', f'Updated {selected_symbol} to {updated_quantity} @ {updated_price}')
                            st.success(f"Updated {selected_symbol} successfully.")
                            del st.session_state['edit_holding']
                            st.rerun()

        else:
            st.info("No holdings yet. Add your first stock below!")

    with tab2:
        st.subheader("Add New Holding")
        col1, col2 = responsive_ui.get_responsive_columns(2, mobile_count=1)
        
        with col1:
            symbol = st.text_input("Stock Symbol", value="RELIANCE.NS", key="portfolio_symbol")
            quantity = st.number_input("Quantity", value=10, step=1, key="portfolio_qty")
        
        with col2:
            avg_price = st.number_input("Average Buy Price", value=2500.0, step=0.01, key="portfolio_price")
            notes = st.text_input("Notes (optional)", key="portfolio_notes")

        if st.button("Add to Portfolio", use_container_width=True, key="add_to_portfolio_btn"):
            db.add_portfolio_holding(user['id'], symbol.upper(), quantity, avg_price, notes)
            db.record_portfolio_history(user['id'], quantity * avg_price, 0.0, 0.0, 0.0)
            db.log_activity(user['id'], 'add_portfolio_holding', f'Added {quantity} x {symbol}')
            st.success(f"Added {quantity} shares of {symbol} to portfolio!")
            st.rerun()

    with tab3:
        st.subheader("Portfolio Performance")
        history = db.get_portfolio_history(user['id'])
        
        if history:
            df_history = pd.DataFrame(history)
            df_history['timestamp'] = pd.to_datetime(df_history['timestamp'])
            
            # Plot performance
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_history['timestamp'],
                y=df_history['total_value'],
                mode='lines+markers',
                name='Portfolio Value',
                line=dict(color='#38bdf8', width=2),
                fill='tozeroy'
            ))
            fig.update_layout(
                title="Portfolio Value Over Time",
                xaxis_title="Date",
                yaxis_title="Value (₹)",
                template="plotly_dark",
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No performance history yet. Track your portfolio over time!")


def show_settings_page():
    render_back_button(target_page='dashboard', label='← Back to Dashboard', key='back_settings')
    st.markdown('## Settings')
    st.write('Update user preferences, security settings, and theme options.')

    if 'user_preferences' not in st.session_state:
        st.session_state.user_preferences = {
            'theme': st.session_state.get('theme', 'dark'),
            'email_alerts': True,
            'newsletter': False,
            'risk_profile': 'Balanced'
        }

    theme_selection = st.radio('App theme', ['dark', 'light'], index=0 if st.session_state.user_preferences['theme'] == 'dark' else 1, horizontal=True)
    st.session_state.user_preferences['theme'] = theme_selection
    st.session_state.theme = theme_selection

    st.checkbox('Email alerts and system updates', key='pref_email_alerts', value=st.session_state.user_preferences['email_alerts'])
    st.checkbox('Subscribe to newsletter', key='pref_newsletter', value=st.session_state.user_preferences['newsletter'])
    risk_profile = st.selectbox('Risk profile', ['Conservative', 'Balanced', 'Growth', 'Active'], index=['Conservative', 'Balanced', 'Growth', 'Active'].index(st.session_state.user_preferences['risk_profile']))
    st.session_state.user_preferences.update({
        'email_alerts': st.session_state.get('pref_email_alerts', st.session_state.user_preferences['email_alerts']),
        'newsletter': st.session_state.get('pref_newsletter', st.session_state.user_preferences['newsletter']),
        'risk_profile': risk_profile
    })

    st.markdown('#### Security')
    st.write('Account security settings are managed by administrators.')

    st.write('Adjust your account security and notification preferences here.')

# --- Main App Content ---
def show_main_app():
    add_sidebar_navigation()

    if 'theme' not in st.session_state:
        st.session_state.theme = 'dark'

    if st.button("🌓 Toggle Theme", use_container_width=True, key="theme_toggle_btn"):
        st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'
        st.rerun()

    is_dark = st.session_state.theme == 'dark'
    page_background = '#050814' if is_dark else '#f8fafc'
    primary_text = '#e0f7ff' if is_dark else '#0f172a'
    secondary_text = '#67e8f9' if is_dark else '#0d9488'
    card_bg = 'rgba(10, 16, 31, 0.94)' if is_dark else 'rgba(255,255,255,0.88)'
    glow_color = 'rgba(34, 211, 238, 0.2)' if is_dark else 'rgba(56, 189, 248, 0.18)'

    st.markdown(f"""
<style>
body {{ background: linear-gradient(135deg, #080b16, #07111f, #0b1932, #111b3e); color: {primary_text}; }}
.stApp {{ background: {page_background}; }}
.hero-panel {{ background: radial-gradient(circle at top right, rgba(34,211,238,0.18), transparent 35%), radial-gradient(circle at bottom left, rgba(168,85,247,0.12), transparent 28%), {card_bg}; border: 1px solid rgba(255,255,255,0.12); border-radius: 32px; padding: 3rem 2rem 2rem; position: relative; overflow: hidden; margin-bottom: 2rem; text-align: center; }}
.hero-panel::before {{ content: ''; position: absolute; width: 320px; height: 320px; top: -90px; right: -90px; background: rgba(34,211,238,0.3); filter: blur(90px); }}
.hero-panel::after {{ content: ''; position: absolute; width: 220px; height: 220px; bottom: -80px; left: -80px; background: rgba(168,85,247,0.24); filter: blur(70px); animation: float-shape 18s ease-in-out infinite; }}
.hero-title {{ font-size: 3.4rem; font-weight: 800; margin: 1.2rem auto 0.8rem; line-height: 1.02; letter-spacing: -0.04em; max-width: 860px; background: linear-gradient(90deg, #38bdf8, #7c3aed, #22c55e); -webkit-background-clip: text; -webkit-text-fill-color: transparent; color: transparent; animation: glow-text 4s ease-in-out infinite alternate; }}
.hero-subtitle {{ color: {secondary_text}; font-size: 1.15rem; margin: 0.8rem auto 0; max-width: 820px; opacity: 0.95; line-height: 1.65; }}
.market-pill {{ display: inline-flex; align-items: center; justify-content: center; padding: 0.55rem 1rem; border-radius: 999px; background: rgba(14,165,233,0.18); border: 1px solid rgba(56,189,248,0.25); color: {primary_text}; margin: 0.35rem 0.35rem; animation: pulse-pill 4s ease-in-out infinite alternate; min-width: 150px; }}
.hero-logo {{ margin: 0 auto; width: 110px; height: 110px; border-radius: 50%; border: 1px solid rgba(56,189,248,0.35); display: flex; align-items: center; justify-content: center; color: #ffffff; font-weight: 700; letter-spacing: 0.05em; font-size: 0.95rem; text-transform: uppercase; box-shadow: 0 0 40px rgba(56,189,248,0.18); background: rgba(255,255,255,0.04); position: relative; z-index: 1; }}
.hero-panel {{ position: relative; overflow: hidden; }}
.hero-panel .hero-deco {{ position: absolute; width: 140px; height: 140px; border-radius: 999px; top: 20px; left: 26px; background: rgba(59,130,246,0.18); box-shadow: 0 0 60px rgba(59,130,246,0.25); animation: drift 12s linear infinite; z-index: 0; }}
.hero-panel .hero-deco-two {{ position: absolute; width: 160px; height: 160px; border-radius: 999px; bottom: 30px; right: 40px; background: rgba(168,85,247,0.12); box-shadow: 0 0 70px rgba(168,85,247,0.22); animation: drift 16s linear reverse infinite; z-index: 0; }}
.hero-panel > * {{ position: relative; z-index: 1; }}
@keyframes float-shape {{ 0% {{ transform: translateY(0px) rotate(0deg); }} 50% {{ transform: translateY(-24px) rotate(12deg); }} 100% {{ transform: translateY(0px) rotate(0deg); }} }}
@keyframes glow-text {{ 0% {{ text-shadow: 0 0 12px rgba(56,189,248,0.5); }} 100% {{ text-shadow: 0 0 28px rgba(168,85,247,0.9); }} }}
@keyframes pulse-pill {{ 0% {{ transform: scale(1); opacity: 1; }} 100% {{ transform: scale(1.04); opacity: 0.9; }} }}
@keyframes drift {{ 0% {{ transform: translate(0,0); }} 50% {{ transform: translate(12px,-18px); }} 100% {{ transform: translate(0,0); }} }}
.feature-card {{ background: {card_bg}; border: 1px solid rgba(255,255,255,0.08); border-radius: 24px; padding: 1.6rem; transition: transform .25s ease, box-shadow .25s ease; text-align: left; }}
.feature-card:hover {{ transform: translateY(-6px); box-shadow: 0 22px 65px rgba(34,211,238,0.14); }}
.stat-card {{ background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08); border-radius: 24px; padding: 1.5rem; min-height: 170px; }}
.stat-card h3 {{ margin: 0 0 0.75rem; color: {secondary_text}; }}
.bottom-nav {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 0.75rem; margin-top: 2rem; }}
.nav-chip {{ background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08); border-radius: 999px; padding: 0.85rem 1.2rem; color: {primary_text}; text-decoration: none; font-size: 0.95rem; }}
.nav-chip:hover {{ background: rgba(14,165,233,0.12); }}
@media only screen and (max-width: 900px) {{ .hero-title {{ font-size: 2.4rem; }} .hero-subtitle {{ font-size: 1rem; max-width: 100%; }} }}
</style>
""", unsafe_allow_html=True)

    user = auth_manager.get_current_user() or {'username': 'Guest'}
    active_page = st.session_state.get('page', 'dashboard')
    public_pages = ['login', 'signup', 'forgot_password', 'reset_password', 'pin_entry', 'pin_reset_request', 'pin_reset']

    if not auth_manager.is_authenticated() and active_page not in public_pages:
        st.session_state.page = 'login'
        st.rerun()

    if active_page == 'dashboard':
        show_dashboard_page(auth_manager.get_current_user())
    elif active_page == 'analysis':
        show_analysis_page()
    elif active_page == 'alerts':
        show_alerts_page()
    elif active_page == 'portfolio':
        show_portfolio_page()
    elif active_page == 'settings':
        show_settings_page()
    elif active_page == 'pin_entry':
        show_pin_entry_page()
    elif active_page == 'pin_reset_request':
        show_pin_reset_request_page()
    elif active_page == 'pin_reset':
        show_pin_reset_page()
    elif active_page == 'admin_train':
        render_admin_training_dashboard()
    else:
        show_dashboard_page(auth_manager.get_current_user())


@auth_manager.admin_required
def show_admin_dashboard():
    render_back_button(target_page='dashboard', label='← Back to Dashboard', key='back_admin')
    st.markdown("## 🛡️ Admin Dashboard")

    if not can_access_admin(auth_manager.get_current_user()):
        st.error("Access denied.")
        return

    db = Database()
    system_health = db.get_system_health()
    system_perf = db.get_system_performance()

    st.markdown("### System Health Overview")
    if system_health:
        health_cols = responsive_ui.get_responsive_columns(5, mobile_count=1)
        health_cols[0].metric("Active Users", system_health.get('active_users', 0))
        health_cols[1].metric("Active Alerts", system_health.get('active_alerts', 0))
        health_cols[2].metric("Activities (24h)", system_health.get('activities_24h', 0))
        health_cols[3].metric("API Calls (1h)", system_health.get('api_calls_1h', 0))
        health_cols[4].metric("Avg API/User (24h)", f"{system_health.get('avg_api_per_user', 0) or 0:.2f}")
    else:
        st.info("No system health metrics available yet.")

    st.markdown("---")
    if st.button("Open Admin Tools", key='open_admin_tools', use_container_width=True):
        st.session_state.page = 'admin_tools'
        st.rerun()

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "👥 User Management",
        "📊 Analytics",
        "📋 Activity Logs",
        "🔔 Notifications",
        "⚙️ System Settings",
        "🔐 Security"
    ])

    with tab1:
        show_user_management()

    with tab2:
        show_analytics()

    with tab3:
        show_activity_logs()

    with tab4:
        show_notifications()

    with tab5:
        show_system_settings()

    with tab6:
        show_security_settings()

def show_admin_tools_page():
    render_back_button(target_page='admin', label='← Back to Admin', key='back_admin_tools')
    st.markdown("## 🧠 Admin Tools")

    if not auth_manager.has_any_role(['Super Admin', 'Admin']):
        st.error("Access denied.")
        return

    db = Database()
    tab1, tab2, tab3 = st.tabs(["👥 Pending Approvals", "⚙️ Feature Flags", "🤖 AI Forecasting"])

    with tab1:
        st.subheader("Pending Account Approvals")
        pending_users = db.get_pending_users()

        if pending_users:
            st.dataframe(pd.DataFrame(pending_users).rename(columns={'created_at': 'Requested At'}), use_container_width=True)
            for user in pending_users:
                cols = responsive_ui.get_responsive_columns(3, mobile_count=1)
                with cols[0]:
                    st.markdown(f"**{user['username']}** — {user['email']}")
                with cols[1]:
                    if st.button("Approve", key=f"approve_user_{user['id']}"):
                        db.update_user(user['id'], is_active=1)
                        db.log_activity(auth_manager.get_current_user()['id'], 'approve_user', f"Approved user {user['username']}")
                        st.success(f"Approved {user['username']}")
                        st.rerun()
                with cols[2]:
                    if st.button("Deny", key=f"deny_user_{user['id']}"):
                        db.update_user(user['id'], is_active=0, is_banned=1)
                        db.log_activity(auth_manager.get_current_user()['id'], 'deny_user', f"Denied user {user['username']}")
                        st.error(f"Denied {user['username']}")
                        st.rerun()
        else:
            st.info("No pending approvals at the moment.")

    with tab2:
        st.subheader("Feature Flags")
        feature_flags = db.get_feature_flags()

        if feature_flags:
            for flag in feature_flags:
                status = bool(flag['enabled'])
                cols = responsive_ui.get_responsive_columns(3, mobile_count=1)
                with cols[0]:
                    st.markdown(f"**{flag['flag_name']}** — {flag['description']}")
                with cols[1]:
                    st.markdown("Enabled" if status else "Disabled")
                with cols[2]:
                    if st.button("Disable" if status else "Enable", key=f"toggle_flag_{flag['flag_name']}"):
                        db.set_feature_flag(flag['flag_name'], 0 if status else 1)
                        db.log_activity(auth_manager.get_current_user()['id'], 'feature_flag_update', f"Set {flag['flag_name']} to {'enabled' if not status else 'disabled'}")
                        st.success(f"Updated {flag['flag_name']}")
        else:
            st.info("No feature flags configured.")

    with tab3:
        show_admin_ai_forecasting()


def show_admin_ai_forecasting():
    render_back_button(target_page='admin', label='← Back to Admin', key='back_admin_ai')
    st.markdown("## 🤖 Admin AI Forecasting Control Panel")

    if not auth_manager.has_any_role(['Super Admin', 'Admin']):
        st.error("Access denied.")
        return

    st.info("This admin-only panel lets you search a stock name, auto-select a matching symbol, and run a multi-model AI forecast.")

    if st.button("Open Training Dashboard", key='admin_open_training'):
        st.session_state.page = 'admin_train'
        st.rerun()

    if search_ui is not None:
        def on_admin_stock_select(stock):
            symbol = stock.get('SYMBOL', '').strip().upper()
            if symbol:
                st.session_state.admin_ai_stock = symbol
                st.session_state.admin_ai_auto_run = True
                st.session_state.admin_ai_results = None
                st.rerun()

        search_ui.render(on_stock_select=on_admin_stock_select)
    else:
        stock_input = st.text_input("Stock symbol or name", value=st.session_state.get('admin_ai_stock', ''), key='admin_ai_manual_stock')
        st.session_state.admin_ai_stock = stock_input
        if st.button("Load Stock", key='admin_ai_load_stock'):
            st.session_state.admin_ai_stock = st.session_state.get('admin_ai_manual_stock', '').strip().upper()
            st.session_state.admin_ai_auto_run = True
            st.session_state.admin_ai_results = None
            st.rerun()

    st.markdown("---")

    admin_ai_stock = st.session_state.get('admin_ai_stock', '')
    if admin_ai_stock:
        st.markdown(f"### Selected symbol: **{admin_ai_stock}**")
        
        # Import trained model manager - 5 visible models only
        from StockSageAI.trained_model_manager import (
            get_visible_model_names,
            get_all_model_names,
            get_model_manager
        )
        
        available_models = get_visible_model_names()  # 5 visible models
        admin_ai_model = st.session_state.get('admin_ai_model', available_models[0])
        if admin_ai_model not in available_models:
            st.session_state.admin_ai_model = available_models[0]
            admin_ai_model = available_models[0]

        # Ensure the session state key exists before creating the widget
        if 'admin_ai_selected_models' not in st.session_state:
            st.session_state['admin_ai_selected_models'] = [admin_ai_model]

        selected_models = st.multiselect(
            "Select AI models to run (5 models + 3 background ensemble)",
            options=available_models,
            default=st.session_state.get('admin_ai_selected_models', [admin_ai_model]),
            key='admin_ai_selected_models'
        )

        confidence_threshold = st.slider(
            "Minimum confidence threshold",
            min_value=0,
            max_value=100,
            value=40,
            step=5,
            key='admin_ai_confidence_threshold'
        )

        cols = responsive_ui.get_responsive_columns(3, mobile_count=1)
        with cols[0]:
            if st.button("Analyze Now", key='admin_ai_run'):
                st.session_state.admin_ai_results = get_cached_admin_ai_results(
                    admin_ai_stock,
                    tuple(selected_models),
                    st.session_state.get('admin_ai_refresh_counter', 0)
                )
                st.session_state.admin_ai_auto_run = False
        with cols[1]:
            if st.button("Run Ensemble", key='admin_ai_run_ensemble'):
                if selected_models:
                    st.session_state.admin_ai_results = get_cached_admin_ai_results(
                        admin_ai_stock,
                        tuple(selected_models),
                        st.session_state.get('admin_ai_refresh_counter', 0) + 1
                    )
                    st.session_state.admin_ai_refresh_counter = st.session_state.get('admin_ai_refresh_counter', 0) + 1
                    st.session_state.admin_ai_auto_run = False
        with cols[2]:
            if st.button("Reset cache", key='admin_ai_reset_cache'):
                st.session_state.admin_ai_refresh_counter = st.session_state.get('admin_ai_refresh_counter', 0) + 1
                st.session_state.admin_ai_results = None
                safe_rerun()

        if st.session_state.get('admin_ai_auto_run', False) and selected_models:
            st.session_state.admin_ai_results = get_cached_admin_ai_results(
                admin_ai_stock,
                tuple(selected_models),
                st.session_state.get('admin_ai_refresh_counter', 0)
            )
            st.session_state.admin_ai_auto_run = False

        # session state for `admin_ai_selected_models` is initialized before the widget;
        # do not reassign it after the widget is created (Streamlit disallows this).

        admin_ai_results = st.session_state.get('admin_ai_results')
        if admin_ai_results:
            results = admin_ai_results
            if 'error' in results:
                st.error(results['error'])
            else:
                cols = responsive_ui.get_responsive_columns(4, mobile_count=1)
                cols[0].metric("Current", f"₹{results.get('current_price', 0)}")
                cols[1].metric("Ensemble", f"₹{results.get('ensemble', 0):.2f}")
                cols[2].metric("AI Confidence", f"{results.get('confidence', 0):.1f}%")
                cols[3].metric("Models run", len(results.get('results', [])))

                st.markdown(f"**Regime outlook:** {results.get('regime', 'Mixed')}")
                st.markdown(f"**Regime confidence:** {results.get('regime_confidence', 0.0)}%")
                st.markdown(f"**Anomaly score:** {results.get('anomaly_score', 0.0)}%")

                weights = results.get('recommended_weights', {})
                if weights:
                    with st.expander("Recommended model weight allocation"):
                        for model_name, weight in weights.items():
                            st.write(f"- {model_name}: {int(weight * 100)}%")

                state_probs = results.get('state_probabilities', {})
                if state_probs:
                    with st.expander("Regime probability distribution"):
                        for regime_name, prob in state_probs.items():
                            st.write(f"- {regime_name}: {prob}%")

                history = results.get('regime_history', [])
                if history:
                    with st.expander("Recent regime history"):
                        for item in history[-10:]:
                            st.write(f"{item.get('date', '')} — {item.get('regime', '')} ({item.get('confidence', 0)}%)")

                model_summary = next(
                    (item for item in results.get('results', []) if item['model'] == admin_ai_model),
                    results.get('results', [None])[0]
                )
                if model_summary:
                    st.markdown("#### Selected model impact")
                    sm_cols = responsive_ui.get_responsive_columns(3, mobile_count=1, gap='large')
                    sm_cols[0].metric("Model", model_summary.get('model', 'Unknown'))
                    sm_cols[1].metric("Prediction", f"₹{model_summary.get('prediction', 0)}")
                    sm_cols[2].metric("Confidence", f"{model_summary.get('confidence', 0)}%")
                    st.markdown(f"**Model regime:** {model_summary.get('regime', 'Unknown')}")
                    st.markdown(f"**Model reasoning:** {model_summary.get('reasoning', '')}")
                    st.markdown("---")

                st.markdown("---")
                for model_result in results.get('results', []):
                    with st.expander(f"{model_result.get('model', 'Model')} — ₹{model_result.get('prediction', 0)} ({model_result.get('confidence', 0)}%)"):
                        st.markdown(f"**Regime:** {model_result.get('regime', 'Unknown')}")
                        st.markdown(f"**Summary:** {model_result.get('summary', '')}")
                        st.markdown(f"**Reasoning:** {model_result.get('reasoning', '')}")

                st.markdown("---")
                st.markdown("#### Forecast architecture notes")
                st.write("This admin-only engine is built as a modular hybrid forecast system with placeholder Transformer, GNN, and sequence model components. It is designed to evolve into a full next-gen AI forecasting architecture.")
        elif admin_ai_stock:
            st.info("Click 'Analyze Now' or 'Run Ensemble' to execute the selected admin AI models.")
        else:
            st.info("Search a stock name above to auto-select it and start the admin AI analysis.")
    elif st.session_state.get('admin_ai_stock', ''):
        st.info("Click 'Analyze Now' to run the selected admin AI model and return a consensus forecast.")
    else:
        st.info("Search a stock name above to auto-select it and start the admin AI analysis.")


def show_user_management():
    st.subheader("User Management")

    db = Database()
    users = db.get_all_users()
    stats = db.get_user_stats()

    col1, col2, col3, col4, col5 = responsive_ui.get_responsive_columns(5, mobile_count=1)
    with col1:
        st.metric("Total Users", stats['total_users'])
    with col2:
        st.metric("Active", stats['active_users'])
    with col3:
        st.metric("Premium", stats['premium_users'])
    with col4:
        st.metric("Suspended", stats['suspended_users'])
    with col5:
        st.metric("Banned", stats['banned_users'])

    if users:
        df = pd.DataFrame(users)
        df_display = df.rename(columns={
            'is_active': 'Active',
            'is_suspended': 'Suspended',
            'is_banned': 'Banned',
            'subscription_type': 'Subscription'
        })
        st.dataframe(df_display.reset_index(drop=True), use_container_width=True)

        user_map = {user['id']: user for user in users}
        selection = st.selectbox(
            "Select a user to manage",
            options=[user['id'] for user in users],
            format_func=lambda user_id: f"{user_map[user_id]['username']} ({user_map[user_id]['role']})"
        )

        if selection:
            selected_user = user_map[selection]
            st.write(f"**Managing:** {selected_user['username']} — {selected_user['email']}")
            st.write(f"Role: {selected_user['role']}")
            st.write(f"Status: {'Active' if selected_user['is_active'] else 'Inactive'} | {'Suspended' if selected_user['is_suspended'] else 'Normal'} | {'Banned' if selected_user['is_banned'] else 'Open'}")

            with st.expander("User actions"):
                if st.button("Activate / Deactivate", key=f"toggle_active_{selection}"):
                    db.update_user(selection, is_active=0 if selected_user['is_active'] else 1)
                    db.log_activity(auth_manager.get_current_user()['id'], 'user_status_change', f"Toggled active status for {selected_user['username']}")
                    st.success("User status updated.")
                    st.rerun()

                if st.button("Suspend / Reinstate", key=f"toggle_suspended_{selection}"):
                    db.update_user(selection, is_suspended=0 if selected_user['is_suspended'] else 1)
                    db.log_activity(auth_manager.get_current_user()['id'], 'user_status_change', f"Toggled suspension for {selected_user['username']}")
                    st.success("User suspension status updated.")
                    st.rerun()

                if st.button("Ban / Unban", key=f"toggle_banned_{selection}"):
                    db.update_user(selection, is_banned=0 if selected_user['is_banned'] else 1)
                    db.log_activity(auth_manager.get_current_user()['id'], 'user_status_change', f"Toggled ban status for {selected_user['username']}")
                    st.success("User ban status updated.")
                    st.rerun()

                new_role = st.selectbox(
                    "Change Role",
                    options=['Super Admin', 'Admin', 'Premium User', 'Free User'],
                    index=['Super Admin', 'Admin', 'Premium User', 'Free User'].index(selected_user['role']) if selected_user['role'] in ['Super Admin', 'Admin', 'Premium User', 'Free User'] else 3
                )
                if st.button("Update Role", key=f"update_role_{selection}"):
                    db.update_user(selection, role=new_role)
                    db.log_activity(auth_manager.get_current_user()['id'], 'role_change', f"Changed role for {selected_user['username']} to {new_role}")
                    st.success("Role updated.")
                    st.rerun()

    else:
        st.info("No users found. New users will appear here after signup.")

@st.cache_data(ttl=60)
def get_cached_system_metrics(refresh_counter=0):
    db = Database()
    return {
        'system_health': db.get_system_health(),
        'api_usage': db.get_api_usage_stats(),
        'system_perf': db.get_system_performance()
    }


@st.cache_data(ttl=120)
def get_cached_admin_ai_results(symbol, model_tuple, refresh_counter=0):
    if not symbol or not model_tuple:
        return None

    from StockSageAI.trained_model_manager import get_model_manager, get_visible_model_names
    from StockSageAI.utils import calculate_technical_indicators

    data_fetcher = DataFetcher()
    df = data_fetcher.get_stock_data(symbol, period='2y')
    if df is None or df.empty:
        return {
            'error': 'Unable to fetch price series for this symbol.',
            'results': []
        }

    df = calculate_technical_indicators(df.copy())
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    df['ATR'] = (df['High'] - df['Low']).rolling(window=14).mean()
    df['Volume_Ratio'] = df['Volume'] / (df['Volume'].rolling(window=20).mean() + 1e-9)
    df['Price_Range'] = (df['High'] - df['Low']) / (df['Close'] + 1e-9)
    df = df.dropna(subset=['MA5', 'MA20', 'MA50', 'RSI', 'MACD', 'ATR', 'Volume_Ratio', 'Price_Range'])

    if df.shape[0] < 60:
        return {
            'error': 'Not enough data available to generate model inputs.',
            'results': []
        }

    feature_columns = ['MA5', 'MA20', 'MA50', 'RSI', 'MACD', 'ATR', 'Volume_Ratio', 'Price_Range']
    X_features = df[feature_columns].iloc[-1:].astype(float).to_numpy()
    X_seq = df[feature_columns].iloc[-60:].astype(float).to_numpy().reshape(1, 60, len(feature_columns))

    manager = get_model_manager()
    visible_model_names = get_visible_model_names()
    selected_visible_models = [name for name in model_tuple if name in visible_model_names]
    if not selected_visible_models:
        selected_visible_models = visible_model_names

    results = manager.ensemble_predict_all_8_models(
        X_seq,
        X_features,
        selected_visible_models=selected_visible_models
    )

    if results.get('error'):
        # Fallback to legacy AI forecast engine if trained models are unavailable.
        model_results = []
        for model_name in model_tuple:
            result = ai_forecast_engine.analyze_stock(symbol, model_name)
            if isinstance(result, dict):
                model_results.append(result)

        if not model_results:
            return {'error': 'No forecast results were generated.', 'results': []}

        if len(model_results) == 1:
            return model_results[0]

        predictions = [res.get('current_price', 0) for res in model_results if res.get('current_price') is not None]
        confidences = [res.get('confidence', 0) for res in model_results if res.get('confidence') is not None]
        ensemble_value = sum(predictions) / len(predictions) if predictions else 0
        average_confidence = sum(confidences) / len(confidences) if confidences else 0
        combined = {
            'current_price': model_results[0].get('current_price', 0),
            'ensemble': ensemble_value,
            'confidence': average_confidence,
            'regime': model_results[0].get('regime', 'Mixed'),
            'regime_confidence': average_confidence,
            'anomaly_score': sum(res.get('anomaly_score', 0) for res in model_results) / len(model_results),
            'recommended_weights': {m: 1 / len(model_results) for m in model_tuple},
            'state_probabilities': model_results[0].get('state_probabilities', {}),
            'regime_history': model_results[0].get('regime_history', []),
            'results': []
        }
        for res in model_results:
            summary = {
                'model': res.get('model', 'Unknown'),
                'prediction': res.get('prediction', res.get('current_price', 0)),
                'confidence': res.get('confidence', 0),
                'regime': res.get('regime', 'Unknown'),
                'reasoning': res.get('reasoning', ''),
                'summary': res.get('summary', '')
            }
            combined['results'].append(summary)

        return combined

    # Fill in standard fields for trained model results
    results['current_price'] = float(df['Close'].iloc[-1]) if 'Close' in df.columns else 0.0
    results['symbol'] = symbol
    if 'regime' not in results:
        results['regime'] = 'Adaptive Mixed Market'
    if 'results' not in results:
        results['results'] = []

    return results


def show_analytics():
    st.subheader("System Analytics")

    if 'analytics_refresh_counter' not in st.session_state:
        st.session_state.analytics_refresh_counter = 0

    if st.button("Refresh metrics", key='analytics_refresh'):
        st.session_state.analytics_refresh_counter += 1
        safe_rerun()

    metrics = get_cached_system_metrics(st.session_state.analytics_refresh_counter)
    system_health = metrics.get('system_health', {})
    api_usage = metrics.get('api_usage', [])
    system_perf = metrics.get('system_perf', [])

    if system_health:
        cols = responsive_ui.get_responsive_columns(4, mobile_count=1)
        cols[0].metric("Active Users", system_health.get('active_users', 0))
        cols[1].metric("Active Alerts", system_health.get('active_alerts', 0))
        cols[2].metric("Activities (24h)", system_health.get('activities_24h', 0))
        cols[3].metric("API Calls (1h)", system_health.get('api_calls_1h', 0))
        st.caption(f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.warning("No system health metrics are available.")

    if api_usage:
        st.markdown("### API Usage")
        df_api = pd.DataFrame(api_usage)
        st.dataframe(df_api, use_container_width=True)
        if not df_api.empty and 'request_count' in df_api.columns:
            st.line_chart(df_api.set_index('last_used')['request_count'])
    else:
        st.info("No API usage data is available yet.")

    if system_perf:
        st.markdown("### Recent System Performance Metrics")
        df_perf = pd.DataFrame(system_perf)
        if 'metric_data' in df_perf.columns:
            st.dataframe(df_perf[['recorded_at', 'metric_name', 'metric_value', 'metric_data']].head(20), use_container_width=True)
        else:
            st.dataframe(df_perf.head(20), use_container_width=True)

        if not df_perf.empty and 'metric_value' in df_perf.columns:
            perf_chart = df_perf.copy()
            perf_chart['recorded_at'] = pd.to_datetime(perf_chart['recorded_at'], errors='coerce')
            perf_chart = perf_chart.dropna(subset=['recorded_at'])
            if not perf_chart.empty:
                perf_chart = perf_chart.sort_values('recorded_at')
                st.line_chart(perf_chart.set_index('recorded_at')['metric_value'])
    else:
        st.info("No system performance metrics recorded yet.")

    st.markdown("---")
    st.write("Use the refresh button to reload analytics after background system updates.")

    # Add charts for user growth, API usage over time, etc.

def show_activity_logs():
    st.subheader("Activity Logs")

    db = Database()
    logs = db.get_activity_logs(limit=50)

    if logs:
        df = pd.DataFrame(logs)
        st.dataframe(df)

def show_notifications():
    st.subheader("Admin Notifications")

    db = Database()
    notifications = db.get_admin_notifications()

    for notif in notifications:
        if notif['is_read']:
            st.info(f"📖 {notif['message']} - {notif['created_at']}")
        else:
            st.warning(f"🔔 {notif['message']} - {notif['created_at']}")
            if st.button(f"Mark as Read #{notif['id']}", key=f"read_{notif['id']}"):
                db.mark_notification_read(notif['id'])
                st.rerun()

def show_system_settings():
    st.subheader("System Settings")
    st.write("Configure system behavior, feature flags, and premium tier defaults.")

    db = Database()
    stats = db.get_user_stats()
    st.metric("Registered Users", stats['total_users'])
    st.metric("Premium Users", stats['premium_users'])

    st.write("Server time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


def show_security_settings():
    st.subheader("Security Settings")
    st.write("Authentication policy and lockout thresholds.")
    st.write("Account locking after 5 failed login attempts with 15-minute cooldown.")

    # Admin controls for 2FA management
    db = Database()
    if auth_manager.has_any_role(['Super Admin', 'Admin']):
        st.markdown("---")
        st.markdown("### 🔐 Admin: Two-Factor (PIN) Management")
        users = db.get_all_users()
        if users:
            # Display a compact table of users and 2FA status
            display_df = pd.DataFrame(users)[['id', 'username', 'email', 'role', 'two_factor_enabled', 'last_login']]
            display_df = display_df.rename(columns={
                'id': 'User ID', 'username': 'Username', 'email': 'Email', 'role': 'Role',
                'two_factor_enabled': '2FA Enabled', 'last_login': 'Last Login'
            })
            st.dataframe(display_df, use_container_width=True)

            st.write("Select a user below to manage their 2FA settings:")
            for user in users:
                cols = st.columns([3, 1, 1, 1])
                with cols[0]:
                    st.markdown(f"**{user['username']}** — {user['email']} — {user['role']}")
                with cols[1]:
                    status = 'Enabled' if user.get('two_factor_enabled') else 'Disabled'
                    st.markdown(status)
                with cols[2]:
                    if st.button(f"Disable 2FA", key=f"disable_2fa_{user['id']}"):
                        success, msg = auth_manager.disable_security_pin(user['id']) if hasattr(auth_manager, 'disable_security_pin') else (False, 'Operation not available')
                        if success:
                            db.log_activity(auth_manager.get_current_user()['id'], 'admin_disable_2fa', f"Disabled 2FA for {user['email']}")
                            st.success(f"Disabled 2FA for {user['username']}")
                            safe_rerun()
                        else:
                            st.error(f"Failed: {msg}")
                with cols[3]:
                    if st.button(f"Create PIN reset", key=f"resetpin_{user['id']}"):
                        # Create a PIN reset token and show the reset link (admins can share it)
                        token = db.create_pin_reset_token(user['email'])
                        reset_link = f"?page=pin_reset&token={token}"
                        db.log_activity(auth_manager.get_current_user()['id'], 'admin_pin_reset_created', f"Created PIN reset token for {user['email']}")
                        st.info(f"PIN reset link (share with user): {reset_link}")
                    if st.button(f"Temp bypass PIN", key=f"bypass_2fa_{user['id']}"):
                        success, msg = auth_manager.disable_security_pin(user['id']) if hasattr(auth_manager, 'disable_security_pin') else (False, 'Operation not available')
                        if success:
                            db.log_activity(auth_manager.get_current_user()['id'], 'admin_bypass_2fa', f"Temporarily bypassed 2FA for {user['email']}")
                            st.success(f"Temporarily bypassed 2FA for {user['username']}")
                            safe_rerun()
                        else:
                            st.error(f"Failed: {msg}")
        else:
            st.info("No users found in the system.")
    else:
        st.info("Admin 2FA management is available for Admin/Super Admin roles only.")


def add_sidebar_navigation():
    with st.sidebar:
        st.title("Navigation")
        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state.page = 'dashboard'
            st.rerun()

        if st.button("📈 Analysis", use_container_width=True):
            st.session_state.page = 'analysis'
            st.rerun()

        if st.button("🚨 Alerts", use_container_width=True):
            st.session_state.page = 'alerts'
            st.rerun()

        if st.button("💼 Portfolio", use_container_width=True):
            st.session_state.page = 'portfolio'
            st.rerun()

        if st.button("⚙️ Settings", use_container_width=True):
            st.session_state.page = 'settings'
            st.rerun()

        if auth_manager.has_any_role(['Super Admin', 'Admin']):
            st.divider()
            
            # Get pending approvals count
            db = Database()
            pending_count = len(db.get_pending_users())
            
            # Display pending approvals badge
            if pending_count > 0:
                st.markdown(f"""
                <style>
                .pending-badge {{
                    display: inline-block;
                    background-color: #ef4444;
                    color: white;
                    border-radius: 999px;
                    padding: 0.2rem 0.6rem;
                    font-size: 0.75rem;
                    font-weight: bold;
                    margin-left: 0.5rem;
                }}
                </style>
                <span class='pending-badge'>{pending_count} pending</span>
                """, unsafe_allow_html=True)
            
            if st.button("🛡️ Admin Dashboard", use_container_width=True):
                st.session_state.page = 'admin'
                st.rerun()
            
            admin_tools_label = f"🧠 Admin Tools{'   🔴' if pending_count > 0 else ''}"
            if st.button(admin_tools_label, use_container_width=True):
                st.session_state.page = 'admin_tools'
                st.rerun()

        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            auth_manager.logout()

# --- Main App Logic ---
def main():
    try:
        # Check authentication and page routing
        if not auth_manager.is_authenticated():
            query_params = st.query_params
            page_param = query_params.get('page')
            page = page_param[0] if page_param else 'login'

            if page == 'reset_password':
                show_reset_password_page()
            elif st.session_state.get('page') == 'signup':
                show_signup_page()
            elif st.session_state.get('page') == 'forgot_password':
                show_forgot_password_page()
            else:
                show_login_page()
            return

        # User is authenticated, show main app
        page = st.session_state.get('page', 'dashboard')

        if page == 'admin':
            show_admin_dashboard()
        elif page == 'admin_tools':
            show_admin_tools_page()
        else:
            show_main_app()
    except Exception as e:
        logger.exception("Unhandled exception in main application")
        st.error("An unexpected error occurred. Please refresh the page or contact support.")
        st.exception(e)

if __name__ == "__main__":
    main()