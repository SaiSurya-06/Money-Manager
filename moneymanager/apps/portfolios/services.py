"""
Services for portfolio management and price updates.
"""
import requests
import json
import logging
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from decimal import Decimal
from .models import Asset
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class PriceUpdateService:
    """Service for updating asset prices from external APIs."""

    def __init__(self):
        self.alpha_vantage_key = getattr(settings, 'ALPHA_VANTAGE_API_KEY', '')
        self.polygon_key = getattr(settings, 'POLYGON_API_KEY', '')

    def update_asset_prices(self, symbols: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        Update prices for specified symbols or all active assets.

        Args:
            symbols: List of asset symbols to update. If None, updates all active assets.

        Returns:
            Dict mapping symbol to success status
        """
        if symbols is None:
            assets = Asset.objects.filter(is_active=True)
            symbols = [asset.symbol for asset in assets]
        else:
            assets = Asset.objects.filter(symbol__in=symbols, is_active=True)

        results = {}

        for asset in assets:
            try:
                success = self._update_single_asset_price(asset)
                results[asset.symbol] = success
            except Exception as e:
                logger.error(f"Error updating price for {asset.symbol}: {str(e)}")
                results[asset.symbol] = False

        return results

    def _update_single_asset_price(self, asset: Asset) -> bool:
        """Update price for a single asset."""
        try:
            # Try different price sources
            price_data = None

            # Try Alpha Vantage first
            if self.alpha_vantage_key and not price_data:
                price_data = self._fetch_alpha_vantage_price(asset.symbol)

            # Try Polygon as fallback
            if self.polygon_key and not price_data:
                price_data = self._fetch_polygon_price(asset.symbol)

            # Try free API as last resort
            if not price_data:
                price_data = self._fetch_free_api_price(asset.symbol)

            if price_data:
                asset.update_price_data(price_data)
                return True

            return False

        except Exception as e:
            logger.error(f"Error updating price for {asset.symbol}: {str(e)}")
            return False

    def _fetch_alpha_vantage_price(self, symbol: str) -> Optional[Dict]:
        """Fetch price data from Alpha Vantage API."""
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': self.alpha_vantage_key
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            quote = data.get('Global Quote', {})

            if quote:
                return {
                    'price': Decimal(str(quote.get('05. price', '0'))),
                    'change': Decimal(str(quote.get('09. change', '0'))),
                    'change_percent': Decimal(str(quote.get('10. change percent', '0%').replace('%', ''))),
                    'volume': int(quote.get('06. volume', '0')),
                }

        except Exception as e:
            logger.error(f"Alpha Vantage API error for {symbol}: {str(e)}")

        return None

    def _fetch_polygon_price(self, symbol: str) -> Optional[Dict]:
        """Fetch price data from Polygon API."""
        try:
            url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev"
            params = {'apikey': self.polygon_key}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            results = data.get('results', [])

            if results:
                result = results[0]
                return {
                    'price': Decimal(str(result.get('c', '0'))),  # close price
                    'change': Decimal(str(result.get('c', '0'))) - Decimal(str(result.get('o', '0'))),
                    'volume': int(result.get('v', '0')),
                }

        except Exception as e:
            logger.error(f"Polygon API error for {symbol}: {str(e)}")

        return None

    def _fetch_free_api_price(self, symbol: str) -> Optional[Dict]:
        """Fetch price data from free API (Yahoo Finance alternative)."""
        try:
            # Using a free API service
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            headers = {'User-Agent': 'Mozilla/5.0 (compatible; MoneyManager/1.0)'}

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            chart = data.get('chart', {})
            results = chart.get('result', [])

            if results:
                result = results[0]
                meta = result.get('meta', {})

                return {
                    'price': Decimal(str(meta.get('regularMarketPrice', '0'))),
                    'change': Decimal(str(meta.get('regularMarketPrice', '0'))) - Decimal(str(meta.get('previousClose', '0'))),
                    'volume': int(meta.get('regularMarketVolume', '0')),
                }

        except Exception as e:
            logger.error(f"Free API error for {symbol}: {str(e)}")

        return None

    def get_cached_price(self, symbol: str) -> Optional[Dict]:
        """Get cached price data for a symbol."""
        cache_key = f"asset_price_{symbol}"
        return cache.get(cache_key)

    def cache_price(self, symbol: str, price_data: Dict, timeout: int = 300):
        """Cache price data for a symbol."""
        cache_key = f"asset_price_{symbol}"
        cache.set(cache_key, price_data, timeout)


class PortfolioAnalyticsService:
    """Service for portfolio analytics and calculations."""

    @staticmethod
    def calculate_portfolio_performance(portfolio):
        """Calculate comprehensive portfolio performance metrics."""
        try:
            holdings = portfolio.holdings.filter(is_active=True)

            if not holdings.exists():
                return {
                    'total_value': 0,
                    'total_cost': 0,
                    'total_gain_loss': 0,
                    'total_gain_loss_percent': 0,
                    'day_change': 0,
                    'day_change_percent': 0,
                }

            total_value = sum(holding.current_value for holding in holdings)
            total_cost = sum(holding.total_cost_basis for holding in holdings)
            total_gain_loss = total_value - total_cost
            total_gain_loss_percent = (total_gain_loss / total_cost * 100) if total_cost > 0 else 0

            day_change = sum(holding.day_change for holding in holdings)
            previous_value = total_value - day_change
            day_change_percent = (day_change / previous_value * 100) if previous_value > 0 else 0

            return {
                'total_value': total_value,
                'total_cost': total_cost,
                'total_gain_loss': total_gain_loss,
                'total_gain_loss_percent': total_gain_loss_percent,
                'day_change': day_change,
                'day_change_percent': day_change_percent,
            }

        except Exception as e:
            logger.error(f"Error calculating portfolio performance for {portfolio.id}: {str(e)}")
            return {}

    @staticmethod
    def get_asset_allocation(portfolio):
        """Get asset allocation breakdown for portfolio."""
        try:
            holdings = portfolio.holdings.filter(is_active=True)
            total_value = sum(holding.current_value for holding in holdings)

            if total_value == 0:
                return []

            allocation = []
            for holding in holdings:
                percentage = (holding.current_value / total_value) * 100
                allocation.append({
                    'symbol': holding.asset.symbol,
                    'name': holding.asset.name,
                    'value': holding.current_value,
                    'percentage': percentage,
                    'asset_type': holding.asset.asset_type,
                })

            return sorted(allocation, key=lambda x: x['percentage'], reverse=True)

        except Exception as e:
            logger.error(f"Error calculating asset allocation for {portfolio.id}: {str(e)}")
            return []


# Service instances
price_update_service = PriceUpdateService()
analytics_service = PortfolioAnalyticsService()