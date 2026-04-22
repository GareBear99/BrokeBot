<!-- ARC-Ecosystem-Hero-Marker -->
# BrokeBot — TRON Funding-Rate Arbitrage Bot

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Built on ARC-Core](https://img.shields.io/badge/built%20on-ARC--Core-5B6CFF)](https://github.com/GareBear99/ARC-Core)
[![Paper-Trading Default](https://img.shields.io/badge/DRY__RUN-default-green)]()

> Educational perpetual-funding-rate arbitrage bot for small accounts. Captures
> funding payments when rates are extreme while keeping price risk tightly
> controlled via ATR-sized stops, daily loss caps, consecutive-loss halt, and a
> DRY-RUN default.

## Why you might read this repo

-   **Complete, working funding-rate strategy** (not a stub): entry filters,
    position sizing, stops/TPs, kill-switches, JSONL structured logs.
-   **Designed for $10–$20 accounts** on USDT-TRC20 so fees don't eat alpha.
-   **Safety-first**: paper-trading mode by default; emergency exits on spread
    widening and rapid price moves; keys never committed.
-   **Small surface area**: ~10 focused Python modules, readable top-to-bottom.

## Part of the ARC ecosystem

BrokeBot is one of several trading/automation systems in the ARC portfolio.
When governed execution, receipts, or replay are required, BrokeBot can emit
its decisions into an **ARC-Core** event spine for tamper-evident trade audit.

-   [ARC-Core](https://github.com/GareBear99/ARC-Core) — governed event +
    receipt spine for AI/trading automations.
-   [omnibinary-runtime](https://github.com/GareBear99/omnibinary-runtime) +
    [Arc-RAR](https://github.com/GareBear99/Arc-RAR) — any-OS portability for
    bot deployment.
-   [Portfolio](https://github.com/GareBear99/Portfolio) — full project index.

## Keywords
`funding rate arbitrage` · `perpetual futures` · `binance futures bot` ·
`crypto trading bot python` · `tron USDT-TRC20` · `delta-neutral` ·
`quantitative finance` · `algorithmic trading` · `kill switch` ·
`paper trading` · `ATR stop loss`

---

<!-- ARC-Official-Docs-Link-Marker -->
## 📖 Official docs

[**Open the rendered official docs → https://garebear99.github.io/BrokeBot/official/BrokeBot_Phase1_25Coin_Playbook_v2.html**](https://garebear99.github.io/BrokeBot/official/BrokeBot_Phase1_25Coin_Playbook_v2.html)

Also available under [`docs/official/`](https://github.com/GareBear99/BrokeBot/tree/main/docs/official) in-tree, and through the Pages landing at [https://garebear99.github.io/BrokeBot/](https://garebear99.github.io/BrokeBot/).



# Broke Bot - TRON Funding Rate Arbitrage

**Educational funding-rate arbitrage bot** that captures perpetual futures funding payments when rates become extreme, while keeping price risk tightly controlled via filters, stops, and kill-switches.

⚠️ **DISCLAIMER**: This is educational software. Trading cryptocurrencies carries significant risk. There is no guarantee of profit. Use paper trading first and risk only what you can afford to lose.

## What It Does

- **Captures funding payments**: Opens positions when funding rates are extreme to collect funding payments
- **Risk management**: Tight controls with stop-losses, position sizing, and multiple safety limits
- **Low leverage**: Designed for 2-5x leverage on small accounts ($10-$20 target)
- **USDT-TRC20**: Uses TRON network for cheap deposits/withdrawals
- **Automated trading**: 5-second polling loop with full automation

## Features

✅ **Multiple Entry Filters**
- Funding rate extremity check (default: ≥0.08%)
- Time-to-funding window (10-90 minutes)
- Liquidity checks (spread ≤0.05%)
- Volatility calm filter (ATR below median, no spikes)
- Trend safety filter (EMA20/50 with momentum)

✅ **Risk Management**
- Position sizing: Risk 1% per trade based on stop distance
- Stop-loss: 0.8x ATR(15m) from entry
- Take-profit: 0.4x ATR(15m) for mean reversion
- Max 2 entries per funding interval, 4 per day
- Daily loss limit: Halt at -2% daily PnL
- Consecutive loss limit: Halt after 2 losses
- Drawdown limit: Stop at -15% from peak
- Emergency exits on spread widening or rapid price moves

✅ **Exchange Support**
- Binance Futures (fully implemented)
- Bybit (placeholder)
- OKX (placeholder)

✅ **Operational Safety**
- Paper trading mode (DRY_RUN)
- JSONL structured logging
- State persistence
- Graceful shutdown (SIGINT/SIGTERM)
- Panic switch to close all positions

## Architecture

```
broke_bot/
├── config.py           # Configuration and constants
├── indicators.py       # ATR, EMA, momentum analyzers
├── exchange_adapter.py # Exchange API abstraction
├── data_fetcher.py     # Market data collection
├── signal_generator.py # Entry signal logic
├── risk_manager.py     # Risk limits and controls
├── position_manager.py # Order execution
├── logger.py          # JSONL logging
├── bot.py             # Main event loop
└── run.py             # Entry point
```

## Installation

### Prerequisites
- Python 3.8+
- pip
- Exchange API keys (for live trading)

### Setup

1. **Navigate to project directory**:
```bash
cd /path/to/arbitrage_suite_updated
```

2. **Create virtual environment** (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

If `requirements.txt` doesn't include these, install manually:
```bash
pip install requests numpy
```

4. **Configure environment**:
```bash
cp .env.broke_bot.example .env
# Edit .env with your settings
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `EXCHANGE` | Exchange to use (binance, bybit, okx) | binance |
| `API_KEY` | Exchange API key | - |
| `API_SECRET` | Exchange API secret | - |
| `TESTNET` | Use testnet | false |
| `SYMBOLS` | Trading symbols (comma-separated) | BTCUSDT |
| `LEVERAGE` | Leverage (2-5x) | 3 |
| `DRY_RUN` | Paper trading mode | true |
| `LOG_PATH` | Log directory | logs/broke_bot |

### Example .env file
```bash
EXCHANGE=binance
API_KEY=your_api_key_here
API_SECRET=your_api_secret_here
SYMBOLS=BTCUSDT,ETHUSDT
LEVERAGE=3
DRY_RUN=true
```

## Usage

### Quick Start (Paper Trading)

```bash
# Using shell script (recommended)
./broke_bot_start.sh

# Or directly with Python
python3 broke_bot/run.py
```

### Command Line Options

```bash
# Paper trade with testnet
python3 broke_bot/run.py --exchange binance --testnet

# Trade multiple symbols
python3 broke_bot/run.py --symbols BTCUSDT,ETHUSDT

# Change leverage
python3 broke_bot/run.py --leverage 2

# Live trading (DANGEROUS!)
python3 broke_bot/run.py --live --exchange binance
```

### View Logs

Logs are written in JSONL format for easy parsing:

```bash
# Tail live logs
tail -f logs/broke_bot/broke_bot_2025-12-15.jsonl

# Parse with jq
cat logs/broke_bot/broke_bot_2025-12-15.jsonl | jq 'select(.type=="entry")'
```

## API Key Setup

### Binance Futures

1. Go to Binance → API Management
2. Create new API key with these permissions:
   - ✅ Enable Reading
   - ✅ Enable Futures
   - ❌ Disable Withdrawals
3. Save API Key and Secret
4. Add to `.env` file

### Security Best Practices

- **Use API keys with trade-only permissions** (no withdrawals)
- **Enable IP whitelisting** if supported
- **Never commit API keys** to version control
- **Use testnet first** before live trading
- **Start with 2x leverage** and small account

## Strategy Details

### Entry Conditions (ALL must be true)

1. **Funding extreme**: `abs(funding_rate) >= 0.08%`
2. **Time window**: Next funding in 10-90 minutes
3. **Liquidity**: Spread ≤ 0.05%, sufficient orderbook depth
4. **Volatility calm**: 
   - ATR(15m) below 7-day median
   - No 3x volume spikes in last 10 minutes
5. **Trend filter**: No strong opposing momentum

### Position Direction

- **Funding > 0**: Longs pay shorts → Open SHORT
- **Funding < 0**: Shorts pay longs → Open LONG

### Exit Conditions

- Take-profit hit (0.4x ATR)
- Stop-loss hit (0.8x ATR)
- Post-funding grace period (5 minutes after funding)
- Emergency: Spread > 0.12% or rapid price move

### Position Sizing

Position size is calculated to risk 1% of equity per trade:

```
stop_distance = 0.8 * ATR(15m)
risk_amount = equity * 0.01
position_size = risk_amount / stop_distance
```

## Monitoring

### Key Metrics to Watch

- **Daily PnL**: Should stay above -2%
- **Consecutive losses**: Max 2 before halt
- **Drawdown**: Must stay above -15%
- **Trades per day**: Max 4
- **Funding payments received**

### Log Types

- `decision`: Entry decision with all inputs
- `entry`: Trade entry with order details
- `exit`: Trade exit with PnL
- `funding_payment`: Funding received
- `risk_limit`: Risk limit triggered
- `emergency_exit`: Emergency close
- `error`: Errors

## Safety Checklist

Before going live:

- [ ] Paper trade for at least 50 funding events
- [ ] Verify fees and funding schedule on exchange
- [ ] Test reduce-only and stop behavior with tiny orders
- [ ] Simulate exchange downtime scenarios
- [ ] Use API keys with minimum permissions
- [ ] Enable IP whitelisting
- [ ] Start with 2x leverage
- [ ] Test panic switch
- [ ] Verify USDT-TRC20 deposit/withdrawal on exchange
- [ ] Maintain TRX balance for network fees

## TRON Operations

### Using USDT-TRC20

1. **Deposits**: 
   - Use TRON network (TRC20) for USDT deposits
   - Significantly cheaper than ERC20
   - Ensure destination address is correct

2. **Withdrawals**:
   - Withdraw profits regularly to avoid giving back gains
   - Target: $20 profit → withdraw immediately
   - Keep small TRX balance for network fees

3. **Network Fees**:
   - Maintain ~1-2 TRX in wallet
   - Covers energy/bandwidth costs
   - Monitor TRX balance

## Troubleshooting

### Common Issues

**"API_KEY required when not in dry run mode"**
- Set API credentials in `.env` file
- Or run in dry-run mode: `DRY_RUN=true`

**"Leverage must be between 2 and 5"**
- Check LEVERAGE setting in `.env`
- Recommended: 2-3x for safety

**"Binance API error"**
- Verify API credentials
- Check IP whitelist settings
- Ensure Futures trading is enabled
- Try testnet first

**No entries being made**
- Funding rates might not be extreme enough
- Check logs for decision reasons
- Volatility might be too high
- Trend filter might be blocking trades

## Development

### Running Tests

```bash
# Unit tests
python -m pytest tests/broke_bot/

# Integration tests (requires testnet keys)
python -m pytest tests/broke_bot/ -m integration
```

### Adding New Exchange

1. Create adapter class in `exchange_adapter.py`
2. Implement all abstract methods
3. Add to factory function
4. Test with testnet

## Performance Expectations

- **Target**: Small, consistent gains from funding payments
- **Win rate**: Variable (30-60% depending on conditions)
- **Hold time**: 8 hours (one funding interval)
- **Trades per day**: 0-4 depending on funding rates
- **Risk**: Primarily price risk during holding period

## Limitations

- Only works when funding rates are extreme
- Requires liquid markets (BTC/ETH recommended)
- Funding rates can change during holding period
- Price risk remains despite hedging attempt
- Requires continuous monitoring in live mode

## Resources

- [Binance Futures API Docs](https://binance-docs.github.io/apidocs/futures/en/)
- [Original Specification](../TRON_Funding_Arbitrage_Bot_Spec.pdf)
- Project logs: `logs/broke_bot/`
- State file: `state/broke_bot_state.json`

## License

Educational use only. See project LICENSE file.

## Support

For issues or questions:
1. Check logs in `logs/broke_bot/`
2. Review configuration in `.env`
3. Verify API key permissions
4. Start with paper trading mode

---

**Remember**: This is a high-risk trading strategy. Never trade with money you cannot afford to lose.

---

<!-- ARC-Trading-Fleet-Nav-Marker -->
## 🧭 ARC Trading Fleet

Six sibling repositories. Same ARC event-and-receipt doctrine. Each has its
own live GitHub Pages docs site, source, and README.

| Repo | One-liner | Source | Docs site |
|---|---|---|---|
| **BrokeBot** (you are here) | TRON Funding-Rate Arbitrage (CEX, Python) | [source](https://github.com/GareBear99/BrokeBot) | [https://garebear99.github.io/BrokeBot/](https://garebear99.github.io/BrokeBot/) |
| [Charm](https://github.com/GareBear99/Charm) | Uniswap v3 Spot Bot on Base (Node.js) | [source](https://github.com/GareBear99/Charm) | [https://garebear99.github.io/Charm/](https://garebear99.github.io/Charm/) |
| [Harvest](https://github.com/GareBear99/Harvest) | Multi-Timeframe Crypto Research Platform (Python) | [source](https://github.com/GareBear99/Harvest) | [https://garebear99.github.io/Harvest/](https://garebear99.github.io/Harvest/) |
| [One-Shot-Multi-Shot](https://github.com/GareBear99/One-Shot-Multi-Shot) | Binary-Options 3-Hearts Engine (JS) | [source](https://github.com/GareBear99/One-Shot-Multi-Shot) | [https://garebear99.github.io/One-Shot-Multi-Shot/](https://garebear99.github.io/One-Shot-Multi-Shot/) |
| [DecaGrid](https://github.com/GareBear99/DecaGrid) | Capital-Ladder Grid Trading Docs Pack | [source](https://github.com/GareBear99/DecaGrid) | [https://garebear99.github.io/DecaGrid/](https://garebear99.github.io/DecaGrid/) |
| [EdgeStack Currency](https://github.com/GareBear99/EdgeStack_Currency) | Event-Sourced Multi-Currency Execution Spec | [source](https://github.com/GareBear99/EdgeStack_Currency) | [https://garebear99.github.io/EdgeStack_Currency/](https://garebear99.github.io/EdgeStack_Currency/) |

### Upstream + meta
- [ARC-Core](https://github.com/GareBear99/ARC-Core) — governed event + receipt spine the fleet plugs into.
- [omnibinary-runtime](https://github.com/GareBear99/omnibinary-runtime) + [Arc-RAR](https://github.com/GareBear99/Arc-RAR) — any-OS portability for deployment.
- [Portfolio](https://github.com/GareBear99/Portfolio) — full project index (audio plugins, games, simulators, AI runtimes, robotics, trading).

---

<!-- ARC-Funding-Badges-Marker -->
## 💖 Support the fleet

If this repo helps you, the maintainer runs the entire ARC ecosystem solo.
Any of the following keep the lights on:

[![Sponsor](https://img.shields.io/badge/GitHub%20Sponsors-GareBear99-ea4aaa?logo=githubsponsors&logoColor=white)](https://github.com/sponsors/GareBear99)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-garebear99-FFDD00?logo=buymeacoffee&logoColor=black)](https://www.buymeacoffee.com/garebear99)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-garebear99-FF5E5B?logo=ko-fi&logoColor=white)](https://ko-fi.com/garebear99)

- **GitHub Sponsors**: <https://github.com/sponsors/GareBear99>
- **Buy Me a Coffee**: <https://www.buymeacoffee.com/garebear99>
- **Ko-fi**: <https://ko-fi.com/garebear99>

Every dollar funds hardening across **ARC-Core + the 15 consumer repos + the four roadmap repos**. One author, one funding pool.
