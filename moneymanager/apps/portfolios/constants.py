"""
Constants for the portfolio/investment system.
Centralized configuration for better maintainability.
"""
from decimal import Decimal
from typing import Dict, List, Tuple

# Asset Types
ASSET_TYPES = [
    ('stock', 'Stock'),
    ('etf', 'ETF'),
    ('mutual_fund', 'Mutual Fund'),
    ('bond', 'Bond'),
    ('crypto', 'Cryptocurrency'),
    ('commodity', 'Commodity'),
    ('reit', 'REIT'),
    ('fixed_deposit', 'Fixed Deposit'),
    ('ppf', 'PPF'),
    ('nps', 'NPS'),
    ('ulip', 'ULIP'),
    ('other', 'Other'),
]

# SIP Frequencies
SIP_FREQUENCIES = [
    ('daily', 'Daily'),
    ('weekly', 'Weekly'),
    ('monthly', 'Monthly'),
    ('quarterly', 'Quarterly'),
    ('semi_annual', 'Semi-Annual'),
    ('annual', 'Annual'),
]

# SIP Status
SIP_STATUS_CHOICES = [
    ('active', 'Active'),
    ('paused', 'Paused'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
]

# Transaction Types
TRANSACTION_TYPES = [
    ('buy', 'Buy'),
    ('sell', 'Sell'),
    ('dividend', 'Dividend'),
    ('split', 'Stock Split'),
    ('merger', 'Merger'),
    ('bonus', 'Bonus'),
    ('rights', 'Rights Issue'),
    ('spin_off', 'Spin-off'),
    ('other', 'Other'),
]

# Currencies
SUPPORTED_CURRENCIES = [
    ('INR', 'Indian Rupee'),
    ('USD', 'US Dollar'),
    ('EUR', 'Euro'),
    ('GBP', 'British Pound'),
    ('JPY', 'Japanese Yen'),
]

# Exchanges
INDIAN_EXCHANGES = [
    ('NSE', 'National Stock Exchange'),
    ('BSE', 'Bombay Stock Exchange'),
    ('MCX', 'Multi Commodity Exchange'),
    ('NCDEX', 'National Commodity & Derivatives Exchange'),
]

# Investment Limits
MIN_SIP_AMOUNT = Decimal('100.00')
MAX_SIP_AMOUNT = Decimal('10000000.00')  # 1 Crore
MIN_INVESTMENT_AMOUNT = Decimal('1.00')
MAX_INVESTMENT_AMOUNT = Decimal('100000000.00')  # 10 Crore

# Time Periods for Analysis
ANALYSIS_PERIODS = [
    ('1D', '1 Day'),
    ('1W', '1 Week'),
    ('1M', '1 Month'),
    ('3M', '3 Months'),
    ('6M', '6 Months'),
    ('1Y', '1 Year'),
    ('2Y', '2 Years'),
    ('3Y', '3 Years'),
    ('5Y', '5 Years'),
    ('10Y', '10 Years'),
    ('MAX', 'All Time'),
]

# Risk Categories
RISK_CATEGORIES = [
    ('very_low', 'Very Low'),
    ('low', 'Low'),
    ('moderate', 'Moderate'),
    ('high', 'High'),
    ('very_high', 'Very High'),
]

# Portfolio Allocation Strategies
ALLOCATION_STRATEGIES = [
    ('conservative', 'Conservative'),
    ('moderate', 'Moderate'),
    ('aggressive', 'Aggressive'),
    ('balanced', 'Balanced'),
    ('growth', 'Growth-Oriented'),
    ('income', 'Income-Oriented'),
]

# API Rate Limits (per minute/day)
API_RATE_LIMITS = {
    'alpha_vantage': {'per_minute': 5, 'per_day': 500},
    'yahoo_finance': {'per_minute': 60, 'per_day': 2000},
    'mutual_fund_api': {'per_minute': 30, 'per_day': 1000},
    'nse_api': {'per_minute': 10, 'per_day': 200},
}

# Cache Timeouts (in seconds)
CACHE_TIMEOUTS = {
    'price_data': 300,  # 5 minutes
    'asset_metadata': 3600,  # 1 hour
    'portfolio_summary': 600,  # 10 minutes
    'sip_calculations': 1800,  # 30 minutes
    'market_indices': 300,  # 5 minutes
}

# Price Update Frequencies
PRICE_UPDATE_FREQUENCIES = {
    'real_time': 60,  # 1 minute
    'intraday': 300,  # 5 minutes
    'daily': 3600,  # 1 hour
    'eod': 86400,  # 24 hours
}

# Financial Calculation Constants
DAYS_IN_YEAR = 365
TRADING_DAYS_IN_YEAR = 252
RISK_FREE_RATE = Decimal('0.06')  # 6% assumed risk-free rate
MARKET_RETURN = Decimal('0.12')  # 12% assumed market return

# Data Validation Rules
VALIDATION_RULES = {
    'symbol_max_length': 20,
    'name_max_length': 200,
    'description_max_length': 1000,
    'notes_max_length': 500,
    'max_decimal_places': 6,
    'max_price_digits': 12,
    'max_amount_digits': 15,
}

# File Upload Limits
FILE_UPLOAD_LIMITS = {
    'max_size_mb': 10,
    'allowed_extensions': ['csv', 'xlsx', 'xls'],
    'max_rows': 10000,
}

# Performance Thresholds
PERFORMANCE_THRESHOLDS = {
    'excellent': Decimal('20.0'),  # >20% annual return
    'good': Decimal('15.0'),       # 15-20% annual return
    'average': Decimal('10.0'),    # 10-15% annual return
    'poor': Decimal('5.0'),        # 5-10% annual return
    'very_poor': Decimal('0.0'),   # <5% annual return
}

# Alert Thresholds
ALERT_THRESHOLDS = {
    'price_change_percent': Decimal('10.0'),  # Alert if price changes >10%
    'portfolio_loss_percent': Decimal('15.0'), # Alert if portfolio loses >15%
    'sip_due_days': 7,  # Alert if SIP due within 7 days
}

# Default Pagination
DEFAULT_PAGINATION = {
    'portfolio_list': 10,
    'sip_list': 10,
    'transaction_list': 20,
    'investment_list': 15,
    'watchlist_assets': 25,
}

# Status Colors (for UI)
STATUS_COLORS = {
    'active': '#28a745',
    'paused': '#ffc107',
    'completed': '#17a2b8',
    'cancelled': '#dc3545',
    'positive': '#28a745',
    'negative': '#dc3545',
    'neutral': '#6c757d',
}

# Export Formats
EXPORT_FORMATS = [
    ('csv', 'CSV'),
    ('xlsx', 'Excel'),
    ('pdf', 'PDF'),
]

# Notification Types
NOTIFICATION_TYPES = [
    ('sip_due', 'SIP Due'),
    ('price_alert', 'Price Alert'),
    ('portfolio_milestone', 'Portfolio Milestone'),
    ('system_update', 'System Update'),
]