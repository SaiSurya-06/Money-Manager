"""
URLs for the imports app.
"""
from django.urls import path
from . import views

app_name = 'imports'

urlpatterns = [
    # Import management
    path('', views.import_home, name='home'),
    path('transactions/', views.import_transactions, name='transactions'),
    path('csv-upload/', views.csv_upload, name='csv_upload'),
    path('bank-sync/', views.bank_sync, name='bank_sync'),
    path('history/', views.import_history, name='history'),
]