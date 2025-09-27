from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from moneymanager.apps.core.models import Category

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up initial data for MoneyManager'

    def handle(self, *args, **options):
        self.stdout.write('Setting up initial data...')

        # Create default categories
        self.create_default_categories()

        self.stdout.write(
            self.style.SUCCESS('Initial data setup completed successfully!')
        )

    def create_default_categories(self):
        """Create default system categories."""
        categories = [
            # Income categories
            {'name': 'Salary', 'category_type': 'income', 'icon': 'bi-cash-coin', 'color': '#28a745'},
            {'name': 'Freelance', 'category_type': 'income', 'icon': 'bi-laptop', 'color': '#17a2b8'},
            {'name': 'Investment Income', 'category_type': 'income', 'icon': 'bi-graph-up', 'color': '#6f42c1'},
            {'name': 'Business Income', 'category_type': 'income', 'icon': 'bi-briefcase', 'color': '#20c997'},
            {'name': 'Other Income', 'category_type': 'income', 'icon': 'bi-plus-circle', 'color': '#6c757d'},

            # Expense categories
            {'name': 'Food & Dining', 'category_type': 'expense', 'icon': 'bi-cup-straw', 'color': '#fd7e14'},
            {'name': 'Groceries', 'category_type': 'expense', 'icon': 'bi-cart', 'color': '#198754'},
            {'name': 'Transportation', 'category_type': 'expense', 'icon': 'bi-car-front', 'color': '#0dcaf0'},
            {'name': 'Gas & Fuel', 'category_type': 'expense', 'icon': 'bi-fuel-pump', 'color': '#dc3545'},
            {'name': 'Shopping', 'category_type': 'expense', 'icon': 'bi-bag', 'color': '#e83e8c'},
            {'name': 'Entertainment', 'category_type': 'expense', 'icon': 'bi-controller', 'color': '#6f42c1'},
            {'name': 'Bills & Utilities', 'category_type': 'expense', 'icon': 'bi-receipt', 'color': '#ffc107'},
            {'name': 'Phone Bill', 'category_type': 'expense', 'icon': 'bi-phone', 'color': '#0d6efd'},
            {'name': 'Internet', 'category_type': 'expense', 'icon': 'bi-wifi', 'color': '#20c997'},
            {'name': 'Rent/Mortgage', 'category_type': 'expense', 'icon': 'bi-house', 'color': '#6c757d'},
            {'name': 'Insurance', 'category_type': 'expense', 'icon': 'bi-shield-check', 'color': '#198754'},
            {'name': 'Healthcare', 'category_type': 'expense', 'icon': 'bi-heart-pulse', 'color': '#dc3545'},
            {'name': 'Education', 'category_type': 'expense', 'icon': 'bi-book', 'color': '#0d6efd'},
            {'name': 'Travel', 'category_type': 'expense', 'icon': 'bi-airplane', 'color': '#fd7e14'},
            {'name': 'Fitness & Sports', 'category_type': 'expense', 'icon': 'bi-heart', 'color': '#e83e8c'},
            {'name': 'Personal Care', 'category_type': 'expense', 'icon': 'bi-person', 'color': '#6f42c1'},
            {'name': 'Clothing', 'category_type': 'expense', 'icon': 'bi-bag', 'color': '#e83e8c'},
            {'name': 'Gifts & Donations', 'category_type': 'expense', 'icon': 'bi-gift', 'color': '#fd7e14'},
            {'name': 'Banking Fees', 'category_type': 'expense', 'icon': 'bi-bank', 'color': '#6c757d'},
            {'name': 'Taxes', 'category_type': 'expense', 'icon': 'bi-receipt-cutoff', 'color': '#dc3545'},
            {'name': 'Other Expenses', 'category_type': 'expense', 'icon': 'bi-three-dots', 'color': '#6c757d'},

            # Transfer category
            {'name': 'Transfer', 'category_type': 'transfer', 'icon': 'bi-arrow-left-right', 'color': '#0dcaf0'},
        ]

        created_count = 0
        for category_data in categories:
            category, created = Category.objects.get_or_create(
                name=category_data['name'],
                category_type=category_data['category_type'],
                defaults={
                    'icon': category_data['icon'],
                    'color': category_data['color'],
                    'is_system_category': True
                }
            )
            if created:
                created_count += 1

        self.stdout.write(
            f'Created {created_count} default categories'
        )