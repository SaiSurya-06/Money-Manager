"""
Views for the imports app.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def import_home(request):
    """Import homepage."""
    return render(request, 'imports/home.html')


@login_required
def import_transactions(request):
    """Import transactions from various sources."""
    return render(request, 'imports/transactions.html')


@login_required
def csv_upload(request):
    """Upload CSV files for import."""
    return render(request, 'imports/csv_upload.html')


@login_required
def bank_sync(request):
    """Bank synchronization."""
    return render(request, 'imports/bank_sync.html')


@login_required
def import_history(request):
    """Import history."""
    return render(request, 'imports/history.html')