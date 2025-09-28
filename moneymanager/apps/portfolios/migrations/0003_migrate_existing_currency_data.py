# Generated manually to migrate existing data from USD to INR

from django.db import migrations


def update_existing_assets_currency(apps, schema_editor):
    """Update existing assets' currency from USD to INR"""
    Asset = apps.get_model('portfolios', 'Asset')
    Asset.objects.filter(currency='USD').update(currency='INR')


def reverse_update_assets_currency(apps, schema_editor):
    """Reverse migration: update currency back from INR to USD"""
    Asset = apps.get_model('portfolios', 'Asset')
    Asset.objects.filter(currency='INR').update(currency='USD')


class Migration(migrations.Migration):
    dependencies = [
        ('portfolios', '0002_update_currency_to_inr'),
    ]

    operations = [
        migrations.RunPython(
            update_existing_assets_currency,
            reverse_update_assets_currency,
        ),
    ]