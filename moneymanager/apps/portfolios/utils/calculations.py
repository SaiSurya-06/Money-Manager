"""
Utility functions for portfolio and investment calculations.
Provides financial calculations, validation, and helper functions.
"""
import math
import numpy as np
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Optional, Tuple, Union
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging

from ..exceptions import CalculationError, ValidationError
from ..constants import DAYS_IN_YEAR, TRADING_DAYS_IN_YEAR, RISK_FREE_RATE

logger = logging.getLogger(__name__)


def safe_decimal(value: Union[str, int, float, Decimal], default: Decimal = Decimal('0')) -> Decimal:
    """Safely convert value to Decimal with error handling."""
    if value is None:
        return default
    
    try:
        return Decimal(str(value))
    except (TypeError, ValueError, OverflowError):
        logger.warning(f"Could not convert {value} to Decimal, using default {default}")
        return default


def round_decimal(value: Decimal, places: int = 2) -> Decimal:
    """Round Decimal to specified places."""
    if not isinstance(value, Decimal):
        value = safe_decimal(value)
    
    quantize_value = Decimal('0.1') ** places
    return value.quantize(quantize_value, rounding=ROUND_HALF_UP)


def calculate_percentage_change(old_value: Decimal, new_value: Decimal) -> Decimal:
    """Calculate percentage change between two values."""
    old_value = safe_decimal(old_value)
    new_value = safe_decimal(new_value)
    
    if old_value == 0:
        return Decimal('0') if new_value == 0 else Decimal('100')
    
    return ((new_value - old_value) / old_value) * 100


def calculate_annualized_return(start_value: Decimal, end_value: Decimal, 
                              start_date: date, end_date: date) -> Decimal:
    """Calculate annualized return between two dates."""
    start_value = safe_decimal(start_value)
    end_value = safe_decimal(end_value)
    
    if start_value == 0:
        return Decimal('0')
    
    days_held = (end_date - start_date).days
    if days_held <= 0:
        return Decimal('0')
    
    # Convert to float for power operation, then back to Decimal
    total_return = float(end_value / start_value)
    years_held = days_held / DAYS_IN_YEAR
    
    try:
        annualized_return = (total_return ** (1.0 / years_held) - 1) * 100
        return safe_decimal(annualized_return)
    except (ZeroDivisionError, OverflowError, ValueError):
        return Decimal('0')


def calculate_xirr(cash_flows: List[Tuple[date, Decimal]], guess: float = 0.1) -> Optional[Decimal]:
    """
    Calculate XIRR (Extended Internal Rate of Return) for irregular cash flows.
    
    Args:
        cash_flows: List of (date, amount) tuples. Investments should be negative.
        guess: Initial guess for the rate
    
    Returns:
        XIRR as a percentage, or None if calculation fails
    """
    if len(cash_flows) < 2:
        return None
    
    # Convert to numpy arrays for calculation
    dates = [cf[0] for cf in cash_flows]
    amounts = [float(cf[1]) for cf in cash_flows]
    
    # Convert dates to days from start
    start_date = min(dates)
    days = [(d - start_date).days for d in dates]
    
    def xnpv(rate, dates, amounts):
        """Calculate NPV for irregular cash flows."""
        return sum([amount / (1 + rate) ** (day / 365.0) for day, amount in zip(dates, amounts)])
    
    def xnpv_derivative(rate, dates, amounts):
        """Calculate derivative of XNPV for Newton-Raphson method."""
        return sum([-amount * day / 365.0 / (1 + rate) ** (day / 365.0 + 1) 
                   for day, amount in zip(dates, amounts)])
    
    # Newton-Raphson method to find IRR
    rate = guess
    for _ in range(100):  # Maximum 100 iterations
        try:
            npv = xnpv(rate, days, amounts)
            dnpv = xnpv_derivative(rate, days, amounts)
            
            if abs(npv) < 1e-6:  # Converged
                return safe_decimal(rate * 100)
            
            if abs(dnpv) < 1e-10:  # Avoid division by zero
                break
                
            rate = rate - npv / dnpv
            
            # Prevent unrealistic rates
            if rate < -0.99 or rate > 10:
                break
                
        except (ZeroDivisionError, OverflowError, ValueError):
            break
    
    return None


