#!/usr/bin/env python3
"""
Test Broke Bot Installation
Quick verification that all modules can be imported
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing Broke Bot installation...")
    print()
    
    tests = []
    
    # Test config
    try:
        from broke_bot.config import Config
        tests.append(("Config module", True, None))
    except Exception as e:
        tests.append(("Config module", False, str(e)))
    
    # Test indicators
    try:
        from broke_bot.indicators import ATR, EMA, MomentumAnalyzer, VolatilityFilter
        tests.append(("Indicators module", True, None))
    except Exception as e:
        tests.append(("Indicators module", False, str(e)))
    
    # Test exchange adapter
    try:
        from broke_bot.exchange_adapter import create_exchange_adapter, BinanceFuturesAdapter
        tests.append(("Exchange adapter module", True, None))
    except Exception as e:
        tests.append(("Exchange adapter module", False, str(e)))
    
    # Test data fetcher
    try:
        from broke_bot.data_fetcher import DataFetcher, MarketData
        tests.append(("Data fetcher module", True, None))
    except Exception as e:
        tests.append(("Data fetcher module", False, str(e)))
    
    # Test signal generator
    try:
        from broke_bot.signal_generator import SignalGenerator
        tests.append(("Signal generator module", True, None))
    except Exception as e:
        tests.append(("Signal generator module", False, str(e)))
    
    # Test risk manager
    try:
        from broke_bot.risk_manager import RiskManager
        tests.append(("Risk manager module", True, None))
    except Exception as e:
        tests.append(("Risk manager module", False, str(e)))
    
    # Test position manager
    try:
        from broke_bot.position_manager import PositionManager, Position
        tests.append(("Position manager module", True, None))
    except Exception as e:
        tests.append(("Position manager module", False, str(e)))
    
    # Test logger
    try:
        from broke_bot.logger import BrokeBotLogger
        tests.append(("Logger module", True, None))
    except Exception as e:
        tests.append(("Logger module", False, str(e)))
    
    # Test main bot
    try:
        from broke_bot.bot import BrokeBot
        tests.append(("Main bot module", True, None))
    except Exception as e:
        tests.append(("Main bot module", False, str(e)))
    
    # Print results
    all_passed = True
    for name, passed, error in tests:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {name}")
        if error:
            print(f"       Error: {error}")
            all_passed = False
    
    print()
    if all_passed:
        print("✓ All tests passed! Broke Bot is ready to use.")
        print()
        print("Next steps:")
        print("1. Copy .env.broke_bot.example to .env")
        print("2. Configure your settings in .env")
        print("3. Run: ./broke_bot_start.sh")
        return 0
    else:
        print("✗ Some tests failed. Check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(test_imports())
