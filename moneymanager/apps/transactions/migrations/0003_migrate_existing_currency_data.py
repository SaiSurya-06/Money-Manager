# Generated manually to migrate existing data from USD to INR

from django.db import migrations


def update_existing_accounts_currency(apps, schema_editor):
    """Update existing accounts' currency from USD to INR"""
    Account = apps.get_model('transactions', 'Account')
    Account.objects.filter(currency='USD').update(currency='INR')


def reverse_update_accounts_currency(apps, schema_editor):
    """Reverse migration: update currency back from INR to USD"""
    Account = apps.get_model('transactions', 'Account')
    Account.objects.filter(currency='INR').update(currency='USD')


class Migration(migrations.Migration):
    dependencies = [
        ('transactions', '0002_update_currency_to_inr'),
    ]

    operations = [
        migrations.RunPython(
            update_existing_accounts_currency,
            reverse_update_accounts_currency,
        ),
    ]