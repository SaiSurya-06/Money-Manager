from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid

from moneymanager.apps.core.models import TimeStampedModel, FamilyGroup, Category

User = get_user_model()


class Account(TimeStampedModel):
    """Bank/financial accounts model."""
    ACCOUNT_TYPES = [
        ('checking', 'Checking'),
        ('savings', 'Savings'),
        ('credit', 'Credit Card'),
        ('investment', 'Investment'),
        ('loan', 'Loan'),
        ('cash', 'Cash'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    bank_name = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='INR')
    is_active = models.BooleanField(default=True)
    include_in_totals = models.BooleanField(default=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accounts')
    family_group = models.ForeignKey(
        FamilyGroup,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='accounts'
    )

    class Meta:
        db_table = 'transactions_account'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_account_type_display()})"

    def update_balance(self):
        """Update account balance based on transactions."""
        from django.db.models import Sum, Q

        # Calculate balance from transactions
        transactions = self.transactions.filter(is_active=True)

        income = transactions.filter(
            transaction_type='income'
        ).aggregate(total=Sum('amount'))['total'] or 0

        expenses = transactions.filter(
            transaction_type='expense'
        ).aggregate(total=Sum('amount'))['total'] or 0

        transfers_in = transactions.filter(
            transaction_type='transfer',
            to_account=self
        ).aggregate(total=Sum('amount'))['total'] or 0

        transfers_out = transactions.filter(
            transaction_type='transfer',
            from_account=self
        ).aggregate(total=Sum('amount'))['total'] or 0

        self.current_balance = income - expenses + transfers_in - transfers_out
        self.save(update_fields=['current_balance'])


class Transaction(TimeStampedModel):
    """Transaction model for all financial transactions."""
    TRANSACTION_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('transfer', 'Transfer'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    description = models.CharField(max_length=255)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')

    # For transfers
    to_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='transfers_in'
    )
    from_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='transfers_out'
    )

    date = models.DateField()
    notes = models.TextField(blank=True)
    receipt = models.ImageField(upload_to='receipts/', null=True, blank=True)

    # Metadata
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    family_group = models.ForeignKey(
        FamilyGroup,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='transactions'
    )
    is_recurring = models.BooleanField(default=False)
    recurring_transaction = models.ForeignKey(
        'RecurringTransaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_transactions'
    )
    is_active = models.BooleanField(default=True)

    # Import tracking
    imported_from = models.CharField(max_length=50, blank=True)
    external_id = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'transactions_transaction'
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['user']),
            models.Index(fields=['family_group']),
        ]

    def __str__(self):
        return f"{self.get_transaction_type_display()}: {self.description} - ₹{self.amount}"

    def save(self, *args, **kwargs):
        # Set family group from account if not set
        if not self.family_group and self.account:
            self.family_group = self.account.family_group

        # Don't trigger signals if we're in the middle of a bulk operation
        skip_signals = kwargs.pop('skip_signals', False)

        super().save(*args, **kwargs)

        # Account balance update is handled by signals unless explicitly skipped
        if not skip_signals and self.account:
            self.account.update_balance()


class RecurringTransaction(TimeStampedModel):
    """Model for recurring transactions."""
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi_annually', 'Semi-annually'),
        ('annually', 'Annually'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    description = models.CharField(max_length=255)
    transaction_type = models.CharField(max_length=20, choices=Transaction.TRANSACTION_TYPES)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='recurring_transactions')

    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    next_due_date = models.DateField()

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recurring_transactions')
    family_group = models.ForeignKey(
        FamilyGroup,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='recurring_transactions'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'transactions_recurring_transaction'
        ordering = ['next_due_date']

    def __str__(self):
        return f"{self.name} - {self.get_frequency_display()}"

    def generate_next_transaction(self):
        """Generate the next transaction for this recurring transaction."""
        from datetime import timedelta
        from dateutil.relativedelta import relativedelta

        if not self.is_active:
            return None

        if self.end_date and self.next_due_date > self.end_date:
            return None

        # Create the transaction
        transaction = Transaction.objects.create(
            amount=self.amount,
            description=self.description,
            transaction_type=self.transaction_type,
            category=self.category,
            account=self.account,
            date=self.next_due_date,
            user=self.user,
            family_group=self.family_group,
            is_recurring=True,
            recurring_transaction=self
        )

        # Calculate next due date
        if self.frequency == 'daily':
            self.next_due_date += timedelta(days=1)
        elif self.frequency == 'weekly':
            self.next_due_date += timedelta(weeks=1)
        elif self.frequency == 'biweekly':
            self.next_due_date += timedelta(weeks=2)
        elif self.frequency == 'monthly':
            self.next_due_date += relativedelta(months=1)
        elif self.frequency == 'quarterly':
            self.next_due_date += relativedelta(months=3)
        elif self.frequency == 'semi_annually':
            self.next_due_date += relativedelta(months=6)
        elif self.frequency == 'annually':
            self.next_due_date += relativedelta(years=1)

        self.save(update_fields=['next_due_date'])
        return transaction


class TransactionTag(TimeStampedModel):
    """Tags for transactions."""
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#007bff')
    family_group = models.ForeignKey(
        FamilyGroup,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='transaction_tags'
    )

    class Meta:
        db_table = 'transactions_tag'
        unique_together = ['name', 'family_group']
        ordering = ['name']

    def __str__(self):
        return self.name


class TransactionTagRelation(models.Model):
    """Many-to-many relationship between transactions and tags."""
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    tag = models.ForeignKey(TransactionTag, on_delete=models.CASCADE)

    class Meta:
        db_table = 'transactions_transaction_tags'
        unique_together = ['transaction', 'tag']