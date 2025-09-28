"""
Utility functions for portfolio management and market data integration.
"""
import requests
import random
from decimal import Decimal
from django.utils import timezone
from .models import Asset



def search_asset_info(symbol_or_name, asset_type='stock'):
    """Search for asset information using real APIs.
    
    Integrates with:
    - Alpha Vantage for stocks
    - Yahoo Finance as fallback
    - MF API for mutual funds
    """
    from .api_services import market_data_service
    from django.conf import settings
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Use real API service for search
        results = market_data_service.search_assets(symbol_or_name)
        
        # Filter by asset type if specified
        if asset_type != 'all':
            results = [r for r in results if r.get('type') == asset_type or r.get('asset_type') == asset_type]
        
        return results[:10]  # Limit to 10 results
        
    except Exception as e:
        logger.error(f"API search failed: {e}")
        
        # Fallback to mock data if enabled
        if settings.API_SETTINGS.get('USE_MOCK_DATA_IF_API_FAILS', True):
            return _get_mock_asset_data(symbol_or_name.upper().strip(), asset_type)
        
        return []


def _get_mock_asset_data(symbol, asset_type):
    """Fallback mock data when APIs fail"""
    # Mock data for demonstration - used as fallback
    mock_assets = {
        'RELIANCE': {
            'symbol': 'RELIANCE',
            'name': 'Reliance Industries Limited',
            'asset_type': 'stock',
            'exchange': 'NSE',
            'current_price': Decimal('2450.75'),
            'sector': 'Energy',
            'industry': 'Oil & Gas'
        },
        'TCS': {
            'symbol': 'TCS',
            'name': 'Tata Consultancy Services Limited',
            'asset_type': 'stock',
            'exchange': 'NSE', 
            'current_price': Decimal('3675.20'),
            'sector': 'Technology',
            'industry': 'IT Services'
        },
        'HDFCBANK': {
            'symbol': 'HDFCBANK',
            'name': 'HDFC Bank Limited',
            'asset_type': 'stock',
            'exchange': 'NSE',
            'current_price': Decimal('1650.45'),
            'sector': 'Financial Services',
            'industry': 'Banking'
        },
        'INFY': {
            'symbol': 'INFY',
            'name': 'Infosys Limited',
            'asset_type': 'stock',
            'exchange': 'NSE',
            'current_price': Decimal('1425.30'),
            'sector': 'Technology',
            'industry': 'IT Services'
        },
        'ICICIBANK': {
            'symbol': 'ICICIBANK',
            'name': 'ICICI Bank Limited',
            'asset_type': 'stock',
            'exchange': 'NSE',
            'current_price': Decimal('1185.75'),
            'sector': 'Financial Services',
            'industry': 'Banking'
        },
        'SBIN': {
            'symbol': 'SBIN',
            'name': 'State Bank of India',
            'asset_type': 'stock',
            'exchange': 'NSE',
            'current_price': Decimal('825.40'),
            'sector': 'Financial Services',
            'industry': 'Banking'
        },
        'AXISBANK': {
            'symbol': 'AXISBANK',
            'name': 'Axis Bank Limited',
            'asset_type': 'stock',
            'exchange': 'NSE',
            'current_price': Decimal('1095.65'),
            'sector': 'Financial Services',
            'industry': 'Banking'
        },
        'BAJFINANCE': {
            'symbol': 'BAJFINANCE',
            'name': 'Bajaj Finance Limited',
            'asset_type': 'stock',
            'exchange': 'NSE',
            'current_price': Decimal('6850.25'),
            'sector': 'Financial Services',
            'industry': 'NBFC'
        },
        'BHARTIARTL': {
            'symbol': 'BHARTIARTL',
            'name': 'Bharti Airtel Limited',
            'asset_type': 'stock',
            'exchange': 'NSE',
            'current_price': Decimal('1545.80'),
            'sector': 'Telecom',
            'industry': 'Telecommunications'
        },
        'ITC': {
            'symbol': 'ITC',
            'name': 'ITC Limited',
            'asset_type': 'stock',
            'exchange': 'NSE',
            'current_price': Decimal('465.30'),
            'sector': 'FMCG',
            'industry': 'Tobacco & Consumer Goods'
        }
    }
    
    # Add some mutual fund examples
    mutual_funds = {
        'ICICIPRUBL': {
            'symbol': 'ICICIPRUBL',
            'name': 'ICICI Prudential Bluechip Fund',
            'asset_type': 'mutual_fund',
            'current_price': Decimal('85.45'),
            'sector': 'Equity',
            'industry': 'Large Cap'
        },
        'SBIMAGNUMF': {
            'symbol': 'SBIMAGNUMF',
            'name': 'SBI Magnum Fund',
            'asset_type': 'mutual_fund',
            'current_price': Decimal('92.30'),
            'sector': 'Equity',
            'industry': 'Multi Cap'
        }
    }
    
    # Search by symbol first, then by name
    result = mock_assets.get(symbol) or mutual_funds.get(symbol)
    
    if not result:
        # Search by name (partial match)
        for asset_data in list(mock_assets.values()) + list(mutual_funds.values()):
            if symbol.lower() in asset_data['name'].lower() or asset_data['name'].lower() in symbol.lower():
                result = asset_data
                break
    
    return result


