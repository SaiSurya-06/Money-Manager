from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()

@register.filter
def div(value, arg):
    """Divides the value by the argument."""
    try:
        # Convert both values to Decimal for precise division
        dividend = Decimal(str(value)) if value is not None else Decimal('0')
        divisor = Decimal(str(arg)) if arg is not None else Decimal('1')
        
        if divisor == 0:
            return 0
        
        result = dividend / divisor
        return float(result)
    except (ValueError, InvalidOperation, TypeError):
        return 0

@register.filter
def multiply(value, arg):
    """Multiplies the value by the argument."""
    try:
        # Convert both values to Decimal for precise multiplication
        multiplicand = Decimal(str(value)) if value is not None else Decimal('0')
        multiplier = Decimal(str(arg)) if arg is not None else Decimal('1')
        
        result = multiplicand * multiplier
        return float(result)
    except (ValueError, InvalidOperation, TypeError):
        return 0

@register.filter
def subtract(value, arg):
    """Subtracts the argument from the value."""
    try:
        minuend = Decimal(str(value)) if value is not None else Decimal('0')
        subtrahend = Decimal(str(arg)) if arg is not None else Decimal('0')
        
        result = minuend - subtrahend
        return float(result)
    except (ValueError, InvalidOperation, TypeError):
        return 0

@register.filter
def percentage(value, total):
    """Calculates percentage of value over total."""
    try:
        val = Decimal(str(value)) if value is not None else Decimal('0')
        tot = Decimal(str(total)) if total is not None else Decimal('1')
        
        if tot == 0:
            return 0
        
        result = (val / tot) * 100
        return float(result)
    except (ValueError, InvalidOperation, TypeError):
        return 0