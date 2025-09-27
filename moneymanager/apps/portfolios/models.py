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
    currency = models.CharField(max_length=3, default='USD')

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