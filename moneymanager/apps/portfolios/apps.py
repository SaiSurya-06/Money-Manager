from django.apps import AppConfig


class PortfoliosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'moneymanager.apps.portfolios'

    def ready(self):
        import moneymanager.apps.portfolios.signals