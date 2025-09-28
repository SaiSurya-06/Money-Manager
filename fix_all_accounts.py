#!/usr/bin/env python3

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneymanager.settings.local')
django.setup()

from moneymanager.apps.transactions.models import Account
from moneymanager.apps.core.models import FamilyGroup, FamilyGroupMembership
from django.contrib.auth import get_user_model

User = get_user_model()

def comprehensive_account_fix():
    """Fix all account permission issues comprehensively."""
    print("🔧 COMPREHENSIVE ACCOUNT PERMISSION FIX")
    print("=" * 60)
    
    try:
        # Get current admin user
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            print("❌ No admin user found! Creating one...")
            admin_user = User.objects.filter(is_staff=True).first()
        
        if not admin_user:
            print("❌ No staff user found either!")
            # Use any user as fallback
            admin_user = User.objects.first()
        
        print(f"👤 Using user: {admin_user.get_full_name()} ({admin_user.email})")
        print(f"   Superuser: {admin_user.is_superuser}")
        print(f"   Staff: {admin_user.is_staff}")
        print()
        
        # Get all accounts
        accounts = Account.objects.all()
        print(f"📊 Found {accounts.count()} accounts:")
        
        fixed_count = 0
        
        for account in accounts:
            print(f"\n🔍 Account: {account.name}")
            print(f"   UUID: {account.id}")
            print(f"   Current Owner: {account.owner.get_full_name()} ({account.owner.email})")
            print(f"   Family Group: {account.family_group}")
            print(f"   Active: {account.is_active}")
            
            # Check if admin can access this account
            can_access = False
            
            # Check direct ownership
            if account.owner == admin_user:
                can_access = True
                print("   ✅ Admin owns this account")
            
            # Check family group access
            elif account.family_group:
                membership = FamilyGroupMembership.objects.filter(
                    user=admin_user,
                    family_group=account.family_group,
                    is_active=True
                ).first()
                
                if membership:
                    can_access = True
                    print(f"   ✅ Admin is {membership.role} in family group '{account.family_group.name}'")
                else:
                    print(f"   ❌ Admin not in family group '{account.family_group.name}'")
            else:
                print("   ❌ Admin cannot access (different owner, no family group)")
            
            # Fix access if needed
            if not can_access:
                print("   🔧 FIXING: Changing owner to admin user")
                account.owner = admin_user
                account.save()
                fixed_count += 1
                print("   ✅ FIXED: Account owner changed to admin")
        
        print(f"\n🎉 SUMMARY:")
        print(f"   Total accounts: {accounts.count()}")
        print(f"   Accounts fixed: {fixed_count}")
        print(f"   Admin user: {admin_user.get_full_name()}")
        print()
        
        # Show admin access URLs
        print("🌐 TEST THESE URLS (login as admin):")
        for account in accounts[:5]:  # Show first 5
            print(f"   View: http://127.0.0.1:8000/transactions/accounts/{account.id}/")
            print(f"   Edit: http://127.0.0.1:8000/transactions/accounts/{account.id}/edit/")
        
        print("\n💡 NEXT STEPS:")
        print("1. Login to Django admin: http://127.0.0.1:8000/admin/")
        print(f"2. Login as: {admin_user.email}")
        print("3. Or create a superuser: python manage.py createsuperuser")
        print("4. Try accessing the account URLs above")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    comprehensive_account_fix()