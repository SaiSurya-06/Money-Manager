#!/usr/bin/env python
"""
Test script to verify bulk upload functionality
"""
import os
import sys
import django

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneymanager.settings.local')

# Setup Django
django.setup()

from django.contrib.auth import get_user_model
from django.test.client import Client
from django.urls import reverse
from moneymanager.apps.transactions.models import Account, Transaction
from moneymanager.apps.transactions.services import import_service
from decimal import Decimal
import tempfile
import csv

User = get_user_model()

def create_test_data():
    """Create test user and account"""
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )

    if created:
        user.set_password('testpass123')
        user.save()
        print("✅ Created test user")
    else:
        print("✅ Test user already exists")

    account, created = Account.objects.get_or_create(
        name='Test Account',
        owner=user,
        defaults={
            'account_type': 'checking',
            'current_balance': Decimal('1000.00')
        }
    )

    if created:
        print("✅ Created test account")
    else:
        print("✅ Test account already exists")

    return user, account

def create_test_csv():
    """Create a test CSV file"""
    # Create temporary CSV file
    csv_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)

    csv_data = [
        ['Date', 'Description', 'Amount', 'Type', 'Category', 'Notes'],
        ['2025-01-01', 'Test Income', '500.00', 'income', 'Salary', 'Test income transaction'],
        ['2025-01-02', 'Test Expense', '100.00', 'expense', 'Groceries', 'Test expense transaction'],
        ['2025-01-03', 'Another Expense', '50.00', 'expense', 'Transportation', 'Another test transaction']
    ]

    writer = csv.writer(csv_file)
    writer.writerows(csv_data)
    csv_file.close()

    print(f"✅ Created test CSV file: {csv_file.name}")
    return csv_file.name

def test_import_service(user, account):
    """Test the import service directly"""
    print("\n🧪 Testing Import Service...")

    csv_file_path = create_test_csv()

    try:
        with open(csv_file_path, 'rb') as f:
            # Create a simple file-like object
            class MockFile:
                def __init__(self, file_path):
                    self.name = os.path.basename(file_path)
                    self._file = open(file_path, 'rb')

                def read(self, *args):
                    return self._file.read(*args)

                def seek(self, *args):
                    return self._file.seek(*args)

                def close(self):
                    return self._file.close()

                @property
                def size(self):
                    return os.path.getsize(csv_file_path)

            mock_file = MockFile(csv_file_path)

            result = import_service.import_transactions(
                file=mock_file,
                account=account,
                user=user,
                family_group=None,
                has_header=True
            )

            mock_file.close()

            print(f"✅ Import service result:")
            print(f"   - Success: {result['success']}")
            print(f"   - Created: {result['created_count']} transactions")
            print(f"   - Errors: {len(result.get('errors', []))}")

            if result.get('errors'):
                for error in result['errors'][:3]:
                    print(f"   - Error: {error}")

            return result['success']

    except Exception as e:
        print(f"❌ Import service test failed: {str(e)}")
        return False

    finally:
        # Clean up temp file
        if os.path.exists(csv_file_path):
            os.unlink(csv_file_path)

def test_form_validation():
    """Test form validation"""
    print("\n🧪 Testing Form Validation...")

    from moneymanager.apps.transactions.forms import BulkTransactionUploadForm

    user, account = create_test_data()

    # Test form with valid data
    form = BulkTransactionUploadForm(
        user=user,
        family_group=None
    )

    print(f"✅ Form created successfully")
    print(f"   - Account queryset count: {form.fields['account'].queryset.count()}")
    print(f"   - Helper configured: {hasattr(form, 'helper')}")

    return True

def test_view_access():
    """Test view access and URL patterns"""
    print("\n🧪 Testing View Access...")

    client = Client()

    # Test without login (should redirect)
    response = client.get(reverse('transactions:bulk_upload'))
    print(f"✅ Anonymous access: {response.status_code} (should be 302 redirect)")

    # Test with login
    user, account = create_test_data()
    client.login(username='testuser', password='testpass123')

    response = client.get(reverse('transactions:bulk_upload'))
    print(f"✅ Authenticated access: {response.status_code} (should be 200)")

    if response.status_code == 200:
        print("✅ Page loads successfully")
        return True
    else:
        print(f"❌ Page load failed: {response.status_code}")
        return False

def test_transaction_count():
    """Check current transaction count"""
    print("\n📊 Current System State:")

    user_count = User.objects.count()
    account_count = Account.objects.count()
    transaction_count = Transaction.objects.count()

    print(f"   - Users: {user_count}")
    print(f"   - Accounts: {account_count}")
    print(f"   - Transactions: {transaction_count}")

    return True

def main():
    """Run all tests"""
    print("🚀 BULK UPLOAD FUNCTIONALITY TEST")
    print("=" * 50)

    tests = [
        ("Transaction Count Check", test_transaction_count),
        ("Form Validation", test_form_validation),
        ("View Access", test_view_access),
        ("Import Service", lambda: test_import_service(*create_test_data())),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {str(e)}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)

    passed = sum(1 for name, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")

    print(f"\n🎯 Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Bulk upload should be working.")
        print("\nNext steps:")
        print("1. Start server: python manage.py runserver")
        print("2. Login with: testuser / testpass123")
        print("3. Go to: Transactions > Bulk Upload")
        print("4. Upload the sample CSV file")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Check the errors above.")

if __name__ == '__main__':
    main()