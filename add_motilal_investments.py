#!/usr/bin/env python
"""
Add sample investments to the Motilal Oswal SIP to demonstrate functionality.
"""
import os
import sys
import django
from datetime import date
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneymanager.settings.local')
django.setup()

from moneymanager.apps.portfolios.models import SIP, SIPInvestment

def add_sample_investments():
    """Add sample investments to Motilal Oswal SIP."""
    print("💰 Adding Sample Investments to Motilal Oswal SIP...")
    print("=" * 60)
    
    try:
        # Find Motilal Oswal SIP
        motilal_sip = SIP.objects.filter(name__icontains='Motilal Oswal').first()
        
        if not motilal_sip:
            print("❌ Motilal Oswal SIP not found")
            return False
        
        print(f"📊 Found SIP: {motilal_sip.name}")
        print(f"   Amount: ₹{motilal_sip.amount}")
        print(f"   Current Investments: {motilal_sip.investments.count()}")
        
        # Sample investment data for Motilal Oswal Midcap Fund
        sample_investments = [
            {'date': date(2025, 2, 9), 'nav': 150.25, 'amount': 1500},
            {'date': date(2025, 3, 9), 'nav': 155.80, 'amount': 1500},
            {'date': date(2025, 4, 9), 'nav': 148.90, 'amount': 1500},
            {'date': date(2025, 5, 9), 'nav': 162.45, 'amount': 1500},
            {'date': date(2025, 6, 9), 'nav': 158.70, 'amount': 1500},
            {'date': date(2025, 7, 9), 'nav': 165.30, 'amount': 1500},
            {'date': date(2025, 8, 9), 'nav': 159.85, 'amount': 1500},
            {'date': date(2025, 9, 9), 'nav': 168.90, 'amount': 1500},
        ]
        
        print(f"\n💾 Creating {len(sample_investments)} sample investments...")
        
        created_count = 0
        for inv_data in sample_investments:
            # Check if investment already exists for this date
            existing = SIPInvestment.objects.filter(
                sip=motilal_sip,
                date=inv_data['date']
            ).exists()
            
            if not existing:
                amount = Decimal(str(inv_data['amount']))
                nav_price = Decimal(str(inv_data['nav']))
                units = amount / nav_price
                
                investment = SIPInvestment.objects.create(
                    sip=motilal_sip,
                    date=inv_data['date'],
                    amount=amount,
                    nav_price=nav_price,
                    units_allocated=units,
                    current_nav=motilal_sip.asset.current_price,
                    notes="Sample investment data"
                )
                
                print(f"   ✅ {investment.date}: ₹{investment.amount} @ ₹{investment.nav_price:.2f} = {investment.units_allocated:.6f} units")
                created_count += 1
            else:
                print(f"   ⏭️ {inv_data['date']}: Investment already exists")
        
        print(f"\n🔄 Updating SIP calculations...")
        
        # Update all investment current values
        for investment in motilal_sip.investments.all():
            investment.calculate_current_value()
        
        # Update SIP totals
        motilal_sip.update_totals()
        
        print(f"📈 SIP Performance Updated:")
        print(f"   Total Investments: {motilal_sip.investments.count()}")
        print(f"   Total Invested: ₹{motilal_sip.total_invested:,.2f}")
        print(f"   Total Units: {motilal_sip.total_units:,.6f}")
        print(f"   Current Value: ₹{motilal_sip.current_value:,.2f}")
        print(f"   Total Returns: ₹{motilal_sip.total_returns:,.2f}")
        print(f"   Returns %: {motilal_sip.returns_percentage:.2f}%")
        print(f"   XIRR: {motilal_sip.xirr:.2f}%")
        
        print(f"\n🌐 View updated SIP at:")
        print(f"   http://127.0.0.1:8000/portfolios/sips/{motilal_sip.pk}/")
        
        print(f"\n🎉 SUCCESS: Added {created_count} new investments!")
        print(f"✅ SIP now shows complete investment history")
        print(f"✅ Performance metrics calculated")
        print(f"✅ Ready for viewing in browser")
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding investments: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = add_sample_investments()
    sys.exit(0 if success else 1)