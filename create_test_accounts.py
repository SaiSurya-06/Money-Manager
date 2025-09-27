#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneymanager.settings.local')
    django.setup()

    from django.contrib.auth import get_user_model
    from moneymanager.apps.transactions.models import Account

    User = get_user_model()
    
    try:
        user = User.objects.get(username='admin')
        account, created = Account.objects.get_or_create(
            name='Test Checking Account',
            owner=user,
            defaults={
                'account_type': 'checking',
                'bank_name': 'Test Bank',
                'current_balance': 1000.00,
                'currency': 'INR'
            }
        )
        print(f'Account {"created" if created else "already exists"}: {account.name}')
        
        # Create a second account for testing
        account2, created2 = Account.objects.get_or_create(
            name='Test Savings Account',
            owner=user,
            defaults={
                'account_type': 'savings',
                'bank_name': 'Test Bank',
                'current_balance': 5000.00,
                'currency': 'INR'
            }
        )
        print(f'Account {"created" if created2 else "already exists"}: {account2.name}')
        
    except User.DoesNotExist:
        print('Admin user not found. Please create a superuser first.')
        sys.exit(1)