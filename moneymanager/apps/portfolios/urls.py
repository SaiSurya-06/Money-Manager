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
]