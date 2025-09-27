from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from moneymanager.apps.budgets.models import Budget, BudgetCategory
from datetime import date
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Update budget spent amounts and check for alerts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--budget-id',
            type=str,
            help='Update only a specific budget by ID',
        )
        parser.add_argument(
            '--send-alerts',
            action='store_true',
            help='Send budget alerts for exceeded thresholds',
        )

    def handle(self, *args, **options):
        budget_id = options.get('budget_id')
        send_alerts = options.get('send_alerts', False)

        today = date.today()

        # Get active budgets
        if budget_id:
            budgets = Budget.objects.filter(
                id=budget_id,
                is_active=True
            )
            if not budgets.exists():
                self.stdout.write(
                    self.style.ERROR(f'Budget with ID {budget_id} not found')
                )
                return
        else:
            # Get all active budgets that are current
            budgets = Budget.objects.filter(
                is_active=True,
                start_date__lte=today,
                end_date__gte=today
            ).select_related('user', 'family_group')

        if not budgets.exists():
            self.stdout.write(
                self.style.SUCCESS('No active budgets found to update')
            )
            return

        updated_count = 0
        alert_count = 0
        error_count = 0

        for budget in budgets:
            try:
                with transaction.atomic():
                    # Update budget spent amount
                    old_spent = budget.spent_amount
                    budget.update_spent_amount()

                    # Update category spent amounts
                    for budget_category in budget.categories.all():
                        budget_category.update_spent_amount()

                    updated_count += 1

                    self.stdout.write(
                        f'Updated budget "{budget.name}": '
                        f'${old_spent} → ${budget.spent_amount} '
                        f'({budget.percentage_spent:.1f}% of ${budget.total_budget})'
                    )

                    # Check for alerts if requested
                    if send_alerts and budget.should_send_alert:
                        budget.send_budget_alert()
                        alert_count += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f'Alert sent for budget "{budget.name}"'
                            )
                        )

            except Exception as e:
                error_count += 1
                logger.error(f'Error updating budget {budget.id}: {str(e)}')
                self.stdout.write(
                    self.style.ERROR(
                        f'Error updating budget "{budget.name}": {str(e)}'
                    )
                )

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'Updated {updated_count} budgets'
            )
        )

        if send_alerts and alert_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Sent {alert_count} budget alerts'
                )
            )

        if error_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'Encountered {error_count} errors'
                )
            )