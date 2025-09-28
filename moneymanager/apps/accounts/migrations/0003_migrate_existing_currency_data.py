# Generated manually to migrate existing data from USD to INR

from django.db import migrations


def update_existing_users_currency(apps, schema_editor):
    """Update existing users' preferred currency from USD to INR"""
    User = apps.get_model('accounts', 'User')
    User.objects.filter(preferred_currency='USD').update(preferred_currency='INR')


def reverse_update_users_currency(apps, schema_editor):
    """Reverse migration: update currency back from INR to USD"""
    User = apps.get_model('accounts', 'User')
    User.objects.filter(preferred_currency='INR').update(preferred_currency='USD')


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0002_update_currency_to_inr'),
    ]

    operations = [
        migrations.RunPython(
            update_existing_users_currency,
            reverse_update_users_currency,
        ),
    ]