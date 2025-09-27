"""
Views for the portfolios app.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.db.models import Sum

from .models import Portfolio, Holding, Asset, Watchlist, Transaction as PortfolioTransaction


class PortfolioListView(LoginRequiredMixin, ListView):
    """List all portfolios."""
    model = Portfolio
    template_name = 'portfolios/portfolio_list.html'
    context_object_name = 'portfolios'

    def get_queryset(self):
        queryset = Portfolio.objects.filter(is_active=True)
        if hasattr(self.request, 'current_family_group') and self.request.current_family_group:
            queryset = queryset.filter(family_group=self.request.current_family_group)
        else:
            queryset = queryset.filter(user=self.request.user, family_group__isnull=True)
        return queryset.order_by('name')


class PortfolioCreateView(LoginRequiredMixin, CreateView):
    """Create a new portfolio."""
    model = Portfolio
    fields = ['name', 'description']
    template_name = 'portfolios/portfolio_form.html'
    success_url = reverse_lazy('portfolios:list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        if hasattr(self.request, 'current_family_group'):
            form.instance.family_group = self.request.current_family_group
        return super().form_valid(form)


class PortfolioDetailView(LoginRequiredMixin, DetailView):
    """Portfolio detail view."""
    model = Portfolio
    template_name = 'portfolios/portfolio_detail.html'
    context_object_name = 'portfolio'

    def get_queryset(self):
        queryset = Portfolio.objects.filter(is_active=True)
        if hasattr(self.request, 'current_family_group') and self.request.current_family_group:
            queryset = queryset.filter(family_group=self.request.current_family_group)
        else:
            queryset = queryset.filter(user=self.request.user, family_group__isnull=True)
        return queryset


class PortfolioUpdateView(LoginRequiredMixin, UpdateView):
    """Update portfolio."""
    model = Portfolio
    fields = ['name', 'description']
    template_name = 'portfolios/portfolio_form.html'
    success_url = reverse_lazy('portfolios:list')


class PortfolioDeleteView(LoginRequiredMixin, DeleteView):
    """Delete portfolio."""
    model = Portfolio
    template_name = 'portfolios/portfolio_confirm_delete.html'
    success_url = reverse_lazy('portfolios:list')


class HoldingListView(LoginRequiredMixin, ListView):
    """List holdings in a portfolio."""
    model = Holding
    template_name = 'portfolios/holding_list.html'
    context_object_name = 'holdings'

    def get_queryset(self):
        self.portfolio = get_object_or_404(Portfolio, pk=self.kwargs['portfolio_pk'])
        return self.portfolio.holdings.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['portfolio'] = self.portfolio
        return context


class HoldingCreateView(LoginRequiredMixin, CreateView):
    """Create a new holding."""
    model = Holding
    fields = ['asset', 'quantity', 'average_cost']
    template_name = 'portfolios/holding_form.html'

    def form_valid(self, form):
        portfolio = get_object_or_404(Portfolio, pk=self.kwargs['portfolio_pk'])
        form.instance.portfolio = portfolio
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('portfolios:holdings_list', kwargs={'portfolio_pk': self.kwargs['portfolio_pk']})


class HoldingUpdateView(LoginRequiredMixin, UpdateView):
    """Update holding."""
    model = Holding
    fields = ['quantity', 'average_cost']
    template_name = 'portfolios/holding_form.html'


class HoldingDeleteView(LoginRequiredMixin, DeleteView):
    """Delete holding."""
    model = Holding
    template_name = 'portfolios/holding_confirm_delete.html'


class TransactionListView(LoginRequiredMixin, ListView):
    """List transactions for a holding."""
    model = PortfolioTransaction
    template_name = 'portfolios/transaction_list.html'
    context_object_name = 'transactions'


class TransactionCreateView(LoginRequiredMixin, CreateView):
    """Create a new transaction."""
    model = PortfolioTransaction
    fields = ['transaction_type', 'date', 'quantity', 'price', 'fees', 'notes']
    template_name = 'portfolios/transaction_form.html'


class TransactionUpdateView(LoginRequiredMixin, UpdateView):
    """Update transaction."""
    model = PortfolioTransaction
    fields = ['transaction_type', 'date', 'quantity', 'price', 'fees', 'notes']
    template_name = 'portfolios/transaction_form.html'


class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    """Delete transaction."""
    model = PortfolioTransaction
    template_name = 'portfolios/transaction_confirm_delete.html'


class WatchlistListView(LoginRequiredMixin, ListView):
    """List watchlists."""
    model = Watchlist
    template_name = 'portfolios/watchlist_list.html'
    context_object_name = 'watchlists'


class WatchlistCreateView(LoginRequiredMixin, CreateView):
    """Create a new watchlist."""
    model = Watchlist
    fields = ['name', 'description', 'assets']
    template_name = 'portfolios/watchlist_form.html'


class WatchlistDetailView(LoginRequiredMixin, DetailView):
    """Watchlist detail view."""
    model = Watchlist
    template_name = 'portfolios/watchlist_detail.html'


class AssetListView(LoginRequiredMixin, ListView):
    """List assets."""
    model = Asset
    template_name = 'portfolios/asset_list.html'
    context_object_name = 'assets'


class AssetDetailView(LoginRequiredMixin, DetailView):
    """Asset detail view."""
    model = Asset
    template_name = 'portfolios/asset_detail.html'


@login_required
def portfolio_analytics(request):
    """Portfolio analytics dashboard."""
    portfolios = Portfolio.objects.filter(is_active=True)
    if hasattr(request, 'current_family_group') and request.current_family_group:
        portfolios = portfolios.filter(family_group=request.current_family_group)
    else:
        portfolios = portfolios.filter(user=request.user, family_group__isnull=True)

    context = {
        'portfolios': portfolios,
    }
    return render(request, 'portfolios/analytics.html', context)