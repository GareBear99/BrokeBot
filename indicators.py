"""
Technical Indicators for Broke Bot
ATR, EMA, and supporting calculations
"""

import numpy as np
from typing import List, Tuple
from collections import deque


class ATR:
    """Average True Range calculator"""
    
    def __init__(self, period: int = 14):
        self.period = period
        self.values = deque(maxlen=1000)  # Keep history for median calculation
    
    @staticmethod
    def true_range(high: float, low: float, prev_close: float) -> float:
        """Calculate True Range for a single candle"""
        return max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        )
    
    def calculate(self, highs: List[float], lows: List[float], closes: List[float]) -> float:
        """
        Calculate ATR from OHLC data
        
        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of close prices
        
        Returns:
            Current ATR value
        """
        if len(highs) < self.period + 1:
            return 0.0
        
        # Calculate true ranges
        true_ranges = []
        for i in range(1, len(highs)):
            tr = self.true_range(highs[i], lows[i], closes[i-1])
            true_ranges.append(tr)
        
        # Simple Moving Average of True Range for initial ATR
        if len(true_ranges) < self.period:
            return 0.0
        
        # Smoothed ATR calculation (Wilder's method)
        atr = sum(true_ranges[:self.period]) / self.period
        
        for tr in true_ranges[self.period:]:
            atr = (atr * (self.period - 1) + tr) / self.period
        
        # Store for median calculation
        self.values.append(atr)
        
        return atr
    
    def get_median(self, lookback_periods: int = None) -> float:
        """Get median ATR over lookback period"""
        if not self.values:
            return 0.0
        
        if lookback_periods:
            values = list(self.values)[-lookback_periods:]
        else:
            values = list(self.values)
        
        return float(np.median(values)) if values else 0.0


class EMA:
    """Exponential Moving Average calculator"""
    
    def __init__(self, period: int):
        self.period = period
        self.multiplier = 2.0 / (period + 1)
        self.ema = None
    
    def calculate(self, prices: List[float]) -> float:
        """
        Calculate EMA from price data
        
        Args:
            prices: List of prices (typically close prices)
        
        Returns:
            Current EMA value
        """
        if len(prices) < self.period:
            return 0.0
        
        # Initialize with SMA
        if self.ema is None:
            self.ema = sum(prices[:self.period]) / self.period
            start_idx = self.period
        else:
            start_idx = 0
        
        # Calculate EMA
        for price in prices[start_idx:]:
            self.ema = (price - self.ema) * self.multiplier + self.ema
        
        return self.ema
    
    def update(self, price: float) -> float:
        """Update EMA with single new price"""
        if self.ema is None:
            self.ema = price
        else:
            self.ema = (price - self.ema) * self.multiplier + self.ema
        return self.ema
    
    def reset(self):
        """Reset EMA state"""
        self.ema = None


class MomentumAnalyzer:
    """Analyze price momentum for trend filter"""
    
    @staticmethod
    def detect_strong_momentum(
        candles: List[dict],
        atr: float,
        range_multiplier: float = 1.5,
        consecutive_threshold: int = 5
    ) -> Tuple[bool, str]:
        """
        Detect strong momentum conditions
        
        Args:
            candles: List of recent candles with OHLC data
            atr: Current ATR value
            range_multiplier: Candle range threshold vs ATR
            consecutive_threshold: Number of consecutive closes in same direction
        
        Returns:
            (has_momentum, direction) - direction is 'up', 'down', or 'none'
        """
        if not candles or len(candles) < 2:
            return False, 'none'
        
        latest = candles[-1]
        
        # Check if latest candle range exceeds threshold
        candle_range = latest['high'] - latest['low']
        range_condition = candle_range > (range_multiplier * atr)
        
        # Check for consecutive closes in same direction
        if len(candles) >= consecutive_threshold:
            recent_closes = [c['close'] for c in candles[-consecutive_threshold:]]
            
            # All increasing
            all_up = all(recent_closes[i] < recent_closes[i+1] 
                        for i in range(len(recent_closes)-1))
            
            # All decreasing
            all_down = all(recent_closes[i] > recent_closes[i+1] 
                          for i in range(len(recent_closes)-1))
            
            consecutive_condition = all_up or all_down
            direction = 'up' if all_up else ('down' if all_down else 'none')
        else:
            consecutive_condition = False
            direction = 'none'
        
        has_momentum = range_condition or consecutive_condition
        
        return has_momentum, direction


class VolatilityFilter:
    """Filter for detecting abnormal volatility spikes"""
    
    def __init__(self, lookback_minutes: int = 10):
        self.lookback_minutes = lookback_minutes
        self.volume_history = deque(maxlen=lookback_minutes)
    
    def check_abnormal_activity(
        self,
        current_volume: float,
        avg_volume: float,
        spike_threshold: float = 3.0
    ) -> bool:
        """
        Check if current volume represents abnormal activity
        
        Args:
            current_volume: Current 1-minute volume
            avg_volume: Average 1-minute volume
            spike_threshold: Multiplier for spike detection
        
        Returns:
            True if abnormal spike detected
        """
        self.volume_history.append(current_volume)
        
        if not avg_volume or avg_volume == 0:
            return False
        
        # Check if any recent volume exceeds threshold
        for vol in self.volume_history:
            if vol > (avg_volume * spike_threshold):
                return True
        
        return False
    
    def is_volatility_calm(
        self,
        current_atr: float,
        median_atr: float,
        recent_volumes: List[float],
        avg_volume: float
    ) -> bool:
        """
        Check if volatility conditions are calm enough for entry
        
        Args:
            current_atr: Current ATR value
            median_atr: 7-day median ATR
            recent_volumes: Recent 1-minute volumes
            avg_volume: Average 1-minute volume
        
        Returns:
            True if conditions are calm
        """
        # ATR should be below median
        if median_atr > 0 and current_atr >= median_atr:
            return False
        
        # No abnormal volume spikes in last 10 minutes
        if recent_volumes and avg_volume > 0:
            for vol in recent_volumes[-self.lookback_minutes:]:
                if vol > (avg_volume * 3.0):  # 3x spike
                    return False
        
        return True
