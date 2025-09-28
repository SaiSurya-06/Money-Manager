"""
Enhanced Portfolio Models with Production-Level Features
Includes improved validation, audit trails, and performance optimizations.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import uuid
from datetime import date

from moneymanager.apps.core.models import TimeStampedModel, FamilyGroup
from .constants import (
    ASSET_TYPES, SIP_FREQUENCIES, SIP_STATUS_CHOICES, TRANSACTION_TYPES,
    SUPPORTED_CURRENCIES, MIN_SIP_AMOUNT, MAX_SIP_AMOUNT,
    MIN_INVESTMENT_AMOUNT, MAX_INVESTMENT_AMOUNT
)
from .utils.validators import InvestmentValidator
from .utils.calculations import safe_decimal, get_next_sip_date

User = get_user_model()


class AuditMixin(models.Model):
    """Mixin for audit trail functionality."""
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='%(app_label)s_%(class)s_created'
    )
    modified_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='%(app_label)s_%(class)s_modified'
    )
    
    class Meta:
        abstract = True


class EnhancedPortfolio(TimeStampedModel, AuditMixin):
    """Enhanced Portfolio model with production features."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, db_index=True)
    description = models.TextField(blank=True)
    
    # Financial data with proper precision
    total_value = models.DecimalField(
        max_digits=18, decimal_places=2, default=0,
        validators=[MinValueValidator(Decimal('0'))]
    )
    total_cost_basis = models.DecimalField(
        max_digits=18, decimal_places=2, default=0,
        validators=[MinValueValidator(Decimal('0'))]
    )
    total_gain_loss = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_gain_loss_percentage = models.DecimalField(
        max_digits=8, decimal_places=4, default=0,
        validators=[MinValueValidator(Decimal('-100')), MaxValueValidator(Decimal('10000'))]
    )
    
    # Relationships
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enhanced_portfolios')
    family_group = models.ForeignKey(
        FamilyGroup,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='enhanced_portfolios'
    )
    
    # Status and metadata
    is_active = models.BooleanField(default=True, db_index=True)
    currency = models.CharField(max_length=3, choices=SUPPORTED_CURRENCIES, default='INR')
    
    # Performance tracking
    last_updated = models.DateTimeField(auto_now=True)
    last_price_update = models.DateTimeField(null=True, blank=True)
    
    # Risk and allocation settings
    target_allocation = models.JSONField(default=dict, blank=True)
    risk_tolerance = models.CharField(
        max_length=20, 
        choices=[
            ('conservative', 'Conservative'),
            ('moderate', 'Moderate'),
            ('aggressive', 'Aggressive'),
        ],
        default='moderate'
    )
    
    class Meta:
        db_table = 'portfolios_enhanced_portfolio'
        ordering = ['name']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['created_at']),
            models.Index(fields=['total_value']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'name'],
                condition=models.Q(is_active=True),
                name='unique_active_portfolio_name'
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    def clean(self):
        """Model validation."""
        super().clean()
        
        # Validate name
        if self.name:
            self.name = InvestmentValidator.validate_name(self.name)
        
        # Validate description
        if self.description:
            self.description = InvestmentValidator.validate_notes(self.description)
    
    def save(self, *args, **kwargs):
        """Override save to add validation and audit trail."""
        self.full_clean()
        super().save(*args, **kwargs)

    def update_portfolio_values(self):
        """Update portfolio totals based on holdings."""
        holdings = self.holdings.filter(is_active=True)

        self.total_value = sum(
            holding.current_value for holding in holdings
        )
        self.total_cost_basis = sum(
            holding.total_cost_basis for holding in holdings
        )
        self.total_gain_loss = self.total_value - self.total_cost_basis

        if self.total_cost_basis > 0:
            self.total_gain_loss_percentage = (
                (self.total_gain_loss / self.total_cost_basis) * 100
            )
        else:
            self.total_gain_loss_percentage = Decimal('0')

        self.last_updated = timezone.now()
        self.save(update_fields=[
            'total_value', 'total_cost_basis', 'total_gain_loss',
            'total_gain_loss_percentage', 'last_updated'
        ])

    @property
    def day_change(self):
        """Calculate total day change for portfolio."""
        return sum(
            holding.day_change for holding in self.holdings.filter(is_active=True)
        )

    @property
    def day_change_percentage(self):
        """Calculate day change percentage for portfolio."""
        if self.total_value > 0:
            previous_value = self.total_value - self.day_change
            if previous_value > 0:
                return (self.day_change / previous_value) * 100
        return Decimal('0')

    def get_asset_allocation(self):
        """Get asset allocation breakdown."""
        holdings = self.holdings.filter(is_active=True).select_related('asset')
        allocation = {}
        
        for holding in holdings:
            asset_type = holding.asset.asset_type
            if asset_type not in allocation:
                allocation[asset_type] = {
                    'total_value': Decimal('0'),
                    'percentage': Decimal('0'),
                    'count': 0
                }
            
            allocation[asset_type]['total_value'] += holding.current_value
            allocation[asset_type]['count'] += 1
        
        # Calculate percentages
        for asset_type, data in allocation.items():
            if self.total_value > 0:
                data['percentage'] = (data['total_value'] / self.total_value) * 100
        
        return allocation

    def check_rebalancing_needed(self):
        """Check if portfolio needs rebalancing based on target allocation."""
        if not self.target_allocation:
            return False
        
        current_allocation = self.get_asset_allocation()
        threshold = Decimal('5')  # 5% threshold
        
        for asset_type, target_pct in self.target_allocation.items():
            current_pct = current_allocation.get(asset_type, {}).get('percentage', 0)
            if abs(current_pct - Decimal(str(target_pct))) > threshold:
                return True
        
        return False


