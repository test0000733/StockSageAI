import os
import streamlit as st
from StockSageAI.training_manager import manager
from StockSageAI import ui_components as ui

AVAILABLE_MODELS = [
    'Transformer Ensemble',
    'LSTM',
    'BiLSTM',
    'CNN-LSTM',
    'GNN Ensemble',
    'XGBoost',
    'Multimodal Fusion',
    'Ensemble Intelligence'
]


def render_admin_training_dashboard():
    from StockSageAI.auth import auth_manager
    from StockSageAI.database import Database

    render_back_button = None
    if not auth_manager.has_any_role(['Super Admin', 'Admin']):
        st.error("❌ Access Denied - Admin privileges required")
        return

    # Header with consistent styling
    st.markdown("""
    <div style='text-align: center; margin-bottom: 2rem;'>
        <h1 style='margin: 0.5rem 0;'>⚙️ Admin Model Training Dashboard</h1>
        <p style='color: #cbd5e1; margin: 0.5rem 0; font-size: 0.95rem;'>Train, tune, and deploy advanced ML models</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    tmp_dir = os.path.join(os.path.dirname(__file__), 'tmp')
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir, exist_ok=True)

    # Main layout with better spacing
    col1, col2 = st.columns([3, 2], gap="large")
    
    with col1:
        st.subheader("🤖 Model Configuration", divider="blue")
        
        # Model selection with better spacing
        model = st.selectbox(
            "Select Model Architecture",
            AVAILABLE_MODELS,
            key='admin_train_select',
            help="Choose the ML architecture to train"
        )
        
        st.markdown("")  # Spacing
        
        # Transformer variant (conditional)
        if model == 'Transformer Ensemble':
            st.markdown("<small style='color: #38bdf8;'>**Transformer Architecture Selection**</small>", unsafe_allow_html=True)
            transformer_variant = st.selectbox(
                "Choose Variant",
                [
                    'Temporal Fusion Transformer',
                    'Informer',
                    'Autoformer',
                    'FEDformer',
                    'PatchTST',
                    'Cross-Attention Transformer',
                    'Multi-Head Time-Series Transformer'
                ],
                key='admin_transformer_variant',
                help="Different Transformer variants for different use cases"
            )
        else:
            transformer_variant = None

        st.markdown("")  # Spacing
        
        # Dataset upload section
        st.markdown("<small style='color: #38bdf8;'>**Dataset Configuration**</small>", unsafe_allow_html=True)
        dataset = st.file_uploader(
            "Upload Custom Dataset (Optional)",
            type=['csv'],
            key='admin_train_dataset',
            help="CSV format: DateTime, OHLCV columns. Max 500MB"
        )
        
        if dataset is not None:
            dataset_path = ui.save_uploaded_csv(dataset, target_dir=tmp_dir)
        else:
            st.info("ℹ️ No custom dataset - will use default historical data")
            dataset_path = None

        st.markdown("")  # Spacing
        
        # Hyperparameters section
        st.markdown("<small style='color: #38bdf8;'>**Training Hyperparameters**</small>", unsafe_allow_html=True)
        
        hp_cols = st.columns(2, gap="medium")
        with hp_cols[0]:
            epochs = st.number_input(
                "Epochs",
                min_value=1,
                max_value=1000,
                value=8,
                step=1,
                key='admin_train_epochs',
                help="Training iterations: 8 (quick) to 32+ (better)"
            )
        with hp_cols[1]:
            lr = st.number_input(
                "Learning Rate",
                value=0.001,
                min_value=0.00001,
                max_value=1.0,
                format="%f",
                key='admin_train_lr',
                help="0.001 (default) works best for most models"
            )
        
        hp_cols2 = st.columns(2, gap="medium")
        with hp_cols2[0]:
            sequence_length = st.number_input(
                "Sequence Length (days)",
                min_value=5,
                max_value=120,
                value=20,
                step=1,
                key='admin_train_seq_len',
                help="Historical lookback window"
            )
        with hp_cols2[1]:
            horizon = st.number_input(
                "Forecast Horizon (days)",
                min_value=1,
                max_value=20,
                value=1,
                step=1,
                key='admin_train_horizon',
                help="How many days ahead to predict"
            )

        st.markdown("")  # Spacing
        
        # Model-specific parameters
        if model in ['LSTM', 'BiLSTM', 'CNN-LSTM']:
            st.markdown("<small style='color: #38bdf8;'>**Sequence Model Parameters**</small>", unsafe_allow_html=True)
            layer_style = st.selectbox(
                "Architecture Style",
                ['Standard', 'Deep', 'Wide'],
                key='admin_sequence_style',
                help="Standard (default) | Deep (better accuracy) | Wide (faster)"
            )
        else:
            layer_style = None

        if model == 'GNN Ensemble':
            st.markdown("<small style='color: #38bdf8;'>**Graph Parameters**</small>", unsafe_allow_html=True)
            graph_depth = st.number_input(
                "Graph Depth",
                min_value=1,
                max_value=6,
                value=3,
                step=1,
                key='admin_train_graph_depth',
                help="Number of graph aggregation layers"
            )
        else:
            graph_depth = None

        if model == 'XGBoost':
            st.markdown("<small style='color: #38bdf8;'>**Boosting Parameters**</small>", unsafe_allow_html=True)
            boosting_rounds = st.number_input(
                "Boosting Rounds",
                min_value=10,
                max_value=500,
                value=100,
                step=10,
                key='admin_train_boost_rounds',
                help="More rounds = better accuracy but slower"
            )
        else:
            boosting_rounds = None

        st.markdown("")  # Spacing
        
        # Advanced options
        st.markdown("<small style='color: #38bdf8;'>**Advanced Options**</small>", unsafe_allow_html=True)
        tune = st.checkbox(
            "🔄 Enable Hyperparameter Tuning (Auto-Optimization)",
            value=False,
            key='admin_train_tune',
            help="Adds 20-30 min but improves accuracy by 5-10%"
        )

        st.markdown("")  # Spacing
        
        # Training button
        btn_col1, btn_col2 = st.columns([3, 1], gap="medium")
        with btn_col1:
            if ui.render_primary_button("🚀 START TRAINING", key='admin_train_start'):
                hyperparams = {
                    'epochs': epochs,
                    'lr': lr,
                    'sequence_length': sequence_length,
                    'horizon': horizon,
                    'variant': transformer_variant,
                    'dataset_path': dataset_path,
                    'sequence_style': layer_style,
                    'graph_depth': graph_depth,
                    'boosting_rounds': boosting_rounds,
                    'tune': tune
                }
                job_id = manager.start_training(model, dataset_path=dataset_path, hyperparams=hyperparams)
                st.session_state.admin_train_job = job_id
                st.session_state.admin_train_status = 'running'
                st.success("✅ Training job submitted!")
                st.rerun()

    with col2:
        st.subheader("📊 Training Status", divider="green")
        
        job = st.session_state.get('admin_train_job')
        if job:
            status = manager.get_status(job)
            if status:
                # Progress indicator
                progress = status.get('progress', 0)
                st.progress(progress / 100 if progress else 0)
                
                st.markdown("")  # Spacing
                
                # Status display with better styling
                status_text = status.get('status', 'Unknown')
                status_color = {
                    'running': '#3b82f6',
                    'completed': '#10b981',
                    'failed': '#ef4444',
                    'queued': '#f59e0b'
                }.get(status_text.lower(), '#38bdf8')
                
                st.markdown(f"<div style='background: rgba(56, 189, 248, 0.1); padding: 1rem; border-radius: 8px; border-left: 4px solid {status_color};'>"
                           f"<strong>Status:</strong> {status_text} | <strong>Progress:</strong> {progress}%</div>", 
                           unsafe_allow_html=True)
                
                st.markdown("")  # Spacing
                
                if status.get('updated_at'):
                    ui.training_status_card(status.get('status', 'Unknown'), progress=progress, updated_at=status.get('updated_at'))
                else:
                    ui.training_status_card(status.get('status', 'Unknown'), progress=progress)
                
                # Metrics display
                metrics = status.get('metrics', {})
                if metrics:
                    st.markdown("**Performance Metrics:**")
                    metrics_cols = st.columns(2)
                    for idx, (key, value) in enumerate(list(metrics.items())[:4]):
                        with metrics_cols[idx % 2]:
                            st.metric(label=key, value=f"{value:.4f}" if isinstance(value, float) else value)
                
                st.markdown("")  # Spacing
                
                # Logs display
                st.markdown("**Training Logs:**")
                logs = status.get('logs', [])[-5:]
                if logs:
                    with st.container(border=True):
                        for log_line in logs:
                            st.text(log_line)
                else:
                    st.info("No logs available yet")
            else:
                st.warning("⏳ Waiting for job to start...")
        else:
            st.info("👈 Configure and start a training job to see progress here")

    # Separator and footer info
    st.markdown("---")
    st.markdown("""
    <div style='background: rgba(56, 189, 248, 0.05); padding: 1rem; border-radius: 8px; border-left: 4px solid #38bdf8;'>
        <strong>ℹ️ Dashboard Features:</strong>
        <ul style='margin: 0.5rem 0; padding-left: 1.25rem;'>
            <li>8 Advanced Models: Transformer, LSTM, BiLSTM, CNN-LSTM, GNN, XGBoost, Multimodal, Ensemble</li>
            <li>Hyperparameter Tuning: Bayesian optimization for automatic parameter discovery</li>
            <li>Real-time Monitoring: Live loss, accuracy, and metric tracking</li>
            <li>Version Control: Automatic model versioning and comparison</li>
            <li>GPU Support: Optimized for NVIDIA GPUs (CPU training also supported)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