def calculate_volatility(returns: List[Decimal], period_days: int = TRADING_DAYS_IN_YEAR) -> Decimal:
    """Calculate volatility (standard deviation) of returns."""
    if len(returns) < 2:
        return Decimal('0')
    
    float_returns = [float(r) for r in returns]
    
    try:
        std_dev = np.std(float_returns, ddof=1)  # Sample standard deviation
        # Annualize volatility
        annualized_volatility = std_dev * math.sqrt(period_days)
        return safe_decimal(annualized_volatility * 100)
    except (ValueError, OverflowError):
        return Decimal('0')


def calculate_sharpe_ratio(portfolio_return: Decimal, volatility: Decimal, 
                         risk_free_rate: Decimal = RISK_FREE_RATE) -> Decimal:
    """Calculate Sharpe ratio."""
    portfolio_return = safe_decimal(portfolio_return)
    volatility = safe_decimal(volatility)
    risk_free_rate = safe_decimal(risk_free_rate) * 100  # Convert to percentage
    
    if volatility == 0:
        return Decimal('0')
    
    return (portfolio_return - risk_free_rate) / volatility


def calculate_sortino_ratio(portfolio_return: Decimal, downside_volatility: Decimal,
                          risk_free_rate: Decimal = RISK_FREE_RATE) -> Decimal:
    """Calculate Sortino ratio (focuses on downside risk)."""
    portfolio_return = safe_decimal(portfolio_return)
    downside_volatility = safe_decimal(downside_volatility)
    risk_free_rate = safe_decimal(risk_free_rate) * 100
    
    if downside_volatility == 0:
        return Decimal('0')
    
    return (portfolio_return - risk_free_rate) / downside_volatility


def calculate_maximum_drawdown(values: List[Decimal]) -> Decimal:
    """Calculate maximum drawdown from peak to trough."""
    if len(values) < 2:
        return Decimal('0')
    
    peak = values[0]
    max_drawdown = Decimal('0')
    
    for value in values:
        if value > peak:
            peak = value
        
        drawdown = (peak - value) / peak * 100 if peak > 0 else Decimal('0')
        max_drawdown = max(max_drawdown, drawdown)
    
    return max_drawdown


def calculate_beta(asset_returns: List[Decimal], market_returns: List[Decimal]) -> Decimal:
    """Calculate beta coefficient relative to market."""
    if len(asset_returns) != len(market_returns) or len(asset_returns) < 2:
        return Decimal('1')  # Default beta of 1
    
    try:
        asset_array = np.array([float(r) for r in asset_returns])
        market_array = np.array([float(r) for r in market_returns])
        
        covariance = np.cov(asset_array, market_array)[0][1]
        market_variance = np.var(market_array, ddof=1)
        
        if market_variance == 0:
            return Decimal('1')
        
        beta = covariance / market_variance
        return safe_decimal(beta)
        
    except (ValueError, ZeroDivisionError):
        return Decimal('1')


def calculate_compound_annual_growth_rate(start_value: Decimal, end_value: Decimal,
                                        years: float) -> Decimal:
    """Calculate CAGR."""
    start_value = safe_decimal(start_value)
    end_value = safe_decimal(end_value)
    
    if start_value == 0 or years <= 0:
        return Decimal('0')
    
    try:
        cagr = ((float(end_value / start_value) ** (1.0 / years)) - 1) * 100
        return safe_decimal(cagr)
    except (ValueError, OverflowError, ZeroDivisionError):
        return Decimal('0')


