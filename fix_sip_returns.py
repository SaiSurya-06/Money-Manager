#!/usr/bin/env python3

import os
import sys
import django
from decimal import Decimal

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneymanager.settings.local')
django.setup()

from moneymanager.apps.portfolios.models import SIP, SIPInvestment

def main():
    print("🔍 Analyzing SIP returns calculation...")
    
    # Find the Motilal Oswal Midcap Direct Growth SIP
    try:
        sip = SIP.objects.filter(name__icontains='Motilal Oswal Midcap Direct Growth').first()
        if not sip:
            print("❌ SIP not found!")
            return
            
        print(f"✅ Found SIP: {sip.name}")
        print(f"   SIP ID: {sip.id}")
        
        # Get all investments
        investments = sip.investments.all().order_by('date')
        print(f"\n📊 Investment Analysis:")
        print(f"   Number of investments: {investments.count()}")
        
        total_invested = Decimal('0')
        total_units = Decimal('0')
        
        print(f"\n📋 Investment Details:")
        for inv in investments:
            total_invested += inv.amount
            total_units += inv.units_allocated
            
            print(f"   {inv.date}: ₹{inv.amount} @ ₹{inv.nav_price} = {inv.units_allocated:.4f} units")
            print(f"      Current Value: ₹{inv.current_value} | Returns: ₹{inv.returns} ({inv.returns_percentage:.2f}%)")
        
        # Current calculations
        current_nav = sip.asset.current_price
        calculated_current_value = total_units * current_nav
        calculated_returns = calculated_current_value - total_invested
        calculated_returns_pct = (calculated_returns / total_invested) * 100 if total_invested > 0 else 0
        
        print(f"\n🧮 Manual Calculation:")
        print(f"   Total Invested: ₹{total_invested:,.2f}")
        print(f"   Total Units: {total_units:.4f}")
        print(f"   Current NAV: ₹{current_nav}")
        print(f"   Calculated Current Value: ₹{calculated_current_value:,.2f}")
        print(f"   Calculated Returns: ₹{calculated_returns:,.2f}")
        print(f"   Calculated Returns %: {calculated_returns_pct:.2f}%")
        
        print(f"\n📈 SIP Model Values:")
        print(f"   SIP Total Invested: ₹{sip.total_invested:,.2f}")
        print(f"   SIP Total Units: {sip.total_units:.4f}")
        print(f"   SIP Current Value: ₹{sip.current_value:,.2f}")
        print(f"   SIP Total Returns: ₹{sip.total_returns:,.2f}")
        print(f"   SIP Returns %: {sip.returns_percentage:.2f}%")
        
        # Compare with screenshot data
        print(f"\n📱 Screenshot Comparison:")
        print(f"   Expected Invested: ₹12,000")
        print(f"   Expected Current Value: ₹12,330 (₹12K + ₹330.1 gain)")
        print(f"   Expected Returns: ₹330.1 (2.8%)")
        print(f"   Expected Individual Returns: 5.14%")
        
        # Check if we need to update values
        if abs(calculated_current_value - sip.current_value) > 0.01:
            print(f"\n⚠️  SIP values need updating!")
            
            # Update SIP values
            sip.total_invested = total_invested
            sip.total_units = total_units
            sip.current_value = calculated_current_value
            sip.total_returns = calculated_returns
            sip.returns_percentage = calculated_returns_pct
            sip.save()
            
            print(f"✅ Updated SIP values")
            
        # Update individual investment current values
        for inv in investments:
            inv.current_nav = current_nav
            inv.current_value = inv.units_allocated * current_nav
            inv.returns = inv.current_value - inv.amount
            if inv.amount > 0:
                inv.returns_percentage = (inv.returns / inv.amount) * 100
            inv.save()
            
        print(f"✅ Updated all investment current values")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()