from django import forms
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, Div, HTML
from crispy_forms.bootstrap import InlineRadios
from datetime import date, datetime
from decimal import Decimal
import requests

from .models import Portfolio, Asset, Holding, Transaction as PortfolioTransaction, Watchlist, SIP, SIPInvestment
from moneymanager.apps.core.models import FamilyGroup


class PortfolioForm(forms.ModelForm):
    """Form for creating and updating portfolios."""
    
    class Meta:
        model = Portfolio
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'My Investment Portfolio'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Brief description of this portfolio...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='col-md-8'),
                css_class='row'
            ),
            'description',
            Div(
                Submit('submit', 'Save Portfolio', css_class='btn btn-primary'),
                css_class='d-grid gap-2 d-md-flex justify-content-md-end'
            )
        )


class AssetSearchForm(forms.Form):
    """Form for searching and adding assets."""
    ASSET_TYPE_CHOICES = [
        ('', 'Select Asset Type'),
        ('stock', 'Stock'),
        ('mutual_fund', 'Mutual Fund'),
        ('etf', 'ETF'),
    ]
    
    asset_type = forms.ChoiceField(
        choices=ASSET_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    symbol_or_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter symbol (RELIANCE) or name (Reliance Industries)'
        }),
        help_text="For stocks: Enter NSE/BSE symbol. For Mutual Funds: Enter scheme name or code."
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('asset_type', css_class='col-md-4'),
                Column('symbol_or_name', css_class='col-md-8'),
                css_class='row'
            ),
            Div(
                Submit('search', 'Search Asset', css_class='btn btn-primary'),
                css_class='d-grid gap-2 d-md-flex justify-content-md-end'
            )
        )


class AssetForm(forms.ModelForm):
    """Form for manually adding/editing assets."""
    
    class Meta:
        model = Asset
        fields = ['symbol', 'name', 'asset_type', 'exchange', 'current_price']
        widgets = {
            'symbol': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'RELIANCE, TCS, etc.'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full company/fund name'
            }),
            'asset_type': forms.Select(attrs={'class': 'form-select'}),
            'exchange': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'NSE, BSE'
            }),
            'current_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('symbol', css_class='col-md-4'),
                Column('name', css_class='col-md-8'),
                css_class='row'
            ),
            Row(
                Column('asset_type', css_class='col-md-4'),
                Column('exchange', css_class='col-md-4'),
                Column('current_price', css_class='col-md-4'),
                css_class='row'
            ),
            Div(
                Submit('submit', 'Save Asset', css_class='btn btn-primary'),
                css_class='d-grid gap-2 d-md-flex justify-content-md-end'
            )
        )
    
    def clean_symbol(self):
        symbol = self.cleaned_data['symbol'].upper().strip()
        if Asset.objects.filter(symbol=symbol).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise ValidationError(f"Asset with symbol '{symbol}' already exists.")
        return symbol


