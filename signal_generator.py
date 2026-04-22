"""
Signal Generator for Broke Bot
Determines when funding is extreme and conditions are calm enough to enter
"""

from typing import Tuple, List, Optional
from .data_fetcher import MarketData
from .config import TradingConfig
from .indicators import MomentumAnalyzer, VolatilityFilter


class SignalGenerator:
    """Generate entry signals based on funding rate and filters"""
    
    def __init__(self, config: TradingConfig):
        self.config = config
        self.momentum_analyzer = MomentumAnalyzer()
        self.volatility_filter = VolatilityFilter(lookback_minutes=10)
    
    def generate_signal(self, data: MarketData, mins_to_funding: float) -> Tuple[Optional[str], List[str]]:
        """
        Generate trading signal based on all entry conditions
        
        Args:
            data: Market data
            mins_to_funding: Minutes until next funding
        
        Returns:
            (side, reasons) - side is 'LONG', 'SHORT', or None; reasons are filter results
        """
        reasons = []
        
        # 1. Check funding extreme
        if abs(data.funding_rate) < self.config.funding_threshold:
            reasons.append("funding_not_extreme")
            return None, reasons
        reasons.append("funding_extreme")
        
        # 2. Check time to funding window
        if not (self.config.funding_window_min_minutes <= mins_to_funding <= self.config.funding_window_max_minutes):
            reasons.append("outside_funding_window")
            return None, reasons
        reasons.append("funding_window_ok")
        
        # 3. Check liquidity (spread)
        if data.spread > self.config.spread_max:
            reasons.append("spread_too_wide")
            return None, reasons
        reasons.append("spread_ok")
        
        # 4. Check volatility is calm
        if not self._is_volatility_calm(data):
            reasons.append("volatility_not_calm")
            return None, reasons
        reasons.append("vol_calm")
        
        # 5. Check trend filter
        side = 'SHORT' if data.funding_rate > 0 else 'LONG'
        if self._trend_filter_blocks(data, side):
            reasons.append("trend_filter_blocked")
            return None, reasons
        reasons.append("trend_filter_passed")
        
        return side, reasons
    
    def _is_volatility_calm(self, data: MarketData) -> bool:
        """Check if volatility conditions are calm"""
        # ATR should be below its median
        if data.median_atr > 0 and data.atr_15m >= data.median_atr:
            return False
        
        # No abnormal volume spikes in last 10 minutes
        if data.avg_volume > 0:
            for vol in data.recent_volumes[-10:]:
                if vol > (data.avg_volume * 3.0):  # 3x spike
                    return False
        
        return True
    
    def _trend_filter_blocks(self, data: MarketData, side: str) -> bool:
        """
        Check if trend filter blocks the trade
        
        Trend safety filter from spec:
        - If funding is positive (want SHORT), do not short if price is above EMA20 
          and EMA20 > EMA50 with strong momentum
        - If funding is negative (want LONG), do not long if price is below EMA20 
          and EMA20 < EMA50 with strong momentum
        """
        if not data.candles_15m or len(data.candles_15m) < 5:
            return False  # Not enough data, allow trade
        
        current_price = data.mark_price
        ema20 = data.ema20_15m
        ema50 = data.ema50_15m
        
        # Need valid EMAs
        if ema20 == 0 or ema50 == 0:
            return False
        
        # Check for strong momentum
        has_momentum, momentum_direction = self.momentum_analyzer.detect_strong_momentum(
            data.candles_15m,
            data.atr_15m,
            range_multiplier=self.config.momentum_range_mult,
            consecutive_threshold=self.config.momentum_consecutive_closes
        )
        
        if not has_momentum:
            return False  # No strong momentum, safe to trade
        
        # Apply trend filter rules
        if side == 'SHORT':
            # Want to short (funding is positive)
            # Block if price above EMA20 and EMA20 > EMA50 with upward momentum
            if current_price > ema20 and ema20 > ema50 and momentum_direction == 'up':
                return True
        
        elif side == 'LONG':
            # Want to long (funding is negative)
            # Block if price below EMA20 and EMA20 < EMA50 with downward momentum
            if current_price < ema20 and ema20 < ema50 and momentum_direction == 'down':
                return True
        
        return False
    
    def determine_side(self, funding_rate: float) -> str:
        """Determine position side based on funding rate"""
        return 'SHORT' if funding_rate > 0 else 'LONG'
