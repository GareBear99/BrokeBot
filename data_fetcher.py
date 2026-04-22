"""
Data Fetcher for Broke Bot
Collects all required market data from exchange
"""

from typing import Dict, List, Optional
from datetime import datetime
from collections import deque

from .exchange_adapter import ExchangeAdapter
from .indicators import ATR, EMA


class MarketData:
    """Container for all market data"""
    
    def __init__(self):
        self.funding_rate: float = 0.0
        self.next_funding_time: int = 0
        self.mark_price: float = 0.0
        self.best_bid: float = 0.0
        self.best_ask: float = 0.0
        self.spread: float = 0.0
        self.bid_quantity: float = 0.0
        self.ask_quantity: float = 0.0
        self.atr_15m: float = 0.0
        self.median_atr: float = 0.0
        self.ema20_15m: float = 0.0
        self.ema50_15m: float = 0.0
        self.volume_1m: float = 0.0
        self.recent_volumes: List[float] = []
        self.avg_volume: float = 0.0
        self.candles_15m: List[Dict] = []
        self.timestamp: datetime = datetime.now()


class DataFetcher:
    """Fetch and process market data"""
    
    def __init__(self, exchange: ExchangeAdapter, atr_period: int = 14,
                 atr_lookback_days: int = 7):
        self.exchange = exchange
        
        # Technical indicators
        self.atr = ATR(period=atr_period)
        self.ema20 = EMA(period=20)
        self.ema50 = EMA(period=50)
        
        # Volume tracking
        self.volume_history = deque(maxlen=60)  # Last 60 1-minute volumes
        
        # ATR lookback (15m candles for 7 days = ~672 candles)
        self.atr_lookback_periods = (atr_lookback_days * 24 * 60) // 15
    
    def fetch_all(self, symbol: str) -> MarketData:
        """Fetch all required data for trading decision"""
        data = MarketData()
        
        try:
            # Funding rate and next funding time
            data.funding_rate, data.next_funding_time = self.exchange.get_funding_rate(symbol)
            
            # Mark price
            data.mark_price = self.exchange.get_mark_price(symbol)
            
            # Orderbook
            orderbook = self.exchange.get_orderbook(symbol)
            data.best_bid = orderbook['best_bid']
            data.best_ask = orderbook['best_ask']
            data.spread = orderbook['spread']
            data.bid_quantity = orderbook['bid_quantity']
            data.ask_quantity = orderbook['ask_quantity']
            
            # 15-minute candles for ATR and EMA
            # Fetch enough history for indicators (100 candles minimum)
            klines_15m = self.exchange.get_klines(symbol, '15m', limit=100)
            data.candles_15m = klines_15m
            
            if len(klines_15m) >= 15:
                highs = [k['high'] for k in klines_15m]
                lows = [k['low'] for k in klines_15m]
                closes = [k['close'] for k in klines_15m]
                
                # Calculate ATR
                data.atr_15m = self.atr.calculate(highs, lows, closes)
                data.median_atr = self.atr.get_median(self.atr_lookback_periods)
                
                # Calculate EMAs
                data.ema20_15m = self.ema20.calculate(closes)
                data.ema50_15m = self.ema50.calculate(closes)
            
            # 1-minute volume for abnormal activity detection
            klines_1m = self.exchange.get_klines(symbol, '1m', limit=60)
            if klines_1m:
                data.volume_1m = klines_1m[-1]['volume']
                data.recent_volumes = [k['volume'] for k in klines_1m]
                
                # Calculate average volume
                if len(data.recent_volumes) > 0:
                    data.avg_volume = sum(data.recent_volumes) / len(data.recent_volumes)
                
                # Update volume history
                self.volume_history.extend(data.recent_volumes)
            
            data.timestamp = datetime.now()
            
        except Exception as e:
            raise Exception(f"Error fetching market data: {e}")
        
        return data
    
    def get_minutes_to_funding(self, next_funding_time: int) -> float:
        """Calculate minutes until next funding"""
        now_ms = int(datetime.now().timestamp() * 1000)
        diff_ms = next_funding_time - now_ms
        return diff_ms / (1000 * 60)
    
    def check_liquidity(self, best_bid: float, best_ask: float, 
                       bid_qty: float, ask_qty: float,
                       min_depth: float = 1000) -> bool:
        """
        Check if liquidity is sufficient
        
        Args:
            best_bid: Best bid price
            best_ask: Best ask price
            bid_qty: Bid quantity in base currency
            ask_qty: Ask quantity in base currency
            min_depth: Minimum depth required in USD
        
        Returns:
            True if liquidity is sufficient
        """
        # Check bid side depth
        bid_depth = bid_qty * best_bid
        ask_depth = ask_qty * best_ask
        
        return bid_depth >= min_depth and ask_depth >= min_depth