class HoldingForm(forms.ModelForm):
    """Form for adding holdings to a portfolio."""
    asset = forms.ModelChoiceField(
        queryset=Asset.objects.filter(is_active=True).order_by('symbol'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Select an asset"
    )
    
    class Meta:
        model = Holding
        fields = ['asset', 'quantity', 'average_cost']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.000001',
                'placeholder': '0.000000'
            }),
            'average_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.portfolio = kwargs.pop('portfolio', None)
        super().__init__(*args, **kwargs)
        
        # Filter out assets already in this portfolio
        if self.portfolio:
            existing_assets = self.portfolio.holdings.filter(is_active=True).values_list('asset', flat=True)
            self.fields['asset'].queryset = Asset.objects.filter(
                is_active=True
            ).exclude(id__in=existing_assets).order_by('symbol')
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'asset',
            Row(
                Column('quantity', css_class='col-md-6'),
                Column('average_cost', css_class='col-md-6'),
                css_class='row'
            ),
            HTML("""
                <div class="alert alert-info mt-3">
                    <i class="bi bi-info-circle me-2"></i>
                    <strong>Note:</strong> Enter the average price you paid per unit. 
                    The system will calculate total cost basis and current P&L automatically.
                </div>
            """),
            Div(
                Submit('submit', 'Add Holding', css_class='btn btn-primary'),
                css_class='d-grid gap-2 d-md-flex justify-content-md-end'
            )
        )
    
    def clean(self):
        cleaned_data = super().clean()
        asset = cleaned_data.get('asset')
        quantity = cleaned_data.get('quantity')
        average_cost = cleaned_data.get('average_cost')
        
        if asset and quantity and average_cost:
            # Check if holding already exists for this asset in the portfolio
            if self.portfolio and not self.instance.pk:
                if self.portfolio.holdings.filter(asset=asset, is_active=True).exists():
                    raise ValidationError(f"You already have holdings for {asset.symbol} in this portfolio.")
            
            # Calculate total cost basis
            total_cost = quantity * average_cost
            cleaned_data['total_cost_basis'] = total_cost
        
        return cleaned_data
    
    def save(self, commit=True):
        holding = super().save(commit=False)
        if self.portfolio:
            holding.portfolio = self.portfolio
        
        # Calculate total cost basis
        holding.total_cost_basis = holding.quantity * holding.average_cost
        
        if commit:
            holding.save()
            # Update values based on current price
            holding.update_values()
        
        return holding


class TransactionForm(forms.ModelForm):
    """Form for portfolio transactions."""
    
    class Meta:
        model = PortfolioTransaction
        fields = ['transaction_type', 'date', 'quantity', 'price', 'fees', 'notes']
        widgets = {
            'transaction_type': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'max': date.today().isoformat()
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.000001',
                'placeholder': '0.000000'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'fees': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00',
                'value': '0.00'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional notes about this transaction...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.holding = kwargs.pop('holding', None)
        super().__init__(*args, **kwargs)
        
        # Set default date to today
        if not self.instance.pk:
            self.fields['date'].initial = date.today()
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('transaction_type', css_class='col-md-6'),
                Column('date', css_class='col-md-6'),
                css_class='row'
            ),
            Row(
                Column('quantity', css_class='col-md-4'),
                Column('price', css_class='col-md-4'),
                Column('fees', css_class='col-md-4'),
                css_class='row'
            ),
            'notes',
            HTML("""
                <div class="alert alert-warning mt-3">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    <strong>Important:</strong> Adding transactions will recalculate your average cost 
                    and update P&L automatically.
                </div>
            """),
            Div(
                Submit('submit', 'Save Transaction', css_class='btn btn-primary'),
                css_class='d-grid gap-2 d-md-flex justify-content-md-end'
            )
        )
    
    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity')
        price = cleaned_data.get('price')
        transaction_type = cleaned_data.get('transaction_type')
        
        if quantity and price:
            # Calculate total amount
            fees = cleaned_data.get('fees') or Decimal('0.00')
            total_amount = (quantity * price) + fees
            cleaned_data['total_amount'] = total_amount
        
        # Validate sell transactions
        if transaction_type == 'sell' and self.holding and quantity:
            if quantity > self.holding.quantity:
                raise ValidationError(
                    f"Cannot sell {quantity} units. You only have {self.holding.quantity} units available."
                )
        
        return cleaned_data
    
    def save(self, commit=True):
        transaction = super().save(commit=False)
        if self.holding:
            transaction.holding = self.holding
            transaction.user = self.holding.portfolio.user
        
        # Set total amount
        if hasattr(self, 'cleaned_data'):
            transaction.total_amount = self.cleaned_data.get('total_amount', 0)
        
        if commit:
            transaction.save()
        
        return transaction


