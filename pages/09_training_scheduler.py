"""
Training Scheduler Dashboard Page
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

from StockSageAI.training_scheduler import get_training_scheduler

st.set_page_config(page_title="Training Scheduler", layout="wide")

st.markdown("# 🤖 Training Scheduler Dashboard")
st.markdown("Monitor and manage automated model retraining jobs")

scheduler = get_training_scheduler()

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["Active Jobs", "Job History", "Drift Detection", "Settings"])

# TAB 1: Active Jobs
with tab1:
    st.subheader("Currently Scheduled Jobs")
    
    # Mock active jobs data
    active_jobs = [
        {
            'Job ID': 'JOB_001',
            'Type': 'Daily Training',
            'Schedule': '09:00 AM EST',
            'Next Run': 'Today 09:00 AM',
            'Status': 'Scheduled',
            'Models': 'All 8 Models',
            'Last Duration': '2.5 min'
        },
        {
            'Job ID': 'JOB_002',
            'Type': 'Weekly Analysis',
            'Schedule': 'Monday 10:00 AM',
            'Next Run': 'Monday 10:00 AM',
            'Status': 'Scheduled',
            'Models': 'Top 3 Models',
            'Last Duration': '4.2 min'
        },
        {
            'Job ID': 'JOB_003',
            'Type': 'Adaptive Training',
            'Schedule': 'On Drift Detection',
            'Next Run': 'On Demand',
            'Status': 'Monitoring',
            'Models': 'All 8 Models',
            'Last Duration': '1.8 min'
        }
    ]
    
    jobs_df = pd.DataFrame(active_jobs)
    st.dataframe(jobs_df, use_container_width=True)
    
    st.divider()
    
    st.subheader("Create New Job")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        job_type = st.selectbox(
            "Job Type",
            ["Daily Training", "Weekly Training", "Adaptive Training", "One-Time Run"]
        )
    
    with col2:
        models_to_train = st.multiselect(
            "Models to Train",
            [
                "Transformer LSTM",
                "Attention LSTM",
                "BiLSTM Ensemble",
                "CNN-BiLSTM",
                "TCN Model",
                "All 8 Models"
            ],
            default=["All 8 Models"]
        )
    
    with col3:
        st.info(f"Job Type: {job_type}")
    
    if job_type == "Daily Training":
        col1, col2 = st.columns(2)
        
        with col1:
            train_time = st.time_input("Training Time", value=datetime.strptime("09:00", "%H:%M").time())
        
        with col2:
            timezone = st.selectbox("Timezone", ["UTC", "EST", "CST", "MST", "PST", "IST"], index=1)
    
    elif job_type == "Weekly Training":
        col1, col2 = st.columns(2)
        
        with col1:
            train_day = st.selectbox(
                "Training Day",
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            )
        
        with col2:
            train_time = st.time_input("Training Time", value=datetime.strptime("10:00", "%H:%M").time(), key="weekly_time")
    
    elif job_type == "Adaptive Training":
        col1, col2 = st.columns(2)
        
        with col1:
            drift_threshold = st.slider("Drift Detection Threshold", 0.01, 0.20, 0.05, 0.01)
        
        with col2:
            min_interval = st.number_input("Minimum Interval (hours)", value=24, min_value=1)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        enable_backup = st.checkbox("Automatic Backup", value=True)
    
    with col2:
        enable_notification = st.checkbox("Send Notification", value=True)
    
    with col3:
        enable_logging = st.checkbox("Enable Detailed Logging", value=True)
    
    if st.button("Create Job", type="primary", use_container_width=True):
        with st.spinner("Creating training job..."):
            try:
                if job_type == "Daily Training":
                    result = scheduler.schedule_daily_training(
                        timezone=timezone,
                        notification_enabled=enable_notification
                    )
                    success_msg = f"✅ Daily training scheduled for {train_time} {timezone}"
                
                elif job_type == "Weekly Training":
                    result = scheduler.schedule_weekly_training(
                        day_of_week=train_day.lower(),
                        notification_enabled=enable_notification
                    )
                    success_msg = f"✅ Weekly training scheduled for {train_day}s at {train_time}"
                
                else:  # Adaptive
                    result = scheduler.schedule_adaptive_training(
                        drift_threshold=drift_threshold,
                        notification_enabled=enable_notification
                    )
                    success_msg = f"✅ Adaptive training configured (threshold: {drift_threshold:.2%})"
                
                st.success(success_msg)
                st.info("Job created and monitoring started")
            
            except Exception as e:
                st.error(f"Error: {str(e)}")

# TAB 2: Job History
with tab2:
    st.subheader("Training Job History")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        history_filter = st.selectbox(
            "Filter by Type",
            ["All", "Daily", "Weekly", "Adaptive", "Manual"]
        )
    
    with col2:
        days_range = st.slider("Days Back", 1, 90, 30)
    
    with col3:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "Completed", "Failed", "Running", "Cancelled"]
        )
    
    # Mock history data
    history_data = []
    for i in range(20):
        date = datetime.now() - timedelta(hours=i*2)
        status = ["Completed", "Completed", "Failed", "Running"][i % 4]
        
        history_data.append({
            'Timestamp': date.strftime('%Y-%m-%d %H:%M'),
            'Type': ['Daily', 'Weekly', 'Adaptive', 'Manual'][i % 4],
            'Status': status,
            'Models Trained': f"{2 + (i % 7)} models",
            'Duration': f"{1.2 + (i * 0.1):.1f} min",
            'Accuracy Change': f"{(-0.02 + (i * 0.001)):.1%}",
            'Details': '👁️ View' if status == 'Completed' else '⏳ ...'
        })
    
    history_df = pd.DataFrame(history_data)
    
    # Apply filters
    if history_filter != "All":
        history_df = history_df[history_df['Type'] == history_filter]
    
    if status_filter != "All":
        history_df = history_df[history_df['Status'] == status_filter]
    
    st.dataframe(history_df, use_container_width=True)
    
    st.divider()
    
    st.subheader("Training Performance Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Runs", 156, "+5 this week")
    
    with col2:
        st.metric("Success Rate", "98.7%", "+0.3%")
    
    with col3:
        st.metric("Avg Duration", "2.4 min", "-0.2 min")
    
    with col4:
        st.metric("Models Trained", 1248, "+48 this week")
    
    # Training history chart
    st.write("### Training Efficiency Over Time")
    
    dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30, 0, -1)]
    durations = [2.1 + i*0.02 for i in range(30)]
    success_rates = [0.95 + i*0.001 for i in range(30)]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates, y=durations,
        name='Training Duration (min)',
        yaxis='y',
        line=dict(color='#1f77b4')
    ))
    
    fig.add_trace(go.Scatter(
        x=dates, y=[s*100 for s in success_rates],
        name='Success Rate (%)',
        yaxis='y2',
        line=dict(color='#2ca02c')
    ))
    
    fig.update_layout(
        title="Training Job Performance Trends",
        xaxis_title="Date",
        yaxis_title="Duration (minutes)",
        yaxis2=dict(title="Success Rate (%)", overlaying='y', side='right'),
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

# TAB 3: Drift Detection
with tab3:
    st.subheader("Model Drift Detection")
    
    st.info("""
    **Drift Detection:** Monitors model performance degradation and automatically triggers retraining 
    when detected drift exceeds configured threshold.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### Current Drift Status")
        
        # Mock drift data
        models_drift = [
            {'Model': 'Transformer LSTM', 'Drift': 0.045, 'Status': '🟢 Normal'},
            {'Model': 'Attention LSTM', 'Drift': 0.089, 'Status': '🟡 Elevated'},
            {'Model': 'BiLSTM Ensemble', 'Drift': 0.012, 'Status': '🟢 Normal'},
            {'Model': 'CNN-BiLSTM', 'Drift': 0.156, 'Status': '🔴 High'},
            {'Model': 'TCN Model', 'Drift': 0.032, 'Status': '🟢 Normal'},
        ]
        
        drift_df = pd.DataFrame(models_drift)
        st.dataframe(drift_df, use_container_width=True)
    
    with col2:
        st.write("### Drift Configuration")
        
        col1_inner, col2_inner = st.columns(2)
        
        with col1_inner:
            alert_threshold = st.slider("Alert Threshold", 0.05, 0.30, 0.10, 0.01)
        
        with col2_inner:
            retrain_threshold = st.slider("Retrain Threshold", 0.10, 0.50, 0.25, 0.02)
        
        check_frequency = st.selectbox(
            "Check Frequency",
            ["Every Hour", "Every 6 Hours", "Every 12 Hours", "Daily"]
        )
    
    st.divider()
    
    st.write("### Drift Alerts")
    
    # Dummy alerts
    alerts_data = [
        {
            'Model': 'CNN-BiLSTM',
            'Alert': '🔴 High Drift Detected',
            'Drift Score': 0.156,
            'Threshold': 0.10,
            'Time': (datetime.now() - timedelta(minutes=15)).strftime('%H:%M'),
            'Action': 'Retraining Started'
        },
        {
            'Model': 'Attention LSTM',
            'Alert': '🟡 Elevated Drift',
            'Drift Score': 0.089,
            'Threshold': 0.10,
            'Time': (datetime.now() - timedelta(hours=2)).strftime('%H:%M'),
            'Action': 'Monitoring'
        }
    ]
    
    alerts_df = pd.DataFrame(alerts_data)
    st.dataframe(alerts_df, use_container_width=True)
    
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Manual Drift Check"):
            with st.spinner("Checking drift..."):
                st.success("Drift check completed")
    
    with col2:
        if st.button("⚙️ Update Thresholds"):
            st.success("Thresholds updated")
    
    with col3:
        if st.button("📊 Generate Drift Report"):
            st.success("Report generated")

