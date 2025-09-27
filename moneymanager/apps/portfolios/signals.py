from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.core.cache import cache
from .models import Portfolio, Holding, Transaction as PortfolioTransaction, Asset
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=PortfolioTransaction)
def update_holding_on_transaction_save(sender, instance, created, **kwargs):
    """Update holding when portfolio transaction is saved."""
    try:
        if instance.holding:
            instance.holding.calculate_average_cost()
            instance.holding.update_values()
            instance.holding.portfolio.update_portfolio_values()

        # Clear related caches
        _clear_portfolio_caches(instance.holding.portfolio if instance.holding else None)

    except Exception as e:
        logger.error(f"Error updating holding for portfolio transaction {instance.id}: {str(e)}")


@receiver(post_delete, sender=PortfolioTransaction)
def update_holding_on_transaction_delete(sender, instance, **kwargs):
    """Update holding when portfolio transaction is deleted."""
    try:
        if instance.holding:
            instance.holding.calculate_average_cost()
            instance.holding.update_values()
            instance.holding.portfolio.update_portfolio_values()

        # Clear related caches
        _clear_portfolio_caches(instance.holding.portfolio if instance.holding else None)

    except Exception as e:
        logger.error(f"Error updating holding after portfolio transaction delete {instance.id}: {str(e)}")


@receiver(post_save, sender=Holding)
def update_portfolio_on_holding_save(sender, instance, **kwargs):
    """Update portfolio totals when holding is saved."""
    try:
        instance.portfolio.update_portfolio_values()
        _clear_portfolio_caches(instance.portfolio)

    except Exception as e:
        logger.error(f"Error updating portfolio for holding {instance.id}: {str(e)}")


@receiver(post_delete, sender=Holding)
def update_portfolio_on_holding_delete(sender, instance, **kwargs):
    """Update portfolio totals when holding is deleted."""
    try:
        instance.portfolio.update_portfolio_values()
        _clear_portfolio_caches(instance.portfolio)

    except Exception as e:
        logger.error(f"Error updating portfolio after holding delete {instance.id}: {str(e)}")


@receiver(post_save, sender=Asset)
def update_holdings_on_price_update(sender, instance, **kwargs):
    """Update all holdings when asset price is updated."""
    try:
        # Only update if price data was actually changed
        if kwargs.get('update_fields') and 'current_price' in kwargs.get('update_fields', []):
            holdings = instance.holdings.filter(is_active=True)

            for holding in holdings:
                holding.update_values()

            # Update portfolios that contain this asset
            portfolios = Portfolio.objects.filter(
                holdings__asset=instance,
                holdings__is_active=True,
                is_active=True
            ).distinct()

            for portfolio in portfolios:
                portfolio.update_portfolio_values()
                _clear_portfolio_caches(portfolio)

    except Exception as e:
        logger.error(f"Error updating holdings for asset price update {instance.symbol}: {str(e)}")


@receiver(pre_save, sender=PortfolioTransaction)
def validate_portfolio_transaction(sender, instance, **kwargs):
    """Validate portfolio transaction before saving."""
    try:
        # Calculate total amount if not provided
        if not instance.total_amount:
            instance.total_amount = instance.quantity * instance.price + instance.fees

        # Validate transaction data
        if instance.quantity <= 0:
            raise ValueError("Transaction quantity must be positive")

        if instance.price <= 0:
            raise ValueError("Transaction price must be positive")

        # Validate transaction types
        valid_types = ['buy', 'sell', 'dividend', 'split', 'merger', 'other']
        if instance.transaction_type not in valid_types:
            raise ValueError(f"Invalid transaction type: {instance.transaction_type}")

    except Exception as e:
        logger.error(f"Error validating portfolio transaction {instance.id}: {str(e)}")
        raise


def _clear_portfolio_caches(portfolio):
    """Clear relevant caches for a portfolio."""
    if not portfolio:
        return

    # Clear portfolio cache
    cache_key = f"portfolio_data_{portfolio.id}"
    cache.delete(cache_key)

    # Clear user portfolio cache
    cache_key = f"user_portfolios_{portfolio.user.id}"
    cache.delete(cache_key)

    # Clear family group portfolio cache if applicable
    if portfolio.family_group:
        cache_key = f"family_group_portfolios_{portfolio.family_group.id}"
        cache.delete(cache_key)