class BulkHoldingUploadForm(forms.Form):
    """Form for bulk upload of holdings via CSV."""
    portfolio = forms.ModelChoiceField(
        queryset=Portfolio.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    csv_file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv'
        }),
        help_text="Upload a CSV file with columns: Symbol, Name, Asset Type, Quantity, Average Cost"
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['portfolio'].queryset = Portfolio.objects.filter(
                user=user, is_active=True
            ).order_by('name')
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'portfolio',
            'csv_file',
            HTML("""
                <div class="alert alert-info mt-3">
                    <h6><i class="bi bi-info-circle me-2"></i>CSV Format:</h6>
                    <p>Your CSV should have these columns (with headers):</p>
                    <ul>
                        <li><strong>Symbol:</strong> Stock/MF symbol (e.g., RELIANCE, TCS)</li>
                        <li><strong>Name:</strong> Full name (e.g., Reliance Industries Ltd)</li>
                        <li><strong>Asset_Type:</strong> stock, mutual_fund, or etf</li>
                        <li><strong>Quantity:</strong> Number of units you own</li>
                        <li><strong>Average_Cost:</strong> Average price per unit</li>
                    </ul>
                </div>
            """),
            Div(
                Submit('upload', 'Upload Holdings', css_class='btn btn-primary'),
                css_class='d-grid gap-2 d-md-flex justify-content-md-end'
            )
        )
    
    def clean_csv_file(self):
        csv_file = self.cleaned_data['csv_file']
        if not csv_file.name.endswith('.csv'):
            raise ValidationError("Please upload a valid CSV file.")
        return csv_file


class WatchlistForm(forms.ModelForm):
    """Form for creating and updating watchlists."""
    
    class Meta:
        model = Watchlist
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'My Watchlist'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description of this watchlist...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'name',
            'description',
            Div(
                Submit('submit', 'Save Watchlist', css_class='btn btn-primary'),
                css_class='d-grid gap-2 d-md-flex justify-content-md-end'
            )
        )


class PriceUpdateForm(forms.Form):
    """Form for manual price updates."""
    assets = forms.ModelMultipleChoiceField(
        queryset=Asset.objects.filter(is_active=True).order_by('symbol'),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Only show assets that user has holdings for
            user_assets = Asset.objects.filter(
                holdings__portfolio__user=user,
                holdings__is_active=True,
                is_active=True
            ).distinct().order_by('symbol')
            self.fields['assets'].queryset = user_assets
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML("""
                <div class="alert alert-info">
                    <i class="bi bi-info-circle me-2"></i>
                    Select assets to update prices for. This will fetch latest prices from the market.
                </div>
            """),
            'assets',
            Div(
                Submit('update', 'Update Prices', css_class='btn btn-success'),
                css_class='d-grid gap-2 d-md-flex justify-content-md-end'
            )
        )


