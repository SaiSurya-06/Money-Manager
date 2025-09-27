from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.core.cache import cache
from .models import Transaction, Account, RecurringTransaction
from ..budgets.models import Budget
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Transaction)
def update_account_balance_on_save(sender, instance, created, **kwargs):
    """Update account balance when transaction is saved."""
    try:
        if instance.account:
            instance.account.update_balance()

        # Update to_account balance for transfers
        if instance.to_account and instance.transaction_type == 'transfer':
            instance.to_account.update_balance()

        # Update from_account balance for transfers
        if instance.from_account and instance.transaction_type == 'transfer':
            instance.from_account.update_balance()

        # Clear related caches
        _clear_transaction_caches(instance)

        # Update budgets if expense transaction
        if instance.transaction_type == 'expense' and instance.is_active:
            _update_related_budgets(instance)

    except Exception as e:
        logger.error(f"Error updating account balance for transaction {instance.id}: {str(e)}")


@receiver(post_delete, sender=Transaction)
def update_account_balance_on_delete(sender, instance, **kwargs):
    """Update account balance when transaction is deleted."""
    try:
        if instance.account:
            instance.account.update_balance()

        # Update to_account balance for transfers
        if instance.to_account and instance.transaction_type == 'transfer':
            instance.to_account.update_balance()

        # Update from_account balance for transfers
        if instance.from_account and instance.transaction_type == 'transfer':
            instance.from_account.update_balance()

        # Clear related caches
        _clear_transaction_caches(instance)

    except Exception as e:
        logger.error(f"Error updating account balance after transaction delete {instance.id}: {str(e)}")


@receiver(pre_save, sender=Transaction)
def validate_transaction_before_save(sender, instance, **kwargs):
    """Validate transaction data before saving."""
    try:
        # Ensure amount is positive
        if instance.amount <= 0:
            raise ValueError("Transaction amount must be positive")

        # Validate transfer transactions
        if instance.transaction_type == 'transfer':
            if not instance.to_account:
                raise ValueError("Transfer transactions must have a to_account")
            if instance.account == instance.to_account:
                raise ValueError("Cannot transfer to the same account")
            # Set from_account to main account for transfers
            instance.from_account = instance.account

        # Set family group from account if not set
        if not instance.family_group and instance.account:
            instance.family_group = instance.account.family_group

        # Validate category type matches transaction type
        if instance.category and instance.category.category_type != instance.transaction_type:
            logger.warning(f"Category type mismatch for transaction {instance.id}")

    except Exception as e:
        logger.error(f"Error validating transaction {instance.id}: {str(e)}")
        raise


@receiver(post_save, sender=RecurringTransaction)
def clear_recurring_transaction_cache(sender, instance, **kwargs):
    """Clear caches when recurring transaction is updated."""
    cache_key = f"recurring_transactions_user_{instance.user.id}"
    cache.delete(cache_key)


def _clear_transaction_caches(transaction):
    """Clear relevant caches for a transaction."""
    # Clear user transaction cache
    cache_key = f"user_transactions_{transaction.user.id}"
    cache.delete(cache_key)

    # Clear family group transaction cache if applicable
    if transaction.family_group:
        cache_key = f"family_group_transactions_{transaction.family_group.id}"
        cache.delete(cache_key)

    # Clear account transaction cache
    if transaction.account:
        cache_key = f"account_transactions_{transaction.account.id}"
        cache.delete(cache_key)


def _update_related_budgets(transaction):
    """Update budgets related to this expense transaction."""
    try:
        # Find active budgets that might be affected
        budgets = Budget.objects.filter(
            is_active=True,
            start_date__lte=transaction.date,
            end_date__gte=transaction.date
        )

        if transaction.family_group:
            budgets = budgets.filter(family_group=transaction.family_group)
        else:
            budgets = budgets.filter(user=transaction.user, family_group__isnull=True)

        # Update budget spent amounts
        for budget in budgets:
            budget.update_spent_amount()

    except Exception as e:
        logger.error(f"Error updating budgets for transaction {transaction.id}: {str(e)}")