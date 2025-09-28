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
        print(f"      Last Updated: {fund.last_price_update or 'Never'}")
        print(f"      Asset Type: {fund.asset_type}")
    
    # Also check if we need to add Direct Growth variant
    direct_growth = funds.filter(name__icontains='Direct')
    print(f"\n🎯 Direct Growth variants: {direct_growth.count()}")
    
    # Search for exact match with screenshot
    exact_match = Asset.objects.filter(name__iexact='Motilal Oswal Midcap Direct Growth')
    if exact_match.exists():
        print(f"\n✅ Exact match found: {exact_match.first().name}")
    else:
        print("\n❌ No exact match for 'Motilal Oswal Midcap Direct Growth'")
        
        # Check if we can add it
        print("\n🔧 We should add this fund to the system!")
        
    # Show all Motilal Oswal funds
    all_motilal = Asset.objects.filter(name__icontains='Motilal Oswal')
    print(f"\n📈 Total Motilal Oswal funds in system: {all_motilal.count()}")

if __name__ == '__main__':
    main()