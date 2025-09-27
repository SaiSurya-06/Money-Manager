#!/usr/bin/env python
"""
Test the date parsing fix for Federal Bank format.
"""
import os
import sys
import django
from datetime import datetime, date

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneymanager.settings.local')
django.setup()

from moneymanager.apps.transactions.services import TransactionImportService

def test_date_parsing_fix():
    print("🧪 TESTING DATE PARSING FIX")
    print("="*50)
    
    service = TransactionImportService()
    
    # Test the problematic date that was showing as February
    test_cases = [
        ("02/06/2023", "June 2, 2023"),   # Should be June 2nd, NOT February 6th
        ("31/05/2023", "May 31, 2023"),   # Should be May 31st
        ("27/06/2023", "June 27, 2023"),  # Should be June 27th
        ("22/05/2023", "May 22, 2023"),   # Should be May 22nd
    ]
    
    print("Testing date parsing priority (DD/MM/YYYY first):")
    
    for date_str, expected in test_cases:
        parsed_date = service._parse_date(date_str)
        
        if parsed_date:
            month_name = parsed_date.strftime("%B")
            day = parsed_date.day
            year = parsed_date.year
            formatted = f"{month_name} {day}, {year}"
            
            # Check if it matches expected
            correct = formatted == expected
            status = "✅ CORRECT" if correct else "❌ WRONG"
            
            print(f"{date_str:12s} → {formatted:15s} | Expected: {expected:15s} | {status}")
            
            # Specific check for the problematic date
            if date_str == "02/06/2023":
                if month_name == "June":
                    print(f"    🎉 SUCCESS: 02/06/2023 correctly parsed as JUNE (not February)")
                else:
                    print(f"    ❌ FAILED: 02/06/2023 parsed as {month_name} (should be JUNE)")
        else:
            print(f"{date_str:12s} → PARSE FAILED")

def test_full_transaction_creation():
    """Test creating a transaction with Federal Bank date to verify end-to-end."""
    print(f"\n🔄 TESTING FULL TRANSACTION CREATION")
    print("="*50)
    
    # Simulate transaction data from Federal Bank parsing
    from moneymanager.apps.transactions.models import Account, Transaction
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    # Create test user and account if needed
    try:
        user = User.objects.get(username='testuser')
    except User.DoesNotExist:
        user = User.objects.create_user(username='testuser', password='testpass')
    
    try:
        account = Account.objects.get(name='Test Account')
    except Account.DoesNotExist:
        account = Account.objects.create(
            name='Test Account',
            account_type='savings',
            balance=0,
            user=user
        )
    
    # Test transaction with problematic date
    test_transaction_data = {
        'date_str': '02/06/2023',  # Should be June 2nd
        'description': 'UPI IN/315312676214/surya.prakhya06@okhdfcba/0000TFR S95759682',
        'amount_str': '100.00',
        'type': 'income',
        'source_line': 'Test line'
    }
    
    service = TransactionImportService()
    
    # Create transaction using the fixed parsing
    try:
        created_transaction = service._create_pdf_transaction(
            test_transaction_data, 1, account, user
        )
        
        if created_transaction:
            # Get the saved transaction from database
            transaction_id = created_transaction['id']
            saved_transaction = Transaction.objects.get(pk=transaction_id)
            
            print(f"Created transaction ID: {transaction_id}")
            print(f"Saved date in DB: {saved_transaction.date}")
            print(f"Date formatted: {saved_transaction.date.strftime('%B %d, %Y')}")
            
            # Check if it's correct
            if saved_transaction.date.month == 6:  # June
                print("✅ SUCCESS: Transaction saved with correct date (June)")
                
                # Clean up test transaction
                saved_transaction.delete()
                print("🧹 Test transaction cleaned up")
            else:
                print(f"❌ FAILED: Transaction saved with wrong month ({saved_transaction.date.month})")
        else:
            print("❌ FAILED: Could not create transaction")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    test_date_parsing_fix()
    test_full_transaction_creation()