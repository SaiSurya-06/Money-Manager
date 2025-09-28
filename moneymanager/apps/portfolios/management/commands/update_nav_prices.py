"""
Management command to update mutual fund NAV prices in real-time
"""
from django.core.management.base import BaseCommand
from moneymanager.apps.portfolios.models import Asset, SIP, SIPInvestment
from moneymanager.apps.portfolios.api_services import market_data_service
import requests
import urllib3
from decimal import Decimal
from django.utils import timezone

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Command(BaseCommand):
    help = 'Update NAV prices for all mutual funds and recalculate SIP returns'

    def add_arguments(self, parser):
        parser.add_argument(
            '--funds',
            nargs='+',
            help='Specific fund symbols to update (optional)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if recently updated',
        )

    def handle(self, *args, **options):
        # Get mutual funds to update
        if options['funds']:
            mutual_funds = Asset.objects.filter(
                symbol__in=options['funds'],
                asset_type='mutual_fund',
                is_active=True
            )
        else:
            mutual_funds = Asset.objects.filter(
                asset_type='mutual_fund',
                is_active=True
            )

        if not mutual_funds.exists():
            self.stdout.write(
                self.style.ERROR('No mutual funds found to update.')
            )
            return

        updated_count = 0
        error_count = 0
        total_funds = mutual_funds.count()

        self.stdout.write(
            f'Updating NAV prices for {total_funds} mutual funds...'
        )

        for fund in mutual_funds:
            try:
                # Check if recently updated (unless force flag is used)
                if not options['force'] and fund.price_updated_at:
                    time_diff = timezone.now() - fund.price_updated_at
                    if time_diff.seconds < 3600:  # Updated within last hour
                        self.stdout.write(
                            self.style.WARNING(
                                f'Skipping {fund.name} - recently updated'
                            )
                        )
                        continue

                # Fetch new NAV price
                new_nav = self.get_real_time_nav(fund.symbol)
                
                if new_nav and new_nav != fund.current_price:
                    old_price = fund.current_price
                    fund.current_price = new_nav
                    fund.price_updated_at = timezone.now()
                    fund.save(update_fields=['current_price', 'price_updated_at'])
                    
                    updated_count += 1
                    change = new_nav - old_price
                    change_pct = (change / old_price * 100) if old_price > 0 else 0
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Updated {fund.name}: ₹{old_price} → ₹{new_nav} '
                            f'({change_pct:+.2f}%)'
                        )
                    )
                    
                    # Update related SIP calculations
                    self.update_sip_calculations(fund)
                    
                elif new_nav:
                    self.stdout.write(
                        f'No price change for {fund.name}: ₹{new_nav}'
                    )
                else:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'Failed to fetch NAV for {fund.name}')
                    )

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'Error updating {fund.name}: {e}')
                )

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nPrice Update Summary:'
                f'\n  Updated: {updated_count} funds'
                f'\n  Errors: {error_count} funds'
                f'\n  Total processed: {total_funds} funds'
            )
        )

    def get_real_time_nav(self, scheme_code):
        """Fetch real-time NAV from MF API"""
        try:
            # MF API for Indian mutual funds
            url = f"https://api.mfapi.in/mf/{scheme_code}"
            response = requests.get(url, timeout=15, verify=False)
            response.raise_for_status()
            
            data = response.json()
            
            if data and isinstance(data, dict) and 'data' in data:
                nav_data = data['data']
                if nav_data and len(nav_data) > 0:
                    latest_nav = nav_data[0].get('nav')
                    if latest_nav:
                        return Decimal(str(latest_nav))
            
        except Exception as e:
            # Try Alpha Vantage as fallback
            try:
                price = market_data_service.get_current_price(scheme_code)
                if price:
                    return Decimal(str(price))
            except:
                pass
        
        return None

    def update_sip_calculations(self, fund):
        """Update SIP calculations for funds with updated NAV"""
        try:
            # Find all SIPs using this fund
            affected_sips = SIP.objects.filter(asset=fund, status='active')
            
            for sip in affected_sips:
                # Update all investment values
                for investment in sip.investments.all():
                    investment.calculate_current_value()
                
                # Update SIP totals and returns
                sip.calculate_returns()
                
                self.stdout.write(
                    f'  Updated SIP: {sip.name} - Returns: {sip.returns_percentage:.2f}%'
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Error updating SIP calculations: {e}')
            )