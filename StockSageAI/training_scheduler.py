"""
Scheduled Automated Training for SP 07 StockSageAI
Automatic model retraining with drift detection and versioning
"""

import schedule
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import json
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class TrainingScheduler:
    """Schedule and manage automated model training"""
    
    def __init__(self, models_dir: str = 'StockSageAI/models'):
        self.models_dir = models_dir
        self.jobs = {}
        self.training_history = []
        self.model_versions = {}
        self.scheduler_running = False
        self._init_scheduler()
    
    def _init_scheduler(self):
        """Initialize scheduler"""
        Path(self.models_dir).mkdir(parents=True, exist_ok=True)
        self._load_training_history()
    
    def schedule_daily_training(self, models: List[str], time: str = '02:00') -> Dict:
        """Schedule daily model training"""
        
        job = {
            'id': f"daily_{datetime.now().timestamp()}",
            'frequency': 'daily',
            'time': time,
            'models': models,
            'status': 'scheduled',
            'created_at': datetime.now().isoformat(),
            'next_run': self._calculate_next_run('daily', time)
        }
        
        self.jobs[job['id']] = job
        
        # Schedule with APScheduler or schedule library
        schedule.every().day.at(time).do(
            self._run_training_job,
            models=models,
            job_id=job['id']
        )
        
        logger.info(f"Scheduled daily training for {models} at {time}")
        
        return job
    
    def schedule_weekly_training(self, models: List[str], day: str = 'monday',
                                time: str = '02:00') -> Dict:
        """Schedule weekly model training"""
        
        job = {
            'id': f"weekly_{datetime.now().timestamp()}",
            'frequency': 'weekly',
            'day': day,
            'time': time,
            'models': models,
            'status': 'scheduled',
            'created_at': datetime.now().isoformat(),
            'next_run': self._calculate_next_run('weekly', time, day)
        }
        
        self.jobs[job['id']] = job
        
        # Schedule weekly training
        day_map = {
            'monday': schedule.every().monday,
            'tuesday': schedule.every().tuesday,
            'wednesday': schedule.every().wednesday,
            'thursday': schedule.every().thursday,
            'friday': schedule.every().friday,
            'saturday': schedule.every().saturday,
            'sunday': schedule.every().sunday
        }
        
        if day.lower() in day_map:
            day_map[day.lower()].at(time).do(
                self._run_training_job,
                models=models,
                job_id=job['id']
            )
        
        logger.info(f"Scheduled {day} weekly training for {models} at {time}")
        
        return job
    
    def schedule_adaptive_training(self, models: List[str], drift_threshold: float = 0.05) -> Dict:
        """Schedule training based on model drift detection"""
        
        job = {
            'id': f"adaptive_{datetime.now().timestamp()}",
            'frequency': 'adaptive',
            'drift_threshold': drift_threshold,
            'models': models,
            'status': 'active',
            'created_at': datetime.now().isoformat(),
            'last_drift_check': None,
            'drift_triggers': 0
        }
        
        self.jobs[job['id']] = job
        
        # Check for drift daily
        schedule.every().day.do(
            self._check_model_drift,
            job_id=job['id'],
            models=models,
            threshold=drift_threshold
        )
        
        logger.info(f"Scheduled adaptive training with drift threshold {drift_threshold}")
        
        return job
    
    def _run_training_job(self, models: List[str], job_id: str) -> Dict:
        """Run training job"""
        
        try:
            start_time = datetime.now()
            
            training_result = {
                'job_id': job_id,
                'started_at': start_time.isoformat(),
                'models_trained': [],
                'models_failed': [],
                'metrics': {}
            }
            
            # Train each model
            for model_name in models:
                try:
                    result = self._train_model(model_name)
                    
                    if result['success']:
                        training_result['models_trained'].append(model_name)
                        training_result['metrics'][model_name] = result['metrics']
                        
                        # Save version
                        self._save_model_version(model_name, result)
                    else:
                        training_result['models_failed'].append(model_name)
                        
                except Exception as e:
                    logger.error(f"Error training {model_name}: {e}")
                    training_result['models_failed'].append(model_name)
            
            end_time = datetime.now()
            training_result['completed_at'] = end_time.isoformat()
            training_result['duration_seconds'] = (end_time - start_time).total_seconds()
            training_result['status'] = 'completed'
            
            # Update job status
            if job_id in self.jobs:
                self.jobs[job_id]['status'] = 'completed'
                self.jobs[job_id]['last_run'] = end_time.isoformat()
                self.jobs[job_id]['next_run'] = self._calculate_next_run(
                    self.jobs[job_id].get('frequency', 'daily'),
                    self.jobs[job_id].get('time', '02:00')
                )
            
            # Save to history
            self.training_history.append(training_result)
            self._save_training_history()
            
            logger.info(f"Training job {job_id} completed: "
                       f"{len(training_result['models_trained'])} trained, "
                       f"{len(training_result['models_failed'])} failed")
            
            return training_result
            
        except Exception as e:
            logger.error(f"Error in training job {job_id}: {e}")
            return {
                'job_id': job_id,
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _train_model(self, model_name: str) -> Dict:
        """Train individual model"""
        
        try:
            # Import and train the model
            # This is a placeholder - actual implementation depends on model type
            
            result = {
                'success': True,
                'model': model_name,
                'trained_at': datetime.now().isoformat(),
                'metrics': {
                    'mse': 0.15 + (hash(model_name) % 10) * 0.01,
                    'rmse': 0.39 + (hash(model_name) % 10) * 0.01,
                    'accuracy': 85 + (hash(model_name) % 10),
                    'training_time': 120 + (hash(model_name) % 100)
                }
            }
            
            logger.info(f"Trained {model_name}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error training model {model_name}: {e}")
            return {
                'success': False,
                'model': model_name,
                'error': str(e)
            }
    
    def _check_model_drift(self, job_id: str, models: List[str],
                          threshold: float) -> Dict:
        """Check for model drift"""
        
        try:
            drift_results = {}
            trigger_retraining = False
            
            for model_name in models:
                # Calculate drift score (simplified)
                drift_score = self._calculate_drift_score(model_name)
                
                drift_results[model_name] = {
                    'drift_score': drift_score,
                    'drift_detected': drift_score > threshold,
                    'threshold': threshold
                }
                
                if drift_score > threshold:
                    trigger_retraining = True
                    logger.warning(f"Model drift detected in {model_name}: {drift_score}")
            
            # Update job info
            if job_id in self.jobs:
                self.jobs[job_id]['last_drift_check'] = datetime.now().isoformat()
                if trigger_retraining:
                    self.jobs[job_id]['drift_triggers'] += 1
                    # Trigger immediate retraining
                    self._run_training_job(models, f"{job_id}_drift_triggered")
            
            return {
                'job_id': job_id,
                'check_time': datetime.now().isoformat(),
                'drift_results': drift_results,
                'retraining_triggered': trigger_retraining
            }
            
        except Exception as e:
            logger.error(f"Error checking model drift: {e}")
            return {'error': str(e)}
    
    def _calculate_drift_score(self, model_name: str) -> float:
        """Calculate model drift score"""
        
        # Simplified drift calculation
        # In production, compare model predictions on recent data
        # against actual values to detect performance degradation
        
        if not self.model_versions.get(model_name):
            return 0.0
        
        recent_version = self.model_versions[model_name][-1] if self.model_versions[model_name] else None
        
        if not recent_version:
            return 0.0
        
        # Compare metrics with historical average
        base_mse = recent_version.get('metrics', {}).get('mse', 1.0)
        
        # Simulate drift score (in production, calculate from actual data)
        drift_score = min(base_mse * (1 + (len(self.model_versions[model_name]) * 0.02)), 0.5)
        
        return drift_score
    
    def _save_model_version(self, model_name: str, result: Dict):
        """Save model version information"""
        
        if model_name not in self.model_versions:
            self.model_versions[model_name] = []
        
        version = {
            'version_id': len(self.model_versions[model_name]) + 1,
            'model': model_name,
            'trained_at': datetime.now().isoformat(),
            'metrics': result.get('metrics', {}),
            'status': 'active'
        }
        
        self.model_versions[model_name].append(version)
        
        # Save to file
        version_file = os.path.join(self.models_dir, f"{model_name}_versions.json")
        try:
            with open(version_file, 'w') as f:
                json.dump(self.model_versions[model_name], f, indent=2)
        except:
            pass
    
    def _save_training_history(self):
        """Save training history"""
        
        history_file = os.path.join(self.models_dir, 'training_history.json')
        try:
            with open(history_file, 'w') as f:
                json.dump(self.training_history[-100:], f, indent=2)  # Keep last 100
        except:
            pass
    
    def _load_training_history(self):
        """Load training history"""
        
        history_file = os.path.join(self.models_dir, 'training_history.json')
        try:
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    self.training_history = json.load(f)
        except:
            pass
    
    def get_training_status(self) -> Dict:
        """Get overall training status"""
        
        return {
            'scheduler_running': self.scheduler_running,
            'active_jobs': len([j for j in self.jobs.values() if j['status'] == 'scheduled']),
            'total_jobs': len(self.jobs),
            'training_history_count': len(self.training_history),
            'jobs': self.jobs,
            'last_training': self.training_history[-1] if self.training_history else None
        }
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get status of specific job"""
        return self.jobs.get(job_id)
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel scheduled job"""
        
        if job_id in self.jobs:
            self.jobs[job_id]['status'] = 'cancelled'
            logger.info(f"Job {job_id} cancelled")
            return True
        
        return False
    
    def start_scheduler(self):
        """Start the scheduler in background thread"""
        
        if self.scheduler_running:
            return
        
        self.scheduler_running = True
        
        def run_scheduler():
            while self.scheduler_running:
                schedule.run_pending()
                import time
                time.sleep(60)  # Check every minute
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        logger.info("Training scheduler started")
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.scheduler_running = False
        logger.info("Training scheduler stopped")
    
    def _calculate_next_run(self, frequency: str, time: str,
                           day: str = None) -> str:
        """Calculate next run time"""
        
        now = datetime.now()
        
        if frequency == 'daily':
            hour, minute = map(int, time.split(':'))
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            if next_run <= now:
                next_run += timedelta(days=1)
        
        elif frequency == 'weekly':
            next_run = now + timedelta(weeks=1)
        
        else:
            next_run = now + timedelta(days=1)
        
        return next_run.isoformat()


# Singleton instance
_training_scheduler = None


def get_training_scheduler():
    global _training_scheduler
    if _training_scheduler is None:
        _training_scheduler = TrainingScheduler()
    return _training_scheduler
