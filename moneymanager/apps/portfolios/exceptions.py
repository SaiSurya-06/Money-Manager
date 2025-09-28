"""
Custom exceptions for the portfolio/investment system.
Provides specific error types for better error handling and debugging.
"""
from typing import Optional, Dict, Any


class InvestmentError(Exception):
    """Base exception for investment-related errors."""
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class PortfolioError(InvestmentError):
    """Portfolio-specific errors."""
    pass


class SIPError(InvestmentError):
    """SIP-specific errors."""
    pass


class AssetError(InvestmentError):
    """Asset-related errors."""
    pass


class PriceDataError(InvestmentError):
    """Price data retrieval errors."""
    pass


class CalculationError(InvestmentError):
    """Investment calculation errors."""
    pass


class ValidationError(InvestmentError):
    """Data validation errors."""
    pass


class APIError(InvestmentError):
    """External API errors."""
    def __init__(self, message: str, api_name: str, status_code: Optional[int] = None, 
                 response_data: Optional[Dict] = None):
        self.api_name = api_name
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(message, f"API_{api_name.upper()}_ERROR", {
            'api_name': api_name,
            'status_code': status_code,
            'response_data': response_data
        })


class RateLimitError(APIError):
    """API rate limit exceeded errors."""
    def __init__(self, api_name: str, retry_after: Optional[int] = None):
        self.retry_after = retry_after
        message = f"Rate limit exceeded for {api_name}"
        if retry_after:
            message += f". Retry after {retry_after} seconds."
        super().__init__(message, api_name)


class InsufficientDataError(InvestmentError):
    """Insufficient data for calculations."""
    pass


class BusinessRuleError(InvestmentError):
    """Business rule violation errors."""
    pass


# Specific investment errors
class InsufficientFundsError(BusinessRuleError):
    """Insufficient funds for investment."""
    pass


class InvalidInvestmentDateError(ValidationError):
    """Invalid investment date."""
    pass


class DuplicateInvestmentError(ValidationError):
    """Duplicate investment record."""
    pass


class AssetNotFoundError(AssetError):
    """Asset not found in database or external sources."""
    pass


class PriceNotAvailableError(PriceDataError):
    """Price data not available for asset."""
    pass


class CalculationNotPossibleError(CalculationError):
    """Cannot perform calculation with available data."""
    pass