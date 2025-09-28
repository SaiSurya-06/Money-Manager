from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid

from moneymanager.apps.core.models import TimeStampedModel, FamilyGroup

User = get_user_model()


class Portfolio(TimeStampedModel):
    """Investment portfolio model."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    total_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_cost_basis = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_gain_loss = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_gain_loss_percentage = models.DecimalField(max_digits=8, decimal_places=4, default=0)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portfolios')
    family_group = models.ForeignKey(
        FamilyGroup,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='portfolios'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'portfolios_portfolio'
        ordering = ['name']

    def __str__(self):
        return self.name

    def update_portfolio_values(self):
        """Update portfolio totals based on holdings."""
        holdings = self.holdings.filter(is_active=True)

        self.total_value = sum(holding.current_value for holding in holdings)
        self.total_cost_basis = sum(holding.total_cost_basis for holding in holdings)
        self.total_gain_loss = self.total_value - self.total_cost_basis

        if self.total_cost_basis > 0:
            self.total_gain_loss_percentage = (
                (self.total_gain_loss / self.total_cost_basis) * 100
            )
        else:
            self.total_gain_loss_percentage = 0

        self.save(update_fields=[
            'total_value', 'total_cost_basis', 'total_gain_loss',
            'total_gain_loss_percentage'
        ])

    @property
    def day_change(self):
        """Calculate total day change for portfolio."""
        return sum(holding.day_change for holding in self.holdings.filter(is_active=True))

    @property
    def day_change_percentage(self):
        """Calculate day change percentage for portfolio."""
        if self.total_value > 0:
            previous_value = self.total_value - self.day_change
            if previous_value > 0:
                return (self.day_change / previous_value) * 100
        return 0


class Asset(TimeStampedModel):
    """Individual assets/securities that can be held in portfolios."""
    ASSET_TYPES = [
        ('stock', 'Stock'),
        ('etf', 'ETF'),
        ('mutual_fund', 'Mutual Fund'),
        ('bond', 'Bond'),
        ('crypto', 'Cryptocurrency'),
        ('commodity', 'Commodity'),
        ('reit', 'REIT'),
        ('other', 'Other'),
    ]

    symbol = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPES)
    exchange = models.CharField(max_length=10, blank=True)
    currency = models.CharField(max_length=3, default='INR')

    # Current price data
    current_price = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    day_change = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    day_change_percentage = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    volume = models.BigIntegerField(default=0)
    market_cap = models.BigIntegerField(null=True, blank=True)

    # Price history tracking
    price_updated_at = models.DateTimeField(null=True, blank=True)

    # Additional info
    sector = models.CharField(max_length=100, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'portfolios_asset'
        ordering = ['symbol']
        indexes = [
            models.Index(fields=['symbol']),
            models.Index(fields=['asset_type']),
        ]

    def __str__(self):
        return f"{self.symbol} - {self.name}"

    def update_price_data(self, price_data):
        """Update asset price data from API."""
        self.current_price = price_data.get('price', self.current_price)
        self.day_change = price_data.get('change', self.day_change)
        self.day_change_percentage = price_data.get('change_percent', self.day_change_percentage)
        self.volume = price_data.get('volume', self.volume)
        self.market_cap = price_data.get('market_cap', self.market_cap)
        self.price_updated_at = timezone.now()

        self.save(update_fields=[
            'current_price', 'day_change', 'day_change_percentage',
            'volume', 'market_cap', 'price_updated_at'
        ])


class Holding(TimeStampedModel):
    """Portfolio holdings - tracks quantity and performance of assets."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='holdings')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='holdings')

    quantity = models.DecimalField(max_digits=15, decimal_places=6)
    average_cost = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    total_cost_basis = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    current_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    gain_loss = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    gain_loss_percentage = models.DecimalField(max_digits=8, decimal_places=4, default=0)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'portfolios_holding'
        unique_together = ['portfolio', 'asset']

    def __str__(self):
        return f"{self.portfolio.name} - {self.asset.symbol}"

    @property
    def day_change(self):
        """Calculate day change for this holding."""
        return self.quantity * self.asset.day_change

    def update_values(self):
        """Update holding values based on current asset price."""
        self.current_value = self.quantity * self.asset.current_price
        self.gain_loss = self.current_value - self.total_cost_basis

        if self.total_cost_basis > 0:
            self.gain_loss_percentage = (self.gain_loss / self.total_cost_basis) * 100
        else:
            self.gain_loss_percentage = 0

        self.save(update_fields=['current_value', 'gain_loss', 'gain_loss_percentage'])

    def calculate_average_cost(self):
        """Recalculate average cost based on transactions."""
        transactions = self.transactions.filter(transaction_type__in=['buy', 'sell'])

        total_shares = 0
        total_cost = 0

        for transaction in transactions.order_by('date'):
            if transaction.transaction_type == 'buy':
                total_cost += transaction.quantity * transaction.price
                total_shares += transaction.quantity
            elif transaction.transaction_type == 'sell':
                if total_shares > 0:
                    # Proportional cost reduction
                    cost_per_share = total_cost / total_shares
                    cost_reduction = transaction.quantity * cost_per_share
                    total_cost -= cost_reduction
                total_shares -= transaction.quantity

        self.quantity = total_shares
        if total_shares > 0:
            self.average_cost = total_cost / total_shares
            self.total_cost_basis = total_cost
        else:
            self.average_cost = 0
            self.total_cost_basis = 0

        self.save(update_fields=['quantity', 'average_cost', 'total_cost_basis'])


