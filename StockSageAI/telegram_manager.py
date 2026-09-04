"""
Telegram Manager - Main orchestrator for the Daily Telegram Forecast System
Coordinates all components: telegram service, forecast generation, scheduling
"""

import logging
import threading
from typing import Dict, Optional, Callable
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

IST = pytz.timezone('Asia/Kolkata')

class TelegramForecastManager:
    """Main manager for Telegram daily forecast system"""
    
    def __init__(self):
        """Initialize manager with all components"""
        logger.info("🚀 Initializing Telegram Forecast Manager...")
        
        # Import all components
        self.telegram_service = None
        self.notifier = None
        self.scheduler = None
        self.api = None
        self.db = None
        self.stock_selector = None
        self.forecast_generator = None
        
        self._scheduler_thread = None
        self._is_running = False
        
        try:
            self._initialize_components()
            logger.info("✅ Telegram Forecast Manager initialized successfully")
        except Exception as e:
            logger.error(f"❌ Error initializing manager: {str(e)}")
            raise
    
    def _initialize_components(self):
        """Initialize all system components"""
        from StockSageAI.telegram_service import get_telegram_service
        from StockSageAI.telegram_notifier import get_telegram_notifier
        from StockSageAI.forecast_scheduler import get_forecast_scheduler
        from StockSageAI.telegram_api import get_telegram_api
        from StockSageAI.database import Database
        from StockSageAI.stock_selector import get_stock_selector
        from StockSageAI.forecast_generator import get_forecast_generator
        
        # Initialize services
        try:
            self.telegram_service = get_telegram_service()
        except Exception as e:
            logger.warning(f"⚠️ Telegram service initialization failed: {str(e)}")
            self.telegram_service = None
        
        self.notifier = get_telegram_notifier()
        self.scheduler = get_forecast_scheduler(callback=self.generate_and_send_forecast)
        self.api = get_telegram_api(self.telegram_service, self.notifier, self.scheduler)
        self.db = Database()
        self.stock_selector = get_stock_selector()
        self.forecast_generator = get_forecast_generator()
        
        logger.info("✅ All components initialized")
    
    def start_scheduler(self, run_in_background: bool = True):
        """
        Start the daily forecast scheduler
        
        Args:
            run_in_background: If True, run scheduler in background thread
        """
        if self._is_running:
            logger.warning("⚠️ Scheduler is already running")
            return
        
        if not self.scheduler:
            logger.error("❌ Scheduler not initialized")
            return
        
        logger.info("🚀 Starting Telegram Forecast Scheduler...")
        
        self._is_running = True
        
        if run_in_background:
            # Run scheduler in background thread
            self._scheduler_thread = threading.Thread(
                target=self.scheduler.start_scheduler,
                daemon=True
            )
            self._scheduler_thread.start()
            logger.info("✅ Scheduler started in background thread")
        else:
            # Run scheduler in blocking mode (for deployment)
            logger.info("⏳ Starting scheduler in blocking mode...")
            self.scheduler.start_scheduler()
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        if self.scheduler:
            self.scheduler.stop()
            self._is_running = False
            logger.info("🛑 Scheduler stopped")
    
    def _get_ranked_top_10_stocks(self, refresh: bool = False) -> list:
        """Return the live ranked Top 10 market universe list used by daily Telegram broadcasts."""
        if self.stock_selector is None:
            from StockSageAI.stock_selector import get_stock_selector
            self.stock_selector = get_stock_selector()

        ranked = self.stock_selector.get_top_10_stocks(use_dynamic=True, refresh=refresh)
        return list(ranked) if ranked else []

    def generate_and_send_forecast(self) -> bool:
        """
        Main forecast execution function
        Called by scheduler at 10:15 AM IST daily
        
        Workflow:
        1. Check if trading day
        2. Select Top 10 stocks
        3. Validate stocks
        4. Generate forecasts
        5. Format message
        6. Send to Telegram
        7. Save to database
        
        Returns:
            True if successful, False otherwise
        """
        try:
            from datetime import date
            
            logger.info("\n" + "="*70)
            logger.info("📊 DAILY TELEGRAM FORECAST GENERATION")
            logger.info("="*70)
            
            now = datetime.now(IST)
            current_date = now.date()
            
            # Step 1: Check if trading day
            if not self.scheduler.is_trading_day(now):
                logger.info("⏸️ Not a trading day, skipping forecast")
                return False
            
            logger.info(f"✅ Trading day confirmed: {current_date}")
            
            # Step 2: Select Top 10 stocks
            logger.info("📊 Step 1: Selecting Top 10 stocks...")
            stocks = self._get_ranked_top_10_stocks(refresh=True)
            logger.info(f"   Selected {len(stocks)} stocks: {stocks}")
            
            # Step 3: Validate stocks
            logger.info("✓ Step 2: Validating stocks...")
            valid_stocks, invalid_stocks = self.stock_selector.validate_stocks(stocks)
            if invalid_stocks:
                logger.warning(f"   ⚠️ Invalid stocks: {invalid_stocks}")
            logger.info(f"   Valid stocks: {len(valid_stocks)}/{len(stocks)}")
            
            if not valid_stocks:
                logger.error("❌ No valid stocks to forecast")
                return False
            
            # Step 4: Generate forecasts
            logger.info("🧠 Step 3: Generating forecasts...")
            forecasts = self.forecast_generator.generate_batch_forecasts(valid_stocks)
            
            # Count results
            successful = sum(1 for f in forecasts.values() if f.get('success'))
            failed = len(forecasts) - successful
            
            logger.info(f"   Generated: {successful} successful, {failed} failed")
            
            if successful == 0:
                logger.error("❌ No forecasts generated")
                return False
            
            # Step 5: Format message
            logger.info("📝 Step 4: Formatting Telegram message...")
            model_performance = self.db.get_model_performance_summary()
            message = self.notifier.format_daily_forecast(forecasts, model_performance)
            logger.info(f"   Message formatted ({len(message)} chars)")
            
            # Step 6: Send to Telegram
            if not self.telegram_service:
                logger.error("❌ Telegram service not available")
                return False
            
            logger.info("📤 Step 5: Sending to Telegram...")
            send_success, message_ids = self.telegram_service.send_long_message(message)
            
            if not send_success:
                logger.error("❌ Failed to send to Telegram")
                # Save failure to database
                self.db.save_notification(
                    current_date,
                    'failed',
                    successful,
                    failed,
                    [],
                    "Telegram API call failed"
                )
                return False
            
            logger.info(f"✅ Sent successfully! Message IDs: {message_ids}")
            
            # Step 7: Save forecasts to database
            logger.info("💾 Step 6: Saving to database...")
            for symbol, forecast_data in forecasts.items():
                if forecast_data.get('success'):
                    self.db.save_forecast(
                        current_date,
                        symbol,
                        forecast_data.get('current_price'),
                        forecast_data.get('forecasts', {}),
                        forecast_data.get('signals', {}),
                        forecast_data.get('confidence', {}),
                        forecast_data.get('sentiment_score'),
                        forecast_data.get('data_timestamp')
                    )
            
            # Save notification record
            self.db.save_notification(
                current_date,
                'sent',
                successful,
                failed,
                message_ids if isinstance(message_ids, list) else [message_ids]
            )
            
            logger.info("✅ Forecasts saved to database")
            
            # Final summary
            logger.info("\n" + "="*70)
            logger.info(f"✅ FORECAST COMPLETED SUCCESSFULLY")
            logger.info(f"   Date: {current_date}")
            logger.info(f"   Stocks: {successful}/{len(forecasts)}")
            logger.info(f"   Message IDs: {message_ids}")
            logger.info("="*70 + "\n")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in forecast generation: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            try:
                from datetime import date
                self.db.save_notification(
                    date.today(),
                    'failed',
                    0,
                    0,
                    [],
                    str(e)
                )
            except:
                pass
            
            return False
    
    def send_manual_forecast(self) -> bool:
        """
        Manually trigger forecast (for admin "Run Now" button)
        
        Returns:
            Success status
        """
        logger.info("🔄 Manual forecast triggered by user")
        return self.generate_and_send_forecast()
    
    def get_system_status(self) -> Dict:
        """Get complete system status"""
        return self.api.get_status() if self.api else {}
    
    def test_telegram(self) -> Dict:
        """Test Telegram connection"""
        return self.api.test_telegram_connection() if self.api else {}
    
    def send_test_message(self) -> Dict:
        """Send test message"""
        return self.api.send_test_message() if self.api else {}
    
    def preview_forecast(self) -> Dict:
        """Preview forecast without sending"""
        try:
            stocks = self._get_ranked_top_10_stocks(refresh=True)
            forecasts = self.forecast_generator.generate_batch_forecasts(stocks)
            return self.api.preview_forecast(forecasts) if self.api else {}
        except Exception as e:
            logger.error(f"Error generating preview: {str(e)}")
            return {"error": str(e)}
    
    def get_forecast_history(self, symbol: Optional[str] = None, days: int = 30) -> list:
        """Get forecast history"""
        return self.db.get_forecast_history(symbol, days) if self.db else []


# Singleton instance
_manager = None

def get_telegram_forecast_manager() -> TelegramForecastManager:
    """Get or create singleton manager instance"""
    global _manager
    if _manager is None:
        _manager = TelegramForecastManager()
    return _manager
