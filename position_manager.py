"""
Position Manager for Broke Bot
Handles entry/exit execution with stops and take profits
"""

from typing import Optional, Dict
from datetime import datetime

from .exchange_adapter import ExchangeAdapter
from .config import TradingConfig, OperationalConfig
from .logger import BrokeBotLogger


class Position:
    """Track current position state"""
    
    def __init__(self, symbol: str, side: str, quantity: float, entry_price: float,
                 stop_price: float, tp_price: float, entry_time: datetime,
                 funding_rate: float):
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.entry_price = entry_price
        self.stop_price = stop_price
        self.tp_price = tp_price
        self.entry_time = entry_time
        self.funding_rate = funding_rate
        self.stop_order_id: Optional[str] = None
        self.tp_order_id: Optional[str] = None
        self.entry_order_id: Optional[str] = None


class PositionManager:
    """Manage position entry and exit"""
    
    def __init__(self, exchange: ExchangeAdapter, config: TradingConfig,
                 operational_config: OperationalConfig, logger: BrokeBotLogger):
        self.exchange = exchange
        self.config = config
        self.operational_config = operational_config
        self.logger = logger
        self.current_position: Optional[Position] = None
    
    def has_position(self) -> bool:
        """Check if we have an open position"""
        return self.current_position is not None
    
    def enter_position(self, symbol: str, side: str, quantity: float,
                      entry_price: float, stop_price: float, tp_price: float,
                      funding_rate: float, atr: float) -> bool:
        """
        Enter a position with stop loss and take profit
        
        Returns True if successful, False otherwise
        """
        if self.operational_config.dry_run:
            self.logger.log_info(f"[DRY RUN] Would enter {side} position", 
                               symbol=symbol, quantity=quantity, price=entry_price)
            # Simulate position in dry run mode
            self.current_position = Position(
                symbol=symbol,
                side=side,
                quantity=quantity,
                entry_price=entry_price,
                stop_price=stop_price,
                tp_price=tp_price,
                entry_time=datetime.now(),
                funding_rate=funding_rate
            )
            return True
        
        try:
            # Place entry order (try limit first, fallback to market)
            try:
                entry_order = self.exchange.place_order(
                    symbol=symbol,
                    side=side,
                    order_type='LIMIT',
                    quantity=quantity,
                    price=entry_price
                )
                entry_order_id = entry_order.get('orderId')
                
                # Wait briefly for fill (in real implementation, should monitor order status)
                # For now, assume filled
                
            except Exception as e:
                self.logger.log_error("limit_order_failed", str(e), symbol=symbol)
                # Fallback to market order
                entry_order = self.exchange.place_order(
                    symbol=symbol,
                    side=side,
                    order_type='MARKET',
                    quantity=quantity
                )
                entry_order_id = entry_order.get('orderId')
            
            # Create position object
            self.current_position = Position(
                symbol=symbol,
                side=side,
                quantity=quantity,
                entry_price=entry_price,
                stop_price=stop_price,
                tp_price=tp_price,
                entry_time=datetime.now(),
                funding_rate=funding_rate
            )
            self.current_position.entry_order_id = entry_order_id
            
            # Place stop loss (stop-market, reduce-only)
            close_side = 'SELL' if side == 'LONG' else 'BUY'
            stop_order = self.exchange.place_order(
                symbol=symbol,
                side=close_side,
                order_type='STOP_MARKET',
                quantity=quantity,
                price=stop_price,
                params={'reduceOnly': 'true', 'closePosition': 'false'}
            )
            self.current_position.stop_order_id = stop_order.get('orderId')
            
            # Place take profit (reduce-only limit)
            tp_order = self.exchange.place_order(
                symbol=symbol,
                side=close_side,
                order_type='TAKE_PROFIT',
                quantity=quantity,
                price=tp_price,
                params={'reduceOnly': 'true', 'closePosition': 'false'}
            )
            self.current_position.tp_order_id = tp_order.get('orderId')
            
            # Log entry
            self.logger.log_entry(
                symbol=symbol,
                side=side,
                quantity=quantity,
                entry_price=entry_price,
                funding_rate=funding_rate,
                order_id=entry_order_id,
                stop_price=stop_price,
                tp_price=tp_price,
                atr=atr
            )
            
            return True
            
        except Exception as e:
            self.logger.log_error("position_entry_failed", str(e), symbol=symbol)
            return False
    
    def close_position(self, reason: str, current_price: float) -> bool:
        """Close current position"""
        if not self.current_position:
            return False
        
        position = self.current_position
        
        if self.operational_config.dry_run:
            pnl = self._calculate_pnl(position, current_price)
            self.logger.log_info(f"[DRY RUN] Would close position", 
                               symbol=position.symbol, reason=reason, pnl=pnl)
            self.logger.log_exit(
                symbol=position.symbol,
                side=position.side,
                quantity=position.quantity,
                exit_price=current_price,
                pnl=pnl,
                reason=reason
            )
            self.current_position = None
            return True
        
        try:
            # Cancel stop and TP orders
            if position.stop_order_id:
                try:
                    self.exchange.cancel_order(position.symbol, position.stop_order_id)
                except Exception:
                    pass  # Order might already be filled
            
            if position.tp_order_id:
                try:
                    self.exchange.cancel_order(position.symbol, position.tp_order_id)
                except Exception:
                    pass
            
            # Close position with market order
            result = self.exchange.close_position(position.symbol)
            
            # Calculate PnL
            pnl = self._calculate_pnl(position, current_price)
            
            # Log exit
            self.logger.log_exit(
                symbol=position.symbol,
                side=position.side,
                quantity=position.quantity,
                exit_price=current_price,
                pnl=pnl,
                reason=reason,
                order_id=result.get('orderId')
            )
            
            self.current_position = None
            return True
            
        except Exception as e:
            self.logger.log_error("position_exit_failed", str(e), symbol=position.symbol)
            return False
    
    def _calculate_pnl(self, position: Position, exit_price: float) -> float:
        """Calculate PnL for position"""
        if position.side == 'LONG':
            pnl = (exit_price - position.entry_price) * position.quantity
        else:  # SHORT
            pnl = (position.entry_price - exit_price) * position.quantity
        return pnl
    
    def get_current_pnl(self, current_price: float) -> float:
        """Get current unrealized PnL"""
        if not self.current_position:
            return 0.0
        return self._calculate_pnl(self.current_position, current_price)
    
    def should_exit_post_funding(self, next_funding_time: int) -> bool:
        """Check if we should exit after funding payment"""
        if not self.current_position:
            return False
        
        # Check if funding time has passed plus grace period
        now_ms = int(datetime.now().timestamp() * 1000)
        grace_ms = self.config.hold_grace_minutes * 60 * 1000
        
        return now_ms > (next_funding_time + grace_ms)