def get_current_price(symbol, asset_type='stock'):
    """Get current market price for an asset using real APIs.
    
    Integrates with multiple market data providers with fallback options.
    """
    from .api_services import market_data_service
    from django.conf import settings
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Use real API service
        price = market_data_service.get_current_price(symbol, asset_type)
        if price:
            return price
            
        # If no price found, try fallback
        logger.warning(f"No price found for {symbol} via APIs")
        
    except Exception as e:
        logger.error(f"Price fetch failed for {symbol}: {e}")
    
    # Fallback to mock data if enabled
    if settings.API_SETTINGS.get('USE_MOCK_DATA_IF_API_FAILS', True):
        return _get_mock_price(symbol, asset_type)
    
    return Decimal('0.00')


def _get_mock_price(symbol, asset_type):
    """Generate mock price as fallback"""
    base_prices = {
        'RELIANCE': 2450.75,
        'TCS': 3675.20,
        'HDFCBANK': 1650.45,
        'INFY': 1425.30,
        'ICICIBANK': 1185.75,
        'SBIN': 825.40,
        'AXISBANK': 1095.65,
        'BAJFINANCE': 6850.25,
        'BHARTIARTL': 1545.80,
        'ITC': 465.30,
        'ICICIPRUBL': 85.45,
        'SBIMAGNUMF': 92.30,
    }
    
    base_price = base_prices.get(symbol.upper(), 100.00)
    
    # Simulate realistic price movement
    if asset_type == 'mutual_fund':
        # Mutual funds have smaller daily movements
        fluctuation = random.uniform(-0.005, 0.005)  # -0.5% to +0.5%
    else:
        # Stocks have larger movements
        fluctuation = random.uniform(-0.03, 0.03)  # -3% to +3%
    
    new_price = base_price * (1 + fluctuation)
    return Decimal(str(round(new_price, 2)))


def update_asset_price(asset):
    """Update the price of a single asset."""
    try:
        new_price = get_current_price(asset.symbol, asset.asset_type)
        if new_price:
            old_price = asset.current_price
            asset.current_price = new_price
            asset.day_change = new_price - old_price
            if old_price > 0:
                asset.day_change_percentage = ((new_price - old_price) / old_price) * 100
            asset.price_updated_at = timezone.now()
            asset.save(update_fields=[
                'current_price', 'day_change', 'day_change_percentage', 'price_updated_at'
            ])
            return True
    except Exception as e:
        print(f"Error updating price for {asset.symbol}: {e}")
    return False


def bulk_update_prices(assets_queryset):
    """Update prices for multiple assets using real APIs with rate limiting."""
    from .api_services import market_data_service
    import time
    import logging
    
    logger = logging.getLogger(__name__)
    updated_count = 0
    errors = []
    
    try:
        # Use market data service for bulk updates
        for asset in assets_queryset:
            try:
                new_price = market_data_service.get_current_price(asset.symbol, asset.asset_type)
                if new_price and new_price != asset.current_price:
                    # Calculate day change
                    day_change = new_price - asset.current_price if asset.current_price else Decimal('0')
                    
                    asset.current_price = new_price
                    asset.day_change = day_change
                    asset.last_updated = timezone.now()
                    asset.save(update_fields=['current_price', 'day_change', 'last_updated'])
                    
                    # Update all holdings of this asset
                    for holding in asset.holdings.filter(is_active=True):
                        try:
                            holding.update_values()
                        except Exception as e:
                            logger.warning(f"Failed to update holding for {asset.symbol}: {e}")
                    
                    updated_count += 1
                    logger.info(f"Updated {asset.symbol}: {asset.current_price}")
                
                # Small delay to respect API rate limits
                time.sleep(0.1)
                
            except Exception as e:
                errors.append(f"{asset.symbol}: {str(e)}")
                logger.error(f"Error updating price for {asset.symbol}: {e}")
                continue
    
    except Exception as e:
        logger.error(f"Bulk price update failed: {e}")
        errors.append(f"Bulk update error: {str(e)}")
    
    return updated_count, errors