class Transaction(TimeStampedModel):
    """Portfolio transactions (buy/sell/dividend)."""
    TRANSACTION_TYPES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
        ('dividend', 'Dividend'),
        ('split', 'Stock Split'),
        ('merger', 'Merger'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    holding = models.ForeignKey(Holding, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    date = models.DateField()
    quantity = models.DecimalField(max_digits=15, decimal_places=6)
    price = models.DecimalField(max_digits=12, decimal_places=4)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    fees = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portfolio_transactions')

    class Meta:
        db_table = 'portfolios_transaction'
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.get_transaction_type_display()} {self.quantity} {self.holding.asset.symbol}"

    def save(self, *args, **kwargs):
        # Calculate total amount if not provided
        if not self.total_amount:
            self.total_amount = self.quantity * self.price + self.fees

        super().save(*args, **kwargs)

        # Update holding values
        self.holding.calculate_average_cost()
        self.holding.update_values()
        self.holding.portfolio.update_portfolio_values()


class Watchlist(TimeStampedModel):
    """User watchlists for tracking assets."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    assets = models.ManyToManyField(Asset, related_name='watchlists')

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlists')
    family_group = models.ForeignKey(
        FamilyGroup,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='watchlists'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'portfolios_watchlist'
        ordering = ['name']

    def __str__(self):
        return self.name


class SIP(TimeStampedModel):
    """Systematic Investment Plan - Monthly recurring investments."""
    FREQUENCY_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi_annual', 'Semi-Annual'),
        ('annual', 'Annual'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='sips')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='sips')
    
    # SIP Configuration
    name = models.CharField(max_length=200, help_text="Name for this SIP")
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('100'))])
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='monthly')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True, help_text="Leave blank for indefinite SIP")
    
    # SIP Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    next_investment_date = models.DateField()
    
    # Investment Tracking
    total_invested = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_units = models.DecimalField(max_digits=15, decimal_places=6, default=0)
    current_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_returns = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    returns_percentage = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    
    # Auto-investment settings
    auto_invest = models.BooleanField(default=False, help_text="Automatically create investments on due dates")
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sips')

    class Meta:
        db_table = 'portfolios_sip'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'next_investment_date']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f"{self.name} - ₹{self.amount} {self.frequency}"

    def calculate_returns(self):
        """Calculate current returns for this SIP."""
        from decimal import Decimal
        
        if self.total_units > 0:
            # Convert to Decimal for calculation
            current_price = Decimal(str(self.asset.current_price))
            self.current_value = self.total_units * current_price
            self.total_returns = self.current_value - self.total_invested
            
            if self.total_invested > 0:
                self.returns_percentage = (self.total_returns / self.total_invested) * 100
            else:
                self.returns_percentage = 0
                
            self.save(update_fields=['current_value', 'total_returns', 'returns_percentage'])

    def get_next_investment_date(self):
        """Calculate next investment date based on frequency."""
        from dateutil.relativedelta import relativedelta
        
        if self.frequency == 'monthly':
            return self.next_investment_date + relativedelta(months=1)
        elif self.frequency == 'quarterly':
            return self.next_investment_date + relativedelta(months=3)
        elif self.frequency == 'semi_annual':
            return self.next_investment_date + relativedelta(months=6)
        elif self.frequency == 'annual':
            return self.next_investment_date + relativedelta(years=1)
        return self.next_investment_date

    def update_totals(self):
        """Update total invested and units from all investments."""
        investments = self.investments.all()
        self.total_invested = sum(inv.amount for inv in investments)
        self.total_units = sum(inv.units_allocated for inv in investments)
        self.calculate_returns()

    @property
    def is_due_for_investment(self):
        """Check if SIP is due for next investment."""
        from django.utils import timezone
        return (self.status == 'active' and 
                self.next_investment_date <= timezone.now().date())

    @property
    def xirr(self):
        """Calculate XIRR (Extended Internal Rate of Return) for this SIP."""
        # This would require implementing XIRR calculation
        # For now, return annualized returns as approximation
        if self.total_invested > 0:
            days_invested = (timezone.now().date() - self.start_date).days
            if days_invested > 0:
                # Convert Decimal to float for power operation
                current_value_float = float(self.current_value)
                total_invested_float = float(self.total_invested)
                annualized_return = ((current_value_float / total_invested_float) ** (365.0 / days_invested) - 1) * 100
                return round(annualized_return, 2)
        return 0

    def save(self, *args, **kwargs):
        """Auto-calculate next_investment_date if not set."""
        from dateutil.relativedelta import relativedelta
        from datetime import datetime, date
        
        if not self.next_investment_date and self.start_date:
            # Ensure start_date is a date object
            start_date = self.start_date
            if isinstance(start_date, str):
                try:
                    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                except ValueError:
                    # If string format is different, try other formats
                    for fmt in ['%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']:
                        try:
                            start_date = datetime.strptime(start_date, fmt).date()
                            break
                        except ValueError:
                            continue
                    else:
                        # If all formats fail, use today as fallback
                        start_date = date.today()
            
            # Set next investment date based on frequency and start date
            if self.frequency == 'monthly':
                self.next_investment_date = start_date + relativedelta(months=1)
            elif self.frequency == 'quarterly':
                self.next_investment_date = start_date + relativedelta(months=3)
            elif self.frequency == 'semi_annual':
                self.next_investment_date = start_date + relativedelta(months=6)
            elif self.frequency == 'annual':
                self.next_investment_date = start_date + relativedelta(years=1)
            else:
                # Default to monthly
                self.next_investment_date = start_date + relativedelta(months=1)
        
        super().save(*args, **kwargs)


class SIPInvestment(TimeStampedModel):
    """Individual SIP investments/installments."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sip = models.ForeignKey(SIP, on_delete=models.CASCADE, related_name='investments')
    
    # Investment Details
    date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    nav_price = models.DecimalField(max_digits=12, decimal_places=4, help_text="NAV/Price at time of investment")
    units_allocated = models.DecimalField(max_digits=15, decimal_places=6)
    
    # Current Values
    current_nav = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    current_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    returns = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    returns_percentage = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    
    # Transaction Info
    transaction_id = models.CharField(max_length=100, blank=True)
    fees = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'portfolios_sip_investment'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['sip', 'date']),
        ]

    def __str__(self):
        return f"{self.sip.name} - {self.date} - ₹{self.amount}"

    def calculate_current_value(self):
        """Update current value based on current NAV."""
        from decimal import Decimal
        
        # Convert all values to Decimal for calculation
        current_price = Decimal(str(self.sip.asset.current_price))
        units = Decimal(str(self.units_allocated))
        
        self.current_nav = current_price
        self.current_value = units * current_price
        self.returns = self.current_value - self.amount
        
        if self.amount > 0:
            self.returns_percentage = (self.returns / self.amount) * 100
        else:
            self.returns_percentage = 0
            
        self.save(update_fields=['current_nav', 'current_value', 'returns', 'returns_percentage'])

    def save(self, *args, **kwargs):
        # Calculate units if not provided
        if not self.units_allocated and self.nav_price > 0:
            self.units_allocated = self.amount / self.nav_price
            
        super().save(*args, **kwargs)
        
        # Update SIP totals
        self.sip.update_totals()


class PriceHistory(TimeStampedModel):
    """Historical price data for assets."""
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='price_history')
    date = models.DateField()
    open_price = models.DecimalField(max_digits=12, decimal_places=4)
    high_price = models.DecimalField(max_digits=12, decimal_places=4)
    low_price = models.DecimalField(max_digits=12, decimal_places=4)
    close_price = models.DecimalField(max_digits=12, decimal_places=4)
    volume = models.BigIntegerField(default=0)

    class Meta:
        db_table = 'portfolios_price_history'
        unique_together = ['asset', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.asset.symbol} - {self.date}"