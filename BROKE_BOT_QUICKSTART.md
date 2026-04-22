# Broke Bot - Quick Start Guide

## 🚀 Get Started in 3 Minutes

### 1. Test Installation
```bash
python3 broke_bot/test_install.py
```

### 2. Run in Paper Trading Mode (Safe)
```bash
# Option A: Using shell script
./broke_bot_start.sh

# Option B: Direct Python
python3 broke_bot/run.py
```

That's it! The bot will start in **DRY RUN** mode (paper trading) with default settings.

## 📊 What You'll See

The bot will:
- Poll every 5 seconds
- Check funding rates on BTCUSDT
- Log all decisions to `logs/broke_bot/broke_bot_YYYY-MM-DD.jsonl`
- Simulate trades when conditions are met (no real money)

## 📝 View Live Logs

```bash
# Tail the log file
tail -f logs/broke_bot/broke_bot_$(date +%Y-%m-%d).jsonl

# Pretty print with jq (if installed)
tail -f logs/broke_bot/broke_bot_$(date +%Y-%m-%d).jsonl | jq '.'
```

## ⚙️ Configuration

### Using Environment Variables
```bash
# Quick test with different symbol
SYMBOLS=ETHUSDT python3 broke_bot/run.py

# Change leverage
LEVERAGE=2 python3 broke_bot/run.py
```

### Using .env File (Recommended)
```bash
# Copy example file
cp .env.broke_bot.example .env

# Edit settings
nano .env  # or your preferred editor

# Run bot
./broke_bot_start.sh
```

## 🎯 Example .env Configuration

```bash
# For paper trading (safe)
EXCHANGE=binance
DRY_RUN=true
SYMBOLS=BTCUSDT
LEVERAGE=3
```

## 📈 Monitor Performance

Key metrics in logs:
- `type: "decision"` - Entry decisions with reasons
- `type: "entry"` - Simulated trades opened
- `type: "exit"` - Simulated trades closed with PnL
- `type: "risk_limit"` - Risk controls triggered

## 🛑 Stop the Bot

Press `Ctrl+C` - the bot will shut down gracefully.

## ⚠️ Before Going Live

**NEVER skip these steps:**

1. ✅ Run paper trading for at least 50 funding cycles
2. ✅ Review all logs and understand the strategy
3. ✅ Set up API keys with **trade-only** permissions (no withdrawals)
4. ✅ Start with minimum account size
5. ✅ Use 2x leverage initially
6. ✅ Enable IP whitelisting on exchange
7. ✅ Test on exchange testnet first

## 🔐 Going Live (Advanced)

```bash
# 1. Set up .env with real API keys
EXCHANGE=binance
API_KEY=your_key_here
API_SECRET=your_secret_here
TESTNET=true  # Use testnet first!
DRY_RUN=false
LEVERAGE=2
SYMBOLS=BTCUSDT

# 2. Run on testnet
python3 broke_bot/run.py --live --testnet

# 3. After successful testnet testing, use mainnet
# Remove TESTNET or set to false
```

## 📚 More Information

- Full documentation: `broke_bot/README.md`
- Original spec: `TRON_Funding_Arbitrage_Bot_Spec.pdf`
- Logs: `logs/broke_bot/`
- State: `state/broke_bot_state.json`

## 🆘 Troubleshooting

**Bot not starting?**
```bash
# Check Python version (need 3.8+)
python3 --version

# Install dependencies
pip install requests numpy

# Run test
python3 broke_bot/test_install.py
```

**No trades happening?**
- Funding rates might not be extreme enough (need >0.08%)
- Check logs for decision reasons
- This is normal - the bot waits for optimal conditions

**API errors?**
- Verify API keys are correct
- Check you're using Futures API keys
- Try testnet first

## 💡 Tips

1. **Paper trade first** - Always run in DRY_RUN mode initially
2. **Check logs** - Review all decision logs to understand behavior
3. **Start small** - Use minimum account size when going live
4. **Monitor closely** - Watch the first few live trades carefully
5. **Use alerts** - Set up monitoring for error logs
6. **Funding schedule** - Funding happens every 8 hours (check your exchange)

## 🎓 Understanding the Strategy

The bot captures **funding payments** in perpetual futures:

1. **When funding > 0**: Longs pay shorts → Bot opens SHORT
2. **When funding < 0**: Shorts pay longs → Bot opens LONG
3. **Holds position** through funding payment (~8 hours)
4. **Exits** after receiving payment
5. **Risk controls** limit losses if price moves adversely

## 📊 Expected Performance

- **Win rate**: 30-60% (varies with market conditions)
- **Hold time**: ~8 hours per trade
- **Trades/day**: 0-4 (depends on funding extremity)
- **Risk**: Price risk during hold period despite hedging

---

**Remember**: This is a **high-risk strategy**. Only trade with money you can afford to lose.

For detailed documentation, see `broke_bot/README.md`
