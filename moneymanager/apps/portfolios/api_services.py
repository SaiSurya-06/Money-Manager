"""
Real API integration services for market data
Replace mock data with actual API calls to various providers
"""

import requests
import urllib3
import yfinance as yf

# Suppress SSL warnings for development/corporate environments
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from decimal import Decimal
from typing import Dict, List, Optional, Union
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
import logging
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiting for API calls"""
    
    def __init__(self):
        self.calls_per_minute = {}
        self.calls_per_day = {}
    
    def can_make_call(self, api_name: str) -> bool:
        """Check if we can make an API call within rate limits"""
        now = timezone.now()
        minute_key = f"{api_name}_{now.strftime('%Y%m%d%H%M')}"
        day_key = f"{api_name}_{now.strftime('%Y%m%d')}"
        
        # Check per-minute limit
        minute_calls = self.calls_per_minute.get(minute_key, 0)
        if minute_calls >= settings.API_SETTINGS['MAX_API_CALLS_PER_MINUTE']:
            return False
        
        # Check per-day limit
        day_calls = self.calls_per_day.get(day_key, 0)
        if day_calls >= settings.API_SETTINGS['MAX_API_CALLS_PER_DAY']:
            return False
        
        return True
    
    def record_call(self, api_name: str):
        """Record an API call"""
        now = timezone.now()
        minute_key = f"{api_name}_{now.strftime('%Y%m%d%H%M')}"
        day_key = f"{api_name}_{now.strftime('%Y%m%d')}"
        
        self.calls_per_minute[minute_key] = self.calls_per_minute.get(minute_key, 0) + 1
        self.calls_per_day[day_key] = self.calls_per_day.get(day_key, 0) + 1


# Global rate limiter instance
rate_limiter = RateLimiter()


class AlphaVantageAPI:
    """Alpha Vantage API integration for global and Indian stocks"""
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self):
        self.api_key = settings.API_SETTINGS['ALPHA_VANTAGE_API_KEY']
        self.timeout = settings.API_SETTINGS['API_REQUEST_TIMEOUT']
    
    def get_stock_price(self, symbol: str) -> Optional[Decimal]:
        """Get current stock price from Alpha Vantage"""
        if not self.api_key or not rate_limiter.can_make_call('alpha_vantage'):
            return None
        
        cache_key = f"alpha_vantage_price_{symbol}"
        cached_price = cache.get(cache_key)
        if cached_price:
            return Decimal(str(cached_price))
        
        try:
            # Use symbol as-is for US stocks, or append .NSE/.BSE for Indian stocks
            if symbol.endswith(('.NS', '.NSE', '.BSE', '.BO')):
                search_symbol = symbol
            elif symbol in ['RELIANCE', 'TCS', 'INFY', 'WIPRO', 'HDFCBANK', 'ICICIBANK', 'SBIN', 'ITC']:  # Known Indian stocks
                search_symbol = f"{symbol}.NSE"
            else:
                search_symbol = symbol  # Use as-is for US and other international stocks
            
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': search_symbol,
                'apikey': self.api_key
            }
            
            response = requests.get(self.BASE_URL, params=params, timeout=self.timeout, verify=False)
            response.raise_for_status()
            
            data = response.json()
            
            if 'Global Quote' in data:
                price = data['Global Quote'].get('05. price')
                if price:
                    price_decimal = Decimal(str(price))
                    cache.set(cache_key, float(price_decimal), timeout=300)  # Cache for 5 minutes
                    rate_limiter.record_call('alpha_vantage')
                    return price_decimal
            
            logger.warning(f"Alpha Vantage: No price data for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Alpha Vantage API error for {symbol}: {e}")
            return None
    
    def search_symbol(self, query: str) -> List[Dict]:
        """Search for symbols using Alpha Vantage"""
        if not self.api_key or not rate_limiter.can_make_call('alpha_vantage'):
            return []
        
        try:
            params = {
                'function': 'SYMBOL_SEARCH',
                'keywords': query,
                'apikey': self.api_key
            }
            
            response = requests.get(self.BASE_URL, params=params, timeout=self.timeout, verify=False)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            if 'bestMatches' in data:
                for match in data['bestMatches'][:10]:  # Limit to 10 results
                    results.append({
                        'symbol': match.get('1. symbol', ''),
                        'name': match.get('2. name', ''),
                        'type': match.get('3. type', ''),
                        'region': match.get('4. region', ''),
                        'currency': match.get('8. currency', '')
                    })
            
            rate_limiter.record_call('alpha_vantage')
            return results
            
        except Exception as e:
            logger.error(f"Alpha Vantage search error: {e}")
            return []


class YahooFinanceAPI:
    """Yahoo Finance API using yfinance library (free but unofficial)"""
    
    def get_stock_price(self, symbol: str) -> Optional[Decimal]:
        """Get current stock price from Yahoo Finance"""
        cache_key = f"yahoo_finance_price_{symbol}"
        cached_price = cache.get(cache_key)
        if cached_price:
            return Decimal(str(cached_price))
        
        try:
            # For Indian stocks, ensure proper suffix
            if symbol.endswith('.NS') or symbol.endswith('.BO'):
                search_symbol = symbol
            elif '.' not in symbol and len(symbol) <= 10:  # Likely Indian stock
                search_symbol = f"{symbol}.NS"  # NSE is more liquid
            else:
                search_symbol = symbol
            
            ticker = yf.Ticker(search_symbol)
            data = ticker.history(period='1d', interval='1m')
            
            if not data.empty:
                current_price = data['Close'].iloc[-1]
                price_decimal = Decimal(str(current_price))
                cache.set(cache_key, float(price_decimal), timeout=300)  # Cache for 5 minutes
                return price_decimal
            
            return None
            
        except Exception as e:
            logger.error(f"Yahoo Finance API error for {symbol}: {e}")
            return None
    
    def get_info(self, symbol: str) -> Optional[Dict]:
        """Get detailed info about a symbol"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return {
                'symbol': symbol,
                'name': info.get('longName', info.get('shortName', '')),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'market_cap': info.get('marketCap'),
                'currency': info.get('currency', 'USD')
            }
        except Exception as e:
            logger.error(f"Yahoo Finance info error for {symbol}: {e}")
            return None


