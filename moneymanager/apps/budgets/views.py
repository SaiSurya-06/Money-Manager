from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from .models import Budget, BudgetCategory, BudgetGoal, BudgetAlert
from .forms import BudgetForm, BudgetGoalForm
from moneymanager.apps.transactions.models import Transaction
from moneymanager.apps.core.models import Category


class BudgetListView(LoginRequiredMixin, ListView):
    """List all budgets."""
    model = Budget
    template_name = 'budgets/budget_list.html'
    context_object_name = 'budgets'

    def get_queryset(self):
        queryset = Budget.objects.filter(is_active=True)

        if hasattr(self.request, 'current_family_group') and self.request.current_family_group:
            queryset = queryset.filter(family_group=self.request.current_family_group)
        else:
            queryset = queryset.filter(user=self.request.user, family_group__isnull=True)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Update spent amounts for all budgets
        for budget in context['budgets']:
            budget.update_spent_amount()

        # Calculate summary statistics
        active_budgets = context['budgets'].filter(
            start_date__lte=date.today(),
            end_date__gte=date.today()
        )

        context['total_budgeted'] = sum(budget.total_budget for budget in active_budgets)
        context['total_spent'] = sum(budget.spent_amount for budget in active_budgets)
        context['active_count'] = active_budgets.count()

        return context


