"""
Validation utilities for portfolio and investment data.
Provides comprehensive validation functions with security considerations.
"""
import re
from decimal import Decimal, InvalidOperation
from typing import Union, List, Dict, Any, Optional
from datetime import date, datetime
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import EmailValidator, URLValidator

from ..exceptions import ValidationError
from ..constants import (
    MIN_SIP_AMOUNT, MAX_SIP_AMOUNT, MIN_INVESTMENT_AMOUNT, MAX_INVESTMENT_AMOUNT,
    VALIDATION_RULES, ASSET_TYPES, SIP_FREQUENCIES, TRANSACTION_TYPES
)


class InvestmentValidator:
    """Comprehensive validation for investment data."""
    
    @staticmethod
    def validate_amount(amount: Union[str, Decimal, int, float], 
                       min_amount: Optional[Decimal] = None,
                       max_amount: Optional[Decimal] = None,
                       field_name: str = "amount") -> Decimal:
        """Validate monetary amounts."""
        try:
            if isinstance(amount, str):
                # Remove common currency symbols and spaces
                amount = re.sub(r'[₹$€£¥,\s]', '', amount)
            
            decimal_amount = Decimal(str(amount))
            
            if decimal_amount < 0:
                raise ValidationError(f"{field_name} cannot be negative")
            
            if decimal_amount == 0:
                raise ValidationError(f"{field_name} must be greater than zero")
            
            # Check minimum amount
            min_val = min_amount or MIN_INVESTMENT_AMOUNT
            if decimal_amount < min_val:
                raise ValidationError(f"{field_name} must be at least ₹{min_val}")
            
            # Check maximum amount
            max_val = max_amount or MAX_INVESTMENT_AMOUNT
            if decimal_amount > max_val:
                raise ValidationError(f"{field_name} cannot exceed ₹{max_val}")
            
            return decimal_amount
            
        except (InvalidOperation, ValueError, TypeError) as e:
            raise ValidationError(f"Invalid {field_name}: {str(e)}")
    
    @staticmethod
    def validate_sip_amount(amount: Union[str, Decimal]) -> Decimal:
        """Validate SIP amount with specific limits."""
        return InvestmentValidator.validate_amount(
            amount, MIN_SIP_AMOUNT, MAX_SIP_AMOUNT, "SIP amount"
        )
    
    @staticmethod
    def validate_price(price: Union[str, Decimal], field_name: str = "price") -> Decimal:
        """Validate price data."""
        try:
            if isinstance(price, str):
                price = re.sub(r'[₹$€£¥,\s]', '', price)
            
            decimal_price = Decimal(str(price))
            
            if decimal_price <= 0:
                raise ValidationError(f"{field_name} must be positive")
            
            # Check for unrealistic prices (basic sanity check)
            if decimal_price > Decimal('1000000'):  # 10 Lakh per unit
                raise ValidationError(f"{field_name} seems unrealistically high")
            
            return decimal_price
            
        except (InvalidOperation, ValueError, TypeError) as e:
            raise ValidationError(f"Invalid {field_name}: {str(e)}")
    
    @staticmethod
    def validate_percentage(percentage: Union[str, Decimal], 
                           min_val: Decimal = Decimal('-100'),
                           max_val: Decimal = Decimal('1000'),
                           field_name: str = "percentage") -> Decimal:
        """Validate percentage values."""
        try:
            if isinstance(percentage, str):
                percentage = percentage.replace('%', '').strip()
            
            decimal_percentage = Decimal(str(percentage))
            
            if decimal_percentage < min_val:
                raise ValidationError(f"{field_name} cannot be less than {min_val}%")
            
            if decimal_percentage > max_val:
                raise ValidationError(f"{field_name} cannot exceed {max_val}%")
            
            return decimal_percentage
            
        except (InvalidOperation, ValueError, TypeError) as e:
            raise ValidationError(f"Invalid {field_name}: {str(e)}")
    
    @staticmethod
    def validate_symbol(symbol: str) -> str:
        """Validate asset symbol."""
        if not symbol or not isinstance(symbol, str):
            raise ValidationError("Symbol is required")
        
        symbol = symbol.strip().upper()
        
        # Check length
        if len(symbol) > VALIDATION_RULES['symbol_max_length']:
            raise ValidationError(f"Symbol too long (max {VALIDATION_RULES['symbol_max_length']} chars)")
        
        # Check format - alphanumeric with some special characters
        if not re.match(r'^[A-Z0-9._-]+$', symbol):
            raise ValidationError("Symbol contains invalid characters")
        
        return symbol
    
    @staticmethod
    def validate_name(name: str, field_name: str = "name") -> str:
        """Validate names (asset, portfolio, SIP names)."""
        if not name or not isinstance(name, str):
            raise ValidationError(f"{field_name} is required")
        
        name = name.strip()
        
        # Check length
        max_length = VALIDATION_RULES['name_max_length']
        if len(name) > max_length:
            raise ValidationError(f"{field_name} too long (max {max_length} chars)")
        
        # Basic XSS protection
        dangerous_patterns = [
            r'<script.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<.*?>',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                raise ValidationError(f"{field_name} contains invalid content")
        
        return name
    
    @staticmethod
    def validate_date(input_date: Union[str, date, datetime], 
                     field_name: str = "date",
                     allow_future: bool = False,
                     allow_past: bool = True) -> date:
        """Validate dates with various constraints."""
        if isinstance(input_date, str):
            try:
                # Try multiple date formats
                formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']
                parsed_date = None
                
                for fmt in formats:
                    try:
                        parsed_date = datetime.strptime(input_date.strip(), fmt).date()
                        break
                    except ValueError:
                        continue
                
                if not parsed_date:
                    raise ValidationError(f"Invalid {field_name} format")
                
                input_date = parsed_date
                
            except Exception as e:
                raise ValidationError(f"Invalid {field_name}: {str(e)}")
        
        elif isinstance(input_date, datetime):
            input_date = input_date.date()
        
        if not isinstance(input_date, date):
            raise ValidationError(f"Invalid {field_name} type")
        
        today = date.today()
        
        if not allow_future and input_date > today:
            raise ValidationError(f"{field_name} cannot be in the future")
        
        if not allow_past and input_date < today:
            raise ValidationError(f"{field_name} cannot be in the past")
        
        # Reasonable date range check (not before 1900 or too far in future)
        if input_date.year < 1900:
            raise ValidationError(f"{field_name} is too far in the past")
        
        if input_date.year > today.year + 50:
            raise ValidationError(f"{field_name} is too far in the future")
        
        return input_date
    
    @staticmethod
    def validate_choice(value: str, choices: List[tuple], field_name: str) -> str:
        """Validate choice fields."""
        if not value:
            raise ValidationError(f"{field_name} is required")
        
        valid_choices = [choice[0] for choice in choices]
        
        if value not in valid_choices:
            raise ValidationError(f"Invalid {field_name}: {value}")
        
        return value
    
    @staticmethod
    def validate_asset_type(asset_type: str) -> str:
        """Validate asset type."""
        return InvestmentValidator.validate_choice(
            asset_type, ASSET_TYPES, "asset type"
        )
    
    @staticmethod
    def validate_sip_frequency(frequency: str) -> str:
        """Validate SIP frequency."""
        return InvestmentValidator.validate_choice(
            frequency, SIP_FREQUENCIES, "SIP frequency"
        )
    
    @staticmethod
    def validate_transaction_type(transaction_type: str) -> str:
        """Validate transaction type."""
        return InvestmentValidator.validate_choice(
            transaction_type, TRANSACTION_TYPES, "transaction type"
        )
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email address."""
        if not email:
            raise ValidationError("Email is required")
        
        validator = EmailValidator()
        try:
            validator(email)
            return email.strip().lower()
        except DjangoValidationError:
            raise ValidationError("Invalid email format")
    
    @staticmethod
    def validate_url(url: str, field_name: str = "URL") -> str:
        """Validate URL."""
        if not url:
            return ""
        
        validator = URLValidator()
        try:
            validator(url)
            return url.strip()
        except DjangoValidationError:
            raise ValidationError(f"Invalid {field_name} format")
    
    @staticmethod
    def validate_quantity(quantity: Union[str, Decimal], field_name: str = "quantity") -> Decimal:
        """Validate quantity/units."""
        try:
            if isinstance(quantity, str):
                quantity = quantity.replace(',', '').strip()
            
            decimal_quantity = Decimal(str(quantity))
            
            if decimal_quantity <= 0:
                raise ValidationError(f"{field_name} must be positive")
            
            # Check for reasonable limits
            if decimal_quantity > Decimal('1000000000'):  # 100 crores units
                raise ValidationError(f"{field_name} exceeds reasonable limit")
            
            return decimal_quantity
            
        except (InvalidOperation, ValueError, TypeError) as e:
            raise ValidationError(f"Invalid {field_name}: {str(e)}")
    
    @staticmethod
    def validate_notes(notes: str, field_name: str = "notes") -> str:
        """Validate notes/description fields."""
        if not notes:
            return ""
        
        notes = notes.strip()
        
        max_length = VALIDATION_RULES['notes_max_length']
        if len(notes) > max_length:
            raise ValidationError(f"{field_name} too long (max {max_length} chars)")
        
        # Basic XSS protection
        dangerous_patterns = [
            r'<script.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, notes, re.IGNORECASE):
                raise ValidationError(f"{field_name} contains invalid content")
        
        return notes


class DataSanitizer:
    """Sanitize input data for security."""
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Remove HTML tags and dangerous content."""
        if not text:
            return ""
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove dangerous JavaScript
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
        
        # Remove event handlers
        text = re.sub(r'on\w+\s*=\s*["\']?[^"\']*["\']?', '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe file operations."""
        if not filename:
            return "unnamed_file"
        
        # Remove directory traversal attempts
        filename = filename.replace('..', '').replace('/', '').replace('\\', '')
        
        # Keep only alphanumeric, dots, hyphens, and underscores
        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        
        # Limit length
        if len(filename) > 100:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:95] + ('.' + ext if ext else '')
        
        return filename
    
    @staticmethod
    def sanitize_sql_input(text: str) -> str:
        """Basic SQL injection prevention."""
        if not text:
            return ""
        
        # Remove common SQL injection patterns
        dangerous_sql = [
            r'union\s+select',
            r'drop\s+table',
            r'delete\s+from',
            r'insert\s+into',
            r'update\s+.*\s+set',
            r'exec\s*\(',
            r'execute\s*\(',
            r'--',
            r'/\*.*\*/',
        ]
        
        text_lower = text.lower()
        for pattern in dangerous_sql:
            if re.search(pattern, text_lower):
                return ""  # Return empty string for suspicious input
        
        return text


def validate_bulk_upload_data(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate bulk upload data."""
    results = {
        'valid_rows': [],
        'invalid_rows': [],
        'errors': [],
        'summary': {
            'total_rows': len(data),
            'valid_rows': 0,
            'invalid_rows': 0,
        }
    }
    
    for i, row in enumerate(data, 1):
        try:
            # Validate each row based on expected fields
            validated_row = {}
            
            # Example validation for SIP data
            if 'amount' in row:
                validated_row['amount'] = InvestmentValidator.validate_sip_amount(row['amount'])
            
            if 'date' in row:
                validated_row['date'] = InvestmentValidator.validate_date(row['date'])
            
            if 'symbol' in row:
                validated_row['symbol'] = InvestmentValidator.validate_symbol(row['symbol'])
            
            # Add more validations as needed
            results['valid_rows'].append({'row_number': i, 'data': validated_row})
            results['summary']['valid_rows'] += 1
            
        except ValidationError as e:
            results['invalid_rows'].append({
                'row_number': i,
                'data': row,
                'errors': [str(e)]
            })
            results['errors'].append(f"Row {i}: {str(e)}")
            results['summary']['invalid_rows'] += 1
    
    return results