class SIPForm(forms.ModelForm):
    """Form for creating and managing SIPs."""
    asset = forms.ModelChoiceField(
        queryset=Asset.objects.filter(is_active=True, asset_type='mutual_fund').order_by('name'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Select a Mutual Fund"
    )
    
    class Meta:
        model = SIP
        fields = ['name', 'portfolio', 'asset', 'amount', 'frequency', 'start_date', 'end_date', 'auto_invest']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'SIP for HDFC Top 100 Fund'
            }),
            'portfolio': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '100',
                'min': '100',
                'placeholder': '5000'
            }),
            'frequency': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'auto_invest': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['portfolio'].queryset = Portfolio.objects.filter(
                user=user, is_active=True
            ).order_by('name')
        
        # Set default start date to today
        if not self.instance.pk:
            self.fields['start_date'].initial = date.today()
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'name',
            Row(
                Column('portfolio', css_class='col-md-6'),
                Column('asset', css_class='col-md-6'),
                css_class='row'
            ),
            Row(
                Column('amount', css_class='col-md-4'),
                Column('frequency', css_class='col-md-4'),
                Column(
                    Field('auto_invest', template='custom_checkbox_field.html'),
                    css_class='col-md-4'
                ),
                css_class='row'
            ),
            Row(
                Column('start_date', css_class='col-md-6'),
                Column('end_date', css_class='col-md-6'),
                css_class='row'
            ),
            HTML("""
                <div class="alert alert-info mt-3">
                    <i class="bi bi-info-circle me-2"></i>
                    <strong>SIP Benefits:</strong>
                    <ul class="mb-0 mt-2">
                        <li>Rupee cost averaging reduces investment risk</li>
                        <li>Disciplined investment approach</li>
                        <li>Auto-invest option for convenience</li>
                        <li>Real-time P&L tracking with XIRR calculation</li>
                    </ul>
                </div>
            """),
            Div(
                Submit('submit', 'Create SIP', css_class='btn btn-success'),
                css_class='d-grid gap-2 d-md-flex justify-content-md-end'
            )
        )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        amount = cleaned_data.get('amount')
        
        # Allow past start dates for tracking existing SIPs
        # No validation needed for start_date - users should be able to track existing SIPs
        
        if start_date and end_date and end_date <= start_date:
            raise ValidationError({'end_date': 'End date must be after start date.'})
        
        if amount and amount < 100:
            raise ValidationError({'amount': 'Minimum SIP amount is ₹100.'})
        
        return cleaned_data
    
    def save(self, commit=True):
        sip = super().save(commit=False)
        
        # Let the model's save method calculate next_investment_date
        # based on start_date and frequency
        
        if commit:
            sip.save()
        
        return sip


class SIPInvestmentForm(forms.ModelForm):
    """Form for adding individual SIP investments."""
    
    class Meta:
        model = SIPInvestment
        fields = ['date', 'amount', 'nav_price', 'transaction_id', 'fees', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'max': date.today().isoformat()
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '5000.00'
            }),
            'nav_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001',
                'placeholder': '45.6780'
            }),
            'transaction_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'TXN123456789'
            }),
            'fees': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00',
                'value': '0.00'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional notes about this investment...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.sip = kwargs.pop('sip', None)
        super().__init__(*args, **kwargs)
        
        # Pre-fill amount from SIP
        if self.sip and not self.instance.pk:
            self.fields['amount'].initial = self.sip.amount
            self.fields['date'].initial = date.today()
            
            # Try to get current NAV price
            if self.sip.asset and self.sip.asset.current_price:
                self.fields['nav_price'].initial = self.sip.asset.current_price
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('date', css_class='col-md-4'),
                Column('amount', css_class='col-md-4'),
                Column('nav_price', css_class='col-md-4'),
                css_class='row'
            ),
            Row(
                Column('transaction_id', css_class='col-md-6'),
                Column('fees', css_class='col-md-6'),
                css_class='row'
            ),
            'notes',
            HTML(f"""
                <div class="alert alert-success mt-3">
                    <i class="bi bi-check-circle me-2"></i>
                    <strong>Recording Investment for:</strong> {self.sip.name if self.sip else 'SIP'}
                    <br><small>Units will be calculated automatically: Amount ÷ NAV Price</small>
                </div>
            """),
            Div(
                Submit('submit', 'Record Investment', css_class='btn btn-success'),
                css_class='d-grid gap-2 d-md-flex justify-content-md-end'
            )
        )
    
    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get('amount')
        nav_price = cleaned_data.get('nav_price')
        investment_date = cleaned_data.get('date')
        
        if amount and amount <= 0:
            raise ValidationError({'amount': 'Investment amount must be greater than 0.'})
        
        if nav_price and nav_price <= 0:
            raise ValidationError({'nav_price': 'NAV price must be greater than 0.'})
        
        if investment_date and investment_date > date.today():
            raise ValidationError({'date': 'Investment date cannot be in the future.'})
        
        # Check if investment already exists for this date
        if self.sip and investment_date and not self.instance.pk:
            if self.sip.investments.filter(date=investment_date).exists():
                raise ValidationError({'date': f'Investment already recorded for {investment_date}.'})
        
        return cleaned_data
    
    def save(self, commit=True):
        investment = super().save(commit=False)
        
        if self.sip:
            investment.sip = self.sip
        
        if commit:
            investment.save()
        
        return investment


