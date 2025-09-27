from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid
from datetime import date

from moneymanager.apps.core.models import TimeStampedModel, FamilyGroup, Category

User = get_user_model()


class Budget(TimeStampedModel):
    """Budget model for tracking spending limits."""
    PERIOD_CHOICES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom Period'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES, default='monthly')

    # Date range for custom periods
    start_date = models.DateField()
    end_date = models.DateField()

    # Budget amounts
    total_budget = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    spent_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remaining_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Alert settings
    alert_percentage = models.IntegerField(
        default=80,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Send alert when this percentage of budget is spent"
    )
    alert_sent = models.BooleanField(default=False)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    family_group = models.ForeignKey(
        FamilyGroup,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='budgets'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'budgets_budget'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.get_period_display()}"

    @property
    def percentage_spent(self):
        """Calculate percentage of budget spent."""
        if self.total_budget > 0:
            return (self.spent_amount / self.total_budget) * 100
        return 0

    @property
    def is_over_budget(self):
        """Check if budget is exceeded."""
        return self.spent_amount > self.total_budget

    @property
    def should_send_alert(self):
        """Check if alert should be sent."""
        return (self.percentage_spent >= self.alert_percentage and
                not self.alert_sent and self.is_active)

    def update_spent_amount(self):
        """Update spent amount based on transactions."""
        from django.db.models import Sum
        from moneymanager.apps.transactions.models import Transaction

        # Get all expense transactions for this budget period
        transactions = Transaction.objects.filter(
            transaction_type='expense',
            date__gte=self.start_date,
            date__lte=self.end_date,
            is_active=True
        )

        # Filter by family group if applicable
        if self.family_group:
            transactions = transactions.filter(family_group=self.family_group)
        else:
            transactions = transactions.filter(user=self.user)

        # Filter by budget categories if any exist
        budget_categories = self.categories.values_list('category', flat=True)
        if budget_categories:
            transactions = transactions.filter(category__in=budget_categories)

        self.spent_amount = transactions.aggregate(
            total=Sum('amount')
        )['total'] or 0

        self.remaining_amount = self.total_budget - self.spent_amount
        self.save(update_fields=['spent_amount', 'remaining_amount'])

        # Check if alert should be sent
        if self.should_send_alert:
            self.send_budget_alert()

    def send_budget_alert(self):
        """Send budget alert notification."""
        from .signals import send_budget_alert

        if self.is_over_budget:
            message = f"Budget '{self.name}' exceeded! Spent ${self.spent_amount} of ${self.total_budget}."
            send_budget_alert(self, 'budget_exceeded', message)
        else:
            percentage = self.percentage_spent
            message = f"Budget '{self.name}' is {percentage:.1f}% spent (${self.spent_amount} of ${self.total_budget})."
            send_budget_alert(self, 'budget_warning', message)

        self.alert_sent = True
        self.save(update_fields=['alert_sent'])

    def reset_for_next_period(self):
        """Reset budget for the next period."""
        from dateutil.relativedelta import relativedelta

        if self.period == 'weekly':
            self.start_date += relativedelta(weeks=1)
            self.end_date += relativedelta(weeks=1)
        elif self.period == 'monthly':
            self.start_date += relativedelta(months=1)
            self.end_date += relativedelta(months=1)
        elif self.period == 'quarterly':
            self.start_date += relativedelta(months=3)
            self.end_date += relativedelta(months=3)
        elif self.period == 'yearly':
            self.start_date += relativedelta(years=1)
            self.end_date += relativedelta(years=1)
        else:
            # For custom periods, don't auto-reset
            return

        self.spent_amount = 0
        self.remaining_amount = self.total_budget
        self.alert_sent = False
        self.save(update_fields=['start_date', 'end_date', 'spent_amount',
                                'remaining_amount', 'alert_sent'])


