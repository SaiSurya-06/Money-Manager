#!/usr/bin/env python3

import os
import sys
import django
from datetime import date, timedelta

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneymanager.settings.local')
django.setup()

from moneymanager.apps.portfolios.models import SIP

def main():
    print("🔄 Testing Auto-Investment Setup...")
    
    # Find existing SIPs
    sips = SIP.objects.all()
    print(f"\n📊 Found {sips.count()} total SIPs:")
    
    for sip in sips:
        print(f"\n  🏛️  {sip.name}")
        print(f"      Auto-Invest: {'✅ Enabled' if sip.auto_invest else '❌ Disabled'}")
        print(f"      Status: {sip.status}")
        print(f"      Next Investment: {sip.next_investment_date}")
        
        # Check if SIP is due
        if sip.next_investment_date <= date.today():
            print(f"      🚨 DUE FOR INVESTMENT!")
        elif sip.next_investment_date <= date.today() + timedelta(days=7):
            days_until = (sip.next_investment_date - date.today()).days
            print(f"      ⏰ Due in {days_until} day(s)")
    
    # Enable auto-invest for all active SIPs (for testing)
    active_sips = SIP.objects.filter(status='active', auto_invest=False)
    if active_sips.exists():
        print(f"\n🔧 Enabling auto-invest for {active_sips.count()} active SIPs...")
        updated_count = active_sips.update(auto_invest=True)
        print(f"✅ Updated {updated_count} SIPs to enable auto-investment")
    
    # Show SIPs that would be processed
    due_sips = SIP.objects.filter(
        auto_invest=True,
        status='active',
        next_investment_date__lte=date.today()
    )
    
    print(f"\n📈 SIPs eligible for automatic investment today:")
    if due_sips.exists():
        total_amount = 0
        for sip in due_sips:
            print(f"  • {sip.name}: ₹{sip.amount} (Due: {sip.next_investment_date})")
            total_amount += sip.amount
        print(f"\n💰 Total investment amount: ₹{total_amount:,.2f}")
        
        print(f"\n🚀 To process these investments, run:")
        print(f"   python manage.py process_auto_sips")
        print(f"   python manage.py process_auto_sips --dry-run  (to preview)")
    else:
        print("  No SIPs are due for investment today.")
    
    print(f"\n📅 Setting up daily auto-investment processing:")
    print(f"   1. Add to crontab (Linux/Mac): 0 9 * * * python manage.py process_auto_sips")
    print(f"   2. Add to Task Scheduler (Windows): Daily at 9:00 AM")
    print(f"   3. Or run manually when needed")

if __name__ == '__main__':
    main()