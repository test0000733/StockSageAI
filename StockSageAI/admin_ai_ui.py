import os
import streamlit as st
from StockSageAI.training_manager import manager

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
        st.error("Access denied.")
        return

    st.markdown("## ⚙️ Admin Model Training Dashboard")

    tmp_dir = os.path.join(os.path.dirname(__file__), 'tmp')
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir, exist_ok=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        model = st.selectbox("Select model to train", AVAILABLE_MODELS, key='admin_train_select')
        if model == 'Transformer Ensemble':
            transformer_variant = st.selectbox(
                "Transformer variant",
                [
                    'Temporal Fusion Transformer',
                    'Informer',
                    'Autoformer',
                    'FEDformer',
                    'PatchTST',
                    'Cross-Attention Transformer',
                    'Multi-Head Time-Series Transformer'
                ],
                key='admin_transformer_variant'
            )
        else:
            transformer_variant = None

        dataset = st.file_uploader("Upload CSV dataset (optional)", type=['csv'], key='admin_train_dataset')
        if dataset is not None:
            dataset_name = dataset.name.replace(' ', '_')
            dataset_path = os.path.join(tmp_dir, f"training_dataset_{dataset_name}")
            with open(dataset_path, 'wb') as f:
                f.write(dataset.getbuffer())
            st.success(f"Dataset saved: {dataset_name}")
        else:
            dataset_path = None

        epochs = st.number_input("Epochs", min_value=1, max_value=1000, value=8, step=1, key='admin_train_epochs')
        lr = st.number_input("Learning rate", value=0.001, format="%f", key='admin_train_lr')
        sequence_length = st.number_input("Sequence length", min_value=5, max_value=120, value=20, step=1, key='admin_train_seq_len')
        horizon = st.number_input("Forecast horizon", min_value=1, max_value=20, value=1, step=1, key='admin_train_horizon')

        if model in ['LSTM', 'BiLSTM', 'CNN-LSTM']:
            layer_style = st.selectbox(
                "Sequence model style",
                ['Standard', 'Deep', 'Wide'],
                key='admin_sequence_style'
            )
        else:
            layer_style = None

        if model == 'GNN Ensemble':
            graph_depth = st.number_input("Graph depth", min_value=1, max_value=6, value=3, step=1, key='admin_train_graph_depth')
        else:
            graph_depth = None

        if model == 'XGBoost':
            boosting_rounds = st.number_input("Boosting rounds", min_value=10, max_value=500, value=100, step=10, key='admin_train_boost_rounds')
        else:
            boosting_rounds = None

        tune = st.checkbox("Enable hyperparameter tuning", value=False, key='admin_train_tune')

        if st.button("Start Training", key='admin_train_start'):
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
            st.rerun()

    with col2:
        st.markdown("### Training jobs")
        job = st.session_state.get('admin_train_job')
        if job:
            status = manager.get_status(job)
            if status:
                st.progress(status.get('progress', 0))
                st.markdown(f"**Status:** {status.get('status')} | **Progress:** {status.get('progress')}%")
                if status.get('updated_at'):
                    st.markdown(f"*Last updated: {status.get('updated_at')}*")
                metrics = status.get('metrics', {})
                if metrics:
                    st.markdown("**Metrics:**")
                    for key, value in metrics.items():
                        st.write(f"- {key}: {value}")
                st.markdown("**Recent logs:**")
                logs = status.get('logs', [])[-6:]
                for l in logs:
                    st.text(l)
            else:
                st.info("No status available yet for this job.")
        else:
            st.info("Start a training job to see live progress here.")

    st.markdown('---')
    st.markdown('**Notes:** This dashboard now supports Transformer, sequence models, GNN, XGBoost, multimodal fusion, and ensemble intelligence training. For production use, configure GPU-enabled runners and the full training stack.')
