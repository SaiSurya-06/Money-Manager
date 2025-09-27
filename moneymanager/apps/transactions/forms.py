from django import forms
from django.contrib.auth import get_user_model
from django.db import models
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, Div
from decimal import Decimal

from .models import Account, Transaction, RecurringTransaction, TransactionTag
from moneymanager.apps.core.models import Category, FamilyGroup

User = get_user_model()


class AccountForm(forms.ModelForm):
    """Form for creating and editing accounts."""

    class Meta:
        model = Account
        fields = ['name', 'account_type', 'bank_name', 'account_number',
                 'current_balance', 'currency', 'is_active', 'include_in_totals']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.family_group = kwargs.pop('family_group', None)
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-6 mb-3'),
                Column('account_type', css_class='form-group col-md-6 mb-3'),
            ),
            Row(
                Column('bank_name', css_class='form-group col-md-6 mb-3'),
                Column('account_number', css_class='form-group col-md-6 mb-3'),
            ),
            Row(
                Column('current_balance', css_class='form-group col-md-6 mb-3'),
                Column('currency', css_class='form-group col-md-6 mb-3'),
            ),
            Row(
                Column('is_active', css_class='form-group col-md-6 mb-3'),
                Column('include_in_totals', css_class='form-group col-md-6 mb-3'),
            ),
            Submit('submit', 'Save Account', css_class='btn btn-primary')
        )

    def save(self, commit=True):
        account = super().save(commit=False)
        if self.user:
            account.owner = self.user
        if self.family_group:
            account.family_group = self.family_group

        if commit:
            account.save()
        return account


class TransactionForm(forms.ModelForm):
    """Form for creating and editing transactions."""

    class Meta:
        model = Transaction
        fields = ['amount', 'description', 'transaction_type', 'category',
                 'account', 'to_account', 'from_account', 'date', 'notes']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.family_group = kwargs.pop('family_group', None)
        super().__init__(*args, **kwargs)

        # Filter accounts and categories by user/family group
        if self.family_group:
            self.fields['account'].queryset = Account.objects.filter(
                family_group=self.family_group, is_active=True
            )
            self.fields['to_account'].queryset = Account.objects.filter(
                family_group=self.family_group, is_active=True
            )
            self.fields['from_account'].queryset = Account.objects.filter(
                family_group=self.family_group, is_active=True
            )
            self.fields['category'].queryset = Category.objects.filter(
                models.Q(family_group=self.family_group) |
                models.Q(is_system_category=True)
            )
        elif self.user:
            self.fields['account'].queryset = Account.objects.filter(
                owner=self.user, is_active=True
            )
            self.fields['to_account'].queryset = Account.objects.filter(
                owner=self.user, is_active=True
            )
            self.fields['from_account'].queryset = Account.objects.filter(
                owner=self.user, is_active=True
            )
            self.fields['category'].queryset = Category.objects.filter(
                models.Q(family_group__isnull=True) |
                models.Q(is_system_category=True)
            )

        # Make transfer fields optional initially
        self.fields['to_account'].required = False
        self.fields['from_account'].required = False

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('transaction_type', css_class='form-group col-md-6 mb-3'),
                Column('amount', css_class='form-group col-md-6 mb-3'),
            ),
            Field('description', css_class='form-group mb-3'),
            Row(
                Column('category', css_class='form-group col-md-6 mb-3'),
                Column('date', css_class='form-group col-md-6 mb-3'),
            ),
            Div(
                Field('account', css_class='form-group mb-3'),
                css_id='regular-account-field'
            ),
            Div(
                Row(
                    Column('from_account', css_class='form-group col-md-6 mb-3'),
                    Column('to_account', css_class='form-group col-md-6 mb-3'),
                ),
                css_id='transfer-account-fields',
                style='display: none;'
            ),
            Field('notes', css_class='form-group mb-3', rows=3),
            Submit('submit', 'Save Transaction', css_class='btn btn-primary')
        )

        # Add JavaScript for transaction type handling
        self.helper.include_media = False

    def clean(self):
        cleaned_data = super().clean()
        transaction_type = cleaned_data.get('transaction_type')
        account = cleaned_data.get('account')
        to_account = cleaned_data.get('to_account')
        from_account = cleaned_data.get('from_account')

        if transaction_type == 'transfer':
            if not to_account or not from_account:
                raise forms.ValidationError(
                    'Both "from account" and "to account" are required for transfers.'
                )
            if to_account == from_account:
                raise forms.ValidationError(
                    'Transfer cannot be made to the same account.'
                )
        else:
            if not account:
                raise forms.ValidationError('Account is required for income and expense transactions.')

        return cleaned_data

    def save(self, commit=True):
        transaction = super().save(commit=False)
        if self.user:
            transaction.user = self.user
        if self.family_group:
            transaction.family_group = self.family_group

        if commit:
            transaction.save()
        return transaction


