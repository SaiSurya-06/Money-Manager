#!/usr/bin/env python3

import os
import sys
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneymanager.settings.local')
django.setup()

from moneymanager.apps.portfolios.models import Asset

def main():
    print("🔍 Searching for Motilal Oswal Midcap funds...")
    
    # Search for all Motilal Oswal funds containing 'Midcap' or 'Mid'
    funds = Asset.objects.filter(
        name__icontains='Motilal Oswal'
    ).filter(
        name__icontains='Mid'
    )
    
    print(f"\n📊 Found {funds.count()} Motilal Oswal Midcap funds:")
    
    for fund in funds:
        print(f"\n  🏛️  {fund.name}")
        print(f"      Symbol: {fund.symbol}")
        print(f"      NAV: ₹{fund.current_price if fund.current_price else 'Not available'}")
        print(f"      Asset Type: {fund.asset_type}")
    
    # Check for exact match with screenshot
    exact_match = Asset.objects.filter(name__iexact='Motilal Oswal Midcap Direct Growth')
    if exact_match.exists():
        print(f"\n✅ Exact match found: {exact_match.first().name}")
    else:
        print("\n❌ No exact match for 'Motilal Oswal Midcap Direct Growth'")
        print("🔧 Adding this fund to the system now...")
        
        # Add the Direct Growth variant
        new_fund = Asset.objects.create(
            name='Motilal Oswal Midcap Direct Growth',
            symbol='MOTILAL_MIDCAP_DIRECT',
            asset_type='MUTUAL_FUND',
            current_price=114.20,  # NAV from screenshot
        )
        print(f"✅ Added: {new_fund.name} with NAV ₹{new_fund.current_price}")
        
    print(f"\n📈 Now showing your SIP-ready Motilal Oswal funds:")
    updated_funds = Asset.objects.filter(name__icontains='Motilal Oswal').filter(name__icontains='Mid')
    for fund in updated_funds:
        print(f"  • {fund.name} - ₹{fund.current_price}")

if __name__ == '__main__':
    main()