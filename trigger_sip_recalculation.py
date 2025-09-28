#!/usr/bin/env python3

import os
import sys
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneymanager.settings.local')
django.setup()

from moneymanager.apps.portfolios.models import SIP

def main():
    print("🔄 Triggering SIP recalculations...")
    
    # Find and recalculate all SIPs
    sips = SIP.objects.filter(name__icontains='Motilal Oswal Midcap Direct Growth')
    
    for sip in sips:
        print(f"\n📊 Recalculating: {sip.name}")
        
        # Trigger the model's built-in calculation methods
        sip.calculate_returns()
        
        # Update individual investments
        for investment in sip.investments.all():
            investment.calculate_current_value()
        
        print(f"   ✅ Updated returns: ₹{sip.total_returns:.2f} ({sip.returns_percentage:.2f}%)")
        
    print(f"\n🎉 All calculations updated!")

if __name__ == '__main__':
    main()