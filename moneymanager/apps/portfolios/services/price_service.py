"""
Price Service Layer - Handles market data and price operations.
Provides unified interface for multiple price data providers.
"""
import logging
from decimal import Decimal
from typing import Dict, Optional, List, Union
from datetime import date, datetime, timedelta
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings

from ..models import Asset, PriceHistory
from ..exceptions import PriceDataError, APIError, RateLimitError
from ..constants import CACHE_TIMEOUTS, API_RATE_LIMITS
from ..api_services import MutualFundAPI, AlphaVantageAPI, YahooFinanceAPI, RateLimiter

logger = logging.getLogger(__name__)


class PriceService:
    """Service for handling asset price data."""
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.mutual_fund_api = MutualFundAPI()
        self.alpha_vantage_api = AlphaVantageAPI()
        self.yahoo_api = YahooFinanceAPI()
    
    @staticmethod
    def get_current_price(symbol: str, asset_type: str = 'stock') -> Decimal:
        """Get current price for an asset with fallback providers."""
        try:
            # Check cache first
            cache_key = f"price_{symbol}_{asset_type}"
            cached_price = cache.get(cache_key)
            if cached_price:
                return Decimal(str(cached_price))
            
            price_service = PriceService()
            price = None
            
            # Try different providers based on asset type
            if asset_type == 'mutual_fund':
                price = price_service._get_mutual_fund_price(symbol)
            elif asset_type in ['stock', 'etf']:
                price = price_service._get_stock_price(symbol)
            else:
                # Try multiple providers for other asset types
                price = price_service._get_generic_price(symbol)
            
            if price is None:
                logger.warning(f"No price data available for {symbol}")
                # Try to get last known price from database
                try:
                    asset = Asset.objects.get(symbol=symbol)
                    if asset.current_price > 0:
                        return asset.current_price
                except Asset.DoesNotExist:
                    pass
                
                raise PriceDataError(f"Price data not available for {symbol}")
            
            # Cache the price for 5 minutes
            cache.set(cache_key, float(price), CACHE_TIMEOUTS['price_data'])
            return price
            
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {str(e)}")
            if isinstance(e, PriceDataError):
                raise
            raise PriceDataError(f"Failed to retrieve price for {symbol}: {str(e)}")
    
    def _get_mutual_fund_price(self, symbol: str) -> Optional[Decimal]:
        """Get mutual fund NAV price."""
        try:
            if not self.rate_limiter.can_make_call('mutual_fund_api'):
                raise RateLimitError('mutual_fund_api')
            
            self.rate_limiter.record_call('mutual_fund_api')
            price_data = self.mutual_fund_api.get_nav_price(symbol)
            
            if price_data and 'price' in price_data:
                return Decimal(str(price_data['price']))
            
        except Exception as e:
            logger.warning(f"Mutual fund API failed for {symbol}: {str(e)}")
        
        # Fallback to other providers
        return self._get_stock_price(symbol)
    
    def _get_stock_price(self, symbol: str) -> Optional[Decimal]:
        """Get stock/ETF price with multiple providers."""
        providers = [
            ('yahoo_finance', self.yahoo_api.get_stock_price),
            ('alpha_vantage', self.alpha_vantage_api.get_quote),
        ]
        
        for provider_name, provider_func in providers:
            try:
                if not self.rate_limiter.can_make_call(provider_name):
                    continue
                
                self.rate_limiter.record_call(provider_name)
                price_data = provider_func(symbol)
                
                if price_data and 'price' in price_data:
                    return Decimal(str(price_data['price']))
                    
            except Exception as e:
                logger.warning(f"{provider_name} failed for {symbol}: {str(e)}")
                continue
        
        return None
    
    def _get_generic_price(self, symbol: str) -> Optional[Decimal]:
        """Get price for other asset types."""
        # Try Yahoo Finance as it has broad coverage
        return self._get_stock_price(symbol)
    
    @staticmethod
    def update_asset_prices(assets: List[Asset] = None, 
                          force_update: bool = False) -> Dict[str, any]:
        """Update prices for multiple assets."""
        try:
            if assets is None:
                # Update all active assets
                assets = Asset.objects.filter(is_active=True)
            
            results = {
                'success_count': 0,
                'error_count': 0,
                'errors': [],
                'updated_assets': []
            }
            
            for asset in assets:
                try:
                    # Skip recently updated assets unless forced
                    if not force_update and asset.price_updated_at:
                        time_diff = timezone.now() - asset.price_updated_at
                        if time_diff.total_seconds() < CACHE_TIMEOUTS['price_data']:
                            continue
                    
                    # Get current price
                    current_price = PriceService.get_current_price(
                        asset.symbol, asset.asset_type
                    )
                    
                    # Calculate day change
                    old_price = asset.current_price
                    day_change = current_price - old_price
                    day_change_percentage = Decimal('0')
                    if old_price > 0:
                        day_change_percentage = (day_change / old_price) * 100
                    
                    # Update asset
                    asset.current_price = current_price
                    asset.day_change = day_change
                    asset.day_change_percentage = day_change_percentage
                    asset.price_updated_at = timezone.now()
                    asset.save(update_fields=[
                        'current_price', 'day_change', 'day_change_percentage',
                        'price_updated_at'
                    ])
                    
                    results['success_count'] += 1
                    results['updated_assets'].append({
                        'symbol': asset.symbol,
                        'old_price': float(old_price),
                        'new_price': float(current_price),
                        'change': float(day_change),
                        'change_percent': float(day_change_percentage)
                    })
                    
                except Exception as e:
                    error_msg = f"Failed to update {asset.symbol}: {str(e)}"
                    logger.error(error_msg)
                    results['error_count'] += 1
                    results['errors'].append(error_msg)
            
            logger.info(f"Price update completed: {results['success_count']} success, "
                       f"{results['error_count']} errors")
            return results
            
        except Exception as e:
            logger.error(f"Failed to update asset prices: {str(e)}")
            raise PriceDataError(f"Failed to update asset prices: {str(e)}")
    
    @staticmethod
    def get_historical_prices(symbol: str, start_date: date, 
                            end_date: date = None) -> List[PriceHistory]:
        """Get historical price data for an asset."""
        try:
            if end_date is None:
                end_date = date.today()
            
            # Try to get from database first
            try:
                asset = Asset.objects.get(symbol=symbol)
                historical_data = PriceHistory.objects.filter(
                    asset=asset,
                    date__gte=start_date,
                    date__lte=end_date
                ).order_by('date')
                
                if historical_data.exists():
                    return list(historical_data)
            except Asset.DoesNotExist:
                pass
            
            # If not available, try to fetch from API
            # This would require implementation based on available APIs
            logger.warning(f"Historical data not available for {symbol}")
            return []
            
        except Exception as e:
            logger.error(f"Failed to get historical prices for {symbol}: {str(e)}")
            return []
    
    @staticmethod
    def create_price_alert(user, asset: Asset, target_price: Decimal,
                         alert_type: str = 'above') -> Dict:
        """Create a price alert for an asset."""
        try:
            # This would integrate with a notification system
            alert_data = {
                'user': user,
                'asset': asset,
                'target_price': target_price,
                'alert_type': alert_type,  # 'above' or 'below'
                'created_at': timezone.now(),
                'is_active': True
            }
            
            # Store in cache or database
            cache_key = f"price_alert_{user.id}_{asset.id}"
            cache.set(cache_key, alert_data, 86400)  # 24 hours
            
            logger.info(f"Created price alert for {asset.symbol} at ₹{target_price}")
            return alert_data
            
        except Exception as e:
            logger.error(f"Failed to create price alert: {str(e)}")
            raise PriceDataError(f"Failed to create price alert: {str(e)}")
    
    @staticmethod
    def check_price_alerts() -> List[Dict]:
        """Check and trigger price alerts."""
        try:
            # This would check all active price alerts
            # Implementation would depend on alert storage mechanism
            triggered_alerts = []
            
            # Placeholder for alert checking logic
            logger.info("Price alerts checked")
            return triggered_alerts
            
        except Exception as e:
            logger.error(f"Failed to check price alerts: {str(e)}")
            return []
    
    @staticmethod
    def get_market_summary() -> Dict:
        """Get overall market summary and indices."""
        try:
            cache_key = "market_summary"
            cached_data = cache.get(cache_key)
            if cached_data:
                return cached_data
            
            # This would fetch major market indices
            # Implementation depends on available APIs
            summary = {
                'nifty_50': {'value': 0, 'change': 0, 'change_percent': 0},
                'sensex': {'value': 0, 'change': 0, 'change_percent': 0},
                'bank_nifty': {'value': 0, 'change': 0, 'change_percent': 0},
                'last_updated': timezone.now().isoformat()
            }
            
            # Cache for 5 minutes
            cache.set(cache_key, summary, CACHE_TIMEOUTS['market_indices'])
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get market summary: {str(e)}")
            return {}
    
    @staticmethod
    def validate_price_data(price_data: Dict) -> bool:
        """Validate price data structure and values."""
        try:
            required_fields = ['price']
            
            for field in required_fields:
                if field not in price_data:
                    return False
                
                if price_data[field] is None:
                    return False
            
            # Validate price is positive
            price = Decimal(str(price_data['price']))
            if price <= 0:
                return False
            
            # Additional validation for change data
            if 'change' in price_data:
                change = Decimal(str(price_data['change']))
                # Change can be negative, so just check it's a valid decimal
            
            return True
            
        except Exception as e:
            logger.error(f"Price data validation failed: {str(e)}")
            return False
    
    @staticmethod
    def get_asset_price_summary(asset: Asset) -> Dict:
        """Get comprehensive price summary for an asset."""
        try:
            # Update current price
            try:
                current_price = PriceService.get_current_price(
                    asset.symbol, asset.asset_type
                )
                if current_price != asset.current_price:
                    old_price = asset.current_price
                    asset.current_price = current_price
                    asset.day_change = current_price - old_price
                    if old_price > 0:
                        asset.day_change_percentage = (asset.day_change / old_price) * 100
                    asset.price_updated_at = timezone.now()
                    asset.save()
            except Exception as e:
                logger.warning(f"Could not update price for {asset.symbol}: {str(e)}")
            
            return {
                'symbol': asset.symbol,
                'name': asset.name,
                'current_price': asset.current_price,
                'day_change': asset.day_change,
                'day_change_percentage': asset.day_change_percentage,
                'last_updated': asset.price_updated_at,
                'asset_type': asset.asset_type,
                'exchange': asset.exchange,
                'currency': asset.currency
            }
            
        except Exception as e:
            logger.error(f"Failed to get asset price summary: {str(e)}")
            return {}