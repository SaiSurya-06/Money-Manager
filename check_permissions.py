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
from django.contrib.auth import get_user_model

User = get_user_model()

def check_account_permissions():
    """Check account permissions and family groups."""
    print("🔍 CHECKING ACCOUNT PERMISSIONS")
    print("=" * 50)
    
    target_uuid = "0152b3ad-d212-400e-b740-f2b4a36095bb"
    
    try:
        account = Account.objects.get(id=target_uuid)
        print(f"📊 Account Details:")
        print(f"  Name: {account.name}")
        print(f"  Owner: {account.owner} ({account.owner.email})")
        print(f"  Family Group: {account.family_group}")
        print(f"  Active: {account.is_active}")
        print()
        
        # Check all users
        users = User.objects.all()
        print(f"👥 All Users ({users.count()}):")
        for user in users:
            print(f"  - {user.get_full_name()} ({user.email})")
            
            # Check if they can access this account
            if hasattr(user, 'current_family_group'):
                family_group = user.current_family_group
            else:
                family_group = None
                
            # Simulate the view's queryset logic
            queryset = Account.objects.filter(is_active=True)
            if family_group:
                queryset = queryset.filter(family_group=family_group)
            else:
                queryset = queryset.filter(owner=user, family_group__isnull=True)
            
            can_access = queryset.filter(id=target_uuid).exists()
            print(f"    - Can access account: {'✅ Yes' if can_access else '❌ No'}")
            print(f"    - Family Group: {family_group}")
            
        print()
        
        # Check family groups
        print("👨‍👩‍👧‍👦 Family Groups:")
        from moneymanager.apps.accounts.models import FamilyGroup
        family_groups = FamilyGroup.objects.all()
        
        for fg in family_groups:
            print(f"  Family: {fg.name}")
            print(f"    Admin: {fg.admin}")
            print(f"    Members: {[m.get_full_name() for m in fg.members.all()]}")
            
            # Check if account belongs to this family group
            if account.family_group == fg:
                print(f"    ✅ This account belongs to this family group")
            else:
                print(f"    ❌ This account does NOT belong to this family group")
            print()
            
    except Account.DoesNotExist:
        print("❌ Account with this UUID does not exist!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_account_permissions()