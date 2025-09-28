#!/usr/bin/env python
"""
Diagnostic script to check the transaction that's causing the 404 error.
This will help identify why the transaction can't be found.
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(r'c:\Surya Automation\SURYA - Money Manager')

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneymanager.settings.local')

# Initialize Django
django.setup()

from moneymanager.apps.transactions.models import Transaction
from django.contrib.auth import get_user_model

User = get_user_model()

def diagnose_transaction_issue():
    """Diagnose the transaction 404 issue."""
    transaction_id = "d8bc4d85-4fb4-49e7-8e18-13c88a1be496"
    
    print("🔍 Transaction Diagnostic Report")
    print("=" * 50)
    print(f"Transaction ID: {transaction_id}")
    
    try:
        # Check if transaction exists at all
        transaction = Transaction.objects.filter(id=transaction_id).first()
        
        if not transaction:
            print("❌ Transaction does not exist in the database")
            
            # Check for similar transactions
            print("\n🔍 Searching for recent transactions...")
            recent_transactions = Transaction.objects.all().order_by('-created_at')[:10]
            
            if recent_transactions:
                print("\n📋 Recent transactions found:")
                for i, trans in enumerate(recent_transactions, 1):
                    print(f"   {i}. ID: {trans.id}")
                    print(f"      Description: {trans.description}")
                    print(f"      Amount: {trans.amount}")
                    print(f"      User: {trans.user.username}")
                    print(f"      Is Active: {trans.is_active}")
                    print(f"      Family Group: {trans.family_group}")
                    print()
            else:
                print("   No transactions found in the database")
        else:
            print("✅ Transaction exists in database")
            print(f"   Description: {transaction.description}")
            print(f"   Amount: {transaction.amount}")
            print(f"   User: {transaction.user.username}")
            print(f"   Is Active: {transaction.is_active}")
            print(f"   Family Group: {transaction.family_group}")
            print(f"   Account: {transaction.account}")
            print(f"   Created: {transaction.created_at}")
            
            # Check if it would be found by the delete view queryset
            print("\n🔍 Checking delete view queryset filters...")
            
            # Simulate the delete view queryset for different users
            users = User.objects.all()[:5]  # Check first 5 users
            
            for user in users:
                # Test the same filtering logic as in TransactionDeleteView
                queryset = Transaction.objects.filter(is_active=True)
                queryset = queryset.filter(user=user, family_group__isnull=True)
                
                if queryset.filter(id=transaction_id).exists():
                    print(f"   ✅ Transaction visible for user: {user.username}")
                else:
                    print(f"   ❌ Transaction NOT visible for user: {user.username}")
            
            # Check reasons why it might not be visible
            print("\n🔍 Potential issues:")
            if not transaction.is_active:
                print("   ❌ Transaction is soft-deleted (is_active=False)")
            
            if transaction.family_group is not None:
                print(f"   ⚠️  Transaction belongs to family group: {transaction.family_group}")
                print("      This might cause visibility issues if user is not in the same family group")
                
    except Exception as e:
        print(f"❌ Error during diagnosis: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n💡 Suggestions:")
    print("1. Check if you're logged in as the correct user")
    print("2. Verify your family group membership if applicable")
    print("3. Check if the transaction was already deleted (soft-deleted)")
    print("4. Try accessing the transaction list to see if it's visible there")

if __name__ == "__main__":
    diagnose_transaction_issue()