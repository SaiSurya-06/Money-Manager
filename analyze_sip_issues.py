#!/usr/bin/env python3

import os
import sys
import django
from decimal import Decimal

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneymanager.settings.local')
django.setup()

from moneymanager.apps.portfolios.models import SIP, SIPInvestment, Asset

def main():
    print("🔍 Analyzing SIP issues from screenshot...")
    
    # List all Motilal Oswal SIPs
    sips = SIP.objects.filter(name__icontains='Motilal')
    print(f"\n📊 Found {sips.count()} Motilal Oswal SIPs:")
    
    for sip in sips:
        print(f"\n  🏛️ SIP: {sip.name}")
        print(f"     ID: {sip.id}")
        print(f"     Asset: {sip.asset.name}")
        print(f"     Asset NAV: ₹{sip.asset.current_price}")
        print(f"     Monthly Amount: ₹{sip.amount}")
        print(f"     Total Invested: ₹{sip.total_invested}")
        print(f"     Current Value: ₹{sip.current_value}")
        print(f"     Returns: ₹{sip.total_returns} ({sip.returns_percentage:.2f}%)")
        print(f"     Status: {sip.status}")
        print(f"     Investments: {sip.investments.count()}")
    
    # Check for the correct SIP (Direct Growth)
    correct_sip = SIP.objects.filter(asset__name__icontains='Direct Growth').first()
    if correct_sip:
        print(f"\n✅ Found Direct Growth SIP: {correct_sip.name}")
        print(f"   Asset: {correct_sip.asset.name}")
        print(f"   NAV: ₹{correct_sip.asset.current_price}")
    else:
        print(f"\n❌ Direct Growth SIP not found!")
    
    # Check for duplicate or incorrect SIPs
    incorrect_sips = SIP.objects.filter(
        name__icontains='Motilal',
        asset__name__icontains='Fund - Growth'
    ).exclude(asset__name__icontains='Direct')
    
    print(f"\n🔧 Found {incorrect_sips.count()} incorrect SIPs to fix:")
    
    for sip in incorrect_sips:
        print(f"   - {sip.name} (using {sip.asset.name})")
        
        # Check if this SIP has the high returns but wrong asset
        if sip.total_returns > 200000:  # High returns like ₹227243
            print(f"     📈 This SIP has high returns (₹{sip.total_returns}) - needs asset correction")
            
            # Find or create the correct Direct Growth asset
            direct_asset, created = Asset.objects.get_or_create(
                name='Motilal Oswal Midcap Direct Growth',
                defaults={
                    'symbol': 'MOTILAL_MIDCAP_DIRECT',
                    'asset_type': 'mutual_fund',
                    'current_price': Decimal('115.43')
                }
            )
            
            if created:
                print(f"     ✅ Created Direct Growth asset")
            
            # Update SIP to use correct asset
            old_asset = sip.asset.name
            sip.asset = direct_asset
            sip.name = f'SIP - {direct_asset.name}'
            sip.save()
            
            print(f"     ✅ Updated SIP asset: {old_asset} → {direct_asset.name}")
            
            # Recalculate with correct NAV
            sip.calculate_returns()
            print(f"     ✅ Recalculated returns: ₹{sip.total_returns} ({sip.returns_percentage:.2f}%)")

if __name__ == '__main__':
    main()