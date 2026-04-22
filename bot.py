"""
Broke Bot - Main Event Loop
5-second polling loop for funding-rate arbitrage
"""

import time
import signal
import sys
from datetime import datetime
from typing import Optional

from .config import Config
from .exchange_adapter import create_exchange_adapter
from .data_fetcher import DataFetcher
from .signal_generator import SignalGenerator
from .risk_manager import RiskManager
from .position_manager import PositionManager
from .logger import BrokeBotLogger


class BrokeBot:
    """Main bot class implementing funding-rate arbitrage strategy"""
    
    def __init__(self, config: Config):
        self.config = config
        self.running = False
        self.panic_mode = False
        
        # Initialize logger
        self.logger = BrokeBotLogger(config.operational.log_path)
        
        # Initialize exchange adapter
        try:
            self.exchange = create_exchange_adapter(
                exchange=config.exchange.exchange,
                api_key=config.exchange.api_key,
                api_secret=config.exchange.api_secret,
                testnet=config.exchange.testnet
            )
        except Exception as e:
            self.logger.log_error("exchange_init_failed", str(e))
            raise
        
        # Initialize modules
        self.data_fetcher = DataFetcher(
            exchange=self.exchange,
            atr_period=config.trading.atr_period,
            atr_lookback_days=config.trading.atr_lookback_days
        )
        self.signal_generator = SignalGenerator(config.trading)
        self.risk_manager = RiskManager(
            config=config.trading,
            state_file=config.operational.state_file
        )
        self.position_manager = PositionManager(
            exchange=self.exchange,
            config=config.trading,
            operational_config=config.operational,
            logger=self.logger
        )
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.log_info("Shutdown signal received, stopping bot...")
        self.stop()
    
    def start(self):
        """Start the bot"""
        self.running = True
        
        # Validate configuration
        errors = self.config.validate()
        if errors:
            for error in errors:
                self.logger.log_error("config_validation_failed", error)
            raise ValueError(f"Configuration validation failed: {errors}")
        
        # Log startup
        mode = "DRY RUN" if self.config.operational.dry_run else "LIVE"
        self.logger.log_info(
            f"Broke Bot starting in {mode} mode",
            exchange=self.config.exchange.exchange,
            symbols=self.config.trading.symbols,
            leverage=self.config.trading.leverage
        )
        
        # Initialize leverage and margin mode for each symbol
        if not self.config.operational.dry_run:
            for symbol in self.config.trading.symbols:
                try:
                    self.exchange.set_leverage(symbol, self.config.trading.leverage)
                    self.exchange.set_margin_mode(symbol, self.config.trading.margin_mode)
                except Exception as e:
                    self.logger.log_error("exchange_setup_failed", str(e), symbol=symbol)
        
        # Main event loop
        self._run_loop()
    
    def stop(self):
        """Stop the bot"""
        self.running = False
        
        # Close any open positions if panic mode
        if self.panic_mode and self.position_manager.has_position():
            self.logger.log_info("Panic mode: closing position")
            position = self.position_manager.current_position
            self.position_manager.close_position("panic_stop", self.exchange.get_mark_price(position.symbol))
    
    def panic(self):
        """Emergency panic switch - cancel all orders and close positions"""
        self.panic_mode = True
        self.logger.log_emergency_exit("ALL", "panic_switch_activated")
        
        for symbol in self.config.trading.symbols:
            try:
                # Close position
                self.exchange.close_position(symbol)
                # Cancel all orders would go here if supported
            except Exception as e:
                self.logger.log_error("panic_close_failed", str(e), symbol=symbol)
        
        self.stop()
    
    def _run_loop(self):
        """Main 5-second polling loop"""
        loop_count = 0
        
        while self.running:
            loop_count += 1
            loop_start = time.time()
            
            try:
                # Process each symbol
                for symbol in self.config.trading.symbols:
                    self._process_symbol(symbol)
                
                # Update equity
                if not self.config.operational.dry_run:
                    try:
                        balance = self.exchange.get_balance()
                        self.risk_manager.update_equity(balance)
                    except Exception as e:
                        self.logger.log_error("balance_fetch_failed", str(e))
                
            except Exception as e:
                self.logger.log_error("loop_error", str(e))
            
            # Sleep to maintain 5-second interval
            elapsed = time.time() - loop_start
            sleep_time = max(0, self.config.trading.loop_interval_seconds - elapsed)
            time.sleep(sleep_time)
        
        self.logger.log_info("Bot stopped")
    
    def _process_symbol(self, symbol: str):
        """Process trading logic for a single symbol"""
        try:
            # Fetch market data
            data = self.data_fetcher.fetch_all(symbol)
            mins_to_funding = self.data_fetcher.get_minutes_to_funding(data.next_funding_time)
            
            # Check if we have a position
            if self.position_manager.has_position():
                self._handle_position(data, mins_to_funding)
            else:
                self._handle_flat(data, mins_to_funding, symbol)
                
        except Exception as e:
            self.logger.log_error("symbol_processing_error", str(e), symbol=symbol)
    
    def _handle_position(self, data, mins_to_funding):
        """Handle logic when we have an open position"""
        position = self.position_manager.current_position
        
        # Check emergency exit conditions
        should_emergency_exit, reason = self.risk_manager.check_emergency_exit(
            data, position.entry_price, position.entry_time
        )
        
        if should_emergency_exit:
            self.logger.log_emergency_exit(position.symbol, reason, 
                                          spread=data.spread, 
                                          price=data.mark_price)
            self.position_manager.close_position(f"emergency_{reason}", data.mark_price)
            pnl = self.position_manager.get_current_pnl(data.mark_price)
            self.risk_manager.record_trade_exit(pnl)
            return
        
        # Check if we should exit after funding
        if self.position_manager.should_exit_post_funding(data.next_funding_time):
            self.logger.log_info("Exiting after funding payment", symbol=position.symbol)
            pnl = self.position_manager.get_current_pnl(data.mark_price)
            self.position_manager.close_position("post_funding", data.mark_price)
            self.risk_manager.record_trade_exit(pnl)
            return
    
    def _handle_flat(self, data, mins_to_funding, symbol: str):
        """Handle logic when we have no position"""
        # Check if halted
        self.risk_manager.check_interval_reset(data.next_funding_time)
        
        if self.risk_manager.is_halted():
            reasons = self.risk_manager.get_halt_reasons()
            # Only log occasionally to avoid spam
            return
        
        # Check if we can open position
        can_open, reason = self.risk_manager.can_open_position()
        if not can_open:
            return
        
        # Generate signal
        side, reasons = self.signal_generator.generate_signal(data, mins_to_funding)
        
        # Log decision
        decision = f"enter_{side.lower()}" if side else "no_entry"
        self.logger.log_decision(
            symbol=symbol,
            state="flat",
            funding_rate=data.funding_rate,
            mins_to_funding=mins_to_funding,
            spread=data.spread,
            atr_15m=data.atr_15m,
            decision=decision,
            reason=reasons,
            ema20=data.ema20_15m,
            ema50=data.ema50_15m,
            median_atr=data.median_atr
        )
        
        if not side:
            return
        
        # Calculate position parameters
        equity = self.risk_manager.state.current_equity
        if equity == 0 and not self.config.operational.dry_run:
            equity = self.exchange.get_balance()
            self.risk_manager.update_equity(equity)
        
        if self.config.operational.dry_run:
            equity = 100.0  # Simulate $100 account in dry run
        
        # Entry price
        entry_price = data.best_bid if side == 'SHORT' else data.best_ask
        
        # Calculate position size
        quantity = self.risk_manager.calculate_position_size(
            equity=equity,
            atr=data.atr_15m,
            entry_price=entry_price,
            leverage=self.config.trading.leverage
        )
        
        # Calculate stop and TP
        stop_price = self.risk_manager.get_stop_price(entry_price, data.atr_15m, side)
        tp_price = self.risk_manager.get_take_profit_price(entry_price, data.atr_15m, side)
        
        # Enter position
        success = self.position_manager.enter_position(
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=entry_price,
            stop_price=stop_price,
            tp_price=tp_price,
            funding_rate=data.funding_rate,
            atr=data.atr_15m
        )
        
        if success:
            self.risk_manager.record_trade_entry()


def main():
    """Entry point for the bot"""
    # Load configuration from environment
    config = Config.from_env()
    
    # Create and start bot
    bot = BrokeBot(config)
    
    try:
        bot.start()
    except KeyboardInterrupt:
        print("\nShutdown requested...")
        bot.stop()
    except Exception as e:
        print(f"Fatal error: {e}")
        bot.logger.log_error("fatal_error", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