class MutualFundAPI:
    """Indian Mutual Fund API using mfapi.in"""
    
    BASE_URL = "https://api.mfapi.in/mf"
    
    def __init__(self):
        self.timeout = settings.API_SETTINGS['API_REQUEST_TIMEOUT']
    
    def get_nav(self, scheme_code: str) -> Optional[Decimal]:
        """Get latest NAV for mutual fund scheme"""
        cache_key = f"mf_nav_{scheme_code}"
        cached_nav = cache.get(cache_key)
        if cached_nav:
            return Decimal(str(cached_nav))
        
        try:
            url = f"{self.BASE_URL}/{scheme_code}"
            response = requests.get(url, timeout=self.timeout, verify=False)
            response.raise_for_status()
            
            data = response.json()
            
            if data and isinstance(data, dict):
                # Get latest NAV
                nav = data.get('data', [{}])[0].get('nav')
                if nav:
                    nav_decimal = Decimal(str(nav))
                    cache.set(cache_key, float(nav_decimal), timeout=3600)  # Cache for 1 hour
                    return nav_decimal
            
            return None
            
        except Exception as e:
            logger.error(f"Mutual Fund API error for {scheme_code}: {e}")
            return None
    
    def search_schemes(self, query: str) -> List[Dict]:
        """Search mutual fund schemes"""
        try:
            url = f"{self.BASE_URL}"
            response = requests.get(url, timeout=self.timeout, verify=False)
            response.raise_for_status()
            
            schemes = response.json()
            results = []
            
            query_lower = query.lower()
            for scheme in schemes:
                if query_lower in scheme.get('schemeName', '').lower():
                    results.append({
                        'symbol': scheme.get('schemeCode', ''),
                        'name': scheme.get('schemeName', ''),
                        'type': 'mutual_fund'
                    })
                    
                    if len(results) >= 10:  # Limit results
                        break
            
            return results
            
        except Exception as e:
            logger.error(f"Mutual Fund search error: {e}")
            return []


class MarketDataService:
    """Unified market data service that tries multiple APIs"""
    
    def __init__(self):
        self.alpha_vantage = AlphaVantageAPI()
        self.yahoo_finance = YahooFinanceAPI()
        self.mutual_fund = MutualFundAPI()
    
    def get_current_price(self, symbol: str, asset_type: str = 'stock') -> Optional[Decimal]:
        """Get current price using the best available API"""
        
        if asset_type == 'mutual_fund':
            # Try mutual fund API first
            price = self.mutual_fund.get_nav(symbol)
            if price:
                return price
        
        # For stocks and other assets, try multiple APIs
        apis_to_try = []
        
        # Prioritize based on API key availability
        if self.alpha_vantage.api_key:
            apis_to_try.append(self.alpha_vantage.get_stock_price)
        
        apis_to_try.append(self.yahoo_finance.get_stock_price)
        
        for api_method in apis_to_try:
            try:
                price = api_method(symbol)
                if price:
                    return price
            except Exception as e:
                logger.warning(f"API method {api_method.__name__} failed for {symbol}: {e}")
                continue
        
        logger.warning(f"All APIs failed for symbol: {symbol}")
        return None
    
    def search_assets(self, query: str) -> List[Dict]:
        """Search for assets across multiple APIs"""
        results = []
        
        # Search stocks
        if self.alpha_vantage.api_key:
            try:
                alpha_results = self.alpha_vantage.search_symbol(query)
                results.extend(alpha_results)
            except Exception as e:
                logger.warning(f"Alpha Vantage search failed: {e}")
        
        # Search mutual funds
        try:
            mf_results = self.mutual_fund.search_schemes(query)
            results.extend(mf_results)
        except Exception as e:
            logger.warning(f"Mutual fund search failed: {e}")
        
        # Remove duplicates and limit results
        seen_symbols = set()
        unique_results = []
        for result in results:
            symbol = result.get('symbol', '')
            if symbol and symbol not in seen_symbols:
                seen_symbols.add(symbol)
                unique_results.append(result)
                
                if len(unique_results) >= 15:  # Limit total results
                    break
        
        return unique_results
    
    def bulk_update_prices(self, symbols: List[str], asset_types: List[str]) -> int:
        """Update prices for multiple assets"""
        updated_count = 0
        
        for symbol, asset_type in zip(symbols, asset_types):
            try:
                price = self.get_current_price(symbol, asset_type)
                if price:
                    # Here you would update your Asset model
                    # Asset.objects.filter(symbol=symbol).update(
                    #     current_price=price,
                    #     last_updated=timezone.now()
                    # )
                    updated_count += 1
                
                # Add small delay to respect rate limits
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Failed to update price for {symbol}: {e}")
        
        return updated_count


# Create global service instance
market_data_service = MarketDataService()