def calculate_portfolio_performance(portfolio, start_date=None, end_date=None):
    """Calculate portfolio performance over a date range."""
    # This would typically use historical price data
    # For now, return current metrics
    return {
        'total_return': portfolio.total_gain_loss,
        'total_return_percentage': portfolio.total_gain_loss_percentage,
        'annualized_return': portfolio.total_gain_loss_percentage,  # Simplified
        'volatility': 15.5,  # Mock volatility
        'sharpe_ratio': 0.85,  # Mock Sharpe ratio
    }


def get_asset_recommendations(user, limit=5):
    """Get asset recommendations based on user's portfolio."""
    # Simple recommendation logic - in production this would be more sophisticated
    
    # Get user's current holdings
    user_assets = Asset.objects.filter(
        holdings__portfolio__user=user,
        holdings__is_active=True
    ).distinct()
    
    user_sectors = set(user_assets.values_list('sector', flat=True))
    
    # Recommend assets from underrepresented sectors
    recommended_assets = Asset.objects.filter(
        is_active=True
    ).exclude(
        id__in=user_assets.values_list('id', flat=True)
    ).order_by('?')[:limit]  # Random selection for now
    
    return recommended_assets


def validate_csv_data(csv_data):
    """Validate CSV data for bulk upload."""
    errors = []
    valid_rows = []
    
    required_fields = ['Symbol', 'Name', 'Asset_Type', 'Quantity', 'Average_Cost']
    valid_asset_types = ['stock', 'mutual_fund', 'etf', 'bond']
    
    for row_num, row in enumerate(csv_data, start=2):
        row_errors = []
        
        # Check required fields
        missing_fields = [field for field in required_fields if not row.get(field, '').strip()]
        if missing_fields:
            row_errors.append(f"Missing fields: {', '.join(missing_fields)}")
        
        # Validate asset type
        asset_type = row.get('Asset_Type', '').strip().lower()
        if asset_type and asset_type not in valid_asset_types:
            row_errors.append(f"Invalid asset type: {asset_type}. Must be one of: {', '.join(valid_asset_types)}")
        
        # Validate numeric fields
        try:
            quantity = float(row.get('Quantity', 0))
            if quantity <= 0:
                row_errors.append("Quantity must be greater than 0")
        except ValueError:
            row_errors.append("Invalid quantity format")
        
        try:
            average_cost = float(row.get('Average_Cost', 0))
            if average_cost <= 0:
                row_errors.append("Average cost must be greater than 0")
        except ValueError:
            row_errors.append("Invalid average cost format")
        
        if row_errors:
            errors.append(f"Row {row_num}: {'; '.join(row_errors)}")
        else:
            valid_rows.append(row)
    
    return valid_rows, errors


# Real-world API integration functions (commented out for now)

def fetch_nse_stock_data(symbol):
    """Fetch stock data from NSE API."""
    # Example implementation for NSE API
    # url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
    # headers = {
    #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    # }
    # try:
    #     response = requests.get(url, headers=headers)
    #     if response.status_code == 200:
    #         data = response.json()
    #         return {
    #             'symbol': symbol,
    #             'current_price': data.get('priceInfo', {}).get('lastPrice', 0),
    #             'day_change': data.get('priceInfo', {}).get('change', 0),
    #             'day_change_percentage': data.get('priceInfo', {}).get('pChange', 0),
    #         }
    # except Exception as e:
    #     print(f"Error fetching NSE data for {symbol}: {e}")
    pass


def fetch_mutual_fund_nav(scheme_code):
    """Fetch mutual fund NAV from AMFI API."""
    # Example implementation for mutual fund data
    # url = f"https://api.mfapi.in/mf/{scheme_code}"
    # try:
    #     response = requests.get(url)
    #     if response.status_code == 200:
    #         data = response.json()
    #         latest_nav = data['data'][0]  # Most recent NAV
    #         return {
    #             'current_price': float(latest_nav['nav']),
    #             'date': latest_nav['date']
    #         }
    # except Exception as e:
    #     print(f"Error fetching MF NAV for {scheme_code}: {e}")
    pass