def get_next_sip_date(current_date: date, frequency: str) -> date:
    """Calculate next SIP investment date based on frequency."""
    if frequency == 'daily':
        return current_date + timedelta(days=1)
    elif frequency == 'weekly':
        return current_date + timedelta(weeks=1)
    elif frequency == 'monthly':
        return current_date + relativedelta(months=1)
    elif frequency == 'quarterly':
        return current_date + relativedelta(months=3)
    elif frequency == 'semi_annual':
        return current_date + relativedelta(months=6)
    elif frequency == 'annual':
        return current_date + relativedelta(years=1)
    else:
        # Default to monthly
        return current_date + relativedelta(months=1)


def validate_investment_amount(amount: Union[str, Decimal], min_amount: Decimal = None,
                             max_amount: Decimal = None) -> Decimal:
    """Validate and sanitize investment amount."""
    try:
        amount = safe_decimal(amount)
        
        if amount <= 0:
            raise ValidationError("Investment amount must be positive")
        
        if min_amount and amount < min_amount:
            raise ValidationError(f"Investment amount must be at least ₹{min_amount}")
        
        if max_amount and amount > max_amount:
            raise ValidationError(f"Investment amount cannot exceed ₹{max_amount}")
        
        return amount
        
    except Exception as e:
        raise ValidationError(f"Invalid investment amount: {str(e)}")


def validate_date_range(start_date: date, end_date: Optional[date] = None) -> bool:
    """Validate date range for investments."""
    if end_date and end_date <= start_date:
        raise ValidationError("End date must be after start date")
    
    # Allow past dates for historical SIP tracking
    return True


def format_currency(amount: Decimal, currency: str = 'INR') -> str:
    """Format amount as currency string."""
    amount = safe_decimal(amount)
    
    if currency == 'INR':
        # Indian number formatting
        amount_str = f"₹{amount:,.2f}"
        return amount_str
    else:
        return f"{currency} {amount:,.2f}"


def format_percentage(value: Decimal, decimal_places: int = 2) -> str:
    """Format decimal as percentage string."""
    value = safe_decimal(value)
    return f"{value:.{decimal_places}f}%"


def calculate_sip_maturity_amount(monthly_amount: Decimal, annual_rate: Decimal,
                                years: int) -> Decimal:
    """Calculate SIP maturity amount using compound interest formula."""
    monthly_amount = safe_decimal(monthly_amount)
    annual_rate = safe_decimal(annual_rate)
    
    if annual_rate == 0:
        return monthly_amount * 12 * years
    
    monthly_rate = annual_rate / 100 / 12
    months = years * 12
    
    try:
        # SIP maturity formula: P * [((1 + r)^n - 1) / r] * (1 + r)
        rate_plus_one = 1 + float(monthly_rate)
        numerator = (rate_plus_one ** months - 1)
        maturity_amount = float(monthly_amount) * numerator / float(monthly_rate) * rate_plus_one
        
        return safe_decimal(maturity_amount)
        
    except (ValueError, OverflowError, ZeroDivisionError):
        return monthly_amount * 12 * years


def calculate_lumpsum_future_value(principal: Decimal, annual_rate: Decimal,
                                 years: int) -> Decimal:
    """Calculate future value of lumpsum investment."""
    principal = safe_decimal(principal)
    annual_rate = safe_decimal(annual_rate)
    
    if annual_rate == 0:
        return principal
    
    try:
        future_value = float(principal) * ((1 + float(annual_rate / 100)) ** years)
        return safe_decimal(future_value)
    except (ValueError, OverflowError):
        return principal


def parse_date_string(date_string: str, formats: List[str] = None) -> date:
    """Parse date string with multiple format support."""
    if formats is None:
        formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%Y/%m/%d']
    
    for fmt in formats:
        try:
            return datetime.strptime(date_string.strip(), fmt).date()
        except ValueError:
            continue
    
    raise ValidationError(f"Unable to parse date: {date_string}")


def sanitize_string(value: str, max_length: int = None, allow_special: bool = True) -> str:
    """Sanitize string input for security."""
    if not isinstance(value, str):
        value = str(value)
    
    # Basic sanitization
    value = value.strip()
    
    if not allow_special:
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', 'script', 'javascript']
        for char in dangerous_chars:
            value = value.replace(char, '')
    
    if max_length:
        value = value[:max_length]
    
    return value