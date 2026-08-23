#!/usr/bin/env python
"""Test backtesting engine Series fix"""
import sys
sys.path.insert(0, '.')

from StockSageAI.backtesting_engine import get_backtest_engine
from datetime import datetime, timedelta

print("🧪 Testing Backtesting Engine Series Fix...")

try:
    backtest = get_backtest_engine()
    
    # Fetch sample data
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=150)).strftime('%Y-%m-%d')
    
    print(f"   📊 Fetching data from {start_date} to {end_date}...")
    df = backtest.fetch_historical_data('AAPL', start_date, end_date)
    
    if df.empty:
        print("   ⚠ No data fetched from AAPL, trying NSE format...")
        df = backtest.fetch_historical_data('INFY.NS', start_date, end_date)
    
    if not df.empty:
        print(f"   ✓ Data fetched: {len(df)} rows")
        
        # Run backtest
        print("   🔄 Running backtest with ma_crossover strategy...")
        result = backtest.backtest(df, 'ma_crossover')
        
        print("   ✅ Backtest completed successfully!")
        print(f"      • Total Return: {result['total_return']:.2f}%")
        print(f"      • Sharpe Ratio: {result['sharpe_ratio']:.2f}")
        print(f"      • Trades Executed: {result['trades']}")
        print(f"      • Win Rate: {result['win_rate']:.1f}%")
        print(f"      • Max Drawdown: {result['max_drawdown']:.2f}%")
        
        # Test other strategies
        print("\n   🔄 Testing RSI strategy...")
        result_rsi = backtest.backtest(df, 'rsi')
        print(f"      ✓ RSI: {result_rsi['total_return']:.2f}% return")
        
        print("\n   🔄 Testing Bollinger Bands strategy...")
        result_bb = backtest.backtest(df, 'bollinger_bands')
        print(f"      ✓ Bollinger: {result_bb['total_return']:.2f}% return")
        
        print("\n✅ ALL TESTS PASSED - Backtesting engine is working!")
    else:
        print("   ⚠ Could not fetch data for testing")
        
except Exception as e:
    print(f"   ❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
