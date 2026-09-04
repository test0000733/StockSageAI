"""
Telegram API - Backend endpoints for Telegram operations
Provides REST API for sending forecasts, testing, and getting status
"""

import logging
import json
from typing import Dict, Optional
from datetime import datetime
from functools import wraps

logger = logging.getLogger(__name__)

# These functions can be integrated into existing API framework
# (FastAPI, Flask, or as Streamlit backend functions)

class TelegramAPI:
    """Backend API for Telegram operations"""
    
    def __init__(self, telegram_service=None, notifier=None, scheduler=None):
        """
        Initialize API with dependencies
        
        Args:
            telegram_service: TelegramService instance
            notifier: TelegramNotifier instance
            scheduler: ForecastScheduler instance
        """
        self.telegram_service = telegram_service
        self.notifier = notifier
        self.scheduler = scheduler
        
        logger.info("✅ Telegram API initialized")
    
    def test_telegram_connection(self) -> Dict:
        """
        Test Telegram connection
        
        Response:
        {
            "success": bool,
            "message": str,
            "timestamp": ISO datetime,
            "bot_info": {"username": str, "id": int} (if connected)
        }
        """
        response = {
            "success": False,
            "message": "",
            "timestamp": datetime.now().isoformat(),
            "bot_info": None
        }
        
        if not self.telegram_service:
            response["message"] = "Telegram service not available"
            return response
        
        is_connected, status_msg = self.telegram_service.test_connection()
        
        response["success"] = is_connected
        response["message"] = status_msg
        
        if is_connected:
            chat_info = self.telegram_service.get_chat_info()
            if chat_info:
                response["bot_info"] = {
                    "chat_id": chat_info.get('id'),
                    "type": chat_info.get('type'),
                    "title": chat_info.get('title', 'Personal')
                }
        
        return response
    
    def send_test_message(self) -> Dict:
        """
        Send test message to Telegram
        
        Response:
        {
            "success": bool,
            "message_id": str (if sent),
            "error": str (if failed),
            "timestamp": ISO datetime
        }
        """
        response = {
            "success": False,
            "message_id": None,
            "error": None,
            "timestamp": datetime.now().isoformat()
        }
        
        if not self.telegram_service or not self.notifier:
            response["error"] = "Telegram not configured"
            return response
        
        try:
            test_msg = self.notifier.format_test_message()
            success, msg_id = self.telegram_service.send_message(test_msg)
            
            response["success"] = success
            response["message_id"] = msg_id
            
            if not success:
                response["error"] = "Failed to send message"
            
        except Exception as e:
            response["error"] = str(e)
            logger.error(f"❌ Test message error: {str(e)}")
        
        return response
    
    def send_forecast(self, forecasts: Dict, validate: bool = True) -> Dict:
        """
        Send forecast to Telegram
        
        Args:
            forecasts: Dict of symbol -> forecast results
            validate: If True, validate before sending
            
        Response:
        {
            "success": bool,
            "message_ids": List[str],
            "stocks_sent": int,
            "stocks_failed": int,
            "error": str (if failed),
            "timestamp": ISO datetime
        }
        """
        response = {
            "success": False,
            "message_ids": [],
            "stocks_sent": 0,
            "stocks_failed": 0,
            "error": None,
            "timestamp": datetime.now().isoformat()
        }
        
        if not forecasts:
            response["error"] = "No forecasts provided"
            return response
        
        if not self.telegram_service or not self.notifier:
            response["error"] = "Telegram not configured"
            return response
        
        try:
            # Count successes
            for symbol, forecast in forecasts.items():
                if forecast.get('success'):
                    response["stocks_sent"] += 1
                else:
                    response["stocks_failed"] += 1
            
            # Format message
            logger.info(f"📨 Formatting forecast message ({response['stocks_sent']} stocks)...")
            message = self.notifier.format_daily_forecast(forecasts)
            
            # Send message
            logger.info("📤 Sending forecast to Telegram...")
            success, msg_ids = self.telegram_service.send_long_message(message)
            
            response["success"] = success
            if isinstance(msg_ids, list):
                response["message_ids"] = [str(m) for m in msg_ids if m]
            elif msg_ids:
                response["message_ids"] = [str(msg_ids)]
            
            if not success:
                response["error"] = "Failed to send to Telegram"
            
        except Exception as e:
            response["error"] = str(e)
            logger.error(f"❌ Send forecast error: {str(e)}")
        
        return response
    
    def preview_forecast(self, forecasts: Dict) -> Dict:
        """
        Preview forecast message without sending
        
        Response:
        {
            "success": bool,
            "preview_message": str,
            "message_length": int,
            "chunks_needed": int,
            "stocks_previewed": int
        }
        """
        response = {
            "success": False,
            "preview_message": "",
            "message_length": 0,
            "chunks_needed": 1,
            "stocks_previewed": 0
        }
        
        if not forecasts:
            response["preview_message"] = "No forecasts to preview"
            return response
        
        if not self.notifier:
            response["preview_message"] = "Notifier not available"
            return response
        
        try:
            # Count successful forecasts
            successful = [f for f in forecasts.values() if f.get('success')]
            response["stocks_previewed"] = len(successful)
            
            # Format message
            message = self.notifier.format_preview_message(forecasts, is_preview=True)
            response["preview_message"] = message
            response["message_length"] = len(message)
            
            # Calculate chunks needed (Telegram limit: 4096 chars)
            response["chunks_needed"] = (len(message) + 4095) // 4096
            response["success"] = True
            
        except Exception as e:
            response["preview_message"] = f"Error generating preview: {str(e)}"
            logger.error(f"❌ Preview error: {str(e)}")
        
        return response
    
    def get_status(self) -> Dict:
        """
        Get system status
        
        Response:
        {
            "telegram_connection": "Connected"|"Disconnected",
            "scheduler_status": "Active"|"Inactive",
            "next_scheduled_run": str (ISO datetime),
            "last_successful_run": str or None,
            "last_failed_run": str or None,
            "is_enabled": bool,
            "schedule_time": "HH:MM",
            "timezone": "Asia/Kolkata",
            "trading_day_today": bool
        }
        """
        response = {
            "telegram_connection": "Disconnected",
            "scheduler_status": "Inactive",
            "next_scheduled_run": None,
            "last_successful_run": None,
            "last_failed_run": None,
            "is_enabled": False,
            "schedule_time": "10:15",
            "timezone": "Asia/Kolkata",
            "trading_day_today": False
        }
        
        # Check Telegram connection
        if self.telegram_service:
            is_connected, _ = self.telegram_service.test_connection()
            response["telegram_connection"] = "Connected" if is_connected else "Disconnected"
        
        # Check scheduler status
        if self.scheduler:
            response["is_enabled"] = self.scheduler.enabled
            response["scheduler_status"] = "Active" if self.scheduler.is_running else "Inactive"
            response["schedule_time"] = self.scheduler.schedule_time
            response["trading_day_today"] = self.scheduler.is_trading_day()
            response["next_scheduled_run"] = self.scheduler.get_next_run_time()
            
            if self.scheduler.last_execution_date:
                response["last_successful_run"] = self.scheduler.last_execution_date.isoformat()
        
        return response
    
    def run_manual_forecast(self) -> Dict:
        """
        Trigger manual forecast run
        
        Response:
        {
            "success": bool,
            "message": str,
            "timestamp": ISO datetime
        }
        """
        response = {
            "success": False,
            "message": "",
            "timestamp": datetime.now().isoformat()
        }
        
        if not self.scheduler:
            response["message"] = "Scheduler not available"
            return response
        
        try:
            logger.info("🔄 Manual forecast triggered via API")
            result = self.scheduler.run_manual_forecast()
            
            response["success"] = result
            response["message"] = "Forecast generated and sent" if result else "Forecast generation failed"
            
        except Exception as e:
            response["message"] = f"Error: {str(e)}"
            logger.error(f"❌ Manual forecast error: {str(e)}")
        
        return response
    
    def get_retry_status(self) -> Dict:
        """
        Get retry/recovery status for failed sends
        
        Response:
        {
            "pending_retries": int,
            "last_retry": str (ISO datetime) or None,
            "retry_queue": List[Dict]
        }
        """
        # This can be extended to track failed sends and retry them
        return {
            "pending_retries": 0,
            "last_retry": None,
            "retry_queue": []
        }


def require_auth(func):
    """Decorator for API endpoints requiring authentication"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Add authentication logic here
        # For now, just call the function
        return func(*args, **kwargs)
    return wrapper


# Singleton instance
_telegram_api = None

def get_telegram_api(
    telegram_service=None,
    notifier=None,
    scheduler=None
) -> TelegramAPI:
    """Get or create singleton API instance"""
    global _telegram_api
    if _telegram_api is None:
        _telegram_api = TelegramAPI(telegram_service, notifier, scheduler)
    return _telegram_api