class BudgetCategory(TimeStampedModel):
    """Categories within a budget with individual limits."""
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='categories')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    allocated_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    spent_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = 'budgets_budget_category'
        unique_together = ['budget', 'category']

    def __str__(self):
        return f"{self.budget.name} - {self.category.name}"

    @property
    def percentage_spent(self):
        """Calculate percentage of category budget spent."""
        if self.allocated_amount > 0:
            return (self.spent_amount / self.allocated_amount) * 100
        return 0

    @property
    def remaining_amount(self):
        """Calculate remaining amount for this category."""
        return self.allocated_amount - self.spent_amount

    def update_spent_amount(self):
        """Update spent amount for this category."""
        from django.db.models import Sum
        from moneymanager.apps.transactions.models import Transaction

        transactions = Transaction.objects.filter(
            transaction_type='expense',
            category=self.category,
            date__gte=self.budget.start_date,
            date__lte=self.budget.end_date,
            is_active=True
        )

        # Filter by family group if applicable
        if self.budget.family_group:
            transactions = transactions.filter(family_group=self.budget.family_group)
        else:
            transactions = transactions.filter(user=self.budget.user)

        self.spent_amount = transactions.aggregate(
            total=Sum('amount')
        )['total'] or 0

        self.save(update_fields=['spent_amount'])


class BudgetGoal(TimeStampedModel):
    """Financial goals with target amounts and deadlines."""
    GOAL_TYPES = [
        ('savings', 'Savings Goal'),
        ('debt_payoff', 'Debt Payoff'),
        ('purchase', 'Purchase Goal'),
        ('emergency_fund', 'Emergency Fund'),
        ('retirement', 'Retirement'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPES)
    target_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    target_date = models.DateField()
    priority = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Priority level (1=Low, 5=High)"
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budget_goals')
    family_group = models.ForeignKey(
        FamilyGroup,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='budget_goals'
    )
    is_active = models.BooleanField(default=True)
    is_achieved = models.BooleanField(default=False)
    achieved_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'budgets_budget_goal'
        ordering = ['-priority', 'target_date']

    def __str__(self):
        return f"{self.name} - ${self.target_amount}"

    @property
    def percentage_complete(self):
        """Calculate percentage of goal completed."""
        if self.target_amount > 0:
            return (self.current_amount / self.target_amount) * 100
        return 0

    @property
    def remaining_amount(self):
        """Calculate remaining amount to reach goal."""
        return max(0, self.target_amount - self.current_amount)

    @property
    def days_remaining(self):
        """Calculate days remaining to reach target date."""
        if self.target_date:
            return (self.target_date - date.today()).days
        return None

    @property
    def monthly_savings_needed(self):
        """Calculate monthly savings needed to reach goal."""
        days_remaining = self.days_remaining
        if days_remaining and days_remaining > 0:
            months_remaining = days_remaining / 30.44  # Average days per month
            if months_remaining > 0:
                return self.remaining_amount / months_remaining
        return 0

    def update_progress(self, amount):
        """Update goal progress."""
        was_achieved = self.is_achieved
        self.current_amount += amount

        if self.current_amount >= self.target_amount and not self.is_achieved:
            self.is_achieved = True
            self.achieved_date = date.today()

            # Send achievement notification
            from .signals import send_goal_alert
            message = f"Congratulations! You've achieved your goal '{self.name}' with ${self.current_amount}!"
            send_goal_alert(self, 'goal_achieved', message)

        self.save(update_fields=['current_amount', 'is_achieved', 'achieved_date'])


class BudgetAlert(TimeStampedModel):
    """Budget alerts and notifications."""
    ALERT_TYPES = [
        ('budget_exceeded', 'Budget Exceeded'),
        ('budget_warning', 'Budget Warning'),
        ('goal_deadline', 'Goal Deadline Approaching'),
        ('goal_achieved', 'Goal Achieved'),
    ]

    budget = models.ForeignKey(
        Budget,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts'
    )
    goal = models.ForeignKey(
        BudgetGoal,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts'
    )
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budget_alerts')

    class Meta:
        db_table = 'budgets_budget_alert'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.user.username}"