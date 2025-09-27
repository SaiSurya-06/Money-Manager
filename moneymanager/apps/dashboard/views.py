from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal

from moneymanager.apps.transactions.models import Transaction, Account
from moneymanager.apps.budgets.models import Budget
from moneymanager.apps.portfolios.models import Portfolio


@login_required
def dashboard_home(request):
    """Main dashboard view with financial overview."""
    # Determine current family group or personal data
    if hasattr(request, 'current_family_group') and request.current_family_group:
        family_group = request.current_family_group
        transactions_qs = Transaction.objects.filter(
            family_group=family_group,
            is_active=True
        )
        accounts_qs = Account.objects.filter(
            family_group=family_group,
            is_active=True
        )
    else:
        family_group = None
        transactions_qs = Transaction.objects.filter(
            user=request.user,
            family_group__isnull=True,
            is_active=True
        )
        accounts_qs = Account.objects.filter(
            owner=request.user,
            family_group__isnull=True,
            is_active=True
        )

    # Calculate date ranges
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    start_of_year = today.replace(month=1, day=1)

    # Account totals
    accounts = accounts_qs.filter(include_in_totals=True)
    total_balance = sum(account.current_balance for account in accounts) or Decimal('0')

    # Monthly income and expenses
    monthly_transactions = transactions_qs.filter(date__gte=start_of_month)

    monthly_income = monthly_transactions.filter(
        transaction_type='income'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    monthly_expenses = monthly_transactions.filter(
        transaction_type='expense'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    net_income = monthly_income - monthly_expenses

    # Recent transactions (last 10)
    recent_transactions = transactions_qs.select_related(
        'category', 'account', 'user'
    ).order_by('-date', '-created_at')[:10]

    # Spending by category (current month)
    spending_by_category = monthly_transactions.filter(
        transaction_type='expense',
        category__isnull=False
    ).values('category__name', 'category__color').annotate(
        total=Sum('amount')
    ).order_by('-total')[:10]

    # Monthly trends (last 12 months)
    monthly_trends = []
    for i in range(12):
        month_date = today.replace(day=1) - timedelta(days=30 * i)
        month_start = month_date.replace(day=1)

        # Calculate next month start
        if month_date.month == 12:
            month_end = month_date.replace(year=month_date.year + 1, month=1, day=1)
        else:
            month_end = month_date.replace(month=month_date.month + 1, day=1)

        month_transactions = transactions_qs.filter(
            date__gte=month_start,
            date__lt=month_end
        )

        income = month_transactions.filter(
            transaction_type='income'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        expenses = month_transactions.filter(
            transaction_type='expense'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        monthly_trends.append({
            'month': month_start,
            'income': income,
            'expenses': expenses
        })

    monthly_trends.reverse()  # Show oldest to newest

    # Active budgets
    active_budgets = Budget.objects.filter(
        is_active=True,
        start_date__lte=today,
        end_date__gte=today
    )

    if family_group:
        active_budgets = active_budgets.filter(family_group=family_group)
    else:
        active_budgets = active_budgets.filter(user=request.user, family_group__isnull=True)

    # Portfolio summary
    portfolios = Portfolio.objects.filter(is_active=True)
    if family_group:
        portfolios = portfolios.filter(family_group=family_group)
    else:
        portfolios = portfolios.filter(user=request.user, family_group__isnull=True)

    total_portfolio_value = sum(portfolio.total_value for portfolio in portfolios) or Decimal('0')

    context = {
        'total_balance': total_balance,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'net_income': net_income,
        'recent_transactions': recent_transactions,
        'accounts': accounts[:5],  # Show top 5 accounts
        'spending_by_category': spending_by_category,
        'monthly_trends': monthly_trends,
        'active_budgets': active_budgets,
        'total_portfolio_value': total_portfolio_value,
        'accounts_count': accounts_qs.count(),
        'transactions_count': transactions_qs.count(),
    }

    return render(request, 'dashboard/home.html', context)


@login_required
def dashboard_analytics(request):
    """Analytics dashboard with detailed charts and insights."""
    # Determine current family group or personal data
    if hasattr(request, 'current_family_group') and request.current_family_group:
        family_group = request.current_family_group
        transactions_qs = Transaction.objects.filter(
            family_group=family_group,
            is_active=True
        )
    else:
        family_group = None
        transactions_qs = Transaction.objects.filter(
            user=request.user,
            family_group__isnull=True,
            is_active=True
        )

    # Date range for analysis (last 12 months)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=365)

    # Category analysis
    category_spending = transactions_qs.filter(
        transaction_type='expense',
        date__gte=start_date,
        category__isnull=False
    ).values(
        'category__name',
        'category__color'
    ).annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')

    # Monthly spending trends by category
    spending_trends = {}
    for category in category_spending:
        category_name = category['category__name']
        monthly_data = transactions_qs.filter(
            transaction_type='expense',
            category__name=category_name,
            date__gte=start_date
        ).extra(
            select={'month': "strftime('%%Y-%%m', date)"}
        ).values('month').annotate(
            total=Sum('amount')
        ).order_by('month')

        spending_trends[category_name] = list(monthly_data)

    # Account balance trends
    account_trends = []
    accounts = Account.objects.filter(is_active=True)
    if family_group:
        accounts = accounts.filter(family_group=family_group)
    else:
        accounts = accounts.filter(owner=request.user, family_group__isnull=True)

    for account in accounts:
        # Simple balance calculation (could be improved with balance history)
        balance_data = []
        for i in range(12):
            month_date = end_date.replace(day=1) - timedelta(days=30 * i)
            balance_data.append({
                'month': month_date.strftime('%Y-%m'),
                'balance': float(account.current_balance)  # Simplified
            })

        account_trends.append({
            'account': account.name,
            'data': list(reversed(balance_data))
        })

    # Top spending merchants/descriptions
    top_merchants = transactions_qs.filter(
        transaction_type='expense',
        date__gte=start_date
    ).values('description').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')[:10]

    # Average transaction amounts
    avg_income = transactions_qs.filter(
        transaction_type='income',
        date__gte=start_date
    ).aggregate(avg=Sum('amount'))['avg'] or Decimal('0')

    avg_expense = transactions_qs.filter(
        transaction_type='expense',
        date__gte=start_date
    ).aggregate(avg=Sum('amount'))['avg'] or Decimal('0')

    context = {
        'category_spending': category_spending,
        'spending_trends': spending_trends,
        'account_trends': account_trends,
        'top_merchants': top_merchants,
        'avg_income': avg_income,
        'avg_expense': avg_expense,
        'date_range': {
            'start': start_date,
            'end': end_date
        }
    }

    return render(request, 'dashboard/analytics.html', context)