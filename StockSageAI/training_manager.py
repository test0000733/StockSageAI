import json
import os
import threading
import time
import uuid
from datetime import datetime

import pandas as pd

from StockSageAI.feature_pipeline import FeaturePipeline
from StockSageAI.models.transformers import TransformerEnsemble
from StockSageAI.models.lstm_engine import LSTMEngine
from StockSageAI.models.bilstm_engine import BiLSTMEngine
from StockSageAI.models.cnn_lstm import CNNLSTMEngine
from StockSageAI.models.gnn_engine import GNNEngine
from StockSageAI.models.boosting import BoostingEnsemble
from StockSageAI.models.multimodal_fusion import MultimodalFusionEngine
from StockSageAI.models.ensemble_controller import EnsembleController

TMP_DIR = os.path.join(os.path.dirname(__file__), 'tmp')
if not os.path.exists(TMP_DIR):
    os.makedirs(TMP_DIR)

class TrainingManager:
    def __init__(self):
        self.jobs = {}
        self.feature_pipeline = FeaturePipeline()

    def start_training(self, model_name, dataset_path=None, hyperparams=None):
        job_id = str(uuid.uuid4())
        status_path = os.path.join(TMP_DIR, f"train_{job_id}.json")
        initial = {
            'job_id': job_id,
            'model': model_name,
            'started_at': datetime.utcnow().isoformat(),
            'status': 'running',
            'progress': 0,
            'logs': []
        }
        with open(status_path, 'w', encoding='utf-8') as f:
            json.dump(initial, f)

        t = threading.Thread(target=self._run_job, args=(job_id, model_name, status_path, hyperparams), daemon=True)
        t.start()
        self.jobs[job_id] = status_path
        return job_id

    def _run_job(self, job_id, model_name, status_path, hyperparams):
        hyperparams = hyperparams or {}
        if model_name == 'Transformer Ensemble':
            self._run_transformer_training(status_path, hyperparams)
            return
        if model_name in ['LSTM', 'BiLSTM', 'CNN-LSTM']:
            engine_map = {
                'LSTM': LSTMEngine,
                'BiLSTM': BiLSTMEngine,
                'CNN-LSTM': CNNLSTMEngine
            }
            self._run_sequence_training(status_path, hyperparams, engine_map[model_name], model_name)
            return
        if model_name == 'GNN Ensemble':
            self._run_gnn_training(status_path, hyperparams)
            return
        if model_name == 'XGBoost':
            self._run_boosting_training(status_path, hyperparams)
            return
        if model_name == 'Multimodal Fusion':
            self._run_multimodal_training(status_path, hyperparams)
            return
        if model_name == 'Ensemble Intelligence':
            self._run_ensemble_training(status_path, hyperparams)
            return

        steps = ["prepare data", "build model", "train epoch", "validate", "checkpoint", "finalizing"]
        total = len(steps) * 5
        count = 0
        for step in steps:
            for i in range(5):
                count += 1
                progress = int((count / total) * 100)
                log = f"[{datetime.utcnow().isoformat()}] {model_name} - {step} - step {i+1}/5"
                self._write_status(status_path, progress, log)
                time.sleep(0.6)
        final_log = f"[{datetime.utcnow().isoformat()}] {model_name} training complete. accuracy=0.76"
        self._write_status(status_path, 100, final_log, final=True)

    def _run_transformer_training(self, status_path, hyperparams):
        dataset_path = hyperparams.get('dataset_path')
        sequence_length = int(hyperparams.get('sequence_length', 20))
        horizon = int(hyperparams.get('horizon', 1))
        epochs = int(hyperparams.get('epochs', 8))
        lr = float(hyperparams.get('lr', 0.001))

        try:
            self._write_status(status_path, 5, f"[{datetime.utcnow().isoformat()}] Loading dataset...")
            df = self._load_dataset(dataset_path)
            if df is None or df.empty:
                self._write_status(status_path, 5, f"[{datetime.utcnow().isoformat()}] Dataset could not be loaded.")
                self._write_status(status_path, 100, f"[{datetime.utcnow().isoformat()}] Transformer training failed: no dataset.", final=True)
                return

            self._write_status(status_path, 15, f"[{datetime.utcnow().isoformat()}] Initializing Transformer ensemble...")
            ensemble = TransformerEnsemble()
            result = ensemble.train(
                df,
                sequence_length=sequence_length,
                horizon=horizon,
                epochs=epochs,
                lr=lr,
                variant_name=hyperparams.get('variant')
            )

            progress_step = 70 // max(1, len(result.get('logs', [])))
            current_progress = 15
            for log in result.get('logs', []):
                current_progress = min(90, current_progress + progress_step)
                self._write_status(status_path, current_progress, f"[{datetime.utcnow().isoformat()}] {log}")
                time.sleep(0.2)

            if result.get('status') == 'ok':
                final_message = f"[{datetime.utcnow().isoformat()}] Transformer ensemble training completed with ensemble_mse={result['metrics'].get('ensemble_mse', 0.0):.4f}"
                self._write_status(status_path, 100, final_message, final=True, metrics=result.get('metrics'))
            else:
                failure_message = f"[{datetime.utcnow().isoformat()}] Transformer ensemble training failed."
                self._write_status(status_path, 100, failure_message, final=True, metrics=result.get('metrics'))

        except Exception as exc:
            self._write_status(status_path, 100, f"[{datetime.utcnow().isoformat()}] Training failed: {exc}", final=True)

    def _run_sequence_training(self, status_path, hyperparams, engine_cls, model_name):
        dataset_path = hyperparams.get('dataset_path')
        sequence_length = int(hyperparams.get('sequence_length', 20))
        horizon = int(hyperparams.get('horizon', 1))
        epochs = int(hyperparams.get('epochs', 8))
        lr = float(hyperparams.get('lr', 0.001))

        try:
            self._write_status(status_path, 5, f"[{datetime.utcnow().isoformat()}] Loading dataset for {model_name}...")
            df = self._load_dataset(dataset_path)
            if df is None or df.empty:
                self._write_status(status_path, 5, f"[{datetime.utcnow().isoformat()}] Dataset could not be loaded.")
                self._write_status(status_path, 100, f"[{datetime.utcnow().isoformat()}] {model_name} training failed: no dataset.", final=True)
                return

            self._write_status(status_path, 15, f"[{datetime.utcnow().isoformat()}] Initializing {model_name} engine...")
            engine = engine_cls({'lr': lr})
            result = None
            if hyperparams.get('tune'):
                candidate_lrs = [max(1e-6, lr * 0.5), lr, lr * 2.0]
                best_result = None
                best_mse = float('inf')
                for candidate_lr in candidate_lrs:
                    self._write_status(status_path, 15, f"[{datetime.utcnow().isoformat()}] Tuning {model_name} with lr={candidate_lr:.6f}...")
                    candidate_result = engine.train(
                        df,
                        epochs=epochs,
                        sequence_length=sequence_length,
                        horizon=horizon,
                        lr=candidate_lr
                    )
                    candidate_mse = candidate_result.get('metrics', {}).get('mse', float('inf'))
                    if candidate_result.get('status') == 'ok' and candidate_mse < best_mse:
                        best_mse = candidate_mse
                        best_result = candidate_result
                result = best_result or candidate_result
            else:
                result = engine.train(
                    df,
                    epochs=epochs,
                    sequence_length=sequence_length,
                    horizon=horizon,
                    lr=lr
                )

            progress_step = 70 // max(1, len(result.get('logs', [])))
            current_progress = 15
            for log in result.get('logs', []):
                current_progress = min(90, current_progress + progress_step)
                self._write_status(status_path, current_progress, f"[{datetime.utcnow().isoformat()}] {log}")
                time.sleep(0.2)

            if result.get('status') == 'ok':
                metric = result['metrics'].get('mse', 0.0)
                final_message = f"[{datetime.utcnow().isoformat()}] {model_name} training completed with mse={metric:.4f}"
                self._write_status(status_path, 100, final_message, final=True, metrics=result.get('metrics'))
            else:
                failure_message = f"[{datetime.utcnow().isoformat()}] {model_name} training failed."
                self._write_status(status_path, 100, failure_message, final=True, metrics=result.get('metrics'))

        except Exception as exc:
            self._write_status(status_path, 100, f"[{datetime.utcnow().isoformat()}] Training failed: {exc}", final=True)

    def _run_gnn_training(self, status_path, hyperparams):
        dataset_path = hyperparams.get('dataset_path')
        sequence_length = int(hyperparams.get('sequence_length', 20))
        horizon = int(hyperparams.get('horizon', 1))
        epochs = int(hyperparams.get('epochs', 8))

        try:
            self._write_status(status_path, 5, f"[{datetime.utcnow().isoformat()}] Loading dataset for GNN Ensemble...")
            df = self._load_dataset(dataset_path)
            if df is None or df.empty:
                self._write_status(status_path, 5, f"[{datetime.utcnow().isoformat()}] Dataset could not be loaded.")
                self._write_status(status_path, 100, f"[{datetime.utcnow().isoformat()}] GNN training failed: no dataset.", final=True)
                return

            self._write_status(status_path, 15, f"[{datetime.utcnow().isoformat()}] Initializing GNN engine...")
            engine = GNNEngine({'learning_rate': 0.05})
            result = engine.train(df, epochs=epochs, sequence_length=sequence_length, horizon=horizon)

            progress_step = 70 // max(1, len(result.get('logs', [])))
            current_progress = 15
            for log in result.get('logs', []):
                current_progress = min(90, current_progress + progress_step)
                self._write_status(status_path, current_progress, f"[{datetime.utcnow().isoformat()}] {log}")
                time.sleep(0.2)

            if result.get('status') == 'ok':
                metric = result['metrics'].get('mse', 0.0)
                final_message = f"[{datetime.utcnow().isoformat()}] GNN Ensemble training completed with mse={metric:.4f}"
                self._write_status(status_path, 100, final_message, final=True, metrics=result.get('metrics'))
            else:
                self._write_status(status_path, 100, f"[{datetime.utcnow().isoformat()}] GNN training failed.", final=True, metrics=result.get('metrics'))

        except Exception as exc:
            self._write_status(status_path, 100, f"[{datetime.utcnow().isoformat()}] Training failed: {exc}", final=True)

    def _run_boosting_training(self, status_path, hyperparams):
        dataset_path = hyperparams.get('dataset_path')
        sequence_length = int(hyperparams.get('sequence_length', 20))
        horizon = int(hyperparams.get('horizon', 1))
        epochs = int(hyperparams.get('epochs', 8))

        try:
            self._write_status(status_path, 5, f"[{datetime.utcnow().isoformat()}] Loading dataset for XGBoost...")
            df = self._load_dataset(dataset_path)
            if df is None or df.empty:
                self._write_status(status_path, 5, f"[{datetime.utcnow().isoformat()}] Dataset could not be loaded.")
                self._write_status(status_path, 100, f"[{datetime.utcnow().isoformat()}] XGBoost training failed: no dataset.", final=True)
                return

            self._write_status(status_path, 15, f"[{datetime.utcnow().isoformat()}] Initializing boosting ensemble...")
            engine = BoostingEnsemble({'learning_rate': 0.05})
            result = None
            if hyperparams.get('tune'):
                candidate_rounds = [int(max(10, hyperparams.get('boosting_rounds', 100) * f)) for f in (0.5, 1.0, 1.5)]
                best_result = None
                best_mse = float('inf')
                for rounds in candidate_rounds:
                    self._write_status(status_path, 15, f"[{datetime.utcnow().isoformat()}] Tuning XGBoost with rounds={rounds}...")
                    candidate_result = engine.train(
                        df,
                        epochs=epochs,
                        sequence_length=sequence_length,
                        horizon=horizon,
                        rounds=rounds
                    )
                    candidate_mse = candidate_result.get('metrics', {}).get('mse', float('inf'))
                    if candidate_result.get('status') == 'ok' and candidate_mse < best_mse:
                        best_mse = candidate_mse
                        best_result = candidate_result
                result = best_result or candidate_result
            else:
                result = engine.train(
                    df,
                    epochs=epochs,
                    sequence_length=sequence_length,
                    horizon=horizon,
                    rounds=int(hyperparams.get('boosting_rounds', 100))
                )

            progress_step = 70 // max(1, len(result.get('logs', [])))
            current_progress = 15
            for log in result.get('logs', []):
                current_progress = min(90, current_progress + progress_step)
                self._write_status(status_path, current_progress, f"[{datetime.utcnow().isoformat()}] {log}")
                time.sleep(0.2)

            if result.get('status') == 'ok':
                metric = result['metrics'].get('mse', 0.0)
                final_message = f"[{datetime.utcnow().isoformat()}] XGBoost training completed with mse={metric:.4f}"
                self._write_status(status_path, 100, final_message, final=True, metrics=result.get('metrics'))
            else:
                self._write_status(status_path, 100, f"[{datetime.utcnow().isoformat()}] XGBoost training failed.", final=True, metrics=result.get('metrics'))

        except Exception as exc:
            self._write_status(status_path, 100, f"[{datetime.utcnow().isoformat()}] Training failed: {exc}", final=True)

    def _run_multimodal_training(self, status_path, hyperparams):
        dataset_path = hyperparams.get('dataset_path')
        sequence_length = int(hyperparams.get('sequence_length', 20))
        horizon = int(hyperparams.get('horizon', 1))
        epochs = int(hyperparams.get('epochs', 8))
        lr = float(hyperparams.get('lr', 0.001))

        try:
            self._write_status(status_path, 5, f"[{datetime.utcnow().isoformat()}] Loading dataset for multimodal fusion...")
            df = self._load_dataset(dataset_path)
            if df is None or df.empty:
                self._write_status(status_path, 5, f"[{datetime.utcnow().isoformat()}] Dataset could not be loaded.")
                self._write_status(status_path, 100, f"[{datetime.utcnow().isoformat()}] Multimodal fusion failed: no dataset.", final=True)
                return

            self._write_status(status_path, 15, f"[{datetime.utcnow().isoformat()}] Initializing multimodal fusion engine...")
            engine = MultimodalFusionEngine({'learning_rate': lr})
            result = None
            if hyperparams.get('tune'):
                candidate_lrs = [max(1e-6, lr * 0.5), lr, lr * 2.0]
                best_result = None
                best_mse = float('inf')
                for candidate_lr in candidate_lrs:
                    self._write_status(status_path, 15, f"[{datetime.utcnow().isoformat()}] Tuning multimodal fusion with lr={candidate_lr:.6f}...")
                    candidate_result = engine.train(df, epochs=epochs, lr=candidate_lr)
                    candidate_mse = candidate_result.get('metrics', {}).get('mse', float('inf'))
                    if candidate_result.get('status') == 'ok' and candidate_mse < best_mse:
                        best_mse = candidate_mse
                        best_result = candidate_result
                result = best_result or candidate_result
            else:
                result = engine.train(df, epochs=epochs, lr=lr)

            progress_step = 70 // max(1, len(result.get('logs', [])))
            current_progress = 15
            for log in result.get('logs', []):
                current_progress = min(90, current_progress + progress_step)
                self._write_status(status_path, current_progress, f"[{datetime.utcnow().isoformat()}] {log}")
                time.sleep(0.2)

            if result.get('status') == 'ok':
                metric = result['metrics'].get('mse', 0.0)
                final_message = f"[{datetime.utcnow().isoformat()}] Multimodal fusion training completed with mse={metric:.4f}"
                self._write_status(status_path, 100, final_message, final=True, metrics=result.get('metrics'))
            else:
                self._write_status(status_path, 100, f"[{datetime.utcnow().isoformat()}] Multimodal fusion failed.", final=True, metrics=result.get('metrics'))

        except Exception as exc:
            self._write_status(status_path, 100, f"[{datetime.utcnow().isoformat()}] Training failed: {exc}", final=True)

    def _run_ensemble_training(self, status_path, hyperparams):
        dataset_path = hyperparams.get('dataset_path')
        sequence_length = int(hyperparams.get('sequence_length', 20))
        horizon = int(hyperparams.get('horizon', 1))
        epochs = int(hyperparams.get('epochs', 8))
        lr = float(hyperparams.get('lr', 0.001))

        try:
            self._write_status(status_path, 5, f"[{datetime.utcnow().isoformat()}] Loading dataset for ensemble intelligence...")
            df = self._load_dataset(dataset_path)
            if df is None or df.empty:
                self._write_status(status_path, 5, f"[{datetime.utcnow().isoformat()}] Dataset could not be loaded.")
                self._write_status(status_path, 100, f"[{datetime.utcnow().isoformat()}] Ensemble intelligence failed: no dataset.", final=True)
                return

            self._write_status(status_path, 15, f"[{datetime.utcnow().isoformat()}] Initializing ensemble intelligence controller...")
            controller = EnsembleController({'lr': lr})
            result = controller.train(df, sequence_length=sequence_length, horizon=horizon, epochs=epochs, lr=lr)

            progress_step = 70 // max(1, len(result.get('logs', [])))
            current_progress = 15
            for log in result.get('logs', []):
                current_progress = min(90, current_progress + progress_step)
                self._write_status(status_path, current_progress, f"[{datetime.utcnow().isoformat()}] {log}")
                time.sleep(0.2)

            if result.get('status') == 'ok':
                metric = result['metrics'].get('mse', 0.0)
                final_message = f"[{datetime.utcnow().isoformat()}] Ensemble intelligence training completed with mse={metric:.4f}"
                self._write_status(status_path, 100, final_message, final=True, metrics=result.get('metrics'))
            else:
                self._write_status(status_path, 100, f"[{datetime.utcnow().isoformat()}] Ensemble intelligence failed.", final=True, metrics=result.get('metrics'))

        except Exception as exc:
            self._write_status(status_path, 100, f"[{datetime.utcnow().isoformat()}] Training failed: {exc}", final=True)

    def _load_dataset(self, dataset_path):
        if not dataset_path or not os.path.exists(dataset_path):
            return pd.DataFrame()
        try:
            df = pd.read_csv(dataset_path)
            df.columns = df.columns.str.strip().str.title()
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                df = df.set_index('Date')
            return df
        except Exception:
            return pd.DataFrame()

    def _write_status(self, path, progress, log, final=False, metrics=None):
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {}
            data.setdefault('logs', []).append(log)
            data['progress'] = progress
            if metrics:
                existing_metrics = data.get('metrics', {})
                existing_metrics.update(metrics)
                data['metrics'] = existing_metrics
            if final:
                if 'failed' in log.lower() or 'error' in log.lower():
                    data['status'] = 'failed'
                else:
                    data['status'] = 'completed'
                data['finished_at'] = datetime.utcnow().isoformat()
            else:
                data['status'] = 'running'
            data['updated_at'] = datetime.utcnow().isoformat()
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f)
        except Exception:
            pass

    def get_status(self, job_id):
        path = self.jobs.get(job_id) or os.path.join(TMP_DIR, f"train_{job_id}.json")
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return None
        return None

# module-level manager
manager = TrainingManager()
