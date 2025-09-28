"""
Management command to add major Indian mutual funds with real-time NAV prices
"""
from django.core.management.base import BaseCommand
from moneymanager.apps.portfolios.models import Asset
from moneymanager.apps.portfolios.api_services import market_data_service
from decimal import Decimal
import requests
import urllib3
from django.utils import timezone

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Command(BaseCommand):
    help = 'Add sample mutual fund assets for SIP testing'

    def handle(self, *args, **options):
        # Major Indian Mutual Funds from requested AMCs
        mutual_funds = [
            # HDFC Mutual Funds
            {
                'symbol': '120716',  # HDFC Top 100 Fund - Growth
                'name': 'HDFC Top 100 Fund - Growth',
                'amc': 'HDFC'
            },
            {
                'symbol': '118525',  # HDFC Equity Fund - Growth
                'name': 'HDFC Equity Fund - Growth',
                'amc': 'HDFC'
            },
            {
                'symbol': '118831',  # HDFC Mid-Cap Opportunities Fund - Growth
                'name': 'HDFC Mid-Cap Opportunities Fund - Growth',
                'amc': 'HDFC'
            },
            {
                'symbol': '118834',  # HDFC Small Cap Fund - Growth
                'name': 'HDFC Small Cap Fund - Growth',
                'amc': 'HDFC'
            },
            {
                'symbol': '118989',  # HDFC Index Fund - SENSEX Plan - Growth
                'name': 'HDFC Index Fund - SENSEX Plan - Growth',
                'amc': 'HDFC'
            },
            {
                'symbol': '119591',  # HDFC Flexicap Fund - Growth
                'name': 'HDFC Flexicap Fund - Growth',
                'amc': 'HDFC'
            },
            {
                'symbol': '118828',  # HDFC Balanced Advantage Fund - Growth
                'name': 'HDFC Balanced Advantage Fund - Growth',
                'amc': 'HDFC'
            },
            
            # SBI Mutual Funds
            {
                'symbol': '120716',  # SBI Bluechip Fund - Growth
                'name': 'SBI Bluechip Fund - Growth',
                'amc': 'SBI'
            },
            {
                'symbol': '119226',  # SBI Focused Equity Fund - Growth
                'name': 'SBI Focused Equity Fund - Growth',
                'amc': 'SBI'
            },
            {
                'symbol': '119527',  # SBI Small Cap Fund - Growth
                'name': 'SBI Small Cap Fund - Growth',
                'amc': 'SBI'
            },
            {
                'symbol': '120503',  # SBI Contra Fund - Growth
                'name': 'SBI Contra Fund - Growth',
                'amc': 'SBI'
            },
            {
                'symbol': '119552',  # SBI Large & Midcap Fund - Growth
                'name': 'SBI Large & Midcap Fund - Growth',
                'amc': 'SBI'
            },
            {
                'symbol': '120577',  # SBI Banking & PSU Debt Fund - Growth
                'name': 'SBI Banking & PSU Debt Fund - Growth',
                'amc': 'SBI'
            },
            {
                'symbol': '119550',  # SBI Nifty Index Fund - Growth
                'name': 'SBI Nifty Index Fund - Growth',
                'amc': 'SBI'
            },
            
            # Axis Mutual Funds
            {
                'symbol': '120503',  # Axis Bluechip Fund - Growth
                'name': 'Axis Bluechip Fund - Growth',
                'amc': 'Axis'
            },
            {
                'symbol': '120505',  # Axis Midcap Fund - Growth
                'name': 'Axis Midcap Fund - Growth',
                'amc': 'Axis'
            },
            {
                'symbol': '120506',  # Axis Small Cap Fund - Growth
                'name': 'Axis Small Cap Fund - Growth',
                'amc': 'Axis'
            },
            {
                'symbol': '120504',  # Axis Focused 25 Fund - Growth
                'name': 'Axis Focused 25 Fund - Growth',
                'amc': 'Axis'
            },
            {
                'symbol': '149734',  # Axis Growth Opportunities Fund - Growth
                'name': 'Axis Growth Opportunities Fund - Growth',
                'amc': 'Axis'
            },
            {
                'symbol': '120502',  # Axis Long Term Equity Fund - Growth
                'name': 'Axis Long Term Equity Fund - Growth (ELSS)',
                'amc': 'Axis'
            },
            {
                'symbol': '120501',  # Axis Nifty 100 Index Fund - Growth
                'name': 'Axis Nifty 100 Index Fund - Growth',
                'amc': 'Axis'
            },
            
            # Motilal Oswal Mutual Funds
            {
                'symbol': '125497',  # Motilal Oswal Large Cap Fund - Growth
                'name': 'Motilal Oswal Large Cap Fund - Growth',
                'amc': 'Motilal Oswal'
            },
            {
                'symbol': '125498',  # Motilal Oswal Midcap Fund - Growth
                'name': 'Motilal Oswal Midcap Fund - Growth',
                'amc': 'Motilal Oswal'
            },
            {
                'symbol': '125499',  # Motilal Oswal Small Cap Fund - Growth
                'name': 'Motilal Oswal Small Cap Fund - Growth',
                'amc': 'Motilal Oswal'
            },
            {
                'symbol': '125500',  # Motilal Oswal Focused 25 Fund - Growth
                'name': 'Motilal Oswal Focused 25 Fund - Growth',
                'amc': 'Motilal Oswal'
            },
            {
                'symbol': '125501',  # Motilal Oswal Nasdaq 100 Fund of Fund - Growth
                'name': 'Motilal Oswal Nasdaq 100 Fund of Fund - Growth',
                'amc': 'Motilal Oswal'
            },
            {
                'symbol': '125502',  # Motilal Oswal S&P 500 Index Fund - Growth
                'name': 'Motilal Oswal S&P 500 Index Fund - Growth',
                'amc': 'Motilal Oswal'
            },
            {
                'symbol': '125503',  # Motilal Oswal Business Cycles Fund - Growth
                'name': 'Motilal Oswal Business Cycles Fund - Growth',
                'amc': 'Motilal Oswal'
            },
            {
                'symbol': '125504',  # Motilal Oswal Nifty 500 Fund - Growth
                'name': 'Motilal Oswal Nifty 500 Fund - Growth',
                'amc': 'Motilal Oswal'
            }
        ]

        created_count = 0
        updated_count = 0
        price_fetch_errors = []

        self.stdout.write(
            self.style.WARNING('Fetching real-time NAV prices from MF API...')
        )

        for fund_data in mutual_funds:
            # Fetch real-time NAV price
            current_nav = self.get_real_time_nav(fund_data['symbol'])
            
            if not current_nav:
                # Fallback to default price if API fails
                current_nav = Decimal('100.00')
                price_fetch_errors.append(fund_data['name'])
            
            asset, created = Asset.objects.get_or_create(
                symbol=fund_data['symbol'],
                defaults={
                    'name': fund_data['name'],
                    'asset_type': 'mutual_fund',
                    'currency': 'INR',
                    'current_price': current_nav,
                    'sector': fund_data['amc'],  # Store AMC in sector field
                    'price_updated_at': timezone.now(),
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created: {asset.name} (NAV: ₹{current_nav})'
                    )
                )
            else:
                # Update price and AMC if asset exists
                asset.current_price = current_nav
                asset.sector = fund_data['amc']
                asset.price_updated_at = timezone.now()
                asset.save(update_fields=['current_price', 'sector', 'price_updated_at'])
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'Updated: {asset.name} (NAV: ₹{current_nav})'
                    )
                )

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Created {created_count} new funds, '
                f'updated {updated_count} existing funds.'
            )
        )
        
        if price_fetch_errors:
            self.stdout.write(
                self.style.ERROR(
                    f'NAV fetch failed for {len(price_fetch_errors)} funds: '
                    f'{", ".join(price_fetch_errors[:3])}'
                    f'{"..." if len(price_fetch_errors) > 3 else ""}'
                )
            )

    def get_real_time_nav(self, scheme_code):
        """Fetch real-time NAV from MF API"""
        try:
            # First try MF API
            url = f"https://api.mfapi.in/mf/{scheme_code}"
            response = requests.get(url, timeout=10, verify=False)
            response.raise_for_status()
            
            data = response.json()
            
            if data and isinstance(data, dict) and 'data' in data:
                nav_data = data['data']
                if nav_data and len(nav_data) > 0:
                    latest_nav = nav_data[0].get('nav')
                    if latest_nav:
                        return Decimal(str(latest_nav))
            
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'MF API error for {scheme_code}: {e}')
            )
        
        # Fallback: Try market data service
        try:
            price = market_data_service.get_current_price(scheme_code)
            if price:
                return Decimal(str(price))
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Market service error for {scheme_code}: {e}')
            )
        
        return None