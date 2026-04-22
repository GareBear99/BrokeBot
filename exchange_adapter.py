"""
Exchange Adapter for Broke Bot
Unified interface for multiple exchanges (Binance, Bybit, OKX)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode


class ExchangeAdapter(ABC):
    """Abstract base class for exchange adapters"""
    
    @abstractmethod
    def get_funding_rate(self, symbol: str) -> Tuple[float, int]:
        """Get current funding rate and next funding timestamp"""
        pass
    
    @abstractmethod
    def get_mark_price(self, symbol: str) -> float:
        """Get current mark price"""
        pass
    
    @abstractmethod
    def get_orderbook(self, symbol: str) -> Dict:
        """Get orderbook with best bid/ask"""
        pass
    
    @abstractmethod
    def get_klines(self, symbol: str, interval: str, limit: int) -> List[Dict]:
        """Get OHLCV candlestick data"""
        pass
    
    @abstractmethod
    def get_24h_volume(self, symbol: str) -> float:
        """Get 24h volume"""
        pass
    
    @abstractmethod
    def set_leverage(self, symbol: str, leverage: int):
        """Set leverage for symbol"""
        pass
    
    @abstractmethod
    def set_margin_mode(self, symbol: str, margin_type: str):
        """Set margin mode (ISOLATED or CROSSED)"""
        pass
    
    @abstractmethod
    def place_order(self, symbol: str, side: str, order_type: str, 
                   quantity: float, price: Optional[float] = None,
                   params: Optional[Dict] = None) -> Dict:
        """Place an order"""
        pass
    
    @abstractmethod
    def cancel_order(self, symbol: str, order_id: str) -> Dict:
        """Cancel an order"""
        pass
    
    @abstractmethod
    def get_position(self, symbol: str) -> Optional[Dict]:
        """Get current position"""
        pass
    
    @abstractmethod
    def get_balance(self) -> float:
        """Get account balance"""
        pass
    
    @abstractmethod
    def close_position(self, symbol: str) -> Dict:
        """Close entire position with market order"""
        pass


class BinanceFuturesAdapter(ExchangeAdapter):
    """Binance Futures API adapter"""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        self.api_key = api_key
        self.api_secret = api_secret
        
        if testnet:
            self.base_url = "https://testnet.binancefuture.com"
        else:
            self.base_url = "https://fapi.binance.com"
        
        self.session = requests.Session()
        self.session.headers.update({
            'X-MBX-APIKEY': api_key
        })
    
    def _sign(self, params: Dict) -> str:
        """Create signature for authenticated requests"""
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _request(self, method: str, endpoint: str, signed: bool = False, **kwargs) -> Dict:
        """Make HTTP request to Binance API"""
        url = f"{self.base_url}{endpoint}"
        
        if signed:
            if 'params' not in kwargs:
                kwargs['params'] = {}
            kwargs['params']['timestamp'] = int(time.time() * 1000)
            kwargs['params']['signature'] = self._sign(kwargs['params'])
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Binance API error: {e}")
    
    def get_funding_rate(self, symbol: str) -> Tuple[float, int]:
        """Get current funding rate and next funding timestamp"""
        data = self._request('GET', '/fapi/v1/premiumIndex', params={'symbol': symbol})
        funding_rate = float(data['lastFundingRate'])
        next_funding_time = int(data['nextFundingTime'])
        return funding_rate, next_funding_time
    
    def get_mark_price(self, symbol: str) -> float:
        """Get current mark price"""
        data = self._request('GET', '/fapi/v1/premiumIndex', params={'symbol': symbol})
        return float(data['markPrice'])
    
    def get_orderbook(self, symbol: str) -> Dict:
        """Get orderbook with best bid/ask"""
        data = self._request('GET', '/fapi/v1/depth', params={'symbol': symbol, 'limit': 5})
        
        best_bid = float(data['bids'][0][0]) if data['bids'] else 0.0
        best_ask = float(data['asks'][0][0]) if data['asks'] else 0.0
        bid_qty = float(data['bids'][0][1]) if data['bids'] else 0.0
        ask_qty = float(data['asks'][0][1]) if data['asks'] else 0.0
        
        return {
            'best_bid': best_bid,
            'best_ask': best_ask,
            'bid_quantity': bid_qty,
            'ask_quantity': ask_qty,
            'spread': (best_ask - best_bid) / best_bid if best_bid > 0 else 0.0
        }
    
    def get_klines(self, symbol: str, interval: str, limit: int) -> List[Dict]:
        """Get OHLCV candlestick data"""
        data = self._request('GET', '/fapi/v1/klines', params={
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        })
        
        klines = []
        for k in data:
            klines.append({
                'timestamp': k[0],
                'open': float(k[1]),
                'high': float(k[2]),
                'low': float(k[3]),
                'close': float(k[4]),
                'volume': float(k[5])
            })
        
        return klines
    
    def get_24h_volume(self, symbol: str) -> float:
        """Get 24h volume"""
        data = self._request('GET', '/fapi/v1/ticker/24hr', params={'symbol': symbol})
        return float(data['volume'])
    
    def set_leverage(self, symbol: str, leverage: int):
        """Set leverage for symbol"""
        self._request('POST', '/fapi/v1/leverage', signed=True, params={
            'symbol': symbol,
            'leverage': leverage
        })
    
    def set_margin_mode(self, symbol: str, margin_type: str):
        """Set margin mode (ISOLATED or CROSSED)"""
        self._request('POST', '/fapi/v1/marginType', signed=True, params={
            'symbol': symbol,
            'marginType': margin_type.upper()
        })
    
    def place_order(self, symbol: str, side: str, order_type: str,
                   quantity: float, price: Optional[float] = None,
                   params: Optional[Dict] = None) -> Dict:
        """Place an order"""
        order_params = {
            'symbol': symbol,
            'side': side.upper(),
            'type': order_type.upper(),
            'quantity': quantity
        }
        
        if price and order_type.upper() in ['LIMIT', 'STOP_MARKET', 'TAKE_PROFIT']:
            if order_type.upper() == 'LIMIT':
                order_params['price'] = price
                order_params['timeInForce'] = 'GTC'
            else:
                order_params['stopPrice'] = price
        
        if params:
            order_params.update(params)
        
        return self._request('POST', '/fapi/v1/order', signed=True, params=order_params)
    
    def cancel_order(self, symbol: str, order_id: str) -> Dict:
        """Cancel an order"""
        return self._request('DELETE', '/fapi/v1/order', signed=True, params={
            'symbol': symbol,
            'orderId': order_id
        })
    
    def get_position(self, symbol: str) -> Optional[Dict]:
        """Get current position"""
        positions = self._request('GET', '/fapi/v2/positionRisk', signed=True)
        
        for pos in positions:
            if pos['symbol'] == symbol:
                position_amt = float(pos['positionAmt'])
                if position_amt != 0:
                    return {
                        'symbol': symbol,
                        'side': 'LONG' if position_amt > 0 else 'SHORT',
                        'quantity': abs(position_amt),
                        'entry_price': float(pos['entryPrice']),
                        'unrealized_pnl': float(pos['unRealizedProfit']),
                        'leverage': int(pos['leverage'])
                    }
        
        return None
    
    def get_balance(self) -> float:
        """Get account balance"""
        account = self._request('GET', '/fapi/v2/account', signed=True)
        return float(account['totalWalletBalance'])
    
    def close_position(self, symbol: str) -> Dict:
        """Close entire position with market order"""
        position = self.get_position(symbol)
        if not position:
            return {'status': 'no_position'}
        
        # Opposite side to close
        close_side = 'SELL' if position['side'] == 'LONG' else 'BUY'
        
        return self.place_order(
            symbol=symbol,
            side=close_side,
            order_type='MARKET',
            quantity=position['quantity'],
            params={'reduceOnly': 'true'}
        )


class BybitAdapter(ExchangeAdapter):
    """Bybit adapter - placeholder for future implementation"""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        raise NotImplementedError("Bybit adapter not yet implemented")
    
    def get_funding_rate(self, symbol: str) -> Tuple[float, int]:
        raise NotImplementedError()
    
    def get_mark_price(self, symbol: str) -> float:
        raise NotImplementedError()
    
    def get_orderbook(self, symbol: str) -> Dict:
        raise NotImplementedError()
    
    def get_klines(self, symbol: str, interval: str, limit: int) -> List[Dict]:
        raise NotImplementedError()
    
    def get_24h_volume(self, symbol: str) -> float:
        raise NotImplementedError()
    
    def set_leverage(self, symbol: str, leverage: int):
        raise NotImplementedError()
    
    def set_margin_mode(self, symbol: str, margin_type: str):
        raise NotImplementedError()
    
    def place_order(self, symbol: str, side: str, order_type: str,
                   quantity: float, price: Optional[float] = None,
                   params: Optional[Dict] = None) -> Dict:
        raise NotImplementedError()
    
    def cancel_order(self, symbol: str, order_id: str) -> Dict:
        raise NotImplementedError()
    
    def get_position(self, symbol: str) -> Optional[Dict]:
        raise NotImplementedError()
    
    def get_balance(self) -> float:
        raise NotImplementedError()
    
    def close_position(self, symbol: str) -> Dict:
        raise NotImplementedError()


class OKXAdapter(ExchangeAdapter):
    """OKX adapter - placeholder for future implementation"""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        raise NotImplementedError("OKX adapter not yet implemented")
    
    def get_funding_rate(self, symbol: str) -> Tuple[float, int]:
        raise NotImplementedError()
    
    def get_mark_price(self, symbol: str) -> float:
        raise NotImplementedError()
    
    def get_orderbook(self, symbol: str) -> Dict:
        raise NotImplementedError()
    
    def get_klines(self, symbol: str, interval: str, limit: int) -> List[Dict]:
        raise NotImplementedError()
    
    def get_24h_volume(self, symbol: str) -> float:
        raise NotImplementedError()
    
    def set_leverage(self, symbol: str, leverage: int):
        raise NotImplementedError()
    
    def set_margin_mode(self, symbol: str, margin_type: str):
        raise NotImplementedError()
    
    def place_order(self, symbol: str, side: str, order_type: str,
                   quantity: float, price: Optional[float] = None,
                   params: Optional[Dict] = None) -> Dict:
        raise NotImplementedError()
    
    def cancel_order(self, symbol: str, order_id: str) -> Dict:
        raise NotImplementedError()
    
    def get_position(self, symbol: str) -> Optional[Dict]:
        raise NotImplementedError()
    
    def get_balance(self) -> float:
        raise NotImplementedError()
    
    def close_position(self, symbol: str) -> Dict:
        raise NotImplementedError()


def create_exchange_adapter(exchange: str, api_key: str, api_secret: str, 
                            testnet: bool = False) -> ExchangeAdapter:
    """Factory function to create exchange adapter"""
    exchange = exchange.lower()
    
    if exchange == 'binance':
        return BinanceFuturesAdapter(api_key, api_secret, testnet)
    elif exchange == 'bybit':
        return BybitAdapter(api_key, api_secret, testnet)
    elif exchange == 'okx':
        return OKXAdapter(api_key, api_secret, testnet)
    else:
        raise ValueError(f"Unsupported exchange: {exchange}")