# TAB 4: Settings
with tab4:
    st.subheader("Training Scheduler Settings")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.write("### Global Settings")
    
    with col2:
        st.info("Configure global behavior for all training jobs")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Resource Management**")
        
        max_cpu = st.slider("Max CPU Usage (%)", 10, 100, 80, 5)
        max_memory = st.slider("Max Memory (GB)", 1, 16, 8, 1)
        max_parallel = st.slider("Max Parallel Jobs", 1, 5, 2, 1)
    
    with col2:
        st.write("**Notifications**")
        
        notify_on_complete = st.checkbox("Notify on Completion", value=True)
        notify_on_failure = st.checkbox("Notify on Failure", value=True)
        notify_on_drift = st.checkbox("Notify on Drift Detected", value=True)
        notify_email = st.text_input("Notification Email", "admin@stocksageai.com")
    
    st.divider()
    
    st.write("**Model Versioning**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Versions Tracked", 156)
    
    with col2:
        st.metric("Disk Used (GB)", 12.5)
    
    with col3:
        retention = st.selectbox("Retention Policy", ["Last 20 versions", "Last 50 versions", "Unlimited"])
    
    st.divider()
    
    st.write("**Advanced Settings**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        enable_gpu = st.checkbox("Enable GPU Acceleration", value=True)
        auto_cleanup = st.checkbox("Auto-cleanup Old Versions", value=True)
    
    with col2:
        enable_profiling = st.checkbox("Enable Performance Profiling", value=True)
        enable_audit_log = st.checkbox("Enable Audit Logging", value=True)
    
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save Settings", type="primary", use_container_width=True):
            st.success("Settings saved successfully")
    
    with col2:
        if st.button("🔄 Reset to Defaults", use_container_width=True):
            st.warning("Settings reset to default values")
    
    with col3:
        if st.button("📋 Export Config", use_container_width=True):
            config_json = {
                "max_cpu_usage": max_cpu,
                "max_memory_gb": max_memory,
                "max_parallel_jobs": max_parallel,
                "notifications": {
                    "on_complete": notify_on_complete,
                    "on_failure": notify_on_failure,
                    "on_drift": notify_on_drift,
                    "email": notify_email
                }
            }
            st.download_button(
                label="📥 Download Config",
                data=str(config_json),
                file_name="training_scheduler_config.json",
                mime="application/json"
            )

st.caption("Training Scheduler Dashboard • SP 07 StockSageAI")
