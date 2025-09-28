#!/usr/bin/env python3

import os
import sys
import django
from datetime import datetime

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneymanager.settings.local')
django.setup()

from moneymanager.apps.transactions.models import Account

def check_accounts():
    """Check what accounts exist in the database."""
    print("🔍 CHECKING ACCOUNTS IN DATABASE")
    print("=" * 50)
    
    # Get all accounts
    accounts = Account.objects.all()
    
    if accounts.exists():
        print(f"📊 Found {accounts.count()} account(s):")
        for i, account in enumerate(accounts, 1):
            print(f"  {i}. UUID: {account.id}")
            print(f"     Name: {account.name}")
            print(f"     Owner: {account.owner}")
            print(f"     Type: {account.get_account_type_display()}")
            print(f"     Active: {account.is_active}")
            print(f"     Balance: {account.current_balance}")
            print("-" * 30)
    else:
        print("❌ No accounts found in the database!")
    
    # Check the specific UUID
    target_uuid = "0152b3ad-d212-400e-b740-f2b4a36095bb"
    print(f"\n🎯 Checking specific UUID: {target_uuid}")
    
    try:
        specific_account = Account.objects.get(id=target_uuid)
        print(f"✅ Found account: {specific_account.name} ({specific_account.owner})")
    except Account.DoesNotExist:
        print("❌ Account with this UUID does not exist!")
    
    # Check active accounts only
    active_accounts = Account.objects.filter(is_active=True)
    print(f"\n📈 Active accounts: {active_accounts.count()}")
    
    # Check if there are any inactive accounts
    inactive_accounts = Account.objects.filter(is_active=False)
    if inactive_accounts.exists():
        print(f"💤 Inactive accounts: {inactive_accounts.count()}")
        for account in inactive_accounts:
            print(f"  - {account.name} (UUID: {account.id})")

if __name__ == "__main__":
    check_accounts()