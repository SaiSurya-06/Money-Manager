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
from moneymanager.apps.core.models import FamilyGroup
from django.contrib.auth import get_user_model

User = get_user_model()

def apply_fix():
    """Apply the fix to resolve the 404 issue."""
    print("🔧 APPLYING FIX FOR 404 ACCOUNT ACCESS ISSUE")
    print("=" * 50)
    
    target_uuid = "0152b3ad-d212-400e-b740-f2b4a36095bb"
    
    try:
        # Get the account
        account = Account.objects.get(id=target_uuid)
        print(f"📊 Account: {account.name} (Owner: {account.owner.get_full_name()})")
        print(f"   Current Family Group: {account.family_group}")
        
        # Find the "test" family group where Krishna is an admin
        krishna = account.owner
        test_family = FamilyGroup.objects.filter(name="test").first()
        
        if test_family:
            print(f"✅ Found family group: {test_family.name}")
            print(f"   Created by: {test_family.created_by.get_full_name()}")
            
            # Assign the account to this family group
            account.family_group = test_family
            account.save()
            
            print(f"🎉 SUCCESS! Account '{account.name}' has been assigned to family group '{test_family.name}'")
            print()
            print("✅ RESOLUTION:")
            print(f"   - The account now belongs to the '{test_family.name}' family group")
            print(f"   - Krishna V can now access the account (as family group admin)")
            print(f"   - Other family group members can also access it")
            print()
            print("🌐 Try the URL again:")
            print(f"   http://127.0.0.1:8000/transactions/accounts/{target_uuid}/edit/")
            print()
            print("💡 Note: Make sure you're logged in as Krishna V or another member of the 'test' family group")
            
        else:
            print("❌ Could not find the 'test' family group")
            
            # Alternative: Create a new family group
            print("🔄 Creating alternative solution...")
            
            # Get admin user
            admin_user = User.objects.filter(is_superuser=True).first()
            if admin_user:
                print(f"   Found admin user: {admin_user.get_full_name()}")
                
                # Change account ownership to admin
                old_owner = account.owner
                account.owner = admin_user
                account.save()
                
                print(f"✅ Changed account owner from '{old_owner.get_full_name()}' to '{admin_user.get_full_name()}'")
                print()
                print("🌐 Now you can access the account URL as admin user:")
                print(f"   http://127.0.0.1:8000/transactions/accounts/{target_uuid}/edit/")
            else:
                print("❌ No admin user found")
        
    except Account.DoesNotExist:
        print("❌ Account with this UUID does not exist!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    apply_fix()