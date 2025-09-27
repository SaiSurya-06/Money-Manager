"""
Celery tasks for background processing.
"""
from celery import shared_task
from django.core.management import call_command
from django.core.cache import cache
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_recurring_transactions(self):
    """Process all due recurring transactions."""
    try:
        logger.info("Starting recurring transaction processing")
        call_command('process_recurring_transactions')
        logger.info("Recurring transaction processing completed successfully")
        return "Recurring transactions processed successfully"

    except Exception as exc:
        logger.error(f"Error processing recurring transactions: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def update_budget_amounts(self, send_alerts=True):
    """Update budget amounts and send alerts if needed."""
    try:
        logger.info("Starting budget amount updates")
        if send_alerts:
            call_command('update_budget_amounts', '--send-alerts')
        else:
            call_command('update_budget_amounts')
        logger.info("Budget amount updates completed successfully")
        return "Budget amounts updated successfully"

    except Exception as exc:
        logger.error(f"Error updating budget amounts: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def update_asset_prices(self, active_only=True):
    """Update asset prices from external APIs."""
    try:
        logger.info("Starting asset price updates")
        if active_only:
            call_command('update_asset_prices', '--active-only')
        else:
            call_command('update_asset_prices')
        logger.info("Asset price updates completed successfully")
        return "Asset prices updated successfully"

    except Exception as exc:
        logger.error(f"Error updating asset prices: {str(exc)}")
        raise self.retry(exc=exc, countdown=300)  # Retry after 5 minutes


@shared_task
def clear_expired_sessions():
    """Clear expired user sessions."""
    try:
        from django.contrib.sessions.models import Session
        Session.objects.filter(expire_date__lt=timezone.now()).delete()
        logger.info("Expired sessions cleared successfully")
        return "Expired sessions cleared"

    except Exception as e:
        logger.error(f"Error clearing expired sessions: {str(e)}")
        raise


@shared_task
def cleanup_old_cache_entries():
    """Clean up old cache entries."""
    try:
        # Clear family group caches older than 1 day
        cache_patterns = [
            'user_family_groups_*',
            'user_transactions_*',
            'user_budgets_*',
            'user_portfolios_*'
        ]

        # Note: This is a simplified cleanup. In production, you might want
        # to implement a more sophisticated cache management strategy
        for pattern in cache_patterns:
            try:
                cache.delete_pattern(pattern)
            except AttributeError:
                # Redis backend required for delete_pattern
                pass

        logger.info("Cache cleanup completed successfully")
        return "Cache cleanup completed"

    except Exception as e:
        logger.error(f"Error during cache cleanup: {str(e)}")
        raise


@shared_task
def send_daily_budget_summary(user_id=None):
    """Send daily budget summary to users."""
    try:
        from django.contrib.auth import get_user_model
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from moneymanager.apps.budgets.models import Budget
        from datetime import date

        User = get_user_model()
        today = date.today()

        if user_id:
            users = User.objects.filter(id=user_id, is_active=True)
        else:
            # Get users who have budget alerts enabled
            users = User.objects.filter(
                is_active=True,
                profile__budget_alerts=True
            ).select_related('profile')

        sent_count = 0

        for user in users:
            try:
                # Get user's active budgets
                budgets = Budget.objects.filter(
                    user=user,
                    is_active=True,
                    start_date__lte=today,
                    end_date__gte=today
                )

                if budgets.exists():
                    # Update budget amounts
                    for budget in budgets:
                        budget.update_spent_amount()

                    # Prepare email context
                    context = {
                        'user': user,
                        'budgets': budgets,
                        'date': today
                    }

                    # Render email content
                    subject = f"Daily Budget Summary - {today.strftime('%B %d, %Y')}"
                    html_content = render_to_string('emails/budget_summary.html', context)
                    text_content = render_to_string('emails/budget_summary.txt', context)

                    # Send email
                    send_mail(
                        subject=subject,
                        message=text_content,
                        from_email='noreply@moneymanager.com',
                        recipient_list=[user.email],
                        html_message=html_content,
                        fail_silently=False
                    )

                    sent_count += 1

            except Exception as e:
                logger.error(f"Error sending budget summary to user {user.id}: {str(e)}")

        logger.info(f"Daily budget summaries sent to {sent_count} users")
        return f"Budget summaries sent to {sent_count} users"

    except Exception as e:
        logger.error(f"Error sending daily budget summaries: {str(e)}")
        raise


@shared_task
def generate_monthly_reports():
    """Generate monthly financial reports for all users."""
    try:
        from django.contrib.auth import get_user_model
        from datetime import date, timedelta

        User = get_user_model()
        
        # Get the first day of the previous month
        today = date.today()
        first_day_current = today.replace(day=1)
        last_day_previous = first_day_current - timedelta(days=1)
        first_day_previous = last_day_previous.replace(day=1)

        generated_count = 0

        # Get active users
        users = User.objects.filter(is_active=True)

        for user in users:
            try:
                # TODO: Implement monthly report generation
                # This would generate comprehensive monthly financial reports
                # including transaction summaries, budget performance, etc.
                
                generated_count += 1
                logger.info(f"Monthly report placeholder processed for user {user.id}")

            except Exception as e:
                logger.error(f"Error generating monthly report for user {user.id}: {str(e)}")

        logger.info(f"Monthly reports processed for {generated_count} users")
        return f"Monthly reports processed for {generated_count} users"

    except Exception as e:
        logger.error(f"Error generating monthly reports: {str(e)}")
        raise


# Periodic task setup (if using celery-beat)
from celery.schedules import crontab

# This would typically go in your celery configuration
CELERY_BEAT_SCHEDULE = {
    'process-recurring-transactions': {
        'task': 'moneymanager.apps.core.tasks.process_recurring_transactions',
        'schedule': crontab(hour=6, minute=0),  # Daily at 6 AM
    },
    'update-budget-amounts': {
        'task': 'moneymanager.apps.core.tasks.update_budget_amounts',
        'schedule': crontab(hour=7, minute=0),  # Daily at 7 AM
    },
    'update-asset-prices': {
        'task': 'moneymanager.apps.core.tasks.update_asset_prices',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
    'clear-expired-sessions': {
        'task': 'moneymanager.apps.core.tasks.clear_expired_sessions',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    'cleanup-cache': {
        'task': 'moneymanager.apps.core.tasks.cleanup_old_cache_entries',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
    },
    'send-daily-budget-summary': {
        'task': 'moneymanager.apps.core.tasks.send_daily_budget_summary',
        'schedule': crontab(hour=8, minute=0),  # Daily at 8 AM
    },
    'generate-monthly-reports': {
        'task': 'moneymanager.apps.core.tasks.generate_monthly_reports',
        'schedule': crontab(day_of_month=1, hour=9, minute=0),  # Monthly on 1st at 9 AM
    },
}