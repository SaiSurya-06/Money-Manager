from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Budget, BudgetGoal, BudgetAlert
from ..transactions.models import Transaction
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Budget)
def clear_budget_cache_on_save(sender, instance, **kwargs):
    """Clear budget caches when budget is saved."""
    _clear_budget_caches(instance)


@receiver(post_delete, sender=Budget)
def clear_budget_cache_on_delete(sender, instance, **kwargs):
    """Clear budget caches when budget is deleted."""
    _clear_budget_caches(instance)


@receiver(post_save, sender=BudgetGoal)
def clear_goal_cache_on_save(sender, instance, **kwargs):
    """Clear goal caches when goal is saved."""
    _clear_goal_caches(instance)


def _clear_budget_caches(budget):
    """Clear relevant caches for a budget."""
    # Clear user budget cache
    cache_key = f"user_budgets_{budget.user.id}"
    cache.delete(cache_key)

    # Clear family group budget cache if applicable
    if budget.family_group:
        cache_key = f"family_group_budgets_{budget.family_group.id}"
        cache.delete(cache_key)


def _clear_goal_caches(goal):
    """Clear relevant caches for a goal."""
    # Clear user goal cache
    cache_key = f"user_goals_{goal.user.id}"
    cache.delete(cache_key)

    # Clear family group goal cache if applicable
    if goal.family_group:
        cache_key = f"family_group_goals_{goal.family_group.id}"
        cache.delete(cache_key)


def send_budget_alert(budget, alert_type, message):
    """Send budget alert notification."""
    try:
        alert = BudgetAlert.objects.create(
            budget=budget,
            alert_type=alert_type,
            message=message,
            user=budget.user
        )

        # TODO: Integrate with notification system (email, push, etc.)
        logger.info(f"Budget alert created: {alert.id} for user {budget.user.id}")

        return alert

    except Exception as e:
        logger.error(f"Error creating budget alert: {str(e)}")
        return None


def send_goal_alert(goal, alert_type, message):
    """Send goal alert notification."""
    try:
        alert = BudgetAlert.objects.create(
            goal=goal,
            alert_type=alert_type,
            message=message,
            user=goal.user
        )

        # TODO: Integrate with notification system (email, push, etc.)
        logger.info(f"Goal alert created: {alert.id} for user {goal.user.id}")

        return alert

    except Exception as e:
        logger.error(f"Error creating goal alert: {str(e)}")
        return None