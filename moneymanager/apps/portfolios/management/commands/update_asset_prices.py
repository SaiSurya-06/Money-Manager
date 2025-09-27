from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction, models
from moneymanager.apps.portfolios.models import Asset, Portfolio
from moneymanager.apps.portfolios.services import price_update_service
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Update asset prices from external APIs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--symbols',
            type=str,
            nargs='+',
            help='Specific asset symbols to update (e.g., AAPL GOOGL)',
        )
        parser.add_argument(
            '--active-only',
            action='store_true',
            help='Update only assets that are actively held in portfolios',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if recently updated',
        )

    def handle(self, *args, **options):
        symbols = options.get('symbols')
        active_only = options.get('active_only', False)
        force = options.get('force', False)

        # Determine which assets to update
        if symbols:
            assets = Asset.objects.filter(
                symbol__in=symbols,
                is_active=True
            )
            if not assets.exists():
                self.stdout.write(
                    self.style.ERROR(f'No active assets found for symbols: {", ".join(symbols)}')
                )
                return
        elif active_only:
            # Get assets that are held in active portfolios
            assets = Asset.objects.filter(
                holdings__portfolio__is_active=True,
                holdings__is_active=True,
                is_active=True
            ).distinct()
        else:
            # Get all active assets
            assets = Asset.objects.filter(is_active=True)

        if not assets.exists():
            self.stdout.write(
                self.style.SUCCESS('No assets found to update')
            )
            return

        # Filter by last update time unless forced
        if not force:
            # Only update assets that haven't been updated in the last hour
            one_hour_ago = timezone.now() - timezone.timedelta(hours=1)
            assets = assets.filter(
                models.Q(price_updated_at__isnull=True) |
                models.Q(price_updated_at__lt=one_hour_ago)
            )

        symbols_to_update = [asset.symbol for asset in assets]

        if not symbols_to_update:
            self.stdout.write(
                self.style.SUCCESS('All assets are up to date')
            )
            return

        self.stdout.write(
            f'Updating prices for {len(symbols_to_update)} assets: {", ".join(symbols_to_update)}'
        )

        # Update prices using the service
        results = price_update_service.update_asset_prices(symbols_to_update)

        success_count = sum(1 for success in results.values() if success)
        failure_count = len(results) - success_count

        # Show results
        for symbol, success in results.items():
            if success:
                asset = Asset.objects.get(symbol=symbol)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ {symbol}: ${asset.current_price} '
                        f'({asset.day_change:+.2f} {asset.day_change_percentage:+.2f}%)'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'✗ {symbol}: Failed to update')
                )

        # Update portfolio values for affected portfolios
        if success_count > 0:
            updated_assets = Asset.objects.filter(
                symbol__in=[s for s, success in results.items() if success]
            )

            portfolios_to_update = Portfolio.objects.filter(
                holdings__asset__in=updated_assets,
                holdings__is_active=True,
                is_active=True
            ).distinct()

            portfolio_count = 0
            for portfolio in portfolios_to_update:
                try:
                    portfolio.update_portfolio_values()
                    portfolio_count += 1
                except Exception as e:
                    logger.error(f'Error updating portfolio {portfolio.id}: {str(e)}')

            if portfolio_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Updated {portfolio_count} portfolios'
                    )
                )

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'Price update complete: {success_count} successful, {failure_count} failed'
            )
        )