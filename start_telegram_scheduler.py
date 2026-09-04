#!/usr/bin/env python
"""
Start Telegram Forecast System
Run this to start the daily 10:15 AM IST forecast scheduler
"""

import os
import sys
import logging
from datetime import datetime
import pytz


class ASCIIOnlyStream:
    """Windows-safe stream that strips emoji and other non-ASCII characters before writing."""
    def __init__(self, stream):
        self.stream = stream

    def write(self, message):
        safe_message = message.encode('ascii', errors='ignore').decode('ascii')
        return self.stream.write(safe_message)

    def flush(self):
        self.stream.flush()

    def isatty(self):
        return getattr(self.stream, 'isatty', lambda: False)()

    @property
    def encoding(self):
        return 'utf-8'


# Add parent directory to path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(ROOT_DIR, 'telegram_forecast.log'), encoding='utf-8'),
        logging.StreamHandler(ASCIIOnlyStream(sys.stdout))
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point for Telegram forecast system"""
    
    logger.info("="*70)
    logger.info("🚀 StockSageAI Telegram Forecast System")
    logger.info("="*70)
    
    try:
        # Import manager
        from StockSageAI.telegram_manager import get_telegram_forecast_manager
        
        # Initialize manager
        logger.info("📥 Initializing Telegram Forecast Manager...")
        manager = get_telegram_forecast_manager()
        
        # Get system status
        logger.info("📊 Checking system status...")
        status = manager.get_system_status()
        
        logger.info(f"   Telegram: {status.get('telegram_connection')}")
        logger.info(f"   Scheduler: {status.get('scheduler_status')}")
        logger.info(f"   Schedule: {status.get('schedule_time')} IST")
        logger.info(f"   Trading Day Today: {status.get('trading_day_today')}")
        
        if status.get('next_scheduled_run'):
            logger.info(f"   Next Run: {status['next_scheduled_run']}")
        
        # Test Telegram connection
        logger.info("\n🧪 Testing Telegram connection...")
        test_result = manager.test_telegram()
        
        if test_result.get('success'):
            logger.info(f"   ✅ {test_result['message']}")
        else:
            logger.error(f"   ❌ {test_result['message']}")
            logger.error("   Cannot proceed without Telegram connection")
            return False
        
        # Start scheduler
        logger.info("\n🚀 Starting forecast scheduler...")
        manager.start_scheduler(run_in_background=False)
        
        # This blocks forever (scheduler loop)
        logger.info("✅ Scheduler running. Press Ctrl+C to stop.")
        
    except KeyboardInterrupt:
        logger.info("\n⏹️ Scheduler stopped by user")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {str(e)}")
        logger.error("   Make sure all dependencies are installed: pip install -r requirements.txt")
        return False
        
    except ValueError as e:
        logger.error(f"❌ Configuration error: {str(e)}")
        logger.error("   Make sure .env file exists with TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        return False
        
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
