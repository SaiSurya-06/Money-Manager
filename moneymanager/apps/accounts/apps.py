from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'moneymanager.apps.accounts'

    def ready(self):
        import moneymanager.apps.accounts.signals