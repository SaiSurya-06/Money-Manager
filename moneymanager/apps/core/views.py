from django.shortcuts import render
from django.http import HttpResponseNotFound, HttpResponseServerError


def custom_404(request, exception):
    """Custom 404 error page."""
    return render(request, 'errors/404.html', status=404)


def custom_500(request):
    """Custom 500 error page."""
    return render(request, 'errors/500.html', status=500)