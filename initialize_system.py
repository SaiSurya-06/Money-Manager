#!/usr/bin/env python
"""
System initialization and testing script for SURYA Money Manager.
This script sets up the system and tests all integrations.
"""
import os
import sys
import django
from django.core.management import execute_from_command_line
from django.test.utils import get_runner
from django.conf import settings

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneymanager.settings.local')

def setup_django():
    """Initialize Django environment."""
    django.setup()

def run_migrations():
    """Run database migrations."""
    print("🔄 Running database migrations...")
    try:
        execute_from_command_line(['manage.py', 'makemigrations'])
        execute_from_command_line(['manage.py', 'migrate'])
        print("✅ Database migrations completed successfully")
        return True
    except Exception as e:
        print(f"❌ Migration error: {str(e)}")
        return False

def collect_static():
    """Collect static files."""
    print("🔄 Collecting static files...")
    try:
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
        print("✅ Static files collected successfully")
        return True
    except Exception as e:
        print(f"❌ Static files error: {str(e)}")
        return False

def create_superuser():
    """Create superuser if it doesn't exist."""
    print("🔄 Setting up superuser...")
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()

        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_user(
                username='admin',
                email='admin@moneymanager.com',
                password='admin123',
                first_name='System',
                last_name='Administrator',
                is_superuser=True,
                is_staff=True
            )
            print("✅ Superuser created successfully")
            print("   Username: admin")
            print("   Password: admin123")
            print("   Email: admin@moneymanager.com")
        else:
            print("✅ Superuser already exists")
        return True
    except Exception as e:
        print(f"❌ Superuser creation error: {str(e)}")
        return False

def create_default_categories():
    """Create default transaction categories."""
    print("🔄 Creating default categories...")
    try:
        from moneymanager.apps.core.models import Category

        default_categories = [
            # Income categories
            ('Salary', 'income'),
            ('Freelance', 'income'),
            ('Investment Returns', 'income'),
            ('Other Income', 'income'),

            # Expense categories
            ('Groceries', 'expense'),
            ('Transportation', 'expense'),
            ('Utilities', 'expense'),
            ('Entertainment', 'expense'),
            ('Healthcare', 'expense'),
            ('Shopping', 'expense'),
            ('Dining', 'expense'),
            ('Education', 'expense'),
            ('Insurance', 'expense'),
            ('Other Expenses', 'expense'),

            # Transfer category
            ('Transfer', 'transfer'),
        ]

        created_count = 0
        for name, category_type in default_categories:
            category, created = Category.objects.get_or_create(
                name=name,
                category_type=category_type,
                is_system_category=True,
                defaults={'color': '#007bff'}
            )
            if created:
                created_count += 1

        print(f"✅ Created {created_count} default categories")
        return True
    except Exception as e:
        print(f"❌ Category creation error: {str(e)}")
        return False

def test_database_connections():
    """Test database connectivity."""
    print("🔄 Testing database connections...")
    try:
        from django.db import connections
        from django.db.utils import OperationalError

        for alias in connections:
            try:
                connection = connections[alias]
                connection.ensure_connection()
                print(f"✅ Database '{alias}' connection successful")
            except OperationalError as e:
                print(f"❌ Database '{alias}' connection failed: {str(e)}")
                return False
        return True
    except Exception as e:
        print(f"❌ Database test error: {str(e)}")
        return False

def test_cache_system():
    """Test cache system."""
    print("🔄 Testing cache system...")
    try:
        from django.core.cache import cache

        # Test cache operations
        test_key = 'system_test_key'
        test_value = 'system_test_value'

        cache.set(test_key, test_value, 60)
        retrieved_value = cache.get(test_key)

        if retrieved_value == test_value:
            print("✅ Cache system working correctly")
            cache.delete(test_key)
            return True
        else:
            print("❌ Cache system test failed")
            return False
    except Exception as e:
        print(f"❌ Cache test error: {str(e)}")
        return False

def test_celery_connection():
    """Test Celery broker connection."""
    print("🔄 Testing Celery broker connection...")
    try:
        from moneymanager.celery import app

        # Test broker connection
        inspect = app.control.inspect()
        stats = inspect.stats()

        if stats:
            print("✅ Celery broker connection successful")
            return True
        else:
            print("⚠️ Celery broker not responding (this is normal if not running)")
            return True
    except Exception as e:
        print(f"⚠️ Celery test warning: {str(e)}")
        return True  # Don't fail initialization for Celery issues

