"""
Risk Manager for Broke Bot
Session-level limits, drawdown tracking, emergency exits
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import deque
import json
from pathlib import Path

from .config import TradingConfig
from .data_fetcher import MarketData


class RiskState:
    """Track risk metrics and limits"""
    
    def __init__(self):
        self.daily_trades: int = 0
        self.interval_trades: int = 0
        self.consecutive_losses: int = 0
        self.daily_pnl: float = 0.0
        self.equity_peak: float = 0.0
        self.current_equity: float = 0.0
        self.last_funding_interval: int = 0
        self.trade_history: deque = deque(maxlen=100)
        self.daily_reset_time: datetime = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for persistence"""
        return {
            'daily_trades': self.daily_trades,
            'interval_trades': self.interval_trades,
            'consecutive_losses': self.consecutive_losses,
            'daily_pnl': self.daily_pnl,
            'equity_peak': self.equity_peak,
            'current_equity': self.current_equity,
            'last_funding_interval': self.last_funding_interval,
            'daily_reset_time': self.daily_reset_time.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Create from dictionary"""
        state = cls()
        state.daily_trades = data.get('daily_trades', 0)
        state.interval_trades = data.get('interval_trades', 0)
        state.consecutive_losses = data.get('consecutive_losses', 0)
        state.daily_pnl = data.get('daily_pnl', 0.0)
        state.equity_peak = data.get('equity_peak', 0.0)
        state.current_equity = data.get('current_equity', 0.0)
        state.last_funding_interval = data.get('last_funding_interval', 0)
        if 'daily_reset_time' in data:
            state.daily_reset_time = datetime.fromisoformat(data['daily_reset_time'])
        return state


class RiskManager:
    """Manage trading risk and enforce limits"""
    
    def __init__(self, config: TradingConfig, state_file: str = "state/broke_bot_state.json"):
        self.config = config
        self.state_file = Path(state_file)
        self.state = self._load_state()
        
        # Halt flags
        self.daily_halt = False
        self.drawdown_halt = False
        self.consecutive_loss_halt = False
    
    def _load_state(self) -> RiskState:
        """Load state from disk"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                return RiskState.from_dict(data)
            except Exception:
                pass
        return RiskState()
    
    def _save_state(self):
        """Save state to disk"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self.state.to_dict(), f, indent=2)
    
    def update_equity(self, current_equity: float):
        """Update current equity and track peak"""
        self.state.current_equity = current_equity
        
        if current_equity > self.state.equity_peak:
            self.state.equity_peak = current_equity
        
        self._save_state()
    
    def check_daily_reset(self):
        """Check if we need to reset daily counters"""
        now = datetime.now()
        if now.date() > self.state.daily_reset_time.date():
            self.state.daily_trades = 0
            self.state.daily_pnl = 0.0
            self.state.daily_reset_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            self.daily_halt = False
            self.consecutive_loss_halt = False
            self._save_state()
    
    def check_interval_reset(self, next_funding_time: int):
        """Check if we need to reset interval counter"""
        if next_funding_time != self.state.last_funding_interval:
            self.state.interval_trades = 0
            self.state.last_funding_interval = next_funding_time
            self._save_state()
    
    def can_open_position(self) -> tuple[bool, Optional[str]]:
        """Check if we can open a new position"""
        self.check_daily_reset()
        
        # Check halt flags
        if self.daily_halt:
            return False, "daily_loss_limit_reached"
        
        if self.drawdown_halt:
            return False, "drawdown_limit_reached"
        
        if self.consecutive_loss_halt:
            return False, "consecutive_loss_limit_reached"
        
        # Check max trades per day
        if self.state.daily_trades >= self.config.max_trades_per_day:
            return False, "max_daily_trades_reached"
        
        # Check max trades per interval
        if self.state.interval_trades >= self.config.max_trades_per_interval:
            return False, "max_interval_trades_reached"
        
        return True, None
    
    def record_trade_entry(self):
        """Record a trade entry"""
        self.state.daily_trades += 1
        self.state.interval_trades += 1
        self._save_state()
    
    def record_trade_exit(self, pnl: float):
        """Record a trade exit and update risk metrics"""
        self.state.daily_pnl += pnl
        
        # Track consecutive losses
        if pnl < 0:
            self.state.consecutive_losses += 1
        else:
            self.state.consecutive_losses = 0
        
        # Check consecutive loss limit
        if self.state.consecutive_losses >= self.config.max_consecutive_losses:
            self.consecutive_loss_halt = True
        
        # Check daily loss limit
        if self.state.daily_pnl <= (self.config.daily_loss_halt * self.state.equity_peak):
            self.daily_halt = True
        
        # Check drawdown limit
        if self.state.equity_peak > 0:
            drawdown = (self.state.current_equity - self.state.equity_peak) / self.state.equity_peak
            if drawdown <= self.config.drawdown_halt:
                self.drawdown_halt = True
        
        self._save_state()
    
    def check_emergency_exit(self, data: MarketData, entry_price: float, 
                            entry_time: datetime) -> tuple[bool, Optional[str]]:
        """
        Check if emergency exit conditions are met
        
        Emergency exit triggers:
        - Spread widens beyond 0.12%
        - Mark price moves 1.2x ATR(15m) in 5 minutes
        """
        # Check spread
        if data.spread > self.config.emergency_spread_threshold:
            return True, "spread_widened"
        
        # Check rapid price movement (if we have recent entry)
        time_since_entry = (datetime.now() - entry_time).total_seconds() / 60
        if time_since_entry <= 5:
            price_change = abs(data.mark_price - entry_price)
            threshold = self.config.emergency_price_move_mult * data.atr_15m
            if price_change > threshold:
                return True, "rapid_price_movement"
        
        return False, None
    
    def calculate_position_size(self, equity: float, atr: float, 
                               entry_price: float, leverage: int) -> float:
        """
        Calculate position size based on risk per trade
        
        Formula: Risk 1% of equity based on stop distance
        Position size = (Equity * Risk%) / (Stop distance in price)
        Stop distance = 0.8 * ATR
        """
        stop_distance = self.config.stop_atr_mult * atr
        risk_amount = equity * self.config.risk_per_trade
        
        # Position size in base currency
        position_size = risk_amount / stop_distance
        
        # Apply leverage (position size is notional value)
        # With leverage, we can control larger position with same capital
        max_position = equity * leverage
        
        # Take the minimum to ensure we don't exceed leverage limits
        return min(position_size, max_position / entry_price)
    
    def get_stop_price(self, entry_price: float, atr: float, side: str) -> float:
        """Calculate stop loss price"""
        stop_distance = self.config.stop_atr_mult * atr
        
        if side == 'LONG':
            return entry_price - stop_distance
        else:  # SHORT
            return entry_price + stop_distance
    
    def get_take_profit_price(self, entry_price: float, atr: float, side: str) -> float:
        """Calculate take profit price"""
        tp_distance = self.config.tp_atr_mult * atr
        
        if side == 'LONG':
            return entry_price + tp_distance
        else:  # SHORT
            return entry_price - tp_distance
    
    def is_halted(self) -> bool:
        """Check if trading is halted"""
        return self.daily_halt or self.drawdown_halt or self.consecutive_loss_halt
    
    def get_halt_reasons(self) -> list[str]:
        """Get list of active halt reasons"""
        reasons = []
        if self.daily_halt:
            reasons.append("daily_loss_limit")
        if self.drawdown_halt:
            reasons.append("drawdown_limit")
        if self.consecutive_loss_halt:
            reasons.append("consecutive_losses")
        return reasons
