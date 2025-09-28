"""
SIP Service Layer - Business logic for SIP operations.
Handles SIP creation, management, and investment processing.
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

from ..models import SIP, SIPInvestment, Asset, Portfolio
from ..exceptions import (
    SIPError, ValidationError, InsufficientDataError, 
    BusinessRuleError, AssetNotFoundError, PriceNotAvailableError
)
from ..utils.calculations import (
    safe_decimal, calculate_xirr, get_next_sip_date, calculate_annualized_return,
    validate_investment_amount, validate_date_range
)
from ..utils.validators import InvestmentValidator
from ..constants import CACHE_TIMEOUTS, MIN_SIP_AMOUNT, MAX_SIP_AMOUNT
from .price_service import PriceService

User = get_user_model()
logger = logging.getLogger(__name__)


class SIPService:
    """Service class for SIP operations."""
    
    @staticmethod
    def create_sip(user: User, portfolio: Portfolio, asset: Asset, 
                   name: str, amount: Decimal, frequency: str,
                   start_date: date, end_date: Optional[date] = None,
                   auto_invest: bool = False) -> SIP:
        """Create a new SIP with comprehensive validation."""
        try:
            # Validate inputs
            name = InvestmentValidator.validate_name(name, "SIP name")
            amount = InvestmentValidator.validate_sip_amount(amount)
            frequency = InvestmentValidator.validate_sip_frequency(frequency)
            start_date = InvestmentValidator.validate_date(
                start_date, "Start date", allow_past=True, allow_future=True
            )
            
            if end_date:
                end_date = InvestmentValidator.validate_date(
                    end_date, "End date", allow_past=True, allow_future=True
                )
                validate_date_range(start_date, end_date)
            
            # Check for duplicate SIP names in the portfolio
            if SIP.objects.filter(
                user=user, 
                portfolio=portfolio, 
                name=name, 
                status='active'
            ).exists():
                raise ValidationError(f"Active SIP with name '{name}' already exists in this portfolio")
            
            # Validate asset type (should be mutual fund for SIP)
            if asset.asset_type != 'mutual_fund':
                logger.warning(f"Creating SIP for non-mutual fund asset: {asset.symbol}")
            
            # Create SIP
            sip = SIP.objects.create(
                user=user,
                portfolio=portfolio,
                asset=asset,
                name=name,
                amount=amount,
                frequency=frequency,
                start_date=start_date,
                end_date=end_date,
                auto_invest=auto_invest,
                status='active'
            )
            
            logger.info(f"Created SIP '{name}' for user {user.username}")
            return sip
            
        except Exception as e:
            logger.error(f"Failed to create SIP: {str(e)}")
            if isinstance(e, (ValidationError, SIPError)):
                raise
            raise SIPError(f"Failed to create SIP: {str(e)}")
    
    @staticmethod
    def get_user_sips(user: User, status: Optional[str] = None, 
                     portfolio: Optional[Portfolio] = None) -> List[SIP]:
        """Get SIPs for a user with optional filtering."""
        try:
            queryset = SIP.objects.filter(user=user)
            
            if status:
                queryset = queryset.filter(status=status)
            
            if portfolio:
                queryset = queryset.filter(portfolio=portfolio)
            
            return list(queryset.order_by('-created_at'))
            
        except Exception as e:
            logger.error(f"Failed to get SIPs for user {user.username}: {str(e)}")
            raise SIPError(f"Failed to retrieve SIPs: {str(e)}")
    
    @staticmethod
    def create_sip_investment(sip: SIP, amount: Decimal, nav_price: Decimal,
                            investment_date: date, transaction_id: str = "",
                            fees: Decimal = Decimal('0'), notes: str = "") -> SIPInvestment:
        """Create a new SIP investment."""
        try:
            # Validate inputs
            amount = validate_investment_amount(amount)
            nav_price = InvestmentValidator.validate_price(nav_price, "NAV price")
            investment_date = InvestmentValidator.validate_date(
                investment_date, "Investment date", allow_past=True, allow_future=False
            )
            
            if fees:
                fees = InvestmentValidator.validate_amount(fees, field_name="fees")
            
            notes = InvestmentValidator.validate_notes(notes)
            
            # Calculate units
            units_allocated = amount / nav_price
            
            # Check for duplicate investment on the same date
            if SIPInvestment.objects.filter(
                sip=sip, 
                date=investment_date
            ).exists():
                raise ValidationError(f"Investment already exists for {investment_date}")
            
            # Create investment
            investment = SIPInvestment.objects.create(
                sip=sip,
                date=investment_date,
                amount=amount,
                nav_price=nav_price,
                units_allocated=units_allocated,
                fees=fees,
                transaction_id=transaction_id,
                notes=notes
            )
            
            # Update SIP totals
            SIPService.update_sip_calculations(sip)
            
            # Update next investment date if this is current
            if investment_date >= sip.next_investment_date:
                sip.next_investment_date = get_next_sip_date(investment_date, sip.frequency)
                sip.save(update_fields=['next_investment_date'])
            
            logger.info(f"Created SIP investment for {sip.name}: ₹{amount} on {investment_date}")
            return investment
            
        except Exception as e:
            logger.error(f"Failed to create SIP investment: {str(e)}")
            if isinstance(e, (ValidationError, SIPError)):
                raise
            raise SIPError(f"Failed to create SIP investment: {str(e)}")
    
    @staticmethod
    def update_sip_calculations(sip: SIP) -> SIP:
        """Update SIP calculations and returns."""
        try:
            investments = sip.investments.all()
            
            if not investments.exists():
                sip.total_invested = Decimal('0')
                sip.total_units = Decimal('0')
                sip.current_value = Decimal('0')
                sip.total_returns = Decimal('0')
                sip.returns_percentage = Decimal('0')
                sip.save(update_fields=[
                    'total_invested', 'total_units', 'current_value',
                    'total_returns', 'returns_percentage'
                ])
                return sip
            
            # Calculate totals
            sip.total_invested = sum(inv.amount for inv in investments)
            sip.total_units = sum(inv.units_allocated for inv in investments)
            
            # Get current NAV price
            try:
                current_nav = PriceService.get_current_price(sip.asset.symbol, sip.asset.asset_type)
                sip.asset.current_price = current_nav
                sip.asset.save(update_fields=['current_price', 'price_updated_at'])
            except Exception as e:
                logger.warning(f"Could not update NAV for {sip.asset.symbol}: {str(e)}")
                current_nav = sip.asset.current_price or Decimal('0')
            
            # Calculate current value and returns
            sip.current_value = sip.total_units * current_nav
            sip.total_returns = sip.current_value - sip.total_invested
            
            if sip.total_invested > 0:
                sip.returns_percentage = (sip.total_returns / sip.total_invested) * 100
            else:
                sip.returns_percentage = Decimal('0')
            
            sip.save(update_fields=[
                'total_invested', 'total_units', 'current_value',
                'total_returns', 'returns_percentage'
            ])
            
            # Update individual investment current values
            for investment in investments:
                investment.calculate_current_value()
            
            # Clear cache
            cache_key = f"sip_performance_{sip.id}"
            cache.delete(cache_key)
            
            return sip
            
        except Exception as e:
            logger.error(f"Failed to update SIP calculations: {str(e)}")
            raise SIPError(f"Failed to update SIP calculations: {str(e)}")
    
    @staticmethod
    def calculate_sip_xirr(sip: SIP) -> Optional[Decimal]:
        """Calculate XIRR for a SIP."""
        try:
            investments = list(sip.investments.all().order_by('date'))
            
            if len(investments) < 2:
                return None
            
            # Prepare cash flows (investments are negative, current value is positive)
            cash_flows = []
            
            # Add investment cash flows (negative)
            for investment in investments:
                cash_flows.append((investment.date, -investment.amount))
            
            # Add current value as final cash flow (positive)
            cash_flows.append((date.today(), sip.current_value))
            
            return calculate_xirr(cash_flows)
            
        except Exception as e:
            logger.error(f"Failed to calculate XIRR for SIP {sip.id}: {str(e)}")
            return None
    
    @staticmethod
    def get_sip_performance_metrics(sip: SIP) -> Dict:
        """Get comprehensive performance metrics for a SIP."""
        try:
            cache_key = f"sip_performance_{sip.id}"
            cached_result = cache.get(cache_key)
            if cached_result:
                return cached_result
            
            # Update calculations first
            sip = SIPService.update_sip_calculations(sip)
            
            # Calculate XIRR
            xirr = SIPService.calculate_sip_xirr(sip)
            
            # Calculate annualized returns
            if sip.investments.exists():
                first_investment = sip.investments.order_by('date').first()
                annualized_return = calculate_annualized_return(
                    sip.total_invested,
                    sip.current_value,
                    first_investment.date,
                    date.today()
                )
            else:
                annualized_return = Decimal('0')
            
            # Calculate investment periods
            investments = sip.investments.all().order_by('date')
            investment_count = investments.count()
            
            months_invested = 0
            if investment_count > 1:
                first_date = investments.first().date
                last_date = investments.last().date
                months_invested = ((last_date.year - first_date.year) * 12 + 
                                 (last_date.month - first_date.month))
            
            # Average investment amount
            avg_investment = sip.total_invested / investment_count if investment_count > 0 else Decimal('0')
            
            result = {
                'total_invested': sip.total_invested,
                'current_value': sip.current_value,
                'total_returns': sip.total_returns,
                'returns_percentage': sip.returns_percentage,
                'xirr': xirr,
                'annualized_return': annualized_return,
                'investment_count': investment_count,
                'months_invested': months_invested,
                'average_investment': avg_investment,
                'total_units': sip.total_units,
                'current_nav': sip.asset.current_price,
                'average_nav': sip.total_invested / sip.total_units if sip.total_units > 0 else Decimal('0'),
            }
            
            # Cache for 30 minutes
            cache.set(cache_key, result, CACHE_TIMEOUTS['sip_calculations'])
            return result
            
        except Exception as e:
            logger.error(f"Failed to calculate SIP performance metrics: {str(e)}")
            return {}
    
    @staticmethod
    def get_due_sips(user: Optional[User] = None) -> List[SIP]:
        """Get SIPs that are due for investment."""
        try:
            queryset = SIP.objects.filter(
                status='active',
                auto_invest=True,
                next_investment_date__lte=date.today()
            )
            
            if user:
                queryset = queryset.filter(user=user)
            
            return list(queryset.order_by('next_investment_date'))
            
        except Exception as e:
            logger.error(f"Failed to get due SIPs: {str(e)}")
            return []
    
    @staticmethod
    def process_automatic_sip_investment(sip: SIP) -> Optional[SIPInvestment]:
        """Process automatic investment for a SIP."""
        try:
            if not sip.auto_invest or sip.status != 'active':
                raise BusinessRuleError("SIP is not configured for auto-investment")
            
            if sip.next_investment_date > date.today():
                raise BusinessRuleError("SIP is not due for investment yet")
            
            # Get current NAV price
            try:
                nav_price = PriceService.get_current_price(sip.asset.symbol, sip.asset.asset_type)
            except Exception as e:
                logger.error(f"Failed to get NAV price for {sip.asset.symbol}: {str(e)}")
                raise PriceNotAvailableError(f"NAV price not available for {sip.asset.symbol}")
            
            # Create investment
            investment = SIPService.create_sip_investment(
                sip=sip,
                amount=sip.amount,
                nav_price=nav_price,
                investment_date=sip.next_investment_date,
                notes="Auto-generated investment"
            )
            
            logger.info(f"Auto-investment processed for SIP {sip.name}: ₹{sip.amount}")
            return investment
            
        except Exception as e:
            logger.error(f"Failed to process automatic SIP investment: {str(e)}")
            if isinstance(e, (BusinessRuleError, PriceNotAvailableError)):
                raise
            raise SIPError(f"Failed to process automatic investment: {str(e)}")
    
    @staticmethod
    def pause_sip(sip: SIP, reason: str = "") -> SIP:
        """Pause a SIP."""
        try:
            if sip.status != 'active':
                raise BusinessRuleError("Only active SIPs can be paused")
            
            sip.status = 'paused'
            if reason:
                sip.notes = f"Paused: {reason}"
            sip.save(update_fields=['status', 'notes'])
            
            logger.info(f"Paused SIP {sip.name}")
            return sip
            
        except Exception as e:
            logger.error(f"Failed to pause SIP: {str(e)}")
            if isinstance(e, BusinessRuleError):
                raise
            raise SIPError(f"Failed to pause SIP: {str(e)}")
    
    @staticmethod
    def resume_sip(sip: SIP) -> SIP:
        """Resume a paused SIP."""
        try:
            if sip.status != 'paused':
                raise BusinessRuleError("Only paused SIPs can be resumed")
            
            sip.status = 'active'
            sip.save(update_fields=['status'])
            
            logger.info(f"Resumed SIP {sip.name}")
            return sip
            
        except Exception as e:
            logger.error(f"Failed to resume SIP: {str(e)}")
            if isinstance(e, BusinessRuleError):
                raise
            raise SIPError(f"Failed to resume SIP: {str(e)}")
    
    @staticmethod
    def complete_sip(sip: SIP) -> SIP:
        """Mark a SIP as completed."""
        try:
            sip.status = 'completed'
            sip.save(update_fields=['status'])
            
            logger.info(f"Completed SIP {sip.name}")
            return sip
            
        except Exception as e:
            logger.error(f"Failed to complete SIP: {str(e)}")
            raise SIPError(f"Failed to complete SIP: {str(e)}")
    
    @staticmethod
    def get_sip_dashboard_data(user: User) -> Dict:
        """Get comprehensive SIP dashboard data."""
        try:
            sips = SIP.objects.filter(user=user).select_related('asset', 'portfolio')
            
            active_sips = sips.filter(status='active')
            
            total_sips = sips.count()
            total_invested = sum(sip.total_invested for sip in sips)
            total_current_value = sum(sip.current_value for sip in sips)
            total_returns = total_current_value - total_invested
            
            returns_percentage = Decimal('0')
            if total_invested > 0:
                returns_percentage = (total_returns / total_invested) * 100
            
            # Due SIPs
            due_sips = SIPService.get_due_sips(user)
            
            # Monthly investment amount
            monthly_investment = sum(
                sip.amount for sip in active_sips 
                if sip.frequency == 'monthly'
            )
            
            return {
                'total_sips': total_sips,
                'active_sips': active_sips.count(),
                'total_invested': total_invested,
                'current_value': total_current_value,
                'total_returns': total_returns,
                'returns_percentage': returns_percentage,
                'due_sips': due_sips,
                'monthly_investment': monthly_investment,
                'sips': list(sips)
            }
            
        except Exception as e:
            logger.error(f"Failed to get SIP dashboard data: {str(e)}")
            raise SIPError(f"Failed to get SIP dashboard data: {str(e)}")