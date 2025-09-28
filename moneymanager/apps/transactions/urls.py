from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    # Transaction URLs
    path('', views.TransactionListView.as_view(), name='list'),
    path('create/', views.TransactionCreateView.as_view(), name='create'),
    path('<uuid:pk>/', views.TransactionUpdateView.as_view(), name='update'),
    path('<uuid:pk>/delete/', views.TransactionDeleteView.as_view(), name='delete'),

    # Account URLs
    path('accounts/', views.AccountListView.as_view(), name='accounts'),
    path('accounts/create/', views.AccountCreateView.as_view(), name='account_create'),
    path('accounts/<uuid:pk>/', views.AccountDetailView.as_view(), name='account_detail'),
    path('accounts/<uuid:pk>/edit/', views.AccountUpdateView.as_view(), name='account_update'),
    path('accounts/<uuid:pk>/delete/', views.AccountDeleteView.as_view(), name='account_delete'),

    # Recurring transactions
    path('recurring/', views.recurring_transactions_list, name='recurring_list'),
    path('recurring/create/', views.RecurringTransactionCreateView.as_view(), name='recurring_create'),
    path('recurring/<uuid:pk>/edit/', views.RecurringTransactionUpdateView.as_view(), name='recurring_edit'),
    path('recurring/<uuid:pk>/delete/', views.RecurringTransactionDeleteView.as_view(), name='recurring_delete'),

    # Bulk operations
    path('bulk-upload/', views.bulk_upload_transactions, name='bulk_upload'),
    path('bulk-delete/', views.bulk_delete_transactions, name='bulk_delete'),
    path('download-template/<str:format>/', views.download_template, name='download_template'),
    
    # Family Admin Oversight URLs
    path('family/', views.FamilyTransactionListView.as_view(), name='family_list'),
    path('family/accounts/', views.FamilyAccountListView.as_view(), name='family_accounts'),
]