class EnhancedAsset(TimeStampedModel, AuditMixin):
    """Enhanced Asset model with comprehensive market data."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    symbol = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=500)  # Increased length for long mutual fund names
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPES, db_index=True)
    
    # Market identifiers
    isin = models.CharField(max_length=12, blank=True, db_index=True)
    exchange = models.CharField(max_length=20, blank=True)
    currency = models.CharField(max_length=3, choices=SUPPORTED_CURRENCIES, default='INR')
    
    # Current price data with higher precision
    current_price = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    day_change = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    day_change_percentage = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    
    # Volume and market data
    volume = models.BigIntegerField(default=0)
    market_cap = models.BigIntegerField(null=True, blank=True)
    
    # Additional financial metrics
    pe_ratio = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    pb_ratio = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    dividend_yield = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    
    # Price tracking
    price_updated_at = models.DateTimeField(null=True, blank=True)
    week_52_high = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    week_52_low = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    
    # Categorization
    sector = models.CharField(max_length=100, blank=True, db_index=True)
    industry = models.CharField(max_digits=100, blank=True)
    description = models.TextField(blank=True)
    
    # Mutual Fund specific data
    nav = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    aum = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)  # Assets Under Management
    expense_ratio = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    fund_manager = models.CharField(max_length=200, blank=True)
    
    # Status and metadata
    is_active = models.BooleanField(default=True, db_index=True)
    is_verified = models.BooleanField(default=False)  # Manual verification flag
    
    # Data quality indicators
    data_source = models.CharField(max_length=50, blank=True)
    data_quality_score = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    class Meta:
        db_table = 'portfolios_enhanced_asset'
        ordering = ['symbol']
        indexes = [
            models.Index(fields=['symbol', 'asset_type']),
            models.Index(fields=['is_active', 'asset_type']),
            models.Index(fields=['sector']),
            models.Index(fields=['price_updated_at']),
        ]

    def __str__(self):
        return f"{self.symbol} - {self.name}"

    def clean(self):
        """Model validation."""
        super().clean()
        
        if self.symbol:
            self.symbol = InvestmentValidator.validate_symbol(self.symbol)
        
        if self.name:
            self.name = InvestmentValidator.validate_name(self.name, "Asset name")

    def update_price_data(self, price_data: dict):
        """Update asset price data from API with validation."""
        if not price_data:
            return
        
        # Validate required fields
        if 'price' not in price_data:
            raise ValidationError("Price data must contain 'price' field")
        
        old_price = self.current_price
        
        # Update basic price data
        self.current_price = safe_decimal(price_data.get('price', 0))
        
        # Calculate or use provided change data
        if 'change' in price_data:
            self.day_change = safe_decimal(price_data['change'])
        elif old_price > 0:
            self.day_change = self.current_price - old_price
        
        if 'change_percent' in price_data:
            self.day_change_percentage = safe_decimal(price_data['change_percent'])
        elif old_price > 0:
            self.day_change_percentage = ((self.current_price - old_price) / old_price) * 100
        
        # Update additional data if provided
        if 'volume' in price_data:
            self.volume = int(price_data['volume'])
        
        if 'market_cap' in price_data:
            self.market_cap = int(price_data['market_cap'])
        
        # Update 52-week high/low
        if self.week_52_high is None or self.current_price > self.week_52_high:
            self.week_52_high = self.current_price
        
        if self.week_52_low is None or self.current_price < self.week_52_low:
            self.week_52_low = self.current_price
        
        # For mutual funds, update NAV
        if self.asset_type == 'mutual_fund' and 'nav' in price_data:
            self.nav = safe_decimal(price_data['nav'])
        
        self.price_updated_at = timezone.now()
        self.save(update_fields=[
            'current_price', 'day_change', 'day_change_percentage',
            'volume', 'market_cap', 'week_52_high', 'week_52_low',
            'nav', 'price_updated_at'
        ])

    @property
    def is_price_stale(self):
        """Check if price data is stale (older than 1 hour for trading hours)."""
        if not self.price_updated_at:
            return True
        
        stale_threshold = timezone.now() - timezone.timedelta(hours=1)
        return self.price_updated_at < stale_threshold

    def get_performance_metrics(self, days=30):
        """Calculate basic performance metrics."""
        # This would calculate returns, volatility etc.
        # Implementation would depend on having historical price data
        return {
            'return_1d': self.day_change_percentage,
            'return_period': Decimal('0'),  # Would calculate from historical data
            'volatility': Decimal('0'),  # Would calculate from historical data
        }


class EnhancedSIP(TimeStampedModel, AuditMixin):
    """Enhanced SIP model with comprehensive features."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic SIP configuration
    name = models.CharField(max_length=200, db_index=True)
    portfolio = models.ForeignKey(
        'EnhancedPortfolio', 
        on_delete=models.CASCADE, 
        related_name='sips'
    )
    asset = models.ForeignKey(
        'EnhancedAsset', 
        on_delete=models.CASCADE, 
        related_name='sips'
    )
    
    # Investment configuration
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[
            MinValueValidator(MIN_SIP_AMOUNT),
            MaxValueValidator(MAX_SIP_AMOUNT)
        ]
    )
    frequency = models.CharField(
        max_length=20, 
        choices=SIP_FREQUENCIES, 
        default='monthly',
        db_index=True
    )
    
    # Date configuration
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(null=True, blank=True)
    next_investment_date = models.DateField(db_index=True)
    
    # Status and settings
    status = models.CharField(
        max_length=20, 
        choices=SIP_STATUS_CHOICES, 
        default='active',
        db_index=True
    )
    auto_invest = models.BooleanField(
        default=False,
        help_text="Automatically create investments on due dates"
    )
    
    # Investment tracking with higher precision
    total_invested = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_units = models.DecimalField(max_digits=18, decimal_places=8, default=0)  # Higher precision for units
    current_value = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_returns = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    returns_percentage = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    
    # Performance metrics
    xirr = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    average_nav = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    
    # Relationship
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enhanced_sips')
    
    # Advanced settings
    step_up_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text="Annual step-up percentage"
    )
    step_up_date = models.DateField(null=True, blank=True)
    
    # Notification settings
    notify_before_investment = models.BooleanField(default=False)
    notification_days = models.IntegerField(
        default=1,
        validators=[MinValueValidator(0), MaxValueValidator(30)]
    )

    class Meta:
        db_table = 'portfolios_enhanced_sip'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'next_investment_date', 'auto_invest']),
            models.Index(fields=['portfolio']),
            models.Index(fields=['asset']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'portfolio', 'name'],
                condition=models.Q(status='active'),
                name='unique_active_sip_name'
            )
        ]

    def __str__(self):
        return f"{self.name} - ₹{self.amount} {self.frequency}"

    def clean(self):
        """Model validation."""
        super().clean()
        
        # Validate name
        if self.name:
            self.name = InvestmentValidator.validate_name(self.name, "SIP name")
        
        # Validate amount
        if self.amount:
            self.amount = InvestmentValidator.validate_sip_amount(self.amount)
        
        # Validate dates
        if self.start_date:
            self.start_date = InvestmentValidator.validate_date(
                self.start_date, allow_past=True, allow_future=True
            )
        
        if self.end_date and self.start_date:
            if self.end_date <= self.start_date:
                raise ValidationError("End date must be after start date")

    def save(self, *args, **kwargs):
        """Override save to calculate next investment date."""
        # Set next_investment_date if not provided
        if not self.next_investment_date and self.start_date:
            self.next_investment_date = get_next_sip_date(self.start_date, self.frequency)
        
        self.full_clean()
        super().save(*args, **kwargs)

    def calculate_returns(self):
        """Calculate comprehensive returns for this SIP."""
        if self.total_units > 0 and self.asset.current_price > 0:
            self.current_value = self.total_units * self.asset.current_price
            self.total_returns = self.current_value - self.total_invested
            
            if self.total_invested > 0:
                self.returns_percentage = (self.total_returns / self.total_invested) * 100
            else:
                self.returns_percentage = Decimal('0')
            
            # Calculate average NAV
            if self.total_units > 0:
                self.average_nav = self.total_invested / self.total_units
                
            self.save(update_fields=[
                'current_value', 'total_returns', 'returns_percentage', 'average_nav'
            ])

    def update_totals(self):
        """Update total invested and units from all investments."""
        investments = self.investments.all()
        
        self.total_invested = sum(inv.amount for inv in investments)
        self.total_units = sum(inv.units_allocated for inv in investments)
        
        self.calculate_returns()

    @property
    def is_due_for_investment(self):
        """Check if SIP is due for next investment."""
        return (
            self.status == 'active' and 
            self.next_investment_date <= date.today() and
            (not self.end_date or self.next_investment_date <= self.end_date)
        )

    @property
    def investment_count(self):
        """Get count of investments made."""
        return self.investments.count()

    @property
    def months_since_start(self):
        """Calculate months since SIP started."""
        if not self.start_date:
            return 0
        
        today = date.today()
        return (today.year - self.start_date.year) * 12 + (today.month - self.start_date.month)

    def get_next_investment_date(self):
        """Calculate next investment date based on frequency."""
        return get_next_sip_date(self.next_investment_date, self.frequency)

    def apply_step_up(self):
        """Apply step-up to SIP amount if configured."""
        if (self.step_up_percentage > 0 and 
            self.step_up_date and 
            date.today() >= self.step_up_date):
            
            # Calculate new amount
            step_up_multiplier = 1 + (self.step_up_percentage / 100)
            self.amount = self.amount * step_up_multiplier
            
            # Set next step-up date (yearly)
            from dateutil.relativedelta import relativedelta
            self.step_up_date = self.step_up_date + relativedelta(years=1)
            
            self.save(update_fields=['amount', 'step_up_date'])

    def pause(self, reason=""):
        """Pause the SIP."""
        if self.status == 'active':
            self.status = 'paused'
            if reason:
                # Could add a notes field for reasons
                pass
            self.save(update_fields=['status'])

    def resume(self):
        """Resume a paused SIP."""
        if self.status == 'paused':
            self.status = 'active'
            self.save(update_fields=['status'])

    def complete(self):
        """Mark SIP as completed."""
        self.status = 'completed'
        self.save(update_fields=['status'])