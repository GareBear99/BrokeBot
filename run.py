#!/usr/bin/env python3
"""
Broke Bot Entry Point
Run the funding-rate arbitrage bot
"""

import sys
import argparse
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from broke_bot.bot import BrokeBot
from broke_bot.config import Config


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Broke Bot - TRON Funding Rate Arbitrage Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run in dry-run mode (default)
  python run.py

  # Run with Binance
  python run.py --exchange binance --symbols BTCUSDT,ETHUSDT

  # Run live (requires API keys)
  python run.py --live --exchange binance

Environment Variables:
  EXCHANGE      - Exchange to use (binance, bybit, okx)
  API_KEY       - Exchange API key
  API_SECRET    - Exchange API secret
  SYMBOLS       - Comma-separated list of symbols
  DRY_RUN       - Set to 'false' for live trading
  LEVERAGE      - Leverage to use (2-5)
  LOG_PATH      - Path to log directory
"""
    )
    
    parser.add_argument('--exchange', type=str, default='binance',
                       help='Exchange to use (binance, bybit, okx)')
    parser.add_argument('--symbols', type=str, default='BTCUSDT',
                       help='Comma-separated list of symbols to trade')
    parser.add_argument('--leverage', type=int, default=3,
                       help='Leverage to use (2-5)')
    parser.add_argument('--live', action='store_true',
                       help='Run in live mode (default is dry-run)')
    parser.add_argument('--testnet', action='store_true',
                       help='Use exchange testnet')
    parser.add_argument('--log-path', type=str, default='logs/broke_bot',
                       help='Path to log directory')
    
    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_args()
    
    # Override environment variables with command line args
    if args.exchange:
        os.environ['EXCHANGE'] = args.exchange
    if args.symbols:
        os.environ['SYMBOLS'] = args.symbols
    if args.leverage:
        os.environ['LEVERAGE'] = str(args.leverage)
    if args.live:
        os.environ['DRY_RUN'] = 'false'
    else:
        os.environ['DRY_RUN'] = 'true'
    if args.testnet:
        os.environ['TESTNET'] = 'true'
    if args.log_path:
        os.environ['LOG_PATH'] = args.log_path
    
    # Load configuration
    config = Config.from_env()
    
    # Validate configuration
    errors = config.validate()
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    
    # Print configuration
    print("=" * 60)
    print("BROKE BOT - TRON Funding Rate Arbitrage")
    print("=" * 60)
    print(f"Mode:      {'LIVE TRADING' if not config.operational.dry_run else 'DRY RUN (PAPER TRADING)'}")
    print(f"Exchange:  {config.exchange.exchange}")
    print(f"Testnet:   {config.exchange.testnet}")
    print(f"Symbols:   {', '.join(config.trading.symbols)}")
    print(f"Leverage:  {config.trading.leverage}x")
    print(f"Risk/Trade: {config.trading.risk_per_trade * 100}%")
    print(f"Log Path:  {config.operational.log_path}")
    print("=" * 60)
    
    if not config.operational.dry_run:
        print("\n⚠️  WARNING: You are running in LIVE mode!")
        print("This bot will execute real trades with real money.")
        response = input("Type 'yes' to continue: ")
        if response.lower() != 'yes':
            print("Aborted.")
            sys.exit(0)
    
    print("\nStarting bot... (Press Ctrl+C to stop)")
    print()
    
    # Create and run bot
    bot = BrokeBot(config)
    
    try:
        bot.start()
    except KeyboardInterrupt:
        print("\n\nShutdown requested by user...")
        bot.stop()
        print("Bot stopped successfully.")
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
