from django.apps import AppConfig


class BudgetsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'moneymanager.apps.budgets'

    def ready(self):
        import moneymanager.apps.budgets.signals