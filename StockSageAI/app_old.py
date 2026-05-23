import streamlit as st
import pandas as pd
import numpy as np
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
from data_fetcher import DataFetcher
from lstm_model import LSTMPredictor
from sentiment_analyzer import SentimentAnalyzer
from recommendation_engine import RecommendationEngine
from news_scraper import NewsScraper
from utils import format_currency, get_stock_symbol
from auth import auth_manager
from database import Database

# Page config
st.set_page_config(
    page_title="SP 07 🚀 AI-Powered Stock Forecasting",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Authentication System ---
def show_login_page():
    st.markdown("""
    <style>
    .auth-container {
        max-width: 400px;
        margin: 2rem auto;
        padding: 2rem;
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        box-shadow: 0 8px 32px rgba(31,38,135,0.37);
    }
    .auth-title {
        text-align: center;
        font-size: 2rem;
        font-weight: 700;
        color: #23a6d5;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    st.markdown('<div class="auth-title">🔐 Login to StockSageAI</div>', unsafe_allow_html=True)

    with st.form("login_form"):
        identifier = st.text_input("Email or Username", key="login_identifier")
        password = st.text_input("Password", type="password", key="login_password")
        remember_me = st.checkbox("Remember me", key="remember_me")

        col1, col2 = st.columns(2)
        with col1:
            login_submitted = st.form_submit_button("Login", use_container_width=True)
        with col2:
            signup_page = st.form_submit_button("Sign Up", use_container_width=True)

    if login_submitted:
        if not identifier or not password:
            st.error("Please fill in all fields.")
        else:
            success, message, user_2fa = auth_manager.login(identifier, password, remember_me)
            if success and user_2fa:
                st.session_state.pending_2fa_user = user_2fa
                st.session_state.page = '2fa'
                st.rerun()
            elif success:
                st.success(message)
                st.session_state.page = 'dashboard'
                st.rerun()
            else:
                st.error(message)

    if signup_page:
        st.session_state.page = 'signup'
        st.rerun()

    if st.button("Forgot Password?"):
        st.session_state.page = 'forgot_password'
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

def show_signup_page():
    st.markdown("""
    <style>
    .auth-container {
        max-width: 400px;
        margin: 2rem auto;
        padding: 2rem;
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        box-shadow: 0 8px 32px rgba(31,38,135,0.37);
    }
    .auth-title {
        text-align: center;
        font-size: 2rem;
        font-weight: 700;
        color: #23a6d5;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    st.markdown('<div class="auth-title">📝 Sign Up for StockSageAI</div>', unsafe_allow_html=True)

    with st.form("signup_form"):
        username = st.text_input("Username", key="signup_username")
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm")

        col1, col2 = st.columns(2)
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

def show_2fa_page():
    st.markdown("""
    <style>
    .auth-container {
        max-width: 400px;
        margin: 2rem auto;
        padding: 2rem;
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        box-shadow: 0 8px 32px rgba(31,38,135,0.37);
    }
    .auth-title {
        text-align: center;
        font-size: 2rem;
        font-weight: 700;
        color: #23a6d5;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    st.markdown('<div class="auth-title">🔐 Two-Factor Authentication</div>', unsafe_allow_html=True)

    st.write("Enter the 6-digit code from your authenticator app:")

    with st.form("2fa_form"):
        code = st.text_input("2FA Code", max_chars=6, key="2fa_code")

        col1, col2 = st.columns(2)
        with col1:
            verify_submitted = st.form_submit_button("Verify", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("Cancel", use_container_width=True)

    if verify_submitted:
        if not code:
            st.error("Please enter the 2FA code.")
        else:
            user = st.session_state.get('pending_2fa_user')
            if user:
                success, message = auth_manager.verify_2fa(user, code)
                if success:
                    st.success(message)
                    st.session_state.page = 'dashboard'
                    if 'pending_2fa_user' in st.session_state:
                        del st.session_state.pending_2fa_user
                    st.rerun()
                else:
                    st.error(message)

    if cancel:
        st.session_state.page = 'login'
        if 'pending_2fa_user' in st.session_state:
            del st.session_state.pending_2fa_user
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

def show_forgot_password_page():
    st.markdown("""
    <style>
    .auth-container {
        max-width: 400px;
        margin: 2rem auto;
        padding: 2rem;
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        box-shadow: 0 8px 32px rgba(31,38,135,0.37);
    }
    .auth-title {
        text-align: center;
        font-size: 2rem;
        font-weight: 700;
        color: #23a6d5;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    st.markdown('<div class="auth-title">🔑 Forgot Password</div>', unsafe_allow_html=True)

    with st.form("forgot_form"):
        email = st.text_input("Email", key="forgot_email")

        col1, col2 = st.columns(2)
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

def show_reset_password_page():
    st.markdown("""
    <style>
    .auth-container {
        max-width: 400px;
        margin: 2rem auto;
        padding: 2rem;
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        box-shadow: 0 8px 32px rgba(31,38,135,0.37);
    }
    .auth-title {
        text-align: center;
        font-size: 2rem;
        font-weight: 700;
        color: #23a6d5;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    st.markdown('<div class="auth-title">🔑 Reset Password</div>', unsafe_allow_html=True)

    # Get token from URL params
    query_params = st.query_params
    token = query_params.get('token', '')

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

# --- Main App Logic ---
def main():
    # Check authentication and page routing
    if not auth_manager.is_authenticated():
        query_params = st.query_params
        page = query_params.get('page', 'login')

        if page == 'reset_password':
            show_reset_password_page()
        elif st.session_state.get('page') == 'signup':
            show_signup_page()
        elif st.session_state.get('page') == 'forgot_password':
            show_forgot_password_page()
        elif st.session_state.get('page') == '2fa':
            show_2fa_page()
        else:
            show_login_page()
        return

    # User is authenticated, show main app
    show_main_app()

def show_main_app():
    # --- Modern MNC Fintech UI: Theme Toggle, Header, Layout ---
# Inject CSS for dark/light mode, glassmorphism, fonts, premium dashboard look, and fix all invalid CSS syntax

st.markdown("""
<link href="https://fonts.googleapis.com/css?family=Inter:400,700|Poppins:600,700|Roboto:400,500&display=swap" rel="stylesheet">
<style>
:root {
    --primary: #23a6d5;
    --primary-dark: #1b4f72;
    --secondary: #f5f6fa;
    --secondary-dark: #222831;
    --accent: #4ECDC4;
    --danger: #ff6b6b;
    --success: #4CAF50;
    --card-bg: rgba(255,255,255,0.08);
    --card-bg-dark: rgba(34,40,49,0.7);
    --shadow: 0 8px 32px 0 rgba(31,38,135,0.37);
    --glass: rgba(255,255,255,0.15);
    --border-radius: 18px;
    --font-heading: 'Poppins', 'Inter', sans-serif;
    --font-body: 'Roboto', 'Inter', sans-serif;
    --transition: 0.3s cubic-bezier(.4,0,.2,1);
}
body, .stApp {
    font-family: var(--font-body);
    background: var(--secondary);
    transition: background 0.4s;
}
[data-theme="dark"] body, [data-theme="dark"] .stApp {
    background: var(--secondary-dark);
}
.stApp {
    min-height: 100vh;
    background: linear-gradient(135deg, #FF6B6B, #EE5A52, #23a6d5, #23d5ab);
    background-size: 400% 400%;
    animation: gradientBG 15s ease infinite;
}
@keyframes gradientBG {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
.header-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: var(--glass);
    backdrop-filter: blur(12px);
    box-shadow: var(--shadow);
    border-radius: var(--border-radius);
    padding: 1rem 2rem;
    margin-bottom: 2rem;
    gap: 0;
}
.header-logo {
    font-family: var(--font-heading);
    font-size: 2rem;
    font-weight: 700;
    color: var(--primary);
    letter-spacing: 2px;
    display: flex;
    align-items: center;
}
.header-nav {
    display: flex;
    gap: 2rem;
    align-items: center;
}
.header-nav a {
    font-family: var(--font-heading);
    font-size: 1.1rem;
    color: var(--primary-dark);
    text-decoration: none;
    padding: 0.5rem 1rem;
    border-radius: 12px;
    transition: background var(--transition), color var(--transition);
    text-align: center;
    display: flex;
    align-items: center;
    justify-content: center;
}
.header-nav a:hover, .header-nav a:active {
    background: var(--primary);
    color: #fff;
    box-shadow: 0 2px 8px rgba(35,166,213,0.12);
}
.header-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: var(--primary);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.3rem;
    color: #fff;
    box-shadow: 0 2px 8px rgba(35,166,213,0.15);
    margin-right: 0.5rem;
}
.theme-toggle {
    margin-left: 1.5rem;
    cursor: pointer;
    font-size: 1.3rem;
    color: var(--primary-dark);
    transition: color var(--transition), transform var(--transition);
    display: flex;
    align-items: center;
    justify-content: center;
}
.theme-toggle:hover, .theme-toggle:active {
    color: var(--accent);
    transform: scale(1.1);
}
[data-theme="dark"] .header-bar, [data-theme="dark"] .chart-container, [data-theme="dark"] .metric-card {
    background: var(--card-bg-dark);
    color: #f5f6fa;
}
[data-theme="dark"] .header-logo { color: var(--accent); }
[data-theme="dark"] .header-nav a { color: #f5f6fa; }
[data-theme="dark"] .header-nav a:hover { background: var(--accent); color: #222831; }
[data-theme="dark"] .header-avatar { background: var(--accent); color: #222831; }
.metric-card, .chart-container {
    background: var(--card-bg);
    backdrop-filter: blur(16px);
    border-radius: var(--border-radius);
    box-shadow: var(--shadow);
    padding: 1.5rem;
    margin-bottom: 1.2rem;
    transition: background var(--transition), box-shadow var(--transition), transform var(--transition);
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
}
.metric-card:hover, .chart-container:hover {
    box-shadow: 0 12px 32px 0 rgba(35,166,213,0.18);
    transform: translateY(-2px) scale(1.01);
}
.hero-section {
    text-align: center;
    margin-bottom: 2rem;
}
.hero-title {
    font-family: var(--font-heading);
    font-size: 2.5rem;
    font-weight: 700;
    color: var(--primary);
    margin-bottom: 0.5rem;
}
.hero-tagline {
    font-family: var(--font-body);
    font-size: 1.3rem;
    color: var(--primary-dark);
    margin-bottom: 2rem;
}
.search-bar {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: 2rem;
    gap: 0.5rem;
}
.search-input {
    font-size: 1.1rem;
    padding: 0.7rem 1.2rem;
    border-radius: 12px;
    border: 1px solid var(--primary);
    width: 350px;
    background: var(--glass);
    color: var(--primary-dark);
    transition: border var(--transition);
    text-align: left;
}
.search-input:focus {
    border: 2px solid var(--accent);
    outline: none;
}
.search-btn {
    background: linear-gradient(90deg, var(--primary), var(--accent));
    color: #fff;
    border: none;
    border-radius: 12px;
    padding: 0.7rem 1.5rem;
    font-size: 1.1rem;
    font-family: var(--font-heading);
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(35,166,213,0.12);
    transition: background var(--transition), transform var(--transition);
    text-align: center;
    display: flex;
    align-items: center;
    justify-content: center;
}
.search-btn:hover, .search-btn:active {
    background: linear-gradient(90deg, var(--accent), var(--primary));
    transform: scale(1.04);
}
.price-ticker {
    background: var(--glass);
    border-radius: 12px;
    padding: 0.7rem 1.2rem;
    font-family: var(--font-heading);
    font-size: 1.1rem;
    color: var(--primary-dark);
    margin-bottom: 1.2rem;
    box-shadow: 0 2px 8px rgba(35,166,213,0.08);
    display: flex;
    gap: 2rem;
    justify-content: center;
    align-items: center;
    overflow-x: auto;
    white-space: nowrap;
}
@keyframes tickerMove {
    0% { transform: translateX(0); }
    100% { transform: translateX(-10%); }
}
.price-alert-section {
    background: var(--glass);
    border-radius: var(--border-radius);
    padding: 1.2rem;
    margin-bottom: 1.2rem;
    box-shadow: var(--shadow);
    display: flex;
    align-items: center;
    gap: 1.5rem;
}
.price-alert-toggle {
    width: 50px;
    height: 28px;
    background: var(--primary);
    border-radius: 14px;
    position: relative;
    cursor: pointer;
    transition: background var(--transition);
    display: flex;
    align-items: center;
}
.price-alert-toggle.active {
    background: var(--accent);
}
.price-alert-toggle .circle {
    position: absolute;
    top: 3px;
    left: 3px;
    width: 22px;
    height: 22px;
    background: #fff;
    border-radius: 50%;
    transition: left var(--transition);
}
.price-alert-toggle.active .circle {
    left: 25px;
}
.price-alert-input {
    font-size: 1rem;
    padding: 0.5rem 1rem;
    border-radius: 10px;
    border: 1px solid var(--primary);
    width: 120px;
    background: var(--glass);
    color: var(--primary-dark);
    text-align: center;
}
.price-alert-btn {
    background: linear-gradient(90deg, var(--primary), var(--accent));
    color: #fff;
    border: none;
    border-radius: 10px;
    padding: 0.5rem 1.2rem;
    font-size: 1rem;
    font-family: var(--font-heading);
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(35,166,213,0.10);
    transition: background var(--transition), transform var(--transition);
    text-align: center;
    display: flex;
    align-items: center;
    justify-content: center;
}
.price-alert-btn:hover, .price-alert-btn:active {
    background: linear-gradient(90deg, var(--accent), var(--primary));
    transform: scale(1.04);
}
.grid-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 2rem;
    align-items: stretch;
    margin-bottom: 2rem;
}
.grid-col {
    display: flex;
    flex-direction: column;
    gap: 1.2rem;
}
@media (max-width: 900px) {
    .header-bar { flex-direction: column; gap: 1rem; }
    .header-nav { gap: 1rem; }
    .hero-title { font-size: 2rem; }
    .search-bar { flex-direction: column; gap: 1rem; }
    .search-input { width: 100%; }
    .grid-row { grid-template-columns: 1fr; gap: 1rem; }
}
@media (max-width: 600px) {
    .header-bar { padding: 1rem; }
    .header-logo { font-size: 1.3rem; }
    .header-avatar { width: 32px; height: 32px; font-size: 1rem; }
    .metric-card, .chart-container { padding: 1rem; }
    .grid-row { grid-template-columns: 1fr; gap: 0.5rem; }
}
</style>
""", unsafe_allow_html=True)

# --- Theme toggle logic ---
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

def toggle_theme():
    st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'

# Add a button to toggle the theme
if st.button("🌓 Toggle Theme", key="theme_toggle_btn"):
    toggle_theme()

# Apply the theme dynamically
theme = st.session_state.theme
st.markdown(f"""
<script>
document.body.setAttribute('data-theme', '{theme}');
window.addEventListener('DOMContentLoaded', function() {{
    document.body.setAttribute('data-theme', '{theme}');
}});
</script>
""", unsafe_allow_html=True)

# Header with theme toggle
st.markdown(
    f"""
    <div class="header-bar">
        <div class="header-logo">🚀 SP 07</div>
        <nav class="header-nav">
            <a href="#">Dashboard</a>
            <a href="#">Analysis</a>
            <a href="#">Alerts</a>
            <a href="#">Portfolio</a>
            <a href="#">Settings</a>
        </nav>
        <div style="display: flex; align-items: center;">
            <div class="header-avatar">👤</div>
            <span class="theme-toggle" onclick="window.dispatchEvent(new Event('toggle-theme'));">🌓</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Hero Section ---
st.markdown("""
<div class="hero-section">
    <div class="hero-title">SP 07 Stock Forecasting</div>
    <div class="hero-tagline">AI-Powered Market Predictions</div>
</div>
""", unsafe_allow_html=True)

# --- Real-time Stock Price Ticker (Yahoo Finance, auto-refresh, sliding animation) ---
def fetch_ticker_data(symbols):
    data = []
    for sym in symbols:
        try:
            info = yf.Ticker(sym).info
            price = info.get('regularMarketPrice', np.nan)
            change = info.get('regularMarketChangePercent', 0)
            data.append((sym, price, change))
        except Exception:
            data.append((sym, np.nan, 0))
    return data

ticker_symbols = ["^NSEI", "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
if 'ticker_data' not in st.session_state or st.session_state.get('ticker_last_update', 0) + 10 < int(datetime.now().timestamp()):
    st.session_state.ticker_data = fetch_ticker_data(ticker_symbols)
    st.session_state.ticker_last_update = int(datetime.now().timestamp())

ticker_html = "".join([
    f"<span style='margin-right:2.5rem;'><strong>{sym.replace('.NS','').replace('^NSEI','NIFTY50')}</strong>: ₹{price:,.2f} <span style='color:{'green' if chg>=0 else 'red'}'>{chg:+.2f}%</span></span>"
    for sym, price, chg in st.session_state.ticker_data
])

# Add a continuously sliding (rotating) ticker using CSS and HTML
st.markdown("""
<style>
.ticker-container {
    width: 100%;
    overflow: hidden;
    position: relative;
    height: 2.5em;
    background: rgba(255,255,255,0.15);
    border-radius: 12px;
    margin-bottom: 1.2rem;
}
.ticker-slide {
    display: inline-block;
    white-space: nowrap;
    animation: ticker-move 30s linear infinite;
    font-size: 1.1rem;
    /* Make the slide much wider than the container for smooth looping */
    min-width: 200%;
    box-sizing: content-box;
}
@keyframes ticker-move {
    0% { transform: translateX(0);}
    100% { transform: translateX(-50%);}
}
</style>
<div class="ticker-container">
    <div class="ticker-slide">
        """ + ticker_html + ticker_html + """
    </div>
</div>
""", unsafe_allow_html=True)

# --- Price Alert System (Real Data, Background Thread, In-App Notification, Email) ---
if 'alerts' not in st.session_state:
    st.session_state.alerts = []
if 'alert_triggered' not in st.session_state:
    st.session_state.alert_triggered = []

def send_email_alert(stock, price, target, alert_type, user_email):
    subject = f"SP 07 Stock Alert: {stock} {'above' if alert_type=='Above' else 'below'} ₹{target}"
    body = f"Stock {stock} is now at ₹{price:.2f}, which is {'above' if alert_type=='Above' else 'below'} your target of ₹{target:.2f}."
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = "sp07alerts@example.com"
    msg['To'] = user_email
    try:
        # Configure SMTP below (use your credentials)
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        smtp_user = "your_email@gmail.com"
        smtp_pass = "your_password"
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, [user_email], msg.as_string())
        server.quit()
        return True
    except Exception:
        return False

def get_stock_price(symbol):
    try:
        info = yf.Ticker(symbol).info
        return info.get('regularMarketPrice', np.nan)
    except Exception:
        return np.nan

def check_alerts_bg():
    while True:
        for alert in st.session_state.alerts:
            if not alert["active"]:
                continue
            price = get_stock_price(alert["symbol"])
            if np.isnan(price):
                alert["last_status"] = "Error fetching price"
                continue
            triggered = False
            if alert["type"] == "Above" and price > alert["target"]:
                triggered = True
            elif alert["type"] == "Below" and price < alert["target"]:
                triggered = True
            if triggered:
                alert["last_status"] = f"Triggered at ₹{price:.2f}"
                alert["active"] = False
                # In-app notification
                st.session_state.alert_triggered.append({
                    "symbol": alert["symbol"],
                    "price": price,
                    "target": alert["target"],
                    "type": alert["type"]
                })
                # Email notification
                send_email_alert(alert["symbol"], price, alert["target"], alert["type"], alert["email"])
            else:
                alert["last_status"] = f"Current: ₹{price:.2f}"
        time.sleep(12)

# Start background thread for alerts (only once)
if 'alert_thread_started' not in st.session_state:
    alert_thread = threading.Thread(target=check_alerts_bg, daemon=True)
    alert_thread.start()
    st.session_state.alert_thread_started = True

st.markdown('<div class="chart-container"><h3>🔔 Real-Time Stock Price Alerts</h3></div>', unsafe_allow_html=True)
with st.form("alert_form"):
    col1, col2, col3, col4 = st.columns([2,2,2,3])
    with col1:
        alert_symbol = st.selectbox("Stock Symbol", ticker_symbols, key="alert_symbol")
    with col2:
        alert_price = st.number_input("Target Price (₹)", min_value=0.0, step=0.01, key="alert_price")
    with col3:
        alert_type = st.selectbox("Alert Type", ["Above", "Below"], key="alert_type")
    with col4:
        user_email = st.text_input("Email for Alert", key="alert_email")
    submitted = st.form_submit_button("Set Alert")
    if submitted and alert_symbol and alert_price and alert_type and user_email:
        st.session_state.alerts.append({
            "symbol": alert_symbol,
            "target": alert_price,
            "type": alert_type,
            "email": user_email,
            "active": True,
            "last_status": "Pending"
        })
        st.success("Alert set successfully!")

# --- Alerts Table & Management ---
st.markdown('<div class="chart-container"><h4>Active Alerts</h4>', unsafe_allow_html=True)
if st.session_state.alerts:
    df_alerts = pd.DataFrame([
        {
            "Stock": a["symbol"].replace('.NS','').replace('^NSEI','NIFTY50'),
            "Target Price": f"₹{a['target']:.2f}",
            "Type": a["type"],
            "Status": a["last_status"],
            "Email": a["email"],
            "Delete": i
        }
        for i, a in enumerate(st.session_state.alerts)
    ])
    st.dataframe(df_alerts[["Stock", "Target Price", "Type", "Status", "Email"]], use_container_width=True)
    for i, a in enumerate(st.session_state.alerts):
        if st.button(f"Delete Alert {i+1}", key=f"delete_alert_{i}"):
            st.session_state.alerts[i]["active"] = False
            st.session_state.alerts[i]["last_status"] = "Deleted"
            st.success("Alert deleted.")
else:
    st.info("No active alerts.")
st.markdown('</div>', unsafe_allow_html=True)

# --- In-app notification for triggered alerts ---
if 'alert_triggered' in st.session_state and st.session_state.alert_triggered:
    for alert in st.session_state.alert_triggered:
        st.toast(
            f"Alert Triggered: {alert['symbol'].replace('.NS','').replace('^NSEI','NIFTY50')} is now at ₹{alert['price']:.2f} ({alert['type']} {alert['target']:.2f})",
            icon="🔔"
        )
    st.session_state.alert_triggered.clear()

# --- Hero Section ---
st.markdown("""
<div class="hero-section">
    <div class="hero-title">SP 07 Stock Forecasting</div>
    <div class="hero-tagline">AI-Powered Market Predictions</div>
</div>
""", unsafe_allow_html=True)





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

# Initialize session states
if 'page' not in st.session_state:
    st.session_state.page = "Home"
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False

# Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select a Page", ["Home", "Stock Analysis", "Market Overview"])
st.session_state.page = page

if page == "Home":
    # Enhanced Welcome screen with beautiful styling
    st.markdown('''
    <div class="chart-container">
        <h2>🎯 Welcome to SP 07 AI-Powered Stock Forecasting!</h2>
        <p style="font-size: 1.2rem; color: #666; text-align: center; margin-bottom: 2rem;">
            Harness the power of advanced AI to forecast Indian stock prices with realistic predictions and intelligent recommendations.
        </p>
        
        
    ''', unsafe_allow_html=True)

elif page == "Stock Analysis":
    # Stock Analysis Parameters
    st.sidebar.header("📊 Stock Analysis Parameters")
    
    # Stock symbol input
    company_input = st.sidebar.text_input(
        "Enter Company Symbol or Name",
        placeholder="e.g., TCS, RELIANCE, INFY, TCS.NS",
        help="Enter NSE stock symbol or company name"
    )

    # Analysis button
    analyze_button = st.sidebar.button("🔍 Analyze Stock", type="primary")

    # Track recently viewed stocks in session state
    if 'recently_viewed' not in st.session_state:
        st.session_state.recently_viewed = []

    if analyze_button and company_input:
        try:
            # Show progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Initialize components
            data_fetcher = DataFetcher()
            lstm_predictor = LSTMPredictor()  # Remove extra arguments
            sentiment_analyzer = SentimentAnalyzer()
            news_scraper = NewsScraper()
            recommendation_engine = RecommendationEngine()
            
            # Step 1: Get stock symbol
            status_text.text("🔍 Validating stock symbol...")
            progress_bar.progress(10)
            
            stock_symbol = get_stock_symbol(company_input)
            
            # Show the symbol being used
            st.info(f"📊 Analyzing: **{stock_symbol}**")
            
            # Step 2: Fetch stock data
            status_text.text("📈 Fetching historical stock data...")
            progress_bar.progress(25)
            
            stock_data = data_fetcher.get_stock_data(stock_symbol)
            if stock_data.empty:
                st.error(f"❌ Could not fetch data for {stock_symbol}")
                st.stop()

            # --- Use full year data for analysis ---
            one_year_ago = stock_data.index[-1] - pd.DateOffset(years=1)
            if len(stock_data) > 0:
                stock_data_year = stock_data[stock_data.index >= one_year_ago]
                if len(stock_data_year) >= 60:  # at least 60 days for LSTM
                    stock_data = stock_data_year

            # Get predictions for all durations (now more robust)
            status_text.text("🧠 Training advanced ML model and generating predictions...")
            progress_bar.progress(50)
            
            forecast_periods = [7, 14, 30]
            all_predictions = {}
            for days in forecast_periods:
                predictions = lstm_predictor.predict(stock_data, days)
                all_predictions[days] = predictions

            predictions = all_predictions[14]  # Default to 14-day prediction
            forecast_days = 14

            # --- Candlestick pattern analysis ---
            def analyze_candlestick_patterns(df):
                # Simple bullish/bearish engulfing detection for last 30 days
                patterns = []
                for i in range(1, min(30, len(df))):
                    prev = df.iloc[-i-1]
                    curr = df.iloc[-i]
                    # Bullish engulfing
                    if curr['Close'] > curr['Open'] and prev['Close'] < prev['Open'] and curr['Open'] < prev['Close'] and curr['Close'] > prev['Open']:
                        patterns.append(('Bullish Engulfing', df.index[-i]))
                    # Bearish engulfing
                    if curr['Close'] < curr['Open'] and prev['Close'] > prev['Open'] and curr['Open'] > prev['Close'] and curr['Close'] < prev['Open']:
                        patterns.append(('Bearish Engulfing', df.index[-i]))
                return patterns

            candlestick_patterns = analyze_candlestick_patterns(stock_data)

            # Step 4: Fetch and analyze news
            status_text.text("📰 Fetching and analyzing news sentiment...")
            progress_bar.progress(75)
            
            company_name = stock_symbol.replace('.NS', '')
            news_headlines = news_scraper.get_news(company_name)
            sentiment_scores = sentiment_analyzer.analyze_sentiment(news_headlines)
            
            # Step 5: Generate recommendation
            status_text.text("🎯 Generating advanced investment recommendation...")
            progress_bar.progress(90)
            # Fix: Remove unsupported keyword arguments from recommendation_engine
            recommendation = recommendation_engine.generate_recommendation(
                stock_data,
                predictions,
                sentiment_scores,
                forecast_days
            )

            # Store results in session state
            st.session_state.stock_symbol = stock_symbol
            st.session_state.stock_data = stock_data
            st.session_state.predictions = predictions
            st.session_state.all_predictions = all_predictions
            st.session_state.forecast_periods = forecast_periods
            st.session_state.sentiment_scores = sentiment_scores
            st.session_state.recommendation = recommendation
            st.session_state.news_headlines = news_headlines
            st.session_state.forecast_days = forecast_days
            st.session_state.candlestick_patterns = candlestick_patterns
            st.session_state.analysis_complete = True
            
            progress_bar.progress(100)
            status_text.text("✅ Analysis complete!")
            
        except Exception as e:
            st.error(f"❌ Error during analysis: {str(e)}")
            st.stop()

    # Display results if analysis is complete
    if st.session_state.analysis_complete:
        # Get data from session state
        stock_data = st.session_state.stock_data
        predictions = st.session_state.predictions
        sentiment_scores = st.session_state.sentiment_scores
        recommendation = st.session_state.recommendation
        news_headlines = st.session_state.news_headlines
        forecast_days = st.session_state.forecast_days
        stock_symbol = st.session_state.stock_symbol
        
        # Calculate current and predicted prices first
        current_price = stock_data['Close'].iloc[-1]
        predicted_price = predictions[-1]
        price_change = predicted_price - current_price
        price_change_pct = (price_change / current_price) * 100

        # Main content area
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.subheader(f"📈 {stock_symbol} - Price Forecast")
            
            # Create price chart
            fig_price = go.Figure()
            
            # Historical data
            fig_price.add_trace(go.Scatter(
                x=stock_data.index,
                y=stock_data['Close'],
                mode='lines',
                name='Historical Price',
                line=dict(color='blue', width=2)
            ))
            
            # Predictions
            future_dates = pd.date_range(
                start=stock_data.index[-1] + timedelta(days=1),
                periods=forecast_days,
                freq='D'
            )
            
            fig_price.add_trace(go.Scatter(
                x=future_dates,
                y=predictions,
                mode='lines+markers',
                name='Forecasted Price',
                line=dict(color='red', width=2, dash='dash'),
                marker=dict(size=6)
            ))
            
            fig_price.update_layout(
                title=f"{stock_symbol} - Historical vs Forecasted Prices",
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
        
        with col1:
            # Add Investment Calculator
            st.markdown('''
            <div class="chart-container">
                <h3>💰 Investment Calculator</h3>
            ''', unsafe_allow_html=True)
            
            # Store previous values in session state
            if 'calc_quantity' not in st.session_state:
                st.session_state.calc_quantity = 100
            if 'calc_purchase_price' not in st.session_state:
                st.session_state.calc_purchase_price = current_price
            if 'calc_target_price' not in st.session_state:
                st.session_state.calc_target_price = predicted_price
            
            # Create three columns for calculator inputs
            calc_col1, calc_col2, calc_col3 = st.columns(3)
            
            with calc_col1:
                quantity = st.number_input("Quantity (No. of Shares)", 
                                         min_value=1, 
                                         value=int(st.session_state.calc_quantity),
                                         step=1,
                                         key='quantity_input')
                st.session_state.calc_quantity = quantity
                
            with calc_col2:
                purchase_price = st.number_input("Purchase Price (₹)", 
                                               min_value=0.01, 
                                               value=float(st.session_state.calc_purchase_price),
                                               format="%.2f",
                                               key='purchase_price_input')
                st.session_state.calc_purchase_price = purchase_price
                
            with calc_col3:
                target_price = st.number_input("Target Selling Price (₹)", 
                                             min_value=0.01,
                                             value=float(st.session_state.calc_target_price),
                                             format="%.2f",
                                             key='target_price_input')
                st.session_state.calc_target_price = target_price
            
            # Calculate investment metrics
            try:
                total_investment = quantity * purchase_price
                estimated_return = quantity * target_price
                profit_loss = estimated_return - total_investment
                profit_loss_percent = (profit_loss / total_investment) * 100 if total_investment > 0 else 0
                
                # Display results in a formatted way
                st.markdown(f'''
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-top: 1rem;">
                    <div class="metric-card" style="margin: 0;">
                        <h4>📈 Investment Summary</h4>
                        <p><strong>Total Investment:</strong> {format_currency(total_investment)}</p>
                        <p><strong>Est. Market Value:</strong> {format_currency(estimated_return)}</p>
                    </div>
                    <div class="metric-card" style="margin: 0; background: {'#e8f5e9' if profit_loss >= 0 else '#ffebee'};">
                        <h4>💵 Profit/Loss Analysis</h4>
                        <p style="color: {'green' if profit_loss >= 0 else 'red'};">
                            <strong>P/L Amount:</strong> {format_currency(abs(profit_loss))} 
                            ({'+' if profit_loss >= 0 else '-'})
                        </p>
                        <p style="color: {'green' if profit_loss >= 0 else 'red'};">
                            <strong>P/L Percent:</strong> {profit_loss_percent:+.2f}%
                        </p>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
                
                # Add realtime verification of data
                last_updated = datetime.now().strftime("%I:%M:%S %p")
                st.markdown(f'''
                <div style="text-align: right; margin-top: 0.5rem; font-size: 0.8rem; color: #666;">
                    Last Updated: {last_updated} | Market Price: {format_currency(current_price)} | 
                    Predicted: {format_currency(predicted_price)} ({price_change_pct:+.2f}%)
                </div>
                ''', unsafe_allow_html=True)
            
            except Exception as e:
                st.error(f"Error in calculations: {str(e)}")
            
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            # Enhanced current price info with styled cards
            current_price = stock_data['Close'].iloc[-1]
            predicted_price = predictions[-1]
            price_change = predicted_price - current_price
            price_change_pct = (price_change / current_price) * 100

            st.markdown(f'''
            <div class="metric-card">
                <h4>💰 Current Price</h4>
                <h2>{format_currency(current_price)}</h2>
                <p>Live market price</p>
            </div>
            ''', unsafe_allow_html=True)

            # --- Practical Predicted Prices for 7, 14, 30 days ---
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown("###🔮Predicted Prices")
            practical_limits = {7: 0.10, 14: 0.15, 30: 0.25}
            for days in [7, 14, 30]:
                pred = st.session_state.all_predictions.get(days)
                if pred is not None and isinstance(pred, (list, np.ndarray)) and len(pred) > 0:
                    raw_pred_price = pred[-1]
                    raw_change_pct = ((raw_pred_price - current_price) / current_price)
                    limit = practical_limits[days]
                    practical_change_pct = np.clip(raw_change_pct, -limit, limit)
                    practical_pred_price = current_price * (1 + practical_change_pct)
                    year_trend = "Uptrend" if stock_data['Close'][-1] > stock_data['Close'][0] else "Downtrend"
                    
                    # Realism check: If predicted change is within ±limit and matches year trend, mark as realistic
                    is_realistic = abs(practical_change_pct) <= limit
                    # If year trend is up but prediction is negative, or year trend is down but prediction is positive, mark as less realistic
                    if (year_trend == "Uptrend" and practical_change_pct < 0) or (year_trend == "Downtrend" and practical_change_pct > 0):
                        is_realistic = False

                    realism_msg = "✅ Realistic" if is_realistic else "⚠️ May not be realistic"
                    
                    st.markdown(f"""
                        <div class="metric-card">
                            <h4>Predicted Price ({days} days)</h4>
                            <h2>{format_currency(practical_pred_price)}</h2>
                            <p style="color: {'green' if practical_change_pct >= 0 else 'red'}">
                                {practical_change_pct*100:+.2f}% expected change
                            </p>
                            <p><strong>Year Trend:</strong> {year_trend}</p>
                            <p><strong>{realism_msg}</strong></p>
                        </div>
                    """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # --- Candlestick pattern analysis display ---
            if st.session_state.candlestick_patterns:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                st.markdown("### 🕯️Recent Candlestick Patterns (last 30 days)")
                for pattern, date in st.session_state.candlestick_patterns:
                    st.markdown(f"- **{pattern}** on {date.strftime('%Y-%m-%d')}")
                st.markdown('</div>', unsafe_allow_html=True)

        with col3:
            # Enhanced recommendation card with animations
            rec_color = {
                'BUY': 'green',
                'SELL': 'red',
                'HOLD': 'orange'
            }
            rec_emoji = {
                'BUY': '🟢',
                'SELL': '🔴',
                'HOLD': '🟡'
            }

            # --- Recommendation based only on prediction result ---
            # Use practical predicted price change for 14 days
            pred_14 = st.session_state.all_predictions.get(14)
            rec_action = "HOLD"
            rec_reason = ""
            rec_confidence = 80.0

            if pred_14 is not None and isinstance(pred_14, (list, np.ndarray)) and len(pred_14) > 0:
                raw_pred_price = pred_14[-1]
                raw_change_pct = ((raw_pred_price - current_price) / current_price)
                practical_change_pct = np.clip(raw_change_pct, -0.15, 0.15)
                if practical_change_pct > 0.03:
                    rec_action = "BUY"
                    rec_reason = "Predicted price shows a clear upward movement over the next 14 days."
                    rec_confidence = 90.0
                elif practical_change_pct < -0.03:
                    rec_action = "SELL"
                    rec_reason = "Predicted price shows a clear downward movement over the next 14 days."
                    rec_confidence = 90.0
                else:
                    rec_action = "HOLD"
                    rec_reason = "Predicted price change is minor; holding is recommended."
                    rec_confidence = 80.0

            rec_class = f"recommendation-{rec_action.lower()}"

            st.markdown(f'''
            <div class="{rec_class}">
                <h2>{rec_emoji[rec_action]} {rec_action}</h2>
                <h3>Confidence: {rec_confidence:.1f}%</h3>
                <p>{rec_reason}</p>
            </div>
            ''', unsafe_allow_html=True)

        # Second row - Sentiment analysis and details
        st.markdown("---")
        
        col4, col5 = st.columns([1, 1])
        
        with col4:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
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
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col5:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.subheader("📊 Analysis Details")
            
            # Technical indicators
            volatility = stock_data['Close'].pct_change().std() * np.sqrt(252) * 100
            
            st.markdown(f"""
            **Technical Analysis:**
            - **Volatility (Annual):** {volatility:.2f}%
            - **52-Week High:** ₹{stock_data['Close'].max():.2f}
            - **52-Week Low:** ₹{stock_data['Close'].min():.2f}
            - **Current Position:** {((current_price - stock_data['Close'].min()) / (stock_data['Close'].max() - stock_data['Close'].min()) * 100):.1f}% of range
            
            **Prediction Details:**
            - **Model Type:** LSTM Neural Network
            - **Training Period:** {len(stock_data)} days
            - **Forecast Horizon:** {forecast_days} days
            - **Expected Return:** {price_change_pct:.2f}%
            """)
            st.markdown('</div>', unsafe_allow_html=True)
        
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
        
        # Enhanced Risk disclaimer and credits
        st.markdown("---")
        st.markdown('''
        <div class="chart-container">
            <h3>⚠️ Risk Disclaimer & Credits</h3>
            <p><strong>Important Notice:</strong> This tool provides AI-generated predictions for educational purposes only. Stock market investments carry significant risk, and past performance does not guarantee future results. Always consult with qualified financial advisors before making investment decisions.</p>
            
           
        ''', unsafe_allow_html=True)

elif page == "Market Overview":
    st.header("📈 Market Overview")

    # --- Budget Filter ---
    st.sidebar.subheader("💸 Budget Filter")
    min_budget = st.sidebar.number_input("Min Price (₹)", min_value=0, value=0, step=1)
    max_budget = st.sidebar.number_input("Max Price (₹)", min_value=0, value=100000, step=1)

    # --- Helper: Get a large list of NSE/BSE symbols ---
    @st.cache_data(ttl=3600)
    def get_all_symbols():
        # For demo: combine popular NSE and BSE stocks
        nse_symbols = [
            "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
            "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
            "WIPRO.NS", "HCLTECH.NS", "ADANIENT.NS", "SUNPHARMA.NS", "TATAMOTORS.NS",
            "LT.NS", "AXISBANK.NS", "MARUTI.NS", "ULTRACEMCO.NS", "TITAN.NS",
            "BAJFINANCE.NS", "ASIANPAINT.NS", "NESTLEIND.NS", "POWERGRID.NS"
        ]
        bse_symbols = [
            "RELIANCE.BO", "TCS.BO", "HDFCBANK.BO", "INFY.BO", "ICICIBANK.BO",
            "HINDUNILVR.BO", "ITC.BO", "SBIN.BO", "BHARTIARTL.BO", "KOTAKBANK.BO",
            "WIPRO.BO", "HCLTECH.BO", "ADANIENT.BO", "SUNPHARMA.BO", "TATAMOTORS.BO",
            "LT.BO", "AXISBANK.BO", "MARUTI.BO", "ULTRACEMCO.BO", "TITAN.BO",
            "BAJFINANCE.BO", "ASIANPAINT.BO", "NESTLEIND.BO", "POWERGRID.BO"
        ]
        return nse_symbols + bse_symbols

    @st.cache_data(ttl=600)
    def fetch_stocks_data(symbols):
        data = []
        for symbol in symbols:
            try:
                stock = yf.Ticker(symbol)
                info = stock.info
                price = info.get('regularMarketPrice', np.nan)
                change = info.get('regularMarketChangePercent', np.nan)
                day_high = info.get('dayHigh', np.nan)
                day_low = info.get('dayLow', np.nan)
                volume = info.get('volume', np.nan)
                data.append({
                    'Symbol': symbol,
                    'Price': price,
                    'Change %': change,
                    'Day High': day_high,
                    'Day Low': day_low,
                    'Volume': volume
                })
            except Exception:
                continue
        return pd.DataFrame(data)

    symbols = get_all_symbols()
    with st.spinner('Fetching market data...'):
        all_stocks_df = fetch_stocks_data(symbols)

    # --- Budget Filtered Stocks ---
    st.markdown('<div class="chart-container"><h3>🔎 Stocks Within Your Budget</h3>', unsafe_allow_html=True)
    if not all_stocks_df.empty and 'Price' in all_stocks_df.columns:
        budget_df = all_stocks_df[
            (all_stocks_df['Price'].notnull()) &
            (all_stocks_df['Price'] >= min_budget) &
            (all_stocks_df['Price'] <= max_budget)
        ].copy()
        if not budget_df.empty:
            for col in ['Price', 'Day High', 'Day Low']:
                budget_df[col] = budget_df[col].apply(lambda x: f"₹{x:,.2f}" if pd.notnull(x) else "N/A")
            budget_df['Change %'] = budget_df['Change %'].apply(lambda x: f"{x:+.2f}%" if pd.notnull(x) else "N/A")
            budget_df['Volume'] = budget_df['Volume'].apply(lambda x: f"{int(x):,}" if pd.notnull(x) else "N/A")
            st.dataframe(budget_df[['Symbol', 'Price', 'Change %', 'Day High', 'Day Low', 'Volume']], use_container_width=True)
        else:
            st.info("No stocks found in this price range.")
    else:
        st.error("No stock data available or 'Price' column missing.")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Top Gainers/Losers from all NSE/BSE stocks ---
    def get_top_movers(df, top=True, n=20):
        df = df[df['Change %'].notnull()]
        return df.sort_values('Change %', ascending=not top).head(n)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.subheader("📈 Top 20 Gainers (NSE/BSE)")
        if not all_stocks_df.empty and 'Change %' in all_stocks_df.columns:
            gainers_df = get_top_movers(all_stocks_df, top=True, n=20)
            for col in ['Price', 'Day High', 'Day Low']:
                gainers_df[col] = gainers_df[col].apply(lambda x: f"₹{x:,.2f}" if pd.notnull(x) else "N/A")
            gainers_df['Change %'] = gainers_df['Change %'].apply(lambda x: f"+{x:.2f}%" if pd.notnull(x) else "N/A")
            gainers_df['Volume'] = gainers_df['Volume'].apply(lambda x: f"{int(x):,}" if pd.notnull(x) else "N/A")
            st.dataframe(gainers_df[['Symbol', 'Price', 'Change %', 'Day High', 'Day Low', 'Volume']], use_container_width=True)
        else:
            st.info("Unable to fetch gainers data")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.subheader("📉 Top 20 Losers (NSE/BSE)")
        if not all_stocks_df.empty and 'Change %' in all_stocks_df.columns:
            losers_df = get_top_movers(all_stocks_df, top=False, n=20)
            for col in ['Price', 'Day High', 'Day Low']:
                losers_df[col] = losers_df[col].apply(lambda x: f"₹{x:,.2f}" if pd.notnull(x) else "N/A")
            losers_df['Change %'] = losers_df['Change %'].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else "N/A")
            losers_df['Volume'] = losers_df['Volume'].apply(lambda x: f"{int(x):,}" if pd.notnull(x) else "N/A")
            st.dataframe(losers_df[['Symbol', 'Price', 'Change %', 'Day High', 'Day Low', 'Volume']], use_container_width=True)
        else:
            st.info("Unable to fetch losers data")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Market Statistics ---
    st.markdown('<div class="chart-container"><h3>📊 Market Statistics</h3>', unsafe_allow_html=True)
    if not all_stocks_df.empty and 'Price' in all_stocks_df.columns and 'Change %' in all_stocks_df.columns and 'Volume' in all_stocks_df.columns:
        valid_prices = all_stocks_df['Price'].dropna()
        valid_changes = all_stocks_df['Change %'].dropna()
        valid_volumes = all_stocks_df['Volume'].dropna()
        if not valid_prices.empty and not valid_changes.empty and not valid_volumes.empty:
            avg_price = valid_prices.mean()
            avg_change = valid_changes.mean()
            total_volume = valid_volumes.sum()
            stats_html = (
                f"- **Average Price:** ₹{avg_price:,.2f}\n"
                f"- **Average Change %:** {avg_change:+.2f}%\n"
                f"- **Total Volume:** {int(total_volume):,}\n"
            )
            st.markdown(stats_html)
        else:
            st.info("No market statistics available.")
    else:
        st.info("No market statistics available.")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Indices Overview ---
    st.markdown('''
    <div class="chart-container">
        <h3>📊 Major Market Indices</h3>
    ''', unsafe_allow_html=True)
    indices = {
        "^NSEI": "NIFTY 50",
        "^BSESN": "SENSEX",
        "^NSEBANK": "NIFTY BANK"
    }
    index_cols = st.columns(len(indices))
    for idx, (symbol, name) in enumerate(indices.items()):
        try:
            index = yf.Ticker(symbol)
            current_price = index.info.get('regularMarketPrice', 0)
            change = index.info.get('regularMarketChangePercent', 0)
            with index_cols[idx]:
                st.metric(
                    name,
                    f"₹{current_price:,.2f}",
                    f"{change:+.2f}%",
                    delta_color="normal"
                )
        except:
            with index_cols[idx]:
                st.error(f"Unable to fetch {name}")
    st.markdown('</div>', unsafe_allow_html=True)

# --- Price Alert Section (functional) ---
if 'alert_enabled' not in st.session_state:
    st.session_state.alert_enabled = False
if 'alert_price' not in st.session_state:
    st.session_state.alert_price = ""
def set_alert():
    st.session_state.alert_enabled = not st.session_state.alert_enabled
def update_alert_price(price):
    st.session_state.alert_price = price

st.markdown("""
<div class="price-alert-section">
    <div class="price-alert-toggle {active}">
        <div class="circle"></div>
    </div>
    <input class="price-alert-input" type="number" min="0" step="0.01" placeholder="Alert Price" id="alertPriceInput" />
    <button class="price-alert-btn" id="setAlertBtn">Set Alert</button>
</div>
<script>
const toggle = document.querySelector('.price-alert-toggle');
const btn = document.getElementById('setAlertBtn');
const input = document.getElementById('alertPriceInput');
if(toggle) {
    toggle.onclick = function() {
        toggle.classList.toggle('active');
        window.parent.postMessage({type: 'toggleAlert'}, '*');
    }
}
if(btn && input) {
    btn.onclick = function() {
        window.parent.postMessage({type: 'setAlert', price: input.value}, '*');
        btn.innerText = 'Alert Set!';
        setTimeout(()=>{btn.innerText='Set Alert';}, 1200);
    }
}
</script>
""".replace("{active}", "active" if st.session_state.alert_enabled else ""), unsafe_allow_html=True)

# --- Responsive Grid Layout for Main Dashboard ---
st.markdown('<div class="grid-row">', unsafe_allow_html=True)
st.markdown('<div class="grid-col">', unsafe_allow_html=True)
# ...existing code for metric cards (Current Price, Predicted Price, Accuracy %, Trend Indicator)...
st.markdown('</div>', unsafe_allow_html=True)
st.markdown('<div class="grid-col">', unsafe_allow_html=True)
# ...existing code for interactive charts (line chart, candlestick chart)...
st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- Button Improvements for Add Stock, Download Report ---

import io
import base64

# --- Enhanced: Generate a detailed Excel report with all forecasts, graph, and recommendations ---
if st.session_state.get('analysis_complete', False):

    # --- Ensure xlsxwriter is available ---
    try:
        import xlsxwriter
    except ImportError:
        st.error("The 'xlsxwriter' package is required for Excel report export. Please install it using 'pip install xlsxwriter'.")
        st.stop()

    # Prepare report for 7, 14, 30 days
    stock_symbol = st.session_state.get("stock_symbol", "")
    stock_data = st.session_state.get("stock_data", pd.DataFrame())
    current_price = stock_data.get("Close", pd.Series()).iloc[-1] if not stock_data.empty else ""
    all_predictions = st.session_state.get("all_predictions", {})
    forecast_periods = st.session_state.get("forecast_periods", [7, 14, 30])
    recommendation = st.session_state.get("recommendation", "")
    rec_map = {7: "N/A", 14: "N/A", 30: "N/A"}

    # Prepare summary table
    summary_rows = [
        ["Stock Symbol", stock_symbol],
        ["Current Price", current_price],
    ]
    for days in forecast_periods:
        preds = all_predictions.get(days)
        if preds is not None and len(preds) > 0:
            pred_price = preds[-1]
            change_pct = ((pred_price - current_price) / current_price) * 100 if current_price else 0
            if change_pct > 3:
                rec = "BUY"
            elif change_pct < -3:
                rec = "SELL"
            else:
                rec = "HOLD"
            rec_map[days] = rec
            summary_rows.append([f"Predicted Price ({days} days)", pred_price])
            summary_rows.append([f"Expected Change % ({days} days)", f"{change_pct:+.2f}%"])
            summary_rows.append([f"Recommendation ({days} days)", rec])
    summary_rows.append(["Overall Recommendation", recommendation])

    # --- Generate forecast comparison graph as image ---
    import plotly.io as pio
    fig = go.Figure()
    # Historical price
    fig.add_trace(go.Scatter(
        x=stock_data.index,
        y=stock_data['Close'],
        mode='lines',
        name='Historical Price',
        line=dict(color='blue', width=2)
    ))
    colors = {7: "orange", 14: "red", 30: "green"}
    for days in forecast_periods:
        preds = all_predictions.get(days)
        if preds is not None and len(preds) > 0:
            future_dates = pd.date_range(
                start=stock_data.index[-1] + timedelta(days=1),
                periods=days,
                freq='D'
            )
            fig.add_trace(go.Scatter(
                x=future_dates,
                y=preds,
                mode='lines+markers',
                name=f'Forecast {days}d',
                line=dict(color=colors.get(days, "gray"), width=2, dash='dash'),
                marker=dict(size=6)
            ))
    fig.update_layout(
        title=f"{stock_symbol} - Historical vs 7/14/30 Day Forecasts",
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

    # --- Write to Excel file in memory ---
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        # Summary sheet
        summary_df = pd.DataFrame(summary_rows, columns=["Metric", "Value"])
        summary_df.to_excel(writer, index=False, sheet_name="Summary")
        workbook = writer.book
        worksheet = writer.sheets["Summary"]

        # Insert the chart image below the summary table (skip if kaleido is not installed)
        try:
            import plotly.io as pio
            img_bytes = pio.to_image(fig, format="png", engine="kaleido")
            worksheet.set_row(0, 24)
            worksheet.set_column(0, 0, 28)
            worksheet.set_column(1, 1, 20)
            worksheet.insert_image('D2', 'forecast.png', {'image_data': io.BytesIO(img_bytes), 'x_scale': 0.8, 'y_scale': 0.8})
        except Exception:
            # If kaleido is not installed, skip image export
            pass

        # Forecasts sheet
        forecast_rows = []
        for days in forecast_periods:
            preds = all_predictions.get(days)
            if preds is not None and len(preds) > 0:
                for i, price in enumerate(preds):
                    forecast_rows.append({
                        "Forecast Days": days,
                        "Day": i+1,
                        "Predicted Price": price
                    })
        if forecast_rows:
            forecast_df = pd.DataFrame(forecast_rows)
            forecast_df.to_excel(writer, index=False, sheet_name="Forecasts")

        # Historical data sheet
        if not stock_data.empty:
            stock_data.reset_index().to_excel(writer, index=False, sheet_name="Historical Data")

        # Recommendations sheet
        rec_rows = []
        for days in forecast_periods:
            preds = all_predictions.get(days)
            if preds is not None and len(preds) > 0:
                pred_price = preds[-1]
                change_pct = ((pred_price - current_price) / current_price) * 100 if current_price else 0
                rec = rec_map[days]
                rec_rows.append({
                    "Period (days)": days,
                    "Predicted Price": pred_price,
                    "Expected Change %": f"{change_pct:+.2f}%",
                    "Recommendation": rec
                })
        rec_rows.append({
            "Period (days)": "Overall",
            "Predicted Price": "",
            "Expected Change %": "",
            "Recommendation": recommendation
        })
        rec_df = pd.DataFrame(rec_rows)
        rec_df.to_excel(writer, index=False, sheet_name="Recommendations")

        # Disclaimer
        disclaimer = [
            ["Disclaimer", "This report is generated for informational purposes only. Investment decisions should be made with caution."]
        ]
        disclaimer_df = pd.DataFrame(disclaimer, columns=["", ""])
        disclaimer_df.to_excel(writer, index=False, sheet_name="Disclaimer")

    excel_buffer.seek(0)

    st.download_button(
        label="⬇️ Download Excel Report (All Forecasts, Graph, Recommendations)",
        data=excel_buffer,
        file_name="stock_analysis_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="download_report_btn_excel"
    )

    # Show all forecasts together with graph and recommendation
    st.markdown("### 📊 Forecast Comparison (7, 14, 30 Days)")
    fig = go.Figure()
    # Historical price
    fig.add_trace(go.Scatter(
        x=stock_data.index,
        y=stock_data['Close'],
        mode='lines',
        name='Historical Price',
        line=dict(color='blue', width=2)
    ))
    colors = {7: "orange", 14: "red", 30: "green"}
    for days in forecast_periods:
        preds = all_predictions.get(days)
        if preds is not None and len(preds) > 0:
            future_dates = pd.date_range(
                start=stock_data.index[-1] + timedelta(days=1),
                periods=days,
                freq='D'
            )
            fig.add_trace(go.Scatter(
                x=future_dates,
                y=preds,
                mode='lines+markers',
                name=f'Forecast {days}d',
                line=dict(color=colors.get(days, "gray"), width=2, dash='dash'),
                marker=dict(size=6)
            ))
    fig.update_layout(
        title=f"{stock_symbol} - Historical vs 7/14/30 Day Forecasts",
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
    st.plotly_chart(fig, use_container_width=True)

    # Show recommendations for each period
    st.markdown("### 📝 Recommendations for Each Forecast Period")
    for days in forecast_periods:
        preds = all_predictions.get(days)
        if preds is not None and len(preds) > 0:
            pred_price = preds[-1]
            change_pct = ((pred_price - current_price) / current_price) * 100 if current_price else 0
            if change_pct > 3:
                rec = "BUY"
                color = "green"
                emoji = "🟢"
            elif change_pct < -3:
                rec = "SELL"
                color = "red"
                emoji = "🔴"
            else:
                rec = "HOLD"
                color = "orange"
                emoji = "🟡"
           

            st.markdown(f"""
                <div class="metric-card" style="border-left: 8px solid {color};">
                    <h4>{emoji} {rec} ({days} days)</h4>
                    <p>Predicted Price: <b>₹{pred_price:,.2f}</b></p>
                    <p>Expected Change: <span style="color:{color};">{change_pct:+.2f}%</span></p>
                </div>
            """, unsafe_allow_html=True)
else:
    st.info("Run an analysis to enable report download.")

    # --- Loading Indicator Example ---
    with st.spinner("Loading data..."):
        pass
    # ...existing code for data loading...
    pass

# ...existing code for navigation, metrics, charts, dashboard, etc...

# --- AI Analysis & Advice Section ---

# Only show if analysis is complete and required data is available
if st.session_state.get("analysis_complete", False):
    st.markdown("---")
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown("## 🤖 AI Analysis & Advice")
    insights = []

    # Safely get all required variables from session_state
    stock_symbol = st.session_state.get("stock_symbol", None)
    stock_data = st.session_state.get("stock_data", None)
    sentiment_scores = st.session_state.get("sentiment_scores", [])
    news_headlines = st.session_state.get("news_headlines", [])
    current_price = None
    if stock_data is not None and not stock_data.empty:
        current_price = stock_data['Close'].iloc[-1]

    # 1. Trending news headlines (top 2-3)
    if news_headlines is not None and len(news_headlines) > 0:
        for i, headline in enumerate(news_headlines[:3]):
            insights.append(f"📰 **Trending News:** {headline['title']} ({headline.get('date', 'recent')})")

    # 2. Dividend declarations (from yfinance info)
    try:
        if stock_symbol:
            info = yf.Ticker(stock_symbol).info
            dividend = info.get('dividendRate', None)
            dividend_yield = info.get('dividendYield', None)
            if dividend and dividend > 0:
                insights.append(f"💸 **Dividend Declared:** ₹{dividend:.2f} per share (Yield: {dividend_yield*100:.2f}%)")
    except Exception:
        pass

    # 3. Recent performance (last 1 month and 1 year)
    try:
        if stock_data is not None and not stock_data.empty:
            if len(stock_data) > 21:
                last_month = stock_data['Close'].iloc[-1] / stock_data['Close'].iloc[-22] - 1
                insights.append(f"📈 **1-Month Return:** {last_month*100:+.2f}%")
            if len(stock_data) > 250:
                last_year = stock_data['Close'].iloc[-1] / stock_data['Close'].iloc[-252] - 1
                insights.append(f"📅 **1-Year Return:** {last_year*100:+.2f}%")
    except Exception:
        pass

    # 4. Analyst ratings (from yfinance info)
    try:
        if 'info' in locals():
            if info.get('recommendationKey'):
                rec_key = info['recommendationKey']
                insights.append(f"⭐ **Analyst Consensus:** {rec_key.capitalize()}")
            if info.get('numberOfAnalystOpinions'):
                insights.append(f"👥 **Number of Analyst Ratings:** {info['numberOfAnalystOpinions']}")
    except Exception:
        pass

    # 5. Volatility
    try:
        if stock_data is not None and not stock_data.empty:
            volatility = stock_data['Close'].pct_change().std() * np.sqrt(252) * 100
            if volatility > 40:
                insights.append("⚠️ **High Volatility:** Price swings are significant, consider risk management.")
            elif volatility < 20:
                insights.append("🛡️ **Low Volatility:** Relatively stable price movement.")
    except Exception:
        pass

    # 6. Price near 52-week high/low
    try:
        if stock_data is not None and not stock_data.empty:
            close = stock_data['Close'].iloc[-1]
            high = stock_data['Close'].max()
            low = stock_data['Close'].min()
            if abs(close - high) / high < 0.03:
                insights.append("🚀 **Near 52-Week High:** Stock is trading close to its yearly peak.")
            elif abs(close - low) / low < 0.03:
                insights.append("🔻 **Near 52-Week Low:** Stock is trading close to its yearly bottom.")
    except Exception:
        pass

    # 7. Sentiment summary
    try:
        if sentiment_scores:
            avg_sentiment = np.mean([s['compound'] for s in sentiment_scores])
            if avg_sentiment > 0.1:
                insights.append("😃 **Market Sentiment:** Positive news flow recently.")
            elif avg_sentiment < -0.1:
                insights.append("😟 **Market Sentiment:** Negative news flow recently.")
            else:
                insights.append("😐 **Market Sentiment:** Neutral/uncertain.")
    except Exception:
        pass

    # 8. Candlestick pattern advisory
    candlestick_patterns = st.session_state.get("candlestick_patterns", [])
    if candlestick_patterns:
        last_pattern, last_date = candlestick_patterns[0]
        if "Bullish" in last_pattern:
            insights.append(f"🟢 **Technical Signal:** Recent {last_pattern} pattern detected on {last_date.strftime('%Y-%m-%d')}.")
        elif "Bearish" in last_pattern:
            insights.append(f"🔴 **Technical Signal:** Recent {last_pattern} pattern detected on {last_date.strftime('%Y-%m-%d')}.")

    # 9. Forecast summary
    try:
        all_predictions = st.session_state.get("all_predictions", {})
        pred_14 = all_predictions.get(14)
        if pred_14 is not None and current_price is not None and len(pred_14) > 0:
            pred_price = pred_14[-1]
            change_pct = ((pred_price - current_price) / current_price) * 100
            if change_pct > 3:
                insights.append("📊 **AI Forecast:** Model expects a significant upward move in the next 2 weeks.")
            elif change_pct < -3:
                insights.append("📊 **AI Forecast:** Model expects a significant downward move in the next 2 weeks.")
            else:
                insights.append("📊 **AI Forecast:** Model expects minor price changes in the next 2 weeks.")
    except Exception:
        pass

    # 10. General advisory
    insights.append("⚠️ **Advisory:** Always diversify your portfolio and consult a financial advisor before making investment decisions.")

    # Display as bullet points
    st.markdown("<ul style='margin-left:1.5em;'>"
        + "".join(f"<li style='margin-bottom:0.5em;'>{pt}</li>" for pt in insights[:10])
        + "</ul>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("Run a stock analysis to view AI-powered insights and advice.")

# --- Admin Dashboard ---
def show_admin_dashboard():
    st.markdown("## 🛡️ Admin Dashboard")

    if not auth_manager.has_any_role(['Super Admin', 'Admin']):
        st.error("Access denied.")
        return

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

def show_user_management():
    st.subheader("User Management")

    db = Database()
    users = db.get_user_stats()

    # User statistics
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Users", users['total_users'])
    with col2:
        st.metric("Active Users", users['active_users'])
    with col3:
        st.metric("Premium Users", users['premium_users'])
    with col4:
        st.metric("Suspended", users['suspended_users'])
    with col5:
        st.metric("Banned", users['banned_users'])

    # User list with actions
    st.subheader("User List")
    # This would show a table of users with edit/delete actions
    # For brevity, showing basic structure

def show_analytics():
    st.subheader("System Analytics")

    db = Database()
    api_usage = db.get_api_usage_stats()

    if api_usage:
        df = pd.DataFrame(api_usage)
        st.dataframe(df)

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
    # System configuration options

def show_security_settings():
    st.subheader("Security Settings")
    # Security-related settings

# Add admin dashboard to sidebar
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
            if st.button("🛡️ Admin Dashboard", use_container_width=True):
                st.session_state.page = 'admin'
                st.rerun()

        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            auth_manager.logout()

# Update the main app to include navigation
def show_main_app():
    add_sidebar_navigation()

    page = st.session_state.get('page', 'dashboard')

    if page == 'admin':
        show_admin_dashboard()
    else:
        # Original app content
        # --- Modern MNC Fintech UI: Theme Toggle, Header, Layout ---

# Call main function
if __name__ == "__main__":
    main()