class BudgetCreateView(LoginRequiredMixin, CreateView):
    """Create a new budget."""
    model = Budget
    form_class = BudgetForm
    template_name = 'budgets/budget_form.html'
    success_url = reverse_lazy('budgets:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['family_group'] = getattr(self.request, 'current_family_group', None)
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Budget created successfully!')
        return response


class BudgetUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing budget."""
    model = Budget
    form_class = BudgetForm
    template_name = 'budgets/budget_form.html'
    success_url = reverse_lazy('budgets:list')

    def get_queryset(self):
        queryset = Budget.objects.filter(is_active=True)
        if hasattr(self.request, 'current_family_group') and self.request.current_family_group:
            queryset = queryset.filter(family_group=self.request.current_family_group)
        else:
            queryset = queryset.filter(user=self.request.user, family_group__isnull=True)
        return queryset

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['family_group'] = getattr(self.request, 'current_family_group', None)
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Budget updated successfully!')
        return response


@login_required
def budget_detail(request, pk):
    """Budget detail view with spending breakdown."""
    queryset = Budget.objects.filter(is_active=True)

    if hasattr(request, 'current_family_group') and request.current_family_group:
        queryset = queryset.filter(family_group=request.current_family_group)
    else:
        queryset = queryset.filter(user=request.user, family_group__isnull=True)

    budget = get_object_or_404(queryset, pk=pk)

    # Update spent amount
    budget.update_spent_amount()

    # Get spending by category within budget period
    transactions_qs = Transaction.objects.filter(
        transaction_type='expense',
        date__gte=budget.start_date,
        date__lte=budget.end_date,
        is_active=True
    )

    if budget.family_group:
        transactions_qs = transactions_qs.filter(family_group=budget.family_group)
    else:
        transactions_qs = transactions_qs.filter(user=budget.user)

    spending_by_category = transactions_qs.filter(
        category__isnull=False
    ).values(
        'category__name',
        'category__color'
    ).annotate(
        total=Sum('amount')
    ).order_by('-total')

    # Get recent transactions
    recent_transactions = transactions_qs.select_related(
        'category', 'account'
    ).order_by('-date', '-created_at')[:10]

    # Calculate progress
    days_total = (budget.end_date - budget.start_date).days + 1
    days_passed = (date.today() - budget.start_date).days + 1
    days_remaining = max(0, (budget.end_date - date.today()).days)

    progress_percentage = min(100, (days_passed / days_total) * 100) if days_total > 0 else 0

    context = {
        'budget': budget,
        'spending_by_category': spending_by_category,
        'recent_transactions': recent_transactions,
        'days_total': days_total,
        'days_passed': days_passed,
        'days_remaining': days_remaining,
        'progress_percentage': progress_percentage,
    }

    return render(request, 'budgets/budget_detail.html', context)


class BudgetGoalListView(LoginRequiredMixin, ListView):
    """List all budget goals."""
    model = BudgetGoal
    template_name = 'budgets/goal_list.html'
    context_object_name = 'goals'

    def get_queryset(self):
        queryset = BudgetGoal.objects.filter(is_active=True)

        if hasattr(self.request, 'current_family_group') and self.request.current_family_group:
            queryset = queryset.filter(family_group=self.request.current_family_group)
        else:
            queryset = queryset.filter(user=self.request.user, family_group__isnull=True)

        return queryset.order_by('-priority', 'target_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        goals = context['goals']
        context['active_goals'] = goals.filter(is_achieved=False)
        context['completed_goals'] = goals.filter(is_achieved=True)

        return context


class BudgetGoalCreateView(LoginRequiredMixin, CreateView):
    """Create a new budget goal."""
    model = BudgetGoal
    form_class = BudgetGoalForm
    template_name = 'budgets/goal_form.html'
    success_url = reverse_lazy('budgets:goals')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['family_group'] = getattr(self.request, 'current_family_group', None)
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Goal created successfully!')
        return response


@login_required
def goal_update_progress(request, pk):
    """Update goal progress."""
    queryset = BudgetGoal.objects.filter(is_active=True)

    if hasattr(request, 'current_family_group') and request.current_family_group:
        queryset = queryset.filter(family_group=request.current_family_group)
    else:
        queryset = queryset.filter(user=request.user, family_group__isnull=True)

    goal = get_object_or_404(queryset, pk=pk)

    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', 0))
            if amount > 0:
                goal.update_progress(amount)
                messages.success(request, f'Added ${amount} to your goal progress!')
            else:
                messages.error(request, 'Please enter a valid amount.')
        except (ValueError, TypeError):
            messages.error(request, 'Please enter a valid amount.')

    return redirect('budgets:goals')


@login_required
def budget_analytics(request):
    """Budget analytics dashboard."""
    # Determine current family group or personal data
    if hasattr(request, 'current_family_group') and request.current_family_group:
        family_group = request.current_family_group
        budgets_qs = Budget.objects.filter(family_group=family_group, is_active=True)
        transactions_qs = Transaction.objects.filter(
            family_group=family_group,
            transaction_type='expense',
            is_active=True
        )
    else:
        family_group = None
        budgets_qs = Budget.objects.filter(user=request.user, family_group__isnull=True, is_active=True)
        transactions_qs = Transaction.objects.filter(
            user=request.user,
            family_group__isnull=True,
            transaction_type='expense',
            is_active=True
        )

    # Current month analysis
    current_month = date.today().replace(day=1)
    next_month = (current_month.replace(day=28) + timedelta(days=4)).replace(day=1)

    current_budgets = budgets_qs.filter(
        start_date__lte=current_month,
        end_date__gte=current_month
    )

    # Update all budget amounts
    for budget in current_budgets:
        budget.update_spent_amount()

    # Monthly trends (last 12 months)
    monthly_trends = []
    for i in range(12):
        month_date = current_month - timedelta(days=30 * i)
        month_start = month_date.replace(day=1)

        if month_date.month == 12:
            month_end = month_date.replace(year=month_date.year + 1, month=1, day=1)
        else:
            month_end = month_date.replace(month=month_date.month + 1, day=1)

        month_budgets = budgets_qs.filter(
            start_date__lte=month_start,
            end_date__gte=month_start
        )

        month_spent = transactions_qs.filter(
            date__gte=month_start,
            date__lt=month_end
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        month_budgeted = sum(budget.total_budget for budget in month_budgets)

        monthly_trends.append({
            'month': month_start,
            'budgeted': month_budgeted,
            'spent': month_spent,
            'variance': month_budgeted - month_spent
        })

    monthly_trends.reverse()

    # Category performance
    category_performance = []
    categories = Category.objects.filter(category_type='expense')

    for category in categories:
        category_budgets = BudgetCategory.objects.filter(
            budget__in=current_budgets,
            category=category
        )

        if category_budgets.exists():
            total_allocated = sum(bc.allocated_amount for bc in category_budgets)
            total_spent = sum(bc.spent_amount for bc in category_budgets)

            category_performance.append({
                'category': category,
                'allocated': total_allocated,
                'spent': total_spent,
                'variance': total_allocated - total_spent,
                'percentage': (total_spent / total_allocated * 100) if total_allocated > 0 else 0
            })

    category_performance.sort(key=lambda x: x['percentage'], reverse=True)

    context = {
        'current_budgets': current_budgets,
        'monthly_trends': monthly_trends,
        'category_performance': category_performance[:10],  # Top 10
        'total_budgeted': sum(budget.total_budget for budget in current_budgets),
        'total_spent': sum(budget.spent_amount for budget in current_budgets),
    }

    return render(request, 'budgets/analytics.html', context)