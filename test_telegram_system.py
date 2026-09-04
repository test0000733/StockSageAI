#!/usr/bin/env python
"""
Test Script for Telegram Forecast System
Validates all components before running in production
"""

import os
import sys
import logging

# Add parent directory to path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_environment():
    """Test environment and dependencies"""
    logger.info("🧪 Testing Environment...")
    
    # Check .env file
    env_path = os.path.join(ROOT_DIR, '.env')
    if not os.path.exists(env_path):
        logger.error("❌ .env file not found")
        return False
    
    logger.info("✅ .env file found")
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check required variables
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token:
        logger.error("❌ TELEGRAM_BOT_TOKEN not set in .env")
        return False
    
    if not chat_id:
        logger.error("❌ TELEGRAM_CHAT_ID not set in .env")
        return False
    
    logger.info("✅ Telegram credentials configured")
    return True


def test_imports():
    """Test that all modules can be imported"""
    logger.info("\n🧪 Testing Imports...")
    
    modules_to_test = [
        'StockSageAI.telegram_service',
        'StockSageAI.telegram_notifier',
        'StockSageAI.telegram_api',
        'StockSageAI.forecast_scheduler',
        'StockSageAI.forecast_generator',
        'StockSageAI.stock_selector',
        'StockSageAI.telegram_manager',
    ]
    
    for module in modules_to_test:
        try:
            __import__(module)
            logger.info(f"✅ {module}")
        except Exception as e:
            logger.error(f"❌ {module}: {str(e)}")
            return False
    
    return True


def test_telegram_connection():
    """Test Telegram connection"""
    logger.info("\n🧪 Testing Telegram Connection...")
    
    try:
        from StockSageAI.telegram_service import get_telegram_service
        
        service = get_telegram_service()
        is_connected, message = service.test_connection()
        
        if is_connected:
            logger.info(f"✅ {message}")
            return True
        else:
            logger.error(f"❌ {message}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return False


def test_telegram_chat():
    """Test Telegram chat accessibility"""
    logger.info("\n🧪 Testing Telegram Chat...")
    
    try:
        from StockSageAI.telegram_service import get_telegram_service
        
        service = get_telegram_service()
        is_valid = service.validate_chat_id()
        
        if is_valid:
            logger.info("✅ Chat ID is valid and accessible")
            return True
        else:
            logger.error("❌ Chat ID validation failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return False


def test_send_test_message():
    """Send test message to verify full end-to-end"""
    logger.info("\n🧪 Sending Test Message...")
    
    try:
        from StockSageAI.telegram_service import get_telegram_service
        from StockSageAI.telegram_notifier import get_telegram_notifier
        
        service = get_telegram_service()
        notifier = get_telegram_notifier()
        
        test_msg = notifier.format_test_message()
        success, msg_id = service.send_message(test_msg)
        
        if success:
            logger.info(f"✅ Test message sent successfully (ID: {msg_id})")
            return True
        else:
            logger.error("❌ Failed to send test message")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return False


def test_forecast_generation():
    """Test forecast generation (quick test with 1 stock)"""
    logger.info("\n🧪 Testing Forecast Generation...")
    
    try:
        from StockSageAI.forecast_generator import get_forecast_generator
        
        generator = get_forecast_generator()
        
        # Test with a single popular stock
        logger.info("   Generating forecast for INFY.NS...")
        result = generator.generate_forecast('INFY.NS')
        
        if result.get('success'):
            logger.info(f"✅ Forecast generated")
            logger.info(f"   Current price: ₹{result.get('current_price')}")
            logger.info(f"   7D forecast: ₹{result.get('forecasts', {}).get(7, 'N/A')}")
            logger.info(f"   14D forecast: ₹{result.get('forecasts', {}).get(14, 'N/A')}")
            logger.info(f"   30D forecast: ₹{result.get('forecasts', {}).get(30, 'N/A')}")
            return True
        else:
            logger.error(f"❌ {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return False


def test_scheduler():
    """Test scheduler initialization"""
    logger.info("\n🧪 Testing Scheduler...")
    
    try:
        from StockSageAI.forecast_scheduler import get_forecast_scheduler
        from datetime import datetime
        import pytz
        
        scheduler = get_forecast_scheduler()
        
        logger.info(f"   Schedule time: {scheduler.schedule_time} IST")
        logger.info(f"   Enabled: {scheduler.enabled}")
        
        # Check if today is trading day
        IST = pytz.timezone('Asia/Kolkata')
        now = datetime.now(IST)
        is_trading = scheduler.is_trading_day(now)
        logger.info(f"   Trading day today: {'✅ Yes' if is_trading else '❌ No'}")
        
        logger.info(f"   Next run: {scheduler.get_next_run_time()}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return False


def test_database():
    """Test database initialization"""
    logger.info("\n🧪 Testing Database...")
    
    try:
        from StockSageAI.database import Database
        
        db = Database()
        logger.info("✅ Database initialized")
        
        # Try to save a test forecast
        from datetime import date
        success = db.save_notification(
            date.today(),
            'test',
            0,
            0,
            [],
            "Test notification"
        )
        
        if success:
            logger.info("✅ Database operations working")
            return True
        else:
            logger.error("❌ Database operations failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return False


def run_all_tests():
    """Run all tests"""
    logger.info("="*70)
    logger.info("🚀 TELEGRAM FORECAST SYSTEM - COMPREHENSIVE TEST SUITE")
    logger.info("="*70)
    
    tests = [
        ("Environment", test_environment),
        ("Imports", test_imports),
        ("Telegram Connection", test_telegram_connection),
        ("Telegram Chat", test_telegram_chat),
        ("Test Message", test_send_test_message),
        ("Forecast Generation", test_forecast_generation),
        ("Scheduler", test_scheduler),
        ("Database", test_database),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            result = test_func()
            results[name] = result
        except Exception as e:
            logger.error(f"❌ {name} test crashed: {str(e)}")
            results[name] = False
    
    # Summary
    logger.info("\n" + "="*70)
    logger.info("📊 TEST SUMMARY")
    logger.info("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {name}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("\n✅ ALL TESTS PASSED - System is ready!")
        return True
    else:
        logger.error(f"\n❌ {total - passed} tests failed - Fix issues before running")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
