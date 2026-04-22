"""
Broke Bot - TRON-Funded Funding Rate Arbitrage Bot
Educational implementation of funding-rate arbitrage strategy
"""

__version__ = "1.0.0"

from .bot import BrokeBot, main
from .config import Config

__all__ = ['BrokeBot', 'Config', 'main']