class BulkSIPInvestmentForm(forms.Form):
    """Form for bulk upload of SIP investments via CSV."""
    sip = forms.ModelChoiceField(
        queryset=SIP.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    csv_file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv'
        }),
        help_text="Upload CSV with columns: Date, Amount, NAV_Price, Transaction_ID, Fees, Notes"
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['sip'].queryset = SIP.objects.filter(
                user=user
            ).order_by('-created_at')
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'sip',
            'csv_file',
            HTML("""
                <div class="alert alert-info mt-3">
                    <h6><i class="bi bi-info-circle me-2"></i>CSV Format for SIP Investments:</h6>
                    <p>Your CSV should have these columns (with headers):</p>
                    <ul>
                        <li><strong>Date:</strong> Investment date (YYYY-MM-DD format)</li>
                        <li><strong>Amount:</strong> Investment amount (e.g., 5000)</li>
                        <li><strong>NAV_Price:</strong> NAV price on that date (e.g., 45.6780)</li>
                        <li><strong>Transaction_ID:</strong> Optional transaction reference</li>
                        <li><strong>Fees:</strong> Optional fees (default 0)</li>
                        <li><strong>Notes:</strong> Optional notes</li>
                    </ul>
                </div>
            """),
            Div(
                Submit('upload', 'Upload SIP Investments', css_class='btn btn-success'),
                css_class='d-grid gap-2 d-md-flex justify-content-md-end'
            )
        )
    
    def clean_csv_file(self):
        csv_file = self.cleaned_data['csv_file']
        if not csv_file.name.endswith('.csv'):
            raise ValidationError("Please upload a valid CSV file.")
        return csv_file


class SIPHistoryImportForm(forms.Form):
    """Form for importing historical SIP investments via CSV."""
    portfolio = forms.ModelChoiceField(
        queryset=Portfolio.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Select the portfolio to import SIPs into"
    )
    csv_file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv'
        }),
        help_text="Upload CSV with your complete SIP investment history"
    )
    create_missing_sips = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Automatically create SIPs if they don't exist"
    )
    update_existing = forms.BooleanField(
        initial=False,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Update existing investments if found"
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['portfolio'].queryset = Portfolio.objects.filter(
                user=user, is_active=True
            ).order_by('name')
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'portfolio',
            'csv_file',
            Row(
                Column(
                    Field('create_missing_sips', template='custom_checkbox_field.html'),
                    css_class='col-md-6'
                ),
                Column(
                    Field('update_existing', template='custom_checkbox_field.html'),
                    css_class='col-md-6'
                ),
                css_class='row'
            ),
            HTML("""
                <div class="alert alert-info mt-3">
                    <h6><i class="bi bi-info-circle me-2"></i>CSV Import Features:</h6>
                    <ul class="mb-0">
                        <li><strong>Smart Fund Matching:</strong> Automatically matches fund names to our database</li>
                        <li><strong>Historical Analysis:</strong> Complete P&L from your first investment</li>
                        <li><strong>Real-time Updates:</strong> Current values calculated with live NAV prices</li>
                        <li><strong>Bulk Import:</strong> Import multiple SIPs and years of data at once</li>
                    </ul>
                </div>
            """),
            Div(
                Submit('import', 'Import SIP History', css_class='btn btn-success'),
                css_class='d-grid gap-2 d-md-flex justify-content-md-end'
            )
        )
    
    def clean_csv_file(self):
        csv_file = self.cleaned_data['csv_file']
        if not csv_file.name.endswith('.csv'):
            raise ValidationError("Please upload a valid CSV file.")
        return csv_file
