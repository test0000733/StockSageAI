#!/usr/bin/env python
"""
Start Telegram Forecast System
Run this to start the daily 10:15 AM IST forecast scheduler
"""

import os
import sys
import logging
import time
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


def run_scheduler_loop(max_restarts: int = 3, restart_delay_seconds: int = 30):
    """Run the scheduler in a loop so it keeps surviving unexpected exits."""
    restart_count = 0

    while True:
        try:
            logger.info("="*70)
            logger.info("🚀 Starting StockSageAI Telegram Forecast Scheduler")
            logger.info("="*70)

            from StockSageAI.telegram_manager import get_telegram_forecast_manager
            manager = get_telegram_forecast_manager()

            status = manager.get_system_status()
            logger.info(f"   Telegram: {status.get('telegram_connection')}")
            logger.info(f"   Scheduler: {status.get('scheduler_status')}")
            logger.info(f"   Schedule: {status.get('schedule_time')} IST")
            logger.info(f"   Trading Day Today: {status.get('trading_day_today')}")
            if status.get('next_scheduled_run'):
                logger.info(f"   Next Run: {status['next_scheduled_run']}")

            logger.info("\n🧪 Testing Telegram connection...")
            test_result = manager.test_telegram()
            if test_result.get('success'):
                logger.info(f"   ✅ {test_result['message']}")
            else:
                logger.error(f"   ❌ {test_result['message']}")
                logger.error("   Telegram connection failed; retrying after delay")
                time.sleep(restart_delay_seconds)
                restart_count += 1
                if restart_count >= max_restarts:
                    raise RuntimeError("Telegram connection failed repeatedly")
                continue

            logger.info("\n🚀 Starting forecast scheduler loop...")
            manager.start_scheduler(run_in_background=False)
            return True

        except KeyboardInterrupt:
            logger.info("\n⏹️ Scheduler stopped by user")
            return True
        except Exception as e:
            logger.error(f"❌ Scheduler crashed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            restart_count += 1
            if restart_count > max_restarts:
                logger.error("❌ Max restarts reached; scheduler will stop")
                return False
            logger.warning(f"🔁 Restarting scheduler in {restart_delay_seconds} seconds (attempt {restart_count}/{max_restarts})")
            time.sleep(restart_delay_seconds)


def main():
    """Main entry point for Telegram forecast system"""
    try:
        return run_scheduler_loop()
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


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
