from django import forms
from django.contrib.auth import get_user_model
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field
from decimal import Decimal
from datetime import date, timedelta

from .models import Budget, BudgetGoal, BudgetCategory
from moneymanager.apps.core.models import Category

User = get_user_model()


class BudgetForm(forms.ModelForm):
    """Form for creating and editing budgets."""

    class Meta:
        model = Budget
        fields = ['name', 'description', 'period', 'start_date', 'end_date',
                 'total_budget', 'alert_percentage']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.family_group = kwargs.pop('family_group', None)
        super().__init__(*args, **kwargs)

        # Set default dates based on period
        if not self.instance.pk:
            today = date.today()
            self.fields['start_date'].initial = today

            if self.fields['period'].initial == 'monthly':
                # Next month end
                if today.month == 12:
                    end_date = date(today.year + 1, 1, 31)
                else:
                    next_month = today.month + 1
                    end_date = date(today.year, next_month, 1) - timedelta(days=1)
                self.fields['end_date'].initial = end_date

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('name', css_class='form-group mb-3'),
            Field('description', css_class='form-group mb-3', rows=3),
            Row(
                Column('period', css_class='form-group col-md-6 mb-3'),
                Column('total_budget', css_class='form-group col-md-6 mb-3'),
            ),
            Row(
                Column('start_date', css_class='form-group col-md-6 mb-3'),
                Column('end_date', css_class='form-group col-md-6 mb-3'),
            ),
            Field('alert_percentage', css_class='form-group mb-3'),
            Submit('submit', 'Save Budget', css_class='btn btn-primary')
        )

        # Add date widgets
        self.fields['start_date'].widget = forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
        self.fields['end_date'].widget = forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if end_date <= start_date:
                raise forms.ValidationError('End date must be after start date.')

        return cleaned_data

    def save(self, commit=True):
        budget = super().save(commit=False)
        if self.user:
            budget.user = self.user
        if self.family_group:
            budget.family_group = self.family_group

        # Set remaining amount initially
        budget.remaining_amount = budget.total_budget

        if commit:
            budget.save()
        return budget


class BudgetCategoryForm(forms.ModelForm):
    """Form for budget category allocation."""

    class Meta:
        model = BudgetCategory
        fields = ['category', 'allocated_amount']

    def __init__(self, *args, **kwargs):
        self.budget = kwargs.pop('budget', None)
        super().__init__(*args, **kwargs)

        # Filter categories to expense categories only
        self.fields['category'].queryset = Category.objects.filter(
            category_type='expense'
        )

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('category', css_class='form-group col-md-6 mb-3'),
                Column('allocated_amount', css_class='form-group col-md-6 mb-3'),
            ),
            Submit('submit', 'Add Category', css_class='btn btn-primary')
        )

    def save(self, commit=True):
        budget_category = super().save(commit=False)
        if self.budget:
            budget_category.budget = self.budget

        if commit:
            budget_category.save()
        return budget_category


class BudgetGoalForm(forms.ModelForm):
    """Form for creating and editing budget goals."""

    class Meta:
        model = BudgetGoal
        fields = ['name', 'description', 'goal_type', 'target_amount',
                 'current_amount', 'target_date', 'priority']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.family_group = kwargs.pop('family_group', None)
        super().__init__(*args, **kwargs)

        # Set default target date (1 year from now)
        if not self.instance.pk:
            self.fields['target_date'].initial = date.today() + timedelta(days=365)
            self.fields['current_amount'].initial = 0
            self.fields['priority'].initial = 3

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('name', css_class='form-group mb-3'),
            Field('description', css_class='form-group mb-3', rows=3),
            Row(
                Column('goal_type', css_class='form-group col-md-6 mb-3'),
                Column('priority', css_class='form-group col-md-6 mb-3'),
            ),
            Row(
                Column('target_amount', css_class='form-group col-md-6 mb-3'),
                Column('current_amount', css_class='form-group col-md-6 mb-3'),
            ),
            Field('target_date', css_class='form-group mb-3'),
            Submit('submit', 'Save Goal', css_class='btn btn-primary')
        )

        # Add date widget
        self.fields['target_date'].widget = forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })

    def clean(self):
        cleaned_data = super().clean()
        target_date = cleaned_data.get('target_date')
        current_amount = cleaned_data.get('current_amount', 0)
        target_amount = cleaned_data.get('target_amount', 0)

        if target_date and target_date <= date.today():
            raise forms.ValidationError('Target date must be in the future.')

        if current_amount < 0:
            raise forms.ValidationError('Current amount cannot be negative.')

        if target_amount <= 0:
            raise forms.ValidationError('Target amount must be greater than zero.')

        if current_amount > target_amount:
            raise forms.ValidationError('Current amount cannot be greater than target amount.')

        return cleaned_data

    def save(self, commit=True):
        goal = super().save(commit=False)
        if self.user:
            goal.user = self.user
        if self.family_group:
            goal.family_group = self.family_group

        if commit:
            goal.save()
        return goal


class BudgetFilterForm(forms.Form):
    """Form for filtering budgets."""
    STATUS_CHOICES = [
        ('', 'All Budgets'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('over_budget', 'Over Budget'),
    ]

    PERIOD_CHOICES = [
        ('', 'All Periods'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    period = forms.ChoiceField(
        choices=PERIOD_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search budgets...'
        })
    )


class GoalProgressForm(forms.Form):
    """Form for updating goal progress."""
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Amount to add',
            'step': '0.01'
        })
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Optional notes...'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('amount', css_class='form-group mb-3'),
            Field('notes', css_class='form-group mb-3'),
            Submit('submit', 'Update Progress', css_class='btn btn-success')
        )