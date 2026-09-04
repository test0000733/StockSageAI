"""
Telegram Dashboard - Admin UI controls for Telegram forecast system
Integrated into the existing Streamlit admin dashboard
"""

import streamlit as st
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def render_telegram_dashboard():
    """
    Render Telegram Forecast section in Admin Dashboard
    
    NOTE: This function should be called from the main admin dashboard
    location in admin_ai_ui.py or the main app.py
    """
    
    # Import required services (lazy import to avoid circular dependencies)
    try:
        from StockSageAI.telegram_service import get_telegram_service
        from StockSageAI.telegram_notifier import get_telegram_notifier
        from StockSageAI.telegram_api import get_telegram_api
        from StockSageAI.forecast_scheduler import get_forecast_scheduler
        from StockSageAI.database import Database
    except ImportError as e:
        st.error(f"❌ Failed to import Telegram modules: {str(e)}")
        return
    
    st.markdown("---")
    st.markdown("## 📨 Telegram Daily Forecast System")
    
    # Get service instances
    telegram_service = get_telegram_service()
    notifier = get_telegram_notifier()
    scheduler = get_forecast_scheduler()
    api = get_telegram_api(telegram_service, notifier, scheduler)
    db = Database()
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Status",
        "🧪 Test",
        "📤 Send",
        "📈 History",
        "⚙️ Settings"
    ])
    
    # ============ TAB 1: STATUS ============
    with tab1:
        st.subheader("System Status", divider="blue")
        
        # Get current status
        status = api.get_status()
        
        # Display status in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            telegram_emoji = "✅" if status["telegram_connection"] == "Connected" else "❌"
            st.metric(
                f"{telegram_emoji} Telegram",
                status["telegram_connection"]
            )
        
        with col2:
            scheduler_emoji = "✅" if scheduler.is_running else "⏸️"
            st.metric(
                f"{scheduler_emoji} Scheduler",
                "Active" if scheduler.is_running else "Inactive"
            )
        
        with col3:
            st.metric(
                "📅 Schedule",
                f"{scheduler.schedule_time} IST"
            )
        
        with col4:
            trading_day = "🟢 Yes" if status["trading_day_today"] else "🔴 No"
            st.metric(
                "📈 Trading Day",
                trading_day
            )
        
        # Next scheduled run
        st.info(f"⏰ Next Scheduled Run: {status['next_scheduled_run']}")
        
        # Last run info
        col1, col2 = st.columns(2)
        with col1:
            if status["last_successful_run"]:
                st.success(f"✅ Last Successful: {status['last_successful_run']}")
            else:
                st.warning("⚠️ No successful run yet")
        
        with col2:
            last_notification = db.get_last_notification_status()
            if last_notification:
                status_text = last_notification.get('status', 'Unknown')
                date_text = last_notification.get('notification_date', 'Unknown')
                if status_text == 'sent':
                    st.success(f"✅ Last Sent: {date_text}")
                else:
                    st.error(f"❌ Last Failed: {date_text}")
    
    # ============ TAB 2: TEST CONNECTION ============
    with tab2:
        st.subheader("Test Telegram Connection", divider="blue")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🧪 Test Connection", type="primary"):
                with st.spinner("Testing Telegram connection..."):
                    result = api.test_telegram_connection()
                    
                    if result["success"]:
                        st.success(result["message"])
                        if result.get("bot_info"):
                            st.json(result["bot_info"])
                    else:
                        st.error(result["message"])
        
        with col2:
            if st.button("📨 Send Test Message", type="primary"):
                with st.spinner("Sending test message..."):
                    result = api.send_test_message()
                    
                    if result["success"]:
                        st.success(f"✅ Test message sent! (ID: {result['message_id']})")
                    else:
                        st.error(f"❌ Failed: {result.get('error', 'Unknown error')}")
    
    # ============ TAB 3: SEND FORECAST ============
    with tab3:
        st.subheader("Manual Forecast Operations", divider="blue")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Run Forecast Now", type="primary", use_container_width=True):
                with st.spinner("⏳ Generating and sending forecasts..."):
                    try:
                        # Import forecast components
                        from StockSageAI.forecast_generator import get_forecast_generator
                        from StockSageAI.stock_selector import get_stock_selector
                        
                        # Generate forecasts
                        selector = get_stock_selector()
                        stocks = selector.get_top_10_stocks()
                        
                        generator = get_forecast_generator()
                        forecasts = generator.generate_batch_forecasts(stocks)
                        
                        # Send to Telegram
                        send_result = api.send_forecast(forecasts)
                        
                        if send_result["success"]:
                            st.success(f"✅ Sent! {send_result['stocks_sent']} stocks forecasted")
                            
                            # Save to database
                            from datetime import date
                            db.save_notification(
                                date.today(),
                                'sent',
                                send_result['stocks_sent'],
                                send_result['stocks_failed'],
                                send_result['message_ids']
                            )
                        else:
                            st.error(f"❌ Failed: {send_result.get('error')}")
                            
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
        with col2:
            if st.button("📊 Preview Forecast", type="secondary", use_container_width=True):
                with st.spinner("⏳ Generating preview..."):
                    try:
                        from StockSageAI.forecast_generator import get_forecast_generator
                        from StockSageAI.stock_selector import get_stock_selector
                        
                        selector = get_stock_selector()
                        stocks = selector.get_top_10_stocks()
                        
                        generator = get_forecast_generator()
                        forecasts = generator.generate_batch_forecasts(stocks)
                        
                        preview = api.preview_forecast(forecasts)
                        
                        st.info(f"Preview Length: {preview['message_length']} chars")
                        
                        with st.expander("📄 View Full Preview"):
                            st.code(preview['preview_message'], language='text')
                            
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
        with col3:
            if st.button("🔁 Retry Failed", type="secondary", use_container_width=True):
                st.info("Use this to retry any failed previous sends")
                retry_status = api.get_retry_status()
                st.write(f"Pending retries: {retry_status['pending_retries']}")
    
    # ============ TAB 4: HISTORY ============
    with tab4:
        st.subheader("Forecast History & Performance", divider="blue")
        
        # Get forecast history
        history = db.get_forecast_history(days=30)
        
        if history:
            # Convert to display format
            display_data = []
            for h in history:
                display_data.append({
                    'Date': h.get('forecast_date'),
                    'Stock': h.get('symbol'),
                    'Current': f"₹{h.get('current_price', 0):.2f}",
                    '7D Signal': h.get('signal_7d'),
                    '14D Signal': h.get('signal_14d'),
                    '30D Signal': h.get('signal_30d'),
                    'Confidence': f"{h.get('confidence_14d', 0):.1f}%"
                })
            
            st.dataframe(display_data, use_container_width=True)
        else:
            st.info("No forecast history available yet")
        
        # Model performance
        st.subheader("Model Performance Metrics")
        performance = db.get_model_performance_summary()
        
        if performance:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Avg Directional Accuracy",
                    f"{performance.get('avg_accuracy', 0):.1f}%"
                )
            with col2:
                st.metric(
                    "Max Accuracy",
                    f"{performance.get('max_accuracy', 0):.1f}%"
                )
            with col3:
                st.metric(
                    "Symbols Evaluated",
                    performance.get('symbols_evaluated', 0)
                )
        else:
            st.info("No performance metrics available yet")
    
    # ============ TAB 5: SETTINGS ============
    with tab5:
        st.subheader("Configuration & Settings", divider="blue")
        
        st.warning("⚠️ Only modify settings if you know what you're doing")
        
        # Scheduler settings
        with st.expander("🔔 Scheduler Settings"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Schedule Time:** {scheduler.schedule_time} IST")
                st.write(f"**Timezone:** Asia/Kolkata")
            
            with col2:
                st.write(f"**Enabled:** {'✅ Yes' if scheduler.enabled else '❌ No'}")
                st.write(f"**Running:** {'✅ Yes' if scheduler.is_running else '❌ No'}")
        
        # Telegram credentials (masked)
        with st.expander("🔐 Telegram Credentials"):
            import os
            from dotenv import load_dotenv
            load_dotenv()
            
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '').replace(':', ':***')
            chat_id = os.getenv('TELEGRAM_CHAT_ID', '***')
            
            st.warning("Credentials are masked for security")
            st.write(f"Bot Token: `{bot_token}`")
            st.write(f"Chat ID: `{int(chat_id)}`")
        
        # Database info
        with st.expander("📦 Database Information"):
            last_notif = db.get_last_notification_status()
            if last_notif:
                st.write(f"Last Notification: {last_notif.get('notification_date')}")
                st.write(f"Status: {last_notif.get('status')}")
                st.write(f"Stocks Sent: {last_notif.get('stocks_sent')}")
                st.write(f"Stocks Failed: {last_notif.get('stocks_failed')}")


# Integration point for admin dashboard
def add_telegram_section_to_admin():
    """
    Call this function from your existing admin dashboard
    to add the Telegram section
    
    Example in admin_ai_ui.py:
    ```
    from StockSageAI.telegram_dashboard import add_telegram_section_to_admin
    
    if st.session_state.admin_ai_auto_run:
        add_telegram_section_to_admin()
    ```
    """
    render_telegram_dashboard()
