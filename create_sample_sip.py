"""
Test script to create sample SIP with investments showing real P&L
"""
import os
import sys
import django
from datetime import date, timedelta
from decimal import Decimal

# Setup Django environment
sys.path.append('C:\\Surya Automation\\SURYA - Money Manager')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneymanager.settings.local')
django.setup()

from django.contrib.auth import get_user_model
from moneymanager.apps.portfolios.models import Portfolio, Asset, SIP, SIPInvestment

User = get_user_model()

def create_sample_sip_data():
    """Create sample SIP and investments for testing"""
    
    # Get or create a test user
    user, created = User.objects.get_or_create(
        email='test@example.com',
        defaults={
            'first_name': 'Test',
            'last_name': 'User',
            'is_active': True
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
    
    # Get or create a portfolio
    portfolio, _ = Portfolio.objects.get_or_create(
        name='My Investment Portfolio',
        user=user,
        defaults={'description': 'Sample portfolio for SIP testing'}
    )
    
    # Get a mutual fund
    try:
        mutual_fund = Asset.objects.get(symbol='HDFC_TOP100')
    except Asset.DoesNotExist:
        print("Please run 'python manage.py add_sample_mutual_funds' first")
        return
    
    # Create SIP
    sip, created = SIP.objects.get_or_create(
        name='HDFC Top 100 Monthly SIP',
        portfolio=portfolio,
        asset=mutual_fund,
        user=user,
        defaults={
            'amount': Decimal('5000'),
            'frequency': 'monthly',
            'start_date': date.today() - timedelta(days=180),  # 6 months ago
            'next_investment_date': date.today(),
            'status': 'active'
        }
    )
    
    if created or not sip.investments.exists():
        print(f"Created SIP: {sip.name}")
        
        # Create past 6 months of investments with realistic NAV progression
        base_nav = Decimal('650.00')  # Starting NAV 6 months ago
        
        investment_dates = [
            date.today() - timedelta(days=150),  # 5 months ago
            date.today() - timedelta(days=120),  # 4 months ago  
            date.today() - timedelta(days=90),   # 3 months ago
            date.today() - timedelta(days=60),   # 2 months ago
            date.today() - timedelta(days=30),   # 1 month ago
            date.today() - timedelta(days=5),    # Recent investment
        ]
        
        nav_prices = [
            Decimal('650.00'),  # Started lower
            Decimal('668.50'),  # Gradual increase
            Decimal('685.25'),  
            Decimal('712.80'),
            Decimal('738.45'),
            Decimal('752.10'),  # Close to current price
        ]
        
        for i, (inv_date, nav_price) in enumerate(zip(investment_dates, nav_prices)):
            investment, created = SIPInvestment.objects.get_or_create(
                sip=sip,
                date=inv_date,
                defaults={
                    'amount': sip.amount,
                    'nav_price': nav_price,
                    'units_allocated': sip.amount / nav_price,
                    'current_nav': mutual_fund.current_price,
                }
            )
            if created:
                print(f"  Added investment: {inv_date} - ₹{investment.amount} @ NAV ₹{nav_price}")
        
        # Update SIP totals
        sip.update_totals()
        print(f"  Total Invested: ₹{sip.total_invested}")
        print(f"  Current Value: ₹{sip.current_value}")
        print(f"  Total Returns: ₹{sip.total_returns} ({sip.returns_percentage:.2f}%)")
        print(f"  XIRR: {sip.xirr:.2f}%")
    
    else:
        print(f"SIP already exists: {sip.name}")
        sip.calculate_returns()
        print(f"  Current Returns: ₹{sip.total_returns} ({sip.returns_percentage:.2f}%)")

if __name__ == '__main__':
    create_sample_sip_data()
    print("\nSample SIP data created! You can now:")
    print("1. Login with email: test@example.com, password: testpass123")
    print("2. Navigate to Portfolios > SIPs")
    print("3. See real-time P&L calculations with live NAV prices")
    print("4. Add new investments and track performance")