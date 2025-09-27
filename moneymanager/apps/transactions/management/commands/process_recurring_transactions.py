from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from moneymanager.apps.transactions.models import RecurringTransaction
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process recurring transactions that are due'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually creating transactions',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No transactions will be created')
            )

        today = timezone.now().date()

        # Get all active recurring transactions that are due
        due_recurring_transactions = RecurringTransaction.objects.filter(
            is_active=True,
            next_due_date__lte=today
        ).select_related('account', 'category', 'user', 'family_group')

        if not due_recurring_transactions.exists():
            self.stdout.write(
                self.style.SUCCESS('No recurring transactions are due today')
            )
            return

        processed_count = 0
        error_count = 0

        for recurring_transaction in due_recurring_transactions:
            try:
                # Check if end date has passed
                if (recurring_transaction.end_date and
                    recurring_transaction.next_due_date > recurring_transaction.end_date):

                    self.stdout.write(
                        self.style.WARNING(
                            f'Recurring transaction {recurring_transaction.name} has ended'
                        )
                    )
                    continue

                if not dry_run:
                    with transaction.atomic():
                        new_transaction = recurring_transaction.generate_next_transaction()

                        if new_transaction:
                            processed_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'Created transaction: {new_transaction.description} '
                                    f'for ${new_transaction.amount}'
                                )
                            )
                        else:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Failed to create transaction for: {recurring_transaction.name}'
                                )
                            )
                else:
                    # Dry run mode
                    self.stdout.write(
                        f'Would create: {recurring_transaction.description} '
                        f'for ${recurring_transaction.amount} on {recurring_transaction.next_due_date}'
                    )
                    processed_count += 1

            except Exception as e:
                error_count += 1
                logger.error(
                    f'Error processing recurring transaction {recurring_transaction.id}: {str(e)}'
                )
                self.stdout.write(
                    self.style.ERROR(
                        f'Error processing {recurring_transaction.name}: {str(e)}'
                    )
                )

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Processed {processed_count} recurring transactions with {error_count} errors'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Would process {processed_count} recurring transactions'
                )
            )