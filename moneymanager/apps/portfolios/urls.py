"""
URLs for the portfolios app.
"""
from django.urls import path
from . import views

app_name = 'portfolios'

urlpatterns = [
    # Portfolio management
    path('', views.PortfolioListView.as_view(), name='list'),
    path('create/', views.PortfolioCreateView.as_view(), name='create'),
    path('<uuid:pk>/', views.PortfolioDetailView.as_view(), name='detail'),
    path('<uuid:pk>/update/', views.PortfolioUpdateView.as_view(), name='update'),
    path('<uuid:pk>/delete/', views.PortfolioDeleteView.as_view(), name='delete'),
    
    # Holdings management
    path('<uuid:portfolio_pk>/holdings/', views.HoldingListView.as_view(), name='holdings_list'),
    path('<uuid:portfolio_pk>/holdings/add/', views.HoldingCreateView.as_view(), name='holding_create'),
    path('holdings/<uuid:pk>/update/', views.HoldingUpdateView.as_view(), name='holding_update'),
    path('holdings/<uuid:pk>/delete/', views.HoldingDeleteView.as_view(), name='holding_delete'),
    
    # Transactions
    path('holdings/<uuid:holding_pk>/transactions/', views.TransactionListView.as_view(), name='transaction_list'),
    path('holdings/<uuid:holding_pk>/transactions/add/', views.TransactionCreateView.as_view(), name='transaction_create'),
    path('transactions/<uuid:pk>/update/', views.TransactionUpdateView.as_view(), name='transaction_update'),
    path('transactions/<uuid:pk>/delete/', views.TransactionDeleteView.as_view(), name='transaction_delete'),
    
    # Watchlists
    path('watchlists/', views.WatchlistListView.as_view(), name='watchlist_list'),
    path('watchlists/create/', views.WatchlistCreateView.as_view(), name='watchlist_create'),
    path('watchlists/<uuid:pk>/', views.WatchlistDetailView.as_view(), name='watchlist_detail'),
    
    # Assets
    path('assets/', views.AssetListView.as_view(), name='asset_list'),
    path('assets/<int:pk>/', views.AssetDetailView.as_view(), name='asset_detail'),
    
    # Analytics
    path('analytics/', views.portfolio_analytics, name='analytics'),
    
    # Enhanced functionality
    path('asset-search/', views.asset_search, name='asset_search'),
    path('<uuid:pk>/update-prices/', views.update_portfolio_prices, name='update_prices'),
    path('bulk-upload/', views.BulkHoldingUploadView.as_view(), name='bulk_upload'),
    path('<uuid:pk>/export-csv/', views.export_portfolio_csv, name='export_csv'),
    
    # Family Admin Oversight URLs
    path('family/', views.FamilyPortfolioListView.as_view(), name='family_list'),
    
    # SIP Management URLs
    path('sips/', views.SIPListView.as_view(), name='sip_list'),
    path('sips/dashboard/', views.sip_dashboard, name='sip_dashboard'),
    path('sips/create/', views.SIPCreateView.as_view(), name='sip_create'),
    path('sips/import-history/', views.SIPHistoryImportView.as_view(), name='sip_import_history'),
    path('sips/<uuid:pk>/', views.SIPDetailView.as_view(), name='sip_detail'),
    path('sips/<uuid:pk>/update/', views.SIPUpdateView.as_view(), name='sip_update'),
    path('sips/<uuid:pk>/delete/', views.SIPDeleteView.as_view(), name='sip_delete'),
    path('sips/<uuid:sip_pk>/invest/', views.SIPInvestmentCreateView.as_view(), name='sip_investment_create'),
    path('sips/<uuid:pk>/bulk-import/', views.sip_bulk_import, name='sip_bulk_import'),
    path('sips/update-prices/', views.update_sip_prices, name='sip_update_prices'),
    path('update-sip-prices/', views.update_sip_prices, name='update_sip_prices'),  # Alternative URL for AJAX calls
    path('sips/<uuid:pk>/chart-data/', views.sip_performance_chart_data, name='sip_chart_data'),
    
    # Enhanced SIP functionality
    path('sips/<uuid:pk>/pause/', views.sip_pause, name='sip_pause'),
    path('sips/<uuid:pk>/resume/', views.sip_resume, name='sip_resume'),
    path('sips/<uuid:pk>/complete/', views.sip_complete, name='sip_complete'),
    path('sips/batch-update/', views.sip_batch_update, name='sip_batch_update'),
    path('sips/auto-process/', views.process_auto_sips, name='process_auto_sips'),
    path('sips/performance-report/', views.sip_performance_report, name='sip_performance_report'),
]