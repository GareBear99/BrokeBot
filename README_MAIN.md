# 🤖 Broke Bot - TRON Funding Rate Arbitrage

A production-grade, educational funding-rate arbitrage bot for perpetual futures that captures funding payments when rates become extreme.

![Status](https://img.shields.io/badge/status-ready-green)
![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-blue)

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Test installation
python3 test_install.py

# 3. Run in paper trading mode (safe)
./broke_bot_start.sh
```

**That's it!** The bot will start monitoring BTCUSDT funding rates in paper trading mode.

📖 **New to this bot?** Start with [BROKE_BOT_QUICKSTART.md](BROKE_BOT_QUICKSTART.md)

📚 **Need details?** See full documentation in [README.md](README.md)

---

## ⚠️ Important Disclaimer

**This is educational software.** Trading cryptocurrencies carries significant risk. There is no guarantee of profit. Funding-rate strategies can lose money due to price movement, spread, fees, and sudden volatility.

- ✅ **Always start with paper trading** (DRY_RUN=true)
- ✅ **Test for 50+ funding cycles** before considering live trading
- ✅ **Use only funds you can afford to lose**
- ✅ **Never use withdrawal-enabled API keys**

---

## 📋 What This Bot Does

The bot implements a **funding-rate arbitrage strategy**:

1. **Monitors funding rates** on perpetual futures (BTCUSDT, ETHUSDT)
2. **Opens positions** when funding becomes extreme (≥0.08%)
3. **Collects funding payments** by being on the paid side
4. **Manages risk** with stops, limits, and multiple safety controls
5. **Exits after funding** payment is received

**Position Direction:**
- When funding is **positive** (longs pay shorts) → Bot opens **SHORT**
- When funding is **negative** (shorts pay longs) → Bot opens **LONG**

---

## ✨ Key Features

### 🎯 Entry Filters
- Funding rate extremity check
- Time-to-funding window (10-90 min)
- Liquidity verification (spread ≤0.05%)
- Volatility calm filter (ATR + volume spikes)
- Trend safety filter (EMA20/50 + momentum)

### 🛡️ Risk Management
- **Position sizing:** 1% risk per trade
- **Stop-loss:** 0.8x ATR from entry
- **Take-profit:** 0.4x ATR for mean reversion
- **Trade limits:** Max 4/day, 2/interval
- **Loss limits:** Daily -2%, consecutive 2 losses
- **Drawdown limit:** -15% from peak
- **Emergency exits:** Auto-close on adverse conditions

### 🔧 Operational Safety
- Paper trading mode (DRY_RUN)
- JSONL structured logging
- State persistence
- Graceful shutdown
- Panic switch
- API key validation

---

## 📁 Project Structure

```
broke_bot/
├── run.py                          # Entry point
├── bot.py                          # Main event loop
├── config.py                       # Configuration
├── exchange_adapter.py             # Exchange APIs
├── data_fetcher.py                 # Market data
├── signal_generator.py             # Entry signals
├── risk_manager.py                 # Risk controls
├── position_manager.py             # Order execution
├── indicators.py                   # Technical indicators
├── logger.py                       # JSONL logging
├── test_install.py                 # Installation test
├── broke_bot_start.sh              # Startup script
├── requirements.txt                # Dependencies
├── .env.broke_bot.example          # Config template
├── README_MAIN.md                  # This file
├── README.md                       # Full documentation
├── BROKE_BOT_QUICKSTART.md         # Quick start guide
├── PROJECT_STRUCTURE.md            # Architecture docs
└── TRON_Funding_Arbitrage_Bot_Spec.pdf  # Original spec
```

---

## 🎮 Usage

### Paper Trading (Recommended First)

```bash
# Default: BTCUSDT, 3x leverage, dry run
./broke_bot_start.sh

# Different symbol
SYMBOLS=ETHUSDT python3 run.py

# Multiple symbols
python3 run.py --symbols BTCUSDT,ETHUSDT

# Lower leverage (safer)
python3 run.py --leverage 2
```

### Configuration

Create `.env` file from template:

```bash
cp .env.broke_bot.example .env
# Edit .env with your settings
```

Example `.env`:
```bash
EXCHANGE=binance
DRY_RUN=true
SYMBOLS=BTCUSDT
LEVERAGE=3
```

### View Logs

```bash
# Tail live logs
tail -f logs/broke_bot_$(date +%Y-%m-%d).jsonl

# Pretty print (requires jq)
tail -f logs/broke_bot_$(date +%Y-%m-%d).jsonl | jq '.'
```

---

## 🔐 Going Live (Advanced Users Only)

**⚠️ Only after extensive paper trading!**

1. Set up Binance Futures API keys (trade-only, no withdrawals)
2. Configure `.env`:
```bash
EXCHANGE=binance
API_KEY=your_key_here
API_SECRET=your_secret_here
TESTNET=true  # Test on testnet first!
DRY_RUN=false
LEVERAGE=2    # Start conservative
```

3. Test on testnet:
```bash
python3 run.py --live --testnet
```

4. After successful testnet testing, switch to mainnet (set `TESTNET=false`)

---

## 📊 Expected Performance

- **Strategy type:** Mean reversion + funding capture
- **Hold time:** ~8 hours (one funding interval)
- **Trades per day:** 0-4 (depends on funding extremity)
- **Win rate:** 30-60% (varies with conditions)
- **Risk:** Price risk during holding period

**This is NOT a high-frequency strategy.** The bot waits for extreme funding conditions, which may be rare.

---

## 🛠️ Supported Exchanges

- ✅ **Binance Futures** (fully implemented)
- ⏳ Bybit (placeholder)
- ⏳ OKX (placeholder)

---

## 📖 Documentation

- **Quick Start:** [BROKE_BOT_QUICKSTART.md](BROKE_BOT_QUICKSTART.md) - Get started in 3 minutes
- **Full Guide:** [README.md](README.md) - Complete documentation
- **Architecture:** [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Technical details
- **Original Spec:** [TRON_Funding_Arbitrage_Bot_Spec.pdf](TRON_Funding_Arbitrage_Bot_Spec.pdf)

---

## 🆘 Troubleshooting

**Bot not starting?**
```bash
python3 test_install.py  # Verify installation
pip install -r requirements.txt  # Install dependencies
```

**No trades happening?**
- Funding rates may not be extreme enough
- Check logs for decision reasons
- This is normal - bot waits for optimal conditions

**API errors?**
- Verify API keys are for Futures trading
- Check IP whitelist settings
- Try testnet first

---

## 🎓 Learning Resources

- **Perpetual Futures:** Understanding funding rates
- **Binance Futures:** [API Documentation](https://binance-docs.github.io/apidocs/futures/en/)
- **ATR Indicator:** Average True Range for volatility
- **EMA Strategy:** Exponential Moving Averages for trends
- **TRON Network:** USDT-TRC20 for low-cost transfers

---

## 📈 Code Statistics

- **Total Lines:** ~2,200
- **Modules:** 9 core + 3 support
- **Test Coverage:** Installation validation
- **Documentation:** 700+ lines

---

## 🔧 Development

### Running Tests
```bash
python3 test_install.py
```

### Adding New Exchange
1. Implement adapter in `exchange_adapter.py`
2. Test with testnet
3. Update documentation

---

## 📝 Version History

### v1.0.0 (2025-12-15)
- Initial release
- Binance Futures support
- Full spec compliance
- Paper trading mode
- JSONL logging
- Comprehensive docs

---

## 🤝 Contributing

This is an educational project. Feel free to:
- Study the code
- Modify for your needs
- Test improvements
- Share learnings

---

## ⚖️ License

Educational use only. See project license.

---

## 🙏 Acknowledgments

Built according to the TRON Funding Rate Arbitrage Bot specification.

---

## 💬 Support

For issues:
1. Check logs in `logs/`
2. Review configuration
3. Verify API permissions
4. Start with paper trading

---

**Remember:** High-risk strategy. Only trade with money you can afford to lose.

For detailed instructions, see [README.md](README.md)
