"""
Forecast Scheduler - Runs daily at 10:15 AM IST
Handles scheduling, idempotency, and notification for trading day validation
"""

import os
import logging
import schedule
import time
from typing import Callable, Optional
from datetime import datetime, time as dt_time
import pytz
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# IST timezone
IST = pytz.timezone('Asia/Kolkata')

# Indian stock market holidays (2024-2026)
INDIAN_MARKET_HOLIDAYS = [
    # 2024
    (2024, 1, 26),   # Republic Day
    (2024, 3, 8),    # Maha Shivaratri
    (2024, 3, 25),   # Holi
    (2024, 3, 29),   # Good Friday
    (2024, 4, 11),   # Eid ul-Fitr
    (2024, 4, 17),   # Ram Navami
    (2024, 4, 21),   # Mahavir Jayanti
    (2024, 5, 23),   # Buddha Purnima
    (2024, 7, 17),   # Muharram
    (2024, 8, 15),   # Independence Day
    (2024, 8, 26),   # Janmashtami
    (2024, 9, 16),   # Milad un-Nabi
    (2024, 10, 2),   # Gandhi Jayanti
    (2024, 10, 12),  # Dussehra
    (2024, 10, 31),  # Diwali
    (2024, 11, 1),   # Diwali (Day 2)
    (2024, 11, 15),  # Guru Nanak Jayanti
    (2024, 12, 25),  # Christmas
    # 2025
    (2025, 1, 26),   # Republic Day
    (2025, 3, 8),    # Maha Shivaratri
    (2025, 3, 14),   # Holi
    (2025, 4, 18),   # Good Friday
    (2025, 4, 21),   # Ram Navami
    (2025, 5, 23),   # Buddha Purnima
    (2025, 6, 28),   # Eid ul-Adha
    (2025, 7, 7),    # Muharram
    (2025, 8, 15),   # Independence Day
    (2025, 8, 25),   # Janmashtami
    (2025, 9, 16),   # Milad un-Nabi
    (2025, 10, 2),   # Gandhi Jayanti
    (2025, 10, 1),   # Dussehra
    (2025, 10, 20),  # Diwali
    (2025, 11, 5),   # Guru Nanak Jayanti
    (2025, 12, 25),  # Christmas
    # 2026
    (2026, 1, 26),   # Republic Day
    (2026, 3, 25),   # Holi
    (2026, 4, 2),    # Good Friday
    (2026, 4, 10),   # Eid ul-Fitr
    (2026, 4, 14),   # Ambedkar Jayanti
    (2026, 5, 15),   # Buddha Purnima
    (2026, 7, 7),    # Muharram
    (2026, 8, 15),   # Independence Day
    (2026, 9, 7),    # Janmashtami
    (2026, 10, 2),   # Gandhi Jayanti
    (2026, 10, 1),   # Dussehra
    (2026, 10, 20),  # Diwali
    (2026, 11, 5),   # Guru Nanak Jayanti
    (2026, 12, 25),  # Christmas
]

