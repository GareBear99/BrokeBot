"""
Broke Bot Configuration
All parameters from the TRON Funding Rate Arbitrage Bot specification
"""

import os
from typing import List
from dataclasses import dataclass


@dataclass
class TradingConfig:
    """Trading parameters"""
    symbol: str = "BTCUSDT"
    symbols: List[str] = None
    leverage: int = 3
    margin_mode: str = "isolated"
    
    # Entry conditions
    funding_threshold: float = 0.0008  # 0.08%
    funding_window_min_minutes: int = 10
    funding_window_max_minutes: int = 90
    spread_max: float = 0.0005  # 0.05%
    
    # Risk management
    risk_per_trade: float = 0.01  # 1%
    stop_atr_mult: float = 0.8
    tp_atr_mult: float = 0.4
    max_trades_per_day: int = 4
    max_trades_per_interval: int = 2
    max_consecutive_losses: int = 2
    daily_loss_halt: float = -0.02  # -2%
    drawdown_halt: float = -0.15  # -15%
    
    # Emergency exit thresholds
    emergency_spread_threshold: float = 0.0012  # 0.12%
    emergency_price_move_mult: float = 1.2  # 1.2x ATR in 5 minutes
    
    # Technical indicators
    atr_period: int = 14
    atr_timeframe: str = "15m"
    ema_fast: int = 20
    ema_slow: int = 50
    ema_timeframe: str = "15m"
    atr_lookback_days: int = 7
    
    # Trend filter
    momentum_range_mult: float = 1.5  # 15m candle range > 1.5x ATR
    momentum_consecutive_closes: int = 5
    
    # Timing
    loop_interval_seconds: int = 5
    hold_grace_minutes: int = 5  # Hold after funding payment
    
    def __post_init__(self):
        if self.symbols is None:
            self.symbols = [self.symbol]


@dataclass
class ExchangeConfig:
    """Exchange connection parameters"""
    exchange: str = os.getenv("EXCHANGE", "binance")
    api_key: str = os.getenv("API_KEY", "")
    api_secret: str = os.getenv("API_SECRET", "")
    testnet: bool = os.getenv("TESTNET", "false").lower() == "true"
    
    # Rate limiting
    max_requests_per_minute: int = 1200
    
    # Order execution
    order_timeout_seconds: int = 30
    limit_order_offset_bps: float = 0.0001  # Try to get maker fill


@dataclass
class OperationalConfig:
    """Operational settings"""
    dry_run: bool = os.getenv("DRY_RUN", "true").lower() == "true"
    log_path: str = os.getenv("LOG_PATH", "logs/broke_bot")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # State persistence
    state_file: str = "state/broke_bot_state.json"
    
    # Safety
    enable_panic_switch: bool = True
    require_api_key_validation: bool = True


class Config:
    """Main configuration container"""
    
    def __init__(self):
        self.trading = TradingConfig()
        self.exchange = ExchangeConfig()
        self.operational = OperationalConfig()
    
    @classmethod
    def from_env(cls):
        """Create config from environment variables"""
        config = cls()
        
        # Override from environment
        if os.getenv("SYMBOLS"):
            config.trading.symbols = os.getenv("SYMBOLS").split(",")
        
        if os.getenv("LEVERAGE"):
            config.trading.leverage = int(os.getenv("LEVERAGE"))
        
        if os.getenv("FUNDING_THRESHOLD"):
            config.trading.funding_threshold = float(os.getenv("FUNDING_THRESHOLD"))
        
        return config
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        # Leverage checks
        if not (2 <= self.trading.leverage <= 5):
            errors.append(f"Leverage must be between 2 and 5, got {self.trading.leverage}")
        
        # Exchange checks
        if not self.exchange.api_key and not self.operational.dry_run:
            errors.append("API_KEY required when not in dry run mode")
        
        if not self.exchange.api_secret and not self.operational.dry_run:
            errors.append("API_SECRET required when not in dry run mode")
        
        # Supported exchanges
        supported = ["binance", "bybit", "okx"]
        if self.exchange.exchange.lower() not in supported:
            errors.append(f"Exchange must be one of {supported}, got {self.exchange.exchange}")
        
        # Risk parameters
        if self.trading.risk_per_trade <= 0 or self.trading.risk_per_trade > 0.05:
            errors.append(f"Risk per trade should be between 0 and 5%, got {self.trading.risk_per_trade*100}%")
        
        return errors