class TransactionFilterForm(forms.Form):
    """Form for filtering transactions."""
    PERIOD_CHOICES = [
        ('', 'All Time'),
        ('today', 'Today'),
        ('week', 'This Week'),
        ('month', 'This Month'),
        ('quarter', 'This Quarter'),
        ('year', 'This Year'),
        ('custom', 'Custom Range'),
    ]

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search transactions...'
        })
    )
    transaction_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Transaction.TRANSACTION_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    account = forms.ModelChoiceField(
        queryset=Account.objects.none(),
        required=False,
        empty_label="All Accounts",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    period = forms.ChoiceField(
        choices=PERIOD_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.family_group = kwargs.pop('family_group', None)
        super().__init__(*args, **kwargs)

        # Filter categories and accounts
        if self.family_group:
            self.fields['category'].queryset = Category.objects.filter(
                models.Q(family_group=self.family_group) |
                models.Q(is_system_category=True)
            )
            self.fields['account'].queryset = Account.objects.filter(
                family_group=self.family_group, is_active=True
            )
        elif self.user:
            self.fields['category'].queryset = Category.objects.filter(
                models.Q(family_group__isnull=True) |
                models.Q(is_system_category=True)
            )
            self.fields['account'].queryset = Account.objects.filter(
                owner=self.user, is_active=True
            )


class RecurringTransactionForm(forms.ModelForm):
    """Form for creating recurring transactions."""

    class Meta:
        model = RecurringTransaction
        fields = ['name', 'amount', 'description', 'transaction_type', 'category',
                 'account', 'frequency', 'start_date', 'end_date']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.family_group = kwargs.pop('family_group', None)
        super().__init__(*args, **kwargs)

        # Filter accounts and categories
        if self.family_group:
            self.fields['account'].queryset = Account.objects.filter(
                family_group=self.family_group, is_active=True
            )
            self.fields['category'].queryset = Category.objects.filter(
                models.Q(family_group=self.family_group) |
                models.Q(is_system_category=True)
            )
        elif self.user:
            self.fields['account'].queryset = Account.objects.filter(
                owner=self.user, is_active=True
            )
            self.fields['category'].queryset = Category.objects.filter(
                models.Q(family_group__isnull=True) |
                models.Q(is_system_category=True)
            )

        self.fields['end_date'].required = False

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('name', css_class='form-group mb-3'),
            Row(
                Column('transaction_type', css_class='form-group col-md-6 mb-3'),
                Column('amount', css_class='form-group col-md-6 mb-3'),
            ),
            Field('description', css_class='form-group mb-3'),
            Row(
                Column('category', css_class='form-group col-md-6 mb-3'),
                Column('account', css_class='form-group col-md-6 mb-3'),
            ),
            Row(
                Column('frequency', css_class='form-group col-md-6 mb-3'),
                Column('start_date', css_class='form-group col-md-6 mb-3'),
            ),
            Field('end_date', css_class='form-group mb-3'),
            Submit('submit', 'Save Recurring Transaction', css_class='btn btn-primary')
        )

    def save(self, commit=True):
        recurring_transaction = super().save(commit=False)
        if self.user:
            recurring_transaction.user = self.user
        if self.family_group:
            recurring_transaction.family_group = self.family_group

        # Set next due date to start date initially
        recurring_transaction.next_due_date = recurring_transaction.start_date

        if commit:
            recurring_transaction.save()
        return recurring_transaction


class BulkTransactionUploadForm(forms.Form):
    """Form for bulk transaction upload."""
    file = forms.FileField(
        label='Transaction File',
        help_text='Upload a CSV, Excel, or PDF file with transaction data (Max 10MB)',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls,.pdf'
        })
    )
    account = forms.ModelChoiceField(
        queryset=Account.objects.none(),
        empty_label="Select an account",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    has_header = forms.BooleanField(
        label='File has header row',
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.family_group = kwargs.pop('family_group', None)
        super().__init__(*args, **kwargs)

        # Filter accounts based on family group or user
        if self.family_group:
            accounts_qs = Account.objects.filter(
                family_group=self.family_group,
                is_active=True
            ).order_by('name')
        elif self.user:
            accounts_qs = Account.objects.filter(
                owner=self.user,
                family_group__isnull=True,
                is_active=True
            ).order_by('name')
        else:
            accounts_qs = Account.objects.none()

        self.fields['account'].queryset = accounts_qs

        # Add crispy forms helper
        from crispy_forms.helper import FormHelper
        from crispy_forms.layout import Layout, Field, Submit, Div, HTML

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.layout = Layout(
            Field('file', css_class='form-group mb-3'),
            Field('account', css_class='form-group mb-3'),
            Field('has_header', css_class='form-check'),
            HTML('<div class="alert alert-info mt-3"><strong>File Format:</strong> '
                 'CSV, Excel, or PDF with columns: Date, Description, Amount, Type (income/expense), Category (optional). '
                 'For PDFs, bank statements with transaction tables are supported.</div>'),
            Submit('submit', 'Upload Transactions', css_class='btn btn-primary')
        )

    def clean_file(self):
        """Validate uploaded file."""
        file = self.cleaned_data.get('file')
        if not file:
            raise forms.ValidationError('Please select a file to upload.')

        # Check file size (10MB limit)
        if file.size > 10 * 1024 * 1024:
            raise forms.ValidationError('File size must be less than 10MB.')

        # Check file extension
        file_name = file.name.lower()
        allowed_extensions = ['.csv', '.xlsx', '.xls', '.pdf']

        if not any(file_name.endswith(ext) for ext in allowed_extensions):
            raise forms.ValidationError(
                f'Unsupported file format. Please upload: {", ".join(allowed_extensions)}'
            )

        return file

    def clean_account(self):
        """Validate selected account."""
        account = self.cleaned_data.get('account')
        if not account:
            raise forms.ValidationError('Please select an account.')

        # Verify user has access to this account
        if self.family_group:
            if account.family_group != self.family_group:
                raise forms.ValidationError('Selected account is not accessible.')
        elif self.user:
            if account.owner != self.user or account.family_group is not None:
                raise forms.ValidationError('Selected account is not accessible.')

        return account