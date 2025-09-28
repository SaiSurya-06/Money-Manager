"""
Portfolio Service Layer - Business logic for portfolio operations.
Provides clean separation between views and models.
"""
import logging
from decimal import Decimal
from typing import List, Dict, Optional, Tuple, Union
from datetime import date, datetime, timedelta
from django.db import transaction
from django.db.models import Sum, Avg, Q, Count
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache

from ..models import Portfolio, Holding, Asset, Transaction as PortfolioTransaction
from ..exceptions import (
    PortfolioError, ValidationError, InsufficientDataError, 
    BusinessRuleError, AssetNotFoundError
)
from ..utils.calculations import (
    safe_decimal, calculate_percentage_change, calculate_annualized_return,
    calculate_volatility, calculate_sharpe_ratio, calculate_maximum_drawdown
)
from ..utils.validators import InvestmentValidator
from ..constants import CACHE_TIMEOUTS, PERFORMANCE_THRESHOLDS

User = get_user_model()
logger = logging.getLogger(__name__)


class PortfolioService:
    """Service class for portfolio operations."""
    
    @staticmethod
    def create_portfolio(user: User, name: str, description: str = "") -> Portfolio:
        """Create a new portfolio with validation."""
        try:
            # Validate inputs
            name = InvestmentValidator.validate_name(name, "Portfolio name")
            description = InvestmentValidator.validate_notes(description, "Description")
            
            # Check for duplicate names
            if Portfolio.objects.filter(user=user, name=name, is_active=True).exists():
                raise ValidationError(f"Portfolio with name '{name}' already exists")
            
            portfolio = Portfolio.objects.create(
                user=user,
                name=name,
                description=description
            )
            
            logger.info(f"Created portfolio '{name}' for user {user.username}")
            return portfolio
            
        except Exception as e:
            logger.error(f"Failed to create portfolio: {str(e)}")
            if isinstance(e, (ValidationError, PortfolioError)):
                raise
            raise PortfolioError(f"Failed to create portfolio: {str(e)}")
    
    @staticmethod
    def get_user_portfolios(user: User, include_inactive: bool = False) -> List[Portfolio]:
        """Get all portfolios for a user."""
        try:
            queryset = Portfolio.objects.filter(user=user)
            if not include_inactive:
                queryset = queryset.filter(is_active=True)
            
            return list(queryset.order_by('name'))
            
        except Exception as e:
            logger.error(f"Failed to get portfolios for user {user.username}: {str(e)}")
            raise PortfolioError(f"Failed to retrieve portfolios: {str(e)}")
    
    @staticmethod
    def update_portfolio_values(portfolio: Portfolio) -> Portfolio:
        """Update portfolio values based on current holdings."""
        try:
            holdings = portfolio.holdings.filter(is_active=True)
            
            # Calculate totals
            total_value = sum(holding.current_value for holding in holdings)
            total_cost_basis = sum(holding.total_cost_basis for holding in holdings)
            total_gain_loss = total_value - total_cost_basis
            
            # Calculate percentage
            if total_cost_basis > 0:
                gain_loss_percentage = (total_gain_loss / total_cost_basis) * 100
            else:
                gain_loss_percentage = Decimal('0')
            
            # Update portfolio
            portfolio.total_value = total_value
            portfolio.total_cost_basis = total_cost_basis
            portfolio.total_gain_loss = total_gain_loss
            portfolio.total_gain_loss_percentage = gain_loss_percentage
            portfolio.save(update_fields=[
                'total_value', 'total_cost_basis', 'total_gain_loss',
                'total_gain_loss_percentage'
            ])
            
            # Clear cache
            cache_key = f"portfolio_summary_{portfolio.id}"
            cache.delete(cache_key)
            
            return portfolio
            
        except Exception as e:
            logger.error(f"Failed to update portfolio values: {str(e)}")
            raise PortfolioError(f"Failed to update portfolio values: {str(e)}")
    
    @staticmethod
    def get_portfolio_performance(portfolio: Portfolio, 
                                days: int = 365) -> Dict[str, Union[Decimal, str]]:
        """Calculate portfolio performance metrics."""
        try:
            cache_key = f"portfolio_perf_{portfolio.id}_{days}"
            cached_result = cache.get(cache_key)
            if cached_result:
                return cached_result
            
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            # Get transactions in the period
            transactions = PortfolioTransaction.objects.filter(
                holding__portfolio=portfolio,
                date__gte=start_date,
                date__lte=end_date
            ).order_by('date')
            
            if not transactions.exists():
                return {
                    'total_return': Decimal('0'),
                    'annualized_return': Decimal('0'),
                    'volatility': Decimal('0'),
                    'sharpe_ratio': Decimal('0'),
                    'max_drawdown': Decimal('0'),
                    'performance_rating': 'insufficient_data'
                }
            
            # Calculate daily returns
            daily_values = []
            # This is simplified - in production, you'd track daily portfolio values
            for transaction in transactions:
                daily_values.append(transaction.total_amount)
            
            if len(daily_values) < 2:
                return {'performance_rating': 'insufficient_data'}
            
            # Calculate metrics
            start_value = daily_values[0]
            end_value = daily_values[-1]
            
            total_return = calculate_percentage_change(start_value, end_value)
            annualized_return = calculate_annualized_return(
                start_value, end_value, start_date, end_date
            )
            
            # Calculate volatility (simplified)
            returns = []
            for i in range(1, len(daily_values)):
                ret = calculate_percentage_change(daily_values[i-1], daily_values[i])
                returns.append(ret)
            
            volatility = calculate_volatility(returns)
            sharpe_ratio = calculate_sharpe_ratio(annualized_return, volatility)
            max_drawdown = calculate_maximum_drawdown([safe_decimal(v) for v in daily_values])
            
            # Performance rating
            performance_rating = PortfolioService._get_performance_rating(annualized_return)
            
            result = {
                'total_return': total_return,
                'annualized_return': annualized_return,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'performance_rating': performance_rating
            }
            
            # Cache for 30 minutes
            cache.set(cache_key, result, CACHE_TIMEOUTS['portfolio_summary'])
            return result
            
        except Exception as e:
            logger.error(f"Failed to calculate portfolio performance: {str(e)}")
            return {'performance_rating': 'error'}
    
    @staticmethod
    def _get_performance_rating(annualized_return: Decimal) -> str:
        """Get performance rating based on returns."""
        if annualized_return >= PERFORMANCE_THRESHOLDS['excellent']:
            return 'excellent'
        elif annualized_return >= PERFORMANCE_THRESHOLDS['good']:
            return 'good'
        elif annualized_return >= PERFORMANCE_THRESHOLDS['average']:
            return 'average'
        elif annualized_return >= PERFORMANCE_THRESHOLDS['poor']:
            return 'poor'
        else:
            return 'very_poor'
    
    @staticmethod
    def get_asset_allocation(portfolio: Portfolio) -> List[Dict]:
        """Get portfolio asset allocation by type, sector, etc."""
        try:
            cache_key = f"portfolio_allocation_{portfolio.id}"
            cached_result = cache.get(cache_key)
            if cached_result:
                return cached_result
            
            # Allocation by asset type
            allocations = portfolio.holdings.filter(is_active=True).values(
                'asset__asset_type',
                'asset__asset_type__name'  # This might need adjustment based on model
            ).annotate(
                total_value=Sum('current_value'),
                count=Count('id')
            ).order_by('-total_value')
            
            result = []
            total_portfolio_value = portfolio.total_value
            
            for allocation in allocations:
                percentage = Decimal('0')
                if total_portfolio_value > 0:
                    percentage = (allocation['total_value'] / total_portfolio_value) * 100
                
                result.append({
                    'asset_type': allocation['asset__asset_type'],
                    'total_value': allocation['total_value'],
                    'percentage': percentage,
                    'count': allocation['count']
                })
            
            # Cache for 10 minutes
            cache.set(cache_key, result, CACHE_TIMEOUTS['portfolio_summary'])
            return result
            
        except Exception as e:
            logger.error(f"Failed to get asset allocation: {str(e)}")
            return []
    
    @staticmethod
    def add_holding(portfolio: Portfolio, asset: Asset, quantity: Decimal,
                   average_cost: Decimal) -> Holding:
        """Add or update a holding in the portfolio."""
        try:
            # Validate inputs
            quantity = InvestmentValidator.validate_quantity(quantity)
            average_cost = InvestmentValidator.validate_price(average_cost)
            
            # Check if holding already exists
            holding, created = Holding.objects.get_or_create(
                portfolio=portfolio,
                asset=asset,
                defaults={
                    'quantity': quantity,
                    'average_cost': average_cost,
                    'total_cost_basis': quantity * average_cost
                }
            )
            
            if not created:
                # Update existing holding
                total_cost = holding.total_cost_basis + (quantity * average_cost)
                total_quantity = holding.quantity + quantity
                
                holding.quantity = total_quantity
                holding.average_cost = total_cost / total_quantity
                holding.total_cost_basis = total_cost
                holding.save()
            
            # Update current value
            holding.update_values()
            
            # Update portfolio totals
            PortfolioService.update_portfolio_values(portfolio)
            
            logger.info(f"Added holding {asset.symbol} to portfolio {portfolio.name}")
            return holding
            
        except Exception as e:
            logger.error(f"Failed to add holding: {str(e)}")
            if isinstance(e, ValidationError):
                raise
            raise PortfolioError(f"Failed to add holding: {str(e)}")
    
    @staticmethod
    def remove_holding(holding: Holding) -> None:
        """Remove a holding from the portfolio."""
        try:
            portfolio = holding.portfolio
            asset_symbol = holding.asset.symbol
            
            # Soft delete by marking inactive
            holding.is_active = False
            holding.save()
            
            # Update portfolio totals
            PortfolioService.update_portfolio_values(portfolio)
            
            logger.info(f"Removed holding {asset_symbol} from portfolio {portfolio.name}")
            
        except Exception as e:
            logger.error(f"Failed to remove holding: {str(e)}")
            raise PortfolioError(f"Failed to remove holding: {str(e)}")
    
    @staticmethod
    def get_portfolio_summary(user: User) -> Dict:
        """Get overall portfolio summary for a user."""
        try:
            cache_key = f"user_portfolio_summary_{user.id}"
            cached_result = cache.get(cache_key)
            if cached_result:
                return cached_result
            
            portfolios = Portfolio.objects.filter(user=user, is_active=True)
            
            total_value = sum(p.total_value for p in portfolios)
            total_cost_basis = sum(p.total_cost_basis for p in portfolios)
            total_gain_loss = total_value - total_cost_basis
            
            gain_loss_percentage = Decimal('0')
            if total_cost_basis > 0:
                gain_loss_percentage = (total_gain_loss / total_cost_basis) * 100
            
            # Calculate day change
            day_change = sum(p.day_change for p in portfolios)
            day_change_percentage = Decimal('0')
            if total_value > 0:
                previous_value = total_value - day_change
                if previous_value > 0:
                    day_change_percentage = (day_change / previous_value) * 100
            
            result = {
                'total_portfolios': portfolios.count(),
                'total_value': total_value,
                'total_cost_basis': total_cost_basis,
                'total_gain_loss': total_gain_loss,
                'gain_loss_percentage': gain_loss_percentage,
                'day_change': day_change,
                'day_change_percentage': day_change_percentage,
                'portfolios': list(portfolios)
            }
            
            # Cache for 5 minutes
            cache.set(cache_key, result, 300)
            return result
            
        except Exception as e:
            logger.error(f"Failed to get portfolio summary: {str(e)}")
            raise PortfolioError(f"Failed to get portfolio summary: {str(e)}")