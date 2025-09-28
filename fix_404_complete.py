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

def fix_404_issue():
    """Complete diagnosis and solution for the 404 issue."""
    print("🔍 COMPLETE 404 DIAGNOSIS & SOLUTION")
    print("=" * 60)
    
    target_uuid = "0152b3ad-d212-400e-b740-f2b4a36095bb"
    
    try:
        account = Account.objects.get(id=target_uuid)
        print(f"📊 ACCOUNT DETAILS:")
        print(f"   UUID: {account.id}")
        print(f"   Name: {account.name}")
        print(f"   Owner: {account.owner.get_full_name()} ({account.owner.email})")
        print(f"   Family Group: {account.family_group}")
        print(f"   Active: {account.is_active}")
        print()
        
        # Check family groups
        print("👨‍👩‍👧‍👦 FAMILY GROUPS:")
        family_groups = FamilyGroup.objects.all()
        if family_groups.exists():
            for fg in family_groups:
                memberships = FamilyGroupMembership.objects.filter(family_group=fg, is_active=True)
                admin_members = memberships.filter(role='admin')
                print(f"  - {fg.name}")
                print(f"    Created by: {fg.created_by.get_full_name()}")
                print(f"    Admins: {[m.user.get_full_name() for m in admin_members]}")
                print(f"    All members: {[m.user.get_full_name() for m in memberships]}")
        else:
            print("  ❌ No family groups exist")
        print()
        
        # Explain the issue
        print("🚨 PROBLEM ANALYSIS:")
        print("The AccountUpdateView restricts access based on:")
        print("1. ✅ Account must be active (this account IS active)")
        print("2. 🔐 Permission check:")
        print("   - If user has family_group: show accounts in that family_group")
        print("   - If no family_group: show only accounts owned by current user")
        print()
        print(f"❌ ISSUE: Current user is NOT '{account.owner.get_full_name()}'")
        print("   Only the account owner can edit accounts when not in a family group.")
        print()
        
        # Provide solutions
        print("✅ SOLUTIONS:")
        print()
        print("OPTION 1: Login as the account owner")
        print("   - Go to /admin/ or login page")
        print(f"   - Login as: {account.owner.email}")
        print("   - Password: (you'll need to know/reset it)")
        print()
        
        print("OPTION 2: Change account ownership")
        print("   - Make the current user the owner of this account")
        print("   - This can be done via Django admin or database")
        print()
        
        print("OPTION 3: Create/Join a family group")  
        print("   - Add both users to the same family group")
        print("   - Update the account to belong to that family group")
        print("   - Then family group members can access the account")
        print()
        
        print("OPTION 4: Modify permissions (Advanced)")
        print("   - Update the AccountUpdateView to allow broader access")
        print("   - ⚠️  This affects security - be careful!")
        print()
        
        # Show practical fix commands
        print("🔧 QUICK FIXES (Django Shell Commands):")
        print("# Fix 1: Change account owner to current admin user")
        print("from moneymanager.apps.transactions.models import Account")
        print("from django.contrib.auth import get_user_model")
        print("User = get_user_model()")
        print(f'account = Account.objects.get(id="{target_uuid}")')
        print('admin_user = User.objects.filter(is_superuser=True).first()')
        print('account.owner = admin_user')
        print('account.save()')
        print('print("Account owner changed!")')
        print()
        
        print("# Fix 2: Create family group and add both users")
        print("from moneymanager.apps.core.models import FamilyGroup, FamilyGroupMembership")
        print('fg = FamilyGroup.objects.create(name="Test Family", created_by=admin_user)')
        print('FamilyGroupMembership.objects.create(user=admin_user, family_group=fg, role="admin")')
        print(f'FamilyGroupMembership.objects.create(user=account.owner, family_group=fg, role="member")')
        print('account.family_group = fg')
        print('account.save()')
        print('print("Family group created and account updated!")')
        
    except Account.DoesNotExist:
        print("❌ Account with this UUID does not exist!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_404_issue()