"""
JSONL Logger for Broke Bot
Structured logging with all decision inputs and outcomes
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List


class BrokeBotLogger:
    """JSONL logger that records all decisions and events"""
    
    def __init__(self, log_dir: str = "logs/broke_bot"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create daily log file
        date_str = datetime.now().strftime("%Y-%m-%d")
        self.log_file = self.log_dir / f"broke_bot_{date_str}.jsonl"
    
    def _write_log(self, log_entry: Dict[str, Any]):
        """Write log entry to JSONL file"""
        with open(self.log_file, 'a') as f:
            json.dump(log_entry, f)
            f.write('\n')
    
    def log_decision(self, symbol: str, state: str, funding_rate: float,
                    mins_to_funding: float, spread: float, atr_15m: float,
                    decision: str, reason: List[str], **kwargs):
        """Log trading decision with all inputs"""
        log_entry = {
            'ts': datetime.now().isoformat(),
            'type': 'decision',
            'symbol': symbol,
            'state': state,
            'funding_rate': funding_rate,
            'mins_to_funding': mins_to_funding,
            'spread': spread,
            'atr15m': atr_15m,
            'decision': decision,
            'reason': reason
        }
        
        # Add any additional fields
        log_entry.update(kwargs)
        
        self._write_log(log_entry)
    
    def log_entry(self, symbol: str, side: str, quantity: float, 
                 entry_price: float, funding_rate: float, order_id: str = None,
                 **kwargs):
        """Log trade entry"""
        log_entry = {
            'ts': datetime.now().isoformat(),
            'type': 'entry',
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'entry_price': entry_price,
            'funding_rate': funding_rate,
            'order_id': order_id
        }
        
        log_entry.update(kwargs)
        self._write_log(log_entry)
    
    def log_exit(self, symbol: str, side: str, quantity: float,
                exit_price: float, pnl: float, reason: str,
                order_id: str = None, **kwargs):
        """Log trade exit"""
        log_entry = {
            'ts': datetime.now().isoformat(),
            'type': 'exit',
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'exit_price': exit_price,
            'pnl': pnl,
            'reason': reason,
            'order_id': order_id
        }
        
        log_entry.update(kwargs)
        self._write_log(log_entry)
    
    def log_funding_payment(self, symbol: str, amount: float, 
                           funding_rate: float):
        """Log funding payment received"""
        log_entry = {
            'ts': datetime.now().isoformat(),
            'type': 'funding_payment',
            'symbol': symbol,
            'amount': amount,
            'funding_rate': funding_rate
        }
        
        self._write_log(log_entry)
    
    def log_risk_limit(self, limit_type: str, current_value: float,
                      threshold: float, action: str):
        """Log risk limit trigger"""
        log_entry = {
            'ts': datetime.now().isoformat(),
            'type': 'risk_limit',
            'limit_type': limit_type,
            'current_value': current_value,
            'threshold': threshold,
            'action': action
        }
        
        self._write_log(log_entry)
    
    def log_emergency_exit(self, symbol: str, reason: str, **kwargs):
        """Log emergency exit event"""
        log_entry = {
            'ts': datetime.now().isoformat(),
            'type': 'emergency_exit',
            'symbol': symbol,
            'reason': reason
        }
        
        log_entry.update(kwargs)
        self._write_log(log_entry)
    
    def log_error(self, error_type: str, message: str, **kwargs):
        """Log error"""
        log_entry = {
            'ts': datetime.now().isoformat(),
            'type': 'error',
            'error_type': error_type,
            'message': message
        }
        
        log_entry.update(kwargs)
        self._write_log(log_entry)
    
    def log_info(self, message: str, **kwargs):
        """Log general info"""
        log_entry = {
            'ts': datetime.now().isoformat(),
            'type': 'info',
            'message': message
        }
        
        log_entry.update(kwargs)
        self._write_log(log_entry)
