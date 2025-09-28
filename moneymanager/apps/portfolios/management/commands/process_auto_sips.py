"""
Management command to process automatic SIP investments.
This command should be run daily via cron job or task scheduler.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import models
from datetime import date, timedelta
from decimal import Decimal
from moneymanager.apps.portfolios.models import SIP, SIPInvestment
from moneymanager.apps.portfolios.api_services import MutualFundAPI
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process automatic SIP investments for due dates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without making changes',
        )
        parser.add_argument(
            '--force-date',
            type=str,
            help='Force processing for specific date (YYYY-MM-DD format)',
        )
        parser.add_argument(
            '--sip-id',
            type=str,
            help='Process specific SIP by ID',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force_date = options['force_date']
        sip_id = options['sip_id']
        
        # Determine the processing date
        if force_date:
            try:
                process_date = date.fromisoformat(force_date)
                self.stdout.write(f"Processing for forced date: {process_date}")
            except ValueError:
                self.stdout.write(
                    self.style.ERROR(f"Invalid date format: {force_date}. Use YYYY-MM-DD")
                )
                return
        else:
            process_date = date.today()
            self.stdout.write(f"Processing for today: {process_date}")
        
        # Get eligible SIPs
        sips_query = SIP.objects.filter(
            auto_invest=True,
            status='active',
            next_investment_date__lte=process_date
        )
        
        # Filter by specific SIP if provided
        if sip_id:
            sips_query = sips_query.filter(id=sip_id)
        
        # Exclude SIPs that have reached end date
        sips_query = sips_query.filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=process_date)
        )
        
        eligible_sips = list(sips_query)
        
        if not eligible_sips:
            self.stdout.write(
                self.style.WARNING("No SIPs due for automatic investment.")
            )
            return
        
        self.stdout.write(
            f"Found {len(eligible_sips)} SIP(s) eligible for automatic investment:"
        )
        
        processed_count = 0
        error_count = 0
        total_amount = Decimal('0')
        
        for sip in eligible_sips:
            try:
                self.stdout.write(f"\n📊 Processing SIP: {sip.name}")
                self.stdout.write(f"   User: {sip.user.username}")
                self.stdout.write(f"   Amount: ₹{sip.amount}")
                self.stdout.write(f"   Due Date: {sip.next_investment_date}")
                self.stdout.write(f"   Asset: {sip.asset.name}")
                
                if dry_run:
                    self.stdout.write("   [DRY RUN] Would create investment")
                    processed_count += 1
                    total_amount += sip.amount
                    continue
                
                # Check if investment already exists for this date
                existing = SIPInvestment.objects.filter(
                    sip=sip,
                    date=sip.next_investment_date
                ).first()
                
                if existing:
                    self.stdout.write(
                        self.style.WARNING(f"   Investment already exists for {sip.next_investment_date}")
                    )
                    # Update next investment date even if investment exists
                    self._update_next_investment_date(sip)
                    continue
                
                # Get current NAV price
                try:
                    nav_price = self._get_nav_price(sip.asset)
                    if not nav_price or nav_price <= 0:
                        self.stdout.write(
                            self.style.ERROR(f"   Could not get valid NAV price for {sip.asset.name}")
                        )
                        error_count += 1
                        continue
                        
                except Exception as nav_error:
                    self.stdout.write(
                        self.style.ERROR(f"   NAV fetch error: {nav_error}")
                    )
                    error_count += 1
                    continue
                
                # Calculate units
                units = sip.amount / nav_price
                
                # Create the investment
                investment = SIPInvestment.objects.create(
                    sip=sip,
                    date=sip.next_investment_date,
                    amount=sip.amount,
                    nav_price=nav_price,
                    units_allocated=units,
                    current_nav=nav_price,
                    current_value=sip.amount,  # Initially same as invested amount
                    returns=Decimal('0'),
                    returns_percentage=Decimal('0')
                )
                
                # Update SIP totals
                sip.total_invested += sip.amount
                sip.total_units += units
                sip.save(update_fields=['total_invested', 'total_units'])
                
                # Update next investment date
                self._update_next_investment_date(sip)
                
                # Recalculate SIP returns
                sip.calculate_returns()
                
                self.stdout.write(
                    self.style.SUCCESS(f"   ✅ Created investment: ₹{sip.amount} @ ₹{nav_price} = {units:.4f} units")
                )
                
                processed_count += 1
                total_amount += sip.amount
                
                # Log the automatic investment
                logger.info(
                    f"Auto-investment created for SIP {sip.name} (ID: {sip.id}): "
                    f"₹{sip.amount} @ ₹{nav_price} on {sip.next_investment_date}"
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"   Error processing SIP {sip.name}: {e}")
                )
                logger.error(f"Error in auto-investment for SIP {sip.id}: {e}")
                error_count += 1
        
        # Summary
        self.stdout.write(f"\n📈 Processing Summary:")
        self.stdout.write(f"   Successfully processed: {processed_count} SIPs")
        self.stdout.write(f"   Total investment amount: ₹{total_amount:,.2f}")
        if error_count > 0:
            self.stdout.write(self.style.WARNING(f"   Errors encountered: {error_count}"))
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\n[DRY RUN] No actual changes were made"))
        else:
            self.stdout.write(self.style.SUCCESS(f"\n✅ Auto-investment processing completed!"))

    def _get_nav_price(self, asset):
        """Get current NAV price for the asset."""
        # First try to use the current price from asset
        if asset.current_price and asset.current_price > 0:
            return asset.current_price
        
        # Try to fetch fresh price using MF API service
        try:
            mf_service = MutualFundAPI()
            fresh_price = mf_service.get_nav(asset.symbol)
            if fresh_price and fresh_price > 0:
                # Update asset price
                asset.current_price = fresh_price
                asset.save(update_fields=['current_price'])
                return fresh_price
        except Exception:
            pass
        
        # Fallback: use asset's current price even if it might be stale
        return asset.current_price

    def _update_next_investment_date(self, sip):
        """Update the next investment date based on frequency."""
        from dateutil.relativedelta import relativedelta
        
        current_next = sip.next_investment_date
        
        if sip.frequency == 'monthly':
            new_next = current_next + relativedelta(months=1)
        elif sip.frequency == 'quarterly':
            new_next = current_next + relativedelta(months=3)
        elif sip.frequency == 'semi_annual':
            new_next = current_next + relativedelta(months=6)
        elif sip.frequency == 'annual':
            new_next = current_next + relativedelta(years=1)
        else:
            new_next = current_next + relativedelta(months=1)  # Default to monthly
        
        sip.next_investment_date = new_next
        sip.save(update_fields=['next_investment_date'])
        
        self.stdout.write(f"   Next investment date updated to: {new_next}")