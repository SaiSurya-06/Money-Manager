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
from moneymanager.apps.core.models import FamilyGroup
from django.contrib.auth import get_user_model

User = get_user_model()

def diagnose_404_issue():
    """Diagnose the 404 issue with account access."""
    print("🔍 DIAGNOSING 404 ACCOUNT ACCESS ISSUE")
    print("=" * 60)
    
    target_uuid = "0152b3ad-d212-400e-b740-f2b4a36095bb"
    
    try:
        account = Account.objects.get(id=target_uuid)
        print(f"📊 Account: {account.name}")
        print(f"   Owner: {account.owner.get_full_name()} ({account.owner.email})")
        print(f"   Family Group: {account.family_group}")
        print(f"   Active: {account.is_active}")
        print()
        
        # Check family groups
        print("👨‍👩‍👧‍👦 Family Groups:")
        family_groups = FamilyGroup.objects.all()
        if family_groups.exists():
            for fg in family_groups:
                print(f"  - {fg.name} (Admin: {fg.admin})")
                members = fg.members.all()
                print(f"    Members: {[m.get_full_name() for m in members]}")
        else:
            print("  ❌ No family groups exist")
        print()
        
        # Show the access logic
        print("🔐 ACCESS LOGIC ANALYSIS:")
        print("The AccountUpdateView.get_queryset() filters accounts as follows:")
        print("1. Only active accounts (✅ This account is active)")
        print("2. IF user has family_group:")
        print("   - Show accounts where family_group = user's family_group")
        print("3. ELSE (no family_group):")
        print("   - Show accounts where owner = current_user AND family_group = None")
        print()
        
        print("🎯 SOLUTION:")
        print("The 404 error occurs because:")
        print("1. The current user is NOT Krishna V (the account owner)")
        print("2. The account has family_group = None") 
        print("3. Only Krishna V can access this account")
        print()
        
        print("✅ TO FIX THIS ISSUE:")
        print("1. Login as krishna@gmail.com, OR")
        print("2. Add Krishna to a family group and update the account's family_group, OR")
        print("3. Change the account owner to the current user")
        print()
        
        print("🔧 QUICK FIXES:")
        print("# Option 1: Login as the account owner")
        print("   Navigate to /admin/ and login as krishna@gmail.com")
        print()
        print("# Option 2: Change account owner to current user")
        print("   (Need to know who the current user is)")
        print()
        print("# Option 3: Add to family group")
        print("   Create a family group and add both users")
        
    except Account.DoesNotExist:
        print("❌ Account with this UUID does not exist!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    diagnose_404_issue()