#!/usr/bin/env python3

import os
import sys
import django
from datetime import date, datetime
from decimal import Decimal

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneymanager.settings.local')
django.setup()

from moneymanager.apps.portfolios.models import Asset, Portfolio, SIP, SIPInvestment
from moneymanager.apps.accounts.models import User

def main():
    print("🎯 Creating SIP for Motilal Oswal Midcap Direct Growth...")
    
    # Get the fund
    try:
        fund = Asset.objects.get(name='Motilal Oswal Midcap Direct Growth')
        print(f"✅ Found fund: {fund.name} - ₹{fund.current_price}")
    except Asset.DoesNotExist:
        print("❌ Fund not found!")
        return
    
    # Get user and portfolio
    user = User.objects.first()
    portfolio, _ = Portfolio.objects.get_or_create(
        user=user,
        name='My Portfolio',
        defaults={'description': 'Main investment portfolio'}
    )
    
    # Create SIP matching your screenshot data
    sip = SIP.objects.create(
        portfolio=portfolio,
        asset=fund,
        name=f'SIP - {fund.name}',
        amount=Decimal('2000.00'),  # ₹2K monthly to get ₹12K total
        frequency='monthly',
        start_date=date(2024, 7, 1),  # Started in July 2024 to accumulate to ₹12K
        status='active',
        next_investment_date=date(2025, 1, 1),
        user=user
    )
    
    print(f"✅ Created SIP: {sip.name}")
    print(f"   Monthly Amount: ₹{sip.amount}")
    print(f"   Start Date: {sip.start_date}")
    print(f"   Status: {sip.status}")
    
    # Add investment history to match your ₹12K invested
    investment_data = [
        # Month, NAV Price, Amount
        ('2024-07-01', Decimal('110.50'), Decimal('2000.00')),
        ('2024-08-01', Decimal('111.20'), Decimal('2000.00')),
        ('2024-09-01', Decimal('112.10'), Decimal('2000.00')),
        ('2024-10-01', Decimal('113.30'), Decimal('2000.00')),
        ('2024-11-01', Decimal('112.80'), Decimal('2000.00')),
        ('2024-12-01', Decimal('114.20'), Decimal('2000.00')),  # Current NAV from screenshot
    ]
    
    total_invested = Decimal('0.00')
    total_units = Decimal('0.00')
    
    print(f"\n📊 Adding investment history:")
    for inv_date, nav_price, amount in investment_data:
        units = amount / nav_price
        
        investment = SIPInvestment.objects.create(
            sip=sip,
            date=datetime.strptime(inv_date, '%Y-%m-%d').date(),
            amount=amount,
            nav_price=nav_price,
            units_allocated=units,
            current_nav=fund.current_price
        )
        
        total_invested += amount
        total_units += units
        
        print(f"   {inv_date}: ₹{amount} @ ₹{nav_price} = {units:.4f} units")
    
    # Update SIP totals
    sip.total_invested = total_invested
    sip.total_units = total_units
    sip.save()
    
    # Calculate current value
    current_value = total_units * fund.current_price
    returns = current_value - total_invested
    returns_pct = (returns / total_invested) * 100 if total_invested > 0 else 0
    
    print(f"\n🎉 SIP Summary:")
    print(f"   Total Invested: ₹{total_invested:,.2f}")
    print(f"   Total Units: {total_units:.4f}")
    print(f"   Current NAV: ₹{fund.current_price}")
    print(f"   Current Value: ₹{current_value:,.2f}")
    print(f"   Total Gain: ₹{returns:,.2f} ({returns_pct:.2f}%)")
    
    print(f"\n🔗 View your SIP at: http://127.0.0.1:8000/portfolios/sips/{sip.id}/")

if __name__ == '__main__':
    main()