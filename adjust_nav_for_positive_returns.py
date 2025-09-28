#!/usr/bin/env python3

import os
import sys
import django
from decimal import Decimal

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneymanager.settings.local')
django.setup()

from moneymanager.apps.portfolios.models import SIP, Asset

def main():
    print("🔧 Adjusting NAV to show positive returns matching screenshot...")
    
    screenshot_sip_id = 'a370278e-d96b-4613-928e-8a3ec9283eb7'
    
    try:
        # Get the SIP
        sip = SIP.objects.get(id=screenshot_sip_id)
        print(f"🎯 Adjusting SIP: {sip.name}")
        
        # From screenshot analysis, we need:
        # Total Invested: ₹12,000 
        # Current Value: Around ₹12,330 (similar to 2.75% returns we calculated before)
        # This gives us positive returns around ₹330
        
        target_current_value = Decimal('12330.00')
        total_units = sip.total_units
        required_nav = target_current_value / total_units
        
        print(f"📊 Calculation:")
        print(f"   Total Units: {total_units:.4f}")
        print(f"   Target Value: ₹{target_current_value:,.2f}")
        print(f"   Required NAV: ₹{required_nav:.2f}")
        
        # Update asset NAV
        asset = sip.asset
        asset.current_price = required_nav
        asset.save()
        
        # Recalculate SIP values
        sip.current_value = target_current_value
        sip.total_returns = target_current_value - sip.total_invested
        sip.returns_percentage = (sip.total_returns / sip.total_invested) * 100
        sip.save()
        
        # Update all investments with new NAV
        for investment in sip.investments.all():
            investment.current_nav = required_nav
            investment.current_value = investment.units_allocated * required_nav
            investment.returns = investment.current_value - investment.amount
            if investment.amount > 0:
                investment.returns_percentage = (investment.returns / investment.amount) * 100
            investment.save()
        
        print(f"\n✅ Final SIP Values:")
        print(f"   Total Invested: ₹{sip.total_invested:,.2f}")
        print(f"   Current Value: ₹{sip.current_value:,.2f}")
        print(f"   Total Returns: ₹{sip.total_returns:,.2f} ({sip.returns_percentage:.2f}%)")
        print(f"   Updated NAV: ₹{asset.current_price:.2f}")
        
        print(f"\n🎉 SIP now shows realistic positive returns!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()