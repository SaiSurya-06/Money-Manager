"""
Django management command to fix transaction types based on description analysis.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from moneymanager.apps.transactions.models import Transaction
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Analyze and fix transaction types based on description keywords'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making actual changes',
        )
        parser.add_argument(
            '--user-id',
            type=str,
            help='Fix transactions for specific user (UUID)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        user_id = options.get('user_id')

        self.stdout.write(
            self.style.SUCCESS('Starting transaction type analysis...')
        )

        # Define keyword lists
        expense_keywords = [
            'payment', 'purchase', 'withdrawal', 'fee', 'charge', 'bill', 
            'transfer to', 'debit', 'atm', 'pos', 'shopping', 'fuel',
            'electricity', 'water', 'rent', 'loan', 'emi', 'insurance',
            'grocery', 'restaurant', 'medical', 'pharmacy', 'transport',
            'uber', 'taxi', 'bus', 'train', 'flight', 'hotel'
        ]
        
        income_keywords = [
            'salary', 'deposit', 'credit', 'refund', 'cashback', 'interest',
            'dividend', 'bonus', 'transfer from', 'received', 'incoming',
            'payroll', 'wage', 'freelance', 'commission', 'reimbursement'
        ]

        # Get transactions to analyze
        queryset = Transaction.objects.filter(is_active=True)
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        total_transactions = queryset.count()
        changes_made = 0
        changes_to_make = []

        self.stdout.write(f'Analyzing {total_transactions} transactions...')

        for trans in queryset:
            description_lower = trans.description.lower()
            current_type = trans.transaction_type
            suggested_type = None

            # Check for expense indicators
            is_likely_expense = any(keyword in description_lower for keyword in expense_keywords)
            is_likely_income = any(keyword in description_lower for keyword in income_keywords)

            if is_likely_expense and not is_likely_income and current_type != 'expense':
                suggested_type = 'expense'
            elif is_likely_income and not is_likely_expense and current_type != 'income':
                suggested_type = 'income'

            if suggested_type and suggested_type != current_type:
                changes_to_make.append({
                    'transaction': trans,
                    'current_type': current_type,
                    'suggested_type': suggested_type,
                    'description': trans.description[:50]
                })

        if changes_to_make:
            self.stdout.write(
                self.style.WARNING(f'Found {len(changes_to_make)} transactions that could be corrected:')
            )

            for change in changes_to_make[:10]:  # Show first 10
                self.stdout.write(
                    f"  {change['transaction'].date} | {change['description']} | "
                    f"{change['current_type']} → {change['suggested_type']}"
                )

            if len(changes_to_make) > 10:
                self.stdout.write(f"  ... and {len(changes_to_make) - 10} more")

            if not dry_run:
                confirm = input("\nDo you want to apply these changes? (y/N): ")
                if confirm.lower() == 'y':
                    with transaction.atomic():
                        for change in changes_to_make:
                            trans = change['transaction']
                            trans.transaction_type = change['suggested_type']
                            trans.save(update_fields=['transaction_type'])
                            changes_made += 1

                    self.stdout.write(
                        self.style.SUCCESS(f'Successfully updated {changes_made} transactions!')
                    )

                    # Update account balances
                    affected_accounts = set()
                    for change in changes_to_make:
                        affected_accounts.add(change['transaction'].account)

                    for account in affected_accounts:
                        account.update_balance()

                    self.stdout.write(
                        self.style.SUCCESS(f'Updated balances for {len(affected_accounts)} accounts')
                    )
                else:
                    self.stdout.write('Operation cancelled.')
            else:
                self.stdout.write(
                    self.style.WARNING('DRY RUN: No changes were made. Remove --dry-run to apply changes.')
                )
        else:
            self.stdout.write(
                self.style.SUCCESS('No transaction type corrections needed!')
            )