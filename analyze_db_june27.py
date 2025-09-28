"""
Database Analysis for June 27th Transactions
Let's check what's currently in the database for June 27th
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneymanager.settings.local')
django.setup()

from moneymanager.apps.transactions.models import Transaction
from datetime import datetime, date

def analyze_june_27_transactions():
    """Analyze what June 27th transactions are currently in the database."""
    print("=" * 80)
    print("JUNE 27TH DATABASE ANALYSIS")
    print("=" * 80)
    
    # Check for June 27, 2024 transactions
    june_27_2024 = date(2024, 6, 27)
    
    transactions = Transaction.objects.filter(date=june_27_2024)
    
    print(f"Found {transactions.count()} transactions on June 27, 2024:")
    print()
    
    for i, trans in enumerate(transactions.order_by('created_at'), 1):
        print(f"{i}. ID: {trans.id}")
        print(f"   Description: {trans.description}")
        print(f"   Amount: ₹{trans.amount}")
        print(f"   Type: {trans.transaction_type}")
        print(f"   Account: {trans.account.name if trans.account else 'None'}")
        print(f"   Created: {trans.created_at}")
        print(f"   Updated: {trans.updated_at}")
        print(f"   Raw Data: {trans.raw_data[:100] if trans.raw_data else 'None'}...")
        print()
    
    # Also check nearby dates
    print("=" * 80)
    print("TRANSACTIONS AROUND JUNE 27TH")
    print("=" * 80)
    
    from datetime import timedelta
    start_date = june_27_2024 - timedelta(days=2)
    end_date = june_27_2024 + timedelta(days=2)
    
    nearby_transactions = Transaction.objects.filter(
        date__range=[start_date, end_date]
    ).order_by('date', 'created_at')
    
    current_date = None
    for trans in nearby_transactions:
        if trans.date != current_date:
            current_date = trans.date
            print(f"\n--- {current_date} ---")
        
        marker = ">>> " if trans.date == june_27_2024 else "    "
        print(f"{marker}{trans.description[:50]} | ₹{trans.amount} | {trans.transaction_type}")
    
    # Check for duplicate detection issues
    print("\n" + "=" * 80)
    print("DUPLICATE ANALYSIS")
    print("=" * 80)
    
    # Check if there are multiple transactions with same description on June 27
    june_27_descriptions = {}
    for trans in transactions:
        desc = trans.description
        if desc not in june_27_descriptions:
            june_27_descriptions[desc] = []
        june_27_descriptions[desc].append(trans)
    
    print(f"Unique descriptions on June 27: {len(june_27_descriptions)}")
    for desc, trans_list in june_27_descriptions.items():
        if len(trans_list) > 1:
            print(f"DUPLICATE: '{desc}' appears {len(trans_list)} times")
        else:
            print(f"UNIQUE: '{desc}'")

def check_hdfc_account_transactions():
    """Check all HDFC account transactions to understand the pattern."""
    print("\n" + "=" * 80)
    print("HDFC ACCOUNT TRANSACTION ANALYSIS")
    print("=" * 80)
    
    # Find HDFC accounts
    from moneymanager.apps.accounts.models import Account
    
    hdfc_accounts = Account.objects.filter(name__icontains='hdfc')
    
    print(f"Found {hdfc_accounts.count()} HDFC accounts:")
    for acc in hdfc_accounts:
        print(f"  - {acc.name} (ID: {acc.id})")
        
        # Get recent transactions
        recent_transactions = Transaction.objects.filter(
            account=acc
        ).order_by('-date')[:20]
        
        print(f"    Recent {recent_transactions.count()} transactions:")
        for trans in recent_transactions:
            print(f"      {trans.date} | {trans.description[:40]} | ₹{trans.amount}")
        print()

def analyze_transaction_import_patterns():
    """Analyze patterns in imported transaction raw data."""
    print("\n" + "=" * 80)
    print("IMPORT PATTERN ANALYSIS")
    print("=" * 80)
    
    # Get transactions with raw data that might be from HDFC
    transactions_with_raw = Transaction.objects.exclude(
        raw_data__isnull=True
    ).exclude(raw_data='')
    
    hdfc_raw_transactions = []
    for trans in transactions_with_raw:
        if trans.raw_data and ('UPI-' in trans.raw_data or 'ATM' in trans.raw_data or '/' in trans.raw_data):
            hdfc_raw_transactions.append(trans)
    
    print(f"Found {len(hdfc_raw_transactions)} transactions with HDFC-like raw data")
    
    # Look specifically for June 27 patterns
    june_27_raw = [
        trans for trans in hdfc_raw_transactions 
        if trans.date.month == 6 and trans.date.day == 27 and trans.date.year == 2024
    ]
    
    print(f"June 27 transactions with raw data: {len(june_27_raw)}")
    for trans in june_27_raw:
        print(f"  Raw: {trans.raw_data}")
        print(f"  Parsed: {trans.description} | ₹{trans.amount}")
        print()

if __name__ == "__main__":
    analyze_june_27_transactions()
    check_hdfc_account_transactions()
    analyze_transaction_import_patterns()