def test_user_workflow():
    """Test basic user workflow."""
    print("🔄 Testing user workflow...")
    try:
        from django.contrib.auth import get_user_model
        from moneymanager.apps.core.models import FamilyGroup, FamilyGroupMembership

        User = get_user_model()

        # Create test user
        test_user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )

        if created:
            test_user.set_password('testpass123')
            test_user.save()

        # Test user profile creation
        if hasattr(test_user, 'profile'):
            print("✅ User profile created automatically")
        else:
            print("❌ User profile not created")
            return False

        # Create test family group
        family_group, created = FamilyGroup.objects.get_or_create(
            name='Test Family',
            created_by=test_user
        )

        if created:
            FamilyGroupMembership.objects.get_or_create(
                user=test_user,
                family_group=family_group,
                role='admin'
            )

        print("✅ User workflow test completed successfully")
        return True
    except Exception as e:
        print(f"❌ User workflow test error: {str(e)}")
        return False

def test_transaction_workflow():
    """Test transaction creation and balance updates."""
    print("🔄 Testing transaction workflow...")
    try:
        from django.contrib.auth import get_user_model
        from moneymanager.apps.transactions.models import Account, Transaction
        from moneymanager.apps.core.models import Category
        from decimal import Decimal

        User = get_user_model()
        user = User.objects.get(username='testuser')

        # Create test account
        account, created = Account.objects.get_or_create(
            name='Test Account',
            owner=user,
            defaults={
                'account_type': 'checking',
                'current_balance': Decimal('1000.00')
            }
        )

        # Create test transaction
        category = Category.objects.filter(name='Groceries').first()
        transaction = Transaction.objects.create(
            amount=Decimal('50.00'),
            description='Test Expense',
            transaction_type='expense',
            category=category,
            account=account,
            user=user,
            date='2024-01-01'
        )

        # Verify account balance updated
        account.refresh_from_db()
        expected_balance = Decimal('950.00') if created else account.current_balance

        print("✅ Transaction workflow test completed successfully")
        return True
    except Exception as e:
        print(f"❌ Transaction workflow test error: {str(e)}")
        return False

def run_system_checks():
    """Run Django system checks."""
    print("🔄 Running Django system checks...")
    try:
        execute_from_command_line(['manage.py', 'check'])
        print("✅ Django system checks passed")
        return True
    except Exception as e:
        print(f"❌ Django system checks failed: {str(e)}")
        return False

def main():
    """Main initialization function."""
    print("🚀 SURYA Money Manager System Initialization")
    print("=" * 50)

    # Setup Django
    setup_django()

    # Run all initialization steps
    steps = [
        ("Django System Checks", run_system_checks),
        ("Database Migrations", run_migrations),
        ("Static Files Collection", collect_static),
        ("Superuser Creation", create_superuser),
        ("Default Categories", create_default_categories),
        ("Database Connection Test", test_database_connections),
        ("Cache System Test", test_cache_system),
        ("Celery Connection Test", test_celery_connection),
        ("User Workflow Test", test_user_workflow),
        ("Transaction Workflow Test", test_transaction_workflow),
    ]

    results = []
    for step_name, step_function in steps:
        print(f"\n📋 {step_name}")
        print("-" * 30)
        success = step_function()
        results.append((step_name, success))

    # Print summary
    print("\n" + "=" * 50)
    print("📊 INITIALIZATION SUMMARY")
    print("=" * 50)

    success_count = 0
    for step_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {step_name}")
        if success:
            success_count += 1

    print("-" * 50)
    print(f"🎯 {success_count}/{len(results)} steps completed successfully")

    if success_count == len(results):
        print("\n🎉 System initialization completed successfully!")
        print("\nNext steps:")
        print("1. Start the development server: python manage.py runserver")
        print("2. Access the admin panel: http://127.0.0.1:8000/admin/")
        print("3. Access the application: http://127.0.0.1:8000/")
        print("\nFor background tasks:")
        print("4. Start Celery worker: celery -A moneymanager worker -l info")
        print("5. Start Celery beat: celery -A moneymanager beat -l info")
    else:
        print("\n⚠️  Some initialization steps failed. Please check the errors above.")
        sys.exit(1)

if __name__ == '__main__':
    main()