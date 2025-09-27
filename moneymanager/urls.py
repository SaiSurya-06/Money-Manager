"""
MoneyManager URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
    path('accounts/', include('moneymanager.apps.accounts.urls')),
    path('dashboard/', include('moneymanager.apps.dashboard.urls')),
    path('transactions/', include('moneymanager.apps.transactions.urls')),
    path('budgets/', include('moneymanager.apps.budgets.urls')),
    path('portfolios/', include('moneymanager.apps.portfolios.urls')),
    path('imports/', include('moneymanager.apps.imports.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Debug toolbar
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass

# Custom error pages
handler404 = 'moneymanager.apps.core.views.custom_404'
handler500 = 'moneymanager.apps.core.views.custom_500'