class ForecastScheduler:
    """Manages daily forecast scheduling at 10:15 AM IST"""
    
    def __init__(self, forecast_callback: Optional[Callable] = None):
        """
        Initialize scheduler
        
        Args:
            forecast_callback: Function to call for forecast generation
        """
        self.schedule_time = os.getenv('FORECAST_SCHEDULE_TIME', '10:15')
        self.enabled = os.getenv('FORECAST_ENABLED', 'true').lower() == 'true'
        self.forecast_callback = forecast_callback
        self.last_execution_date = None
        self.is_running = False
        
        logger.info(f"✅ Forecast Scheduler initialized (Time: {self.schedule_time} IST)")
    
    def is_trading_day(self, check_date: Optional[datetime] = None) -> bool:
        """
        Check if a date is a valid NSE/BSE trading day
        
        Returns:
            True if trading day, False otherwise
        """
        if check_date is None:
            check_date = datetime.now(IST)
        
        # Check if weekend (Saturday=5, Sunday=6)
        if check_date.weekday() >= 5:
            logger.debug(f"⏸️ {check_date.date()} is a weekend")
            return False
        
        # Check if market holiday
        date_tuple = (check_date.year, check_date.month, check_date.day)
        if date_tuple in INDIAN_MARKET_HOLIDAYS:
            logger.info(f"🎉 {check_date.date()} is a market holiday")
            return False
        
        logger.debug(f"✅ {check_date.date()} is a trading day")
        return True
    
    def should_run_today(self) -> bool:
        """
        Determine if scheduler should run today
        
        Checks:
        - Trading day validation
        - Idempotency (only once per day)
        - Enabled flag
        """
        if not self.enabled:
            logger.info("⏸️ Forecast scheduler is disabled")
            return False
        
        today = datetime.now(IST).date()
        
        # Check idempotency - only run once per day
        if self.last_execution_date == today:
            logger.info(f"⏭️ Already executed today ({today}), skipping")
            return False
        
        # Check if trading day
        if not self.is_trading_day():
            logger.info("⏸️ Not a trading day, skipping forecast")
            return False
        
        logger.info(f"✅ Should run today: {today} is a trading day")
        return True
    
    def get_next_run_time(self) -> str:
        """Get formatted next run time"""
        now = datetime.now(IST)
        schedule_hour, schedule_minute = map(int, self.schedule_time.split(':'))
        
        # Check if we're past scheduled time today
        scheduled_time = now.replace(hour=schedule_hour, minute=schedule_minute, second=0, microsecond=0)
        
        if now >= scheduled_time:
            # Already passed, find next trading day
            check_date = now
            for _ in range(7):  # Check next 7 days
                check_date = check_date.replace(day=check_date.day + 1)
                if self.is_trading_day(check_date):
                    next_run = check_date.replace(hour=schedule_hour, minute=schedule_minute)
                    return next_run.strftime('%d %b %Y %H:%M IST')
        else:
            # Today is the next run
            if self.is_trading_day():
                return scheduled_time.strftime('%d %b %Y %H:%M IST')
        
        return "Unknown"
    
    def start_scheduler(self):
        """Start the scheduler in blocking mode (for servers)"""
        if not self.enabled:
            logger.warning("⏸️ Scheduler is disabled")
            return
        
        if self.forecast_callback is None:
            logger.error("❌ No forecast callback provided")
            return
        
        logger.info("🚀 Starting Forecast Scheduler...")
        
        # Schedule daily at specified time
        schedule.every().day.at(self.schedule_time).do(self._scheduled_run)
        
        self.is_running = True
        logger.info(f"📅 Scheduled to run daily at {self.schedule_time} IST")
        
        # Run scheduler in blocking loop
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("⏹️ Scheduler stopped by user")
            self.stop()
        except Exception as e:
            logger.error(f"❌ Scheduler error: {str(e)}")
            self.stop()
    
    def stop(self):
        """Stop the scheduler"""
        self.is_running = False
        schedule.clear()
        logger.info("🛑 Scheduler stopped")
    
    def _scheduled_run(self):
        """Internal callback for scheduled execution"""
        now = datetime.now(IST)
        logger.info(f"\n{'='*60}")
        logger.info(f"⏰ Scheduled Forecast Run - {now.strftime('%d %b %Y %H:%M:%S IST')}")
        logger.info(f"{'='*60}")
        
        # Check if should run
        if not self.should_run_today():
            logger.info("⏭️ Skipping forecast (not a trading day or already run today)")
            return
        
        # Execute forecast
        if self.forecast_callback:
            try:
                logger.info("⏳ Starting forecast generation...")
                result = self.forecast_callback()
                
                if result:
                    self.last_execution_date = now.date()
                    logger.info(f"✅ Forecast completed successfully")
                    logger.info(f"   Last execution: {self.last_execution_date}")
                else:
                    logger.error("❌ Forecast callback returned False")
                    
            except Exception as e:
                logger.error(f"❌ Error during scheduled forecast: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
    
    def run_manual_forecast(self) -> bool:
        """
        Manually trigger forecast (for admin "Run Now" button)
        
        Returns:
            Success status
        """
        logger.info("🔄 Manual forecast triggered")
        
        if self.forecast_callback is None:
            logger.error("❌ No forecast callback available")
            return False
        
        try:
            result = self.forecast_callback()
            return result if result is not None else True
        except Exception as e:
            logger.error(f"❌ Error in manual forecast: {str(e)}")
            return False


# Singleton instance
_forecast_scheduler = None

def get_forecast_scheduler(callback: Optional[Callable] = None) -> ForecastScheduler:
    """Get or create singleton scheduler instance"""
    global _forecast_scheduler
    if _forecast_scheduler is None:
        _forecast_scheduler = ForecastScheduler(callback)
    return _forecast_scheduler
