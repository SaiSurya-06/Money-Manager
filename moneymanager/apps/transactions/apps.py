from django.apps import AppConfig


class TransactionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'moneymanager.apps.transactions'

    def ready(self):
        import moneymanager.apps.transactions.signals