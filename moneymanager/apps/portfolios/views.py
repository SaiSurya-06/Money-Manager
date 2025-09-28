"""
Views for the portfolios app.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, FormView
from django.urls import reverse_lazy, reverse
from django.db.models import Sum, Q, Count, Avg
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.utils import timezone
from decimal import Decimal
import csv
import io
import json
from datetime import datetime, timedelta

from .models import Portfolio, Holding, Asset, Watchlist, Transaction as PortfolioTransaction, PriceHistory, SIP, SIPInvestment
from .forms import (
    PortfolioForm, AssetForm, AssetSearchForm, HoldingForm, 
    TransactionForm, BulkHoldingUploadForm, WatchlistForm, PriceUpdateForm,
    SIPForm, SIPInvestmentForm, SIPHistoryImportForm
)


class PortfolioListView(LoginRequiredMixin, ListView):
    """List all portfolios."""
    model = Portfolio
    template_name = 'portfolios/portfolio_list.html'
    context_object_name = 'portfolios'

    def get_queryset(self):
        queryset = Portfolio.objects.filter(is_active=True)
        # Show only user's own portfolios - keep portfolios private
        queryset = queryset.filter(user=self.request.user)
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
    """Enhanced portfolio detail view with comprehensive P&L calculations and analytics."""
    model = Portfolio
    template_name = 'portfolios/portfolio_detail.html'
    context_object_name = 'portfolio'

    def get_queryset(self):
        queryset = Portfolio.objects.filter(is_active=True)
        if hasattr(self.request, 'current_family_group') and self.request.current_family_group:
            queryset = queryset.filter(family_group=self.request.current_family_group)
        else:
            queryset = queryset.filter(user=self.request.user, family_group__isnull=True)
        return queryset.select_related().prefetch_related('holdings__asset', 'holdings__transactions')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        portfolio = self.object
        
        # Get all active holdings with their assets
        holdings = portfolio.holdings.filter(is_active=True).select_related('asset')
        
        # Sort and filter holdings based on query parameters
        sort_by = self.request.GET.get('sort', '-current_value')
        asset_type = self.request.GET.get('asset_type')
        
        if asset_type:
            holdings = holdings.filter(asset__asset_type=asset_type)
        
        # Apply sorting
        if sort_by in ['-gain_loss_percentage', 'gain_loss_percentage', '-current_value', 'current_value']:
            holdings = sorted(holdings, key=lambda h: getattr(h, sort_by.lstrip('-')), 
                            reverse=sort_by.startswith('-'))
        else:
            holdings = holdings.order_by(sort_by)
        
        # Calculate portfolio totals
        total_holdings = len(holdings)
        portfolio_value = sum(holding.current_value for holding in holdings)
        total_cost_basis = sum(holding.total_cost for holding in holdings)
        total_gain_loss = portfolio_value - total_cost_basis
        total_gain_loss_percentage = (total_gain_loss / total_cost_basis * 100) if total_cost_basis > 0 else 0
        
        # Find best and worst performers
        best_performer = None
        worst_performer = None
        
        if holdings:
            holdings_with_performance = [h for h in holdings if hasattr(h, 'gain_loss_percentage')]
            if holdings_with_performance:
                best_performer = max(holdings_with_performance, key=lambda h: h.gain_loss_percentage)
                worst_performer = min(holdings_with_performance, key=lambda h: h.gain_loss_percentage)
        
        # Calculate asset allocation
        asset_allocation = []
        if holdings:
            allocation_data = {}
            for holding in holdings:
                asset_type = holding.asset.asset_type
                if asset_type not in allocation_data:
                    allocation_data[asset_type] = {'total_value': 0, 'count': 0}
                allocation_data[asset_type]['total_value'] += holding.current_value
                allocation_data[asset_type]['count'] += 1
            
            for asset_type, data in allocation_data.items():
                asset_allocation.append({
                    'asset__asset_type': asset_type,
                    'total_value': data['total_value'],
                    'count': data['count']
                })
        
        # Get recent transactions
        recent_transactions = PortfolioTransaction.objects.filter(
            holding__portfolio=portfolio,
            is_active=True
        ).select_related('holding__asset').order_by('-date')[:5]
        
        # Update portfolio object with calculated values
        portfolio.total_value = portfolio_value
        portfolio.total_cost_basis = total_cost_basis
        portfolio.total_gain_loss = total_gain_loss
        portfolio.total_gain_loss_percentage = total_gain_loss_percentage
        
        context.update({
            'holdings': holdings,
            'total_holdings': total_holdings,
            'best_performer': best_performer,
            'worst_performer': worst_performer,
            'asset_allocation': asset_allocation,
            'recent_transactions': recent_transactions,
            'can_edit': portfolio.user == self.request.user or (
                hasattr(self.request, 'current_family_group') and 
                portfolio.family_group == self.request.current_family_group
            ),
        })
        
        return context


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
    """Enhanced holding creation with asset search and portfolio context."""
    model = Holding
    form_class = HoldingForm
    template_name = 'portfolios/holding_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['portfolio'] = get_object_or_404(Portfolio, pk=self.kwargs['portfolio_pk'])
        return kwargs

    def form_valid(self, form):
        portfolio = get_object_or_404(Portfolio, pk=self.kwargs['portfolio_pk'])
        form.instance.portfolio = portfolio
        
        # Create initial transaction if specified
        response = super().form_valid(form)
        
        if form.cleaned_data.get('create_initial_transaction'):
            PortfolioTransaction.objects.create(
                holding=self.object,
                transaction_type='buy',
                quantity=form.cleaned_data['quantity'],
                price_per_unit=form.cleaned_data['average_cost'],
                total_amount=form.cleaned_data['quantity'] * form.cleaned_data['average_cost'],
                date=timezone.now().date(),
                description='Initial holding purchase'
            )
        
        messages.success(
            self.request, 
            f'Successfully added {self.object.asset.symbol} to your portfolio!'
        )
        return response

    def get_success_url(self):
        return reverse('portfolios:detail', kwargs={'pk': self.kwargs['portfolio_pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['portfolio'] = get_object_or_404(Portfolio, pk=self.kwargs['portfolio_pk'])
        context['asset_search_form'] = AssetSearchForm()
        return context


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


# Family Admin Oversight Views
class FamilyPortfolioListView(LoginRequiredMixin, ListView):
    """List all portfolios from family members - for family group admins only."""
    model = Portfolio
    template_name = 'portfolios/family_portfolio_list.html'
    context_object_name = 'portfolios'

    def dispatch(self, request, *args, **kwargs):
        # Only allow family group admins to access this view
        if not (hasattr(request, 'current_family_group') and request.current_family_group and 
                request.user.is_family_group_admin(request.current_family_group)):
            from django.contrib import messages
            from django.shortcuts import redirect
            messages.error(request, 'You must be a family group admin to access this page.')
            return redirect('portfolios:list')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        from django.db.models import Q
        queryset = Portfolio.objects.filter(is_active=True)
        # Show all portfolios from family members (excluding current user's own portfolios)
        if hasattr(self.request, 'current_family_group') and self.request.current_family_group:
            family_members = self.request.current_family_group.members.exclude(id=self.request.user.id)
            queryset = queryset.filter(
                Q(family_group=self.request.current_family_group) |
                Q(user__in=family_members, family_group__isnull=True)
            )
        else:
            queryset = Portfolio.objects.none()
        return queryset.order_by('user__first_name', 'user__last_name', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_family_group'] = getattr(self.request, 'current_family_group', None)
        context['is_family_admin_view'] = True
        return context


# Enhanced Portfolio Functionality Views

@login_required
def asset_search(request):
    """AJAX endpoint for asset search functionality."""
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse({'results': []})
    
    try:
        # Use utility function for asset search
        from .utils import search_asset_info
        results = search_asset_info(query)
        
        # Also search existing assets in database
        existing_assets = Asset.objects.filter(
            Q(symbol__icontains=query) | Q(name__icontains=query)
        ).values('id', 'symbol', 'name', 'asset_type', 'current_price')[:10]
        
        # Combine results
        all_results = list(existing_assets) + results[:10]
        
        return JsonResponse({
            'results': all_results[:15],  # Limit to 15 total results
            'query': query
        })
        
    except Exception as e:
        return JsonResponse({
            'results': [],
            'error': str(e)
        }, status=500)


@login_required
def update_portfolio_prices(request, pk):
    """Update all asset prices in a portfolio."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        portfolio = get_object_or_404(Portfolio, pk=pk, user=request.user)
        
        from .utils import bulk_update_prices
        
        # Get all unique assets in the portfolio
        asset_ids = portfolio.holdings.filter(is_active=True).values_list('asset_id', flat=True).distinct()
        assets = Asset.objects.filter(id__in=asset_ids)
        
        updated_count = bulk_update_prices(assets)
        
        return JsonResponse({
            'success': True,
            'updated_count': updated_count,
            'message': f'Updated prices for {updated_count} assets'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


class BulkHoldingUploadView(LoginRequiredMixin, FormView):
    """Bulk upload holdings from CSV file."""
    form_class = BulkHoldingUploadForm
    template_name = 'portfolios/bulk_upload.html'
    
    def form_valid(self, form):
        try:
            csv_file = form.cleaned_data['csv_file']
            portfolio = form.cleaned_data['portfolio']
            
            # Process CSV file
            decoded_file = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(decoded_file))
            
            created_count = 0
            errors = []
            
            for row_num, row in enumerate(csv_reader, start=2):
                try:
                    # Get or create asset
                    asset, created = Asset.objects.get_or_create(
                        symbol=row['symbol'].upper().strip(),
                        defaults={
                            'name': row.get('name', row['symbol']),
                            'asset_type': row.get('asset_type', 'stock'),
                            'current_price': Decimal(row.get('current_price', '0'))
                        }
                    )
                    
                    # Create holding
                    holding, created = Holding.objects.get_or_create(
                        portfolio=portfolio,
                        asset=asset,
                        defaults={
                            'quantity': Decimal(row['quantity']),
                            'average_cost': Decimal(row['average_cost'])
                        }
                    )
                    
                    if created:
                        created_count += 1
                        
                        # Create initial transaction
                        PortfolioTransaction.objects.create(
                            holding=holding,
                            transaction_type='buy',
                            quantity=holding.quantity,
                            price_per_unit=holding.average_cost,
                            total_amount=holding.quantity * holding.average_cost,
                            date=timezone.now().date(),
                            description='Bulk import'
                        )
                    
                except Exception as e:
                    errors.append(f'Row {row_num}: {str(e)}')
            
            if created_count > 0:
                messages.success(self.request, f'Successfully imported {created_count} holdings.')
            
            if errors:
                for error in errors:
                    messages.error(self.request, error)
            
            return redirect('portfolios:detail', pk=portfolio.pk)
            
        except Exception as e:
            messages.error(self.request, f'Error processing file: {str(e)}')
            return self.form_invalid(form)


@login_required
def export_portfolio_csv(request, pk):
    """Export portfolio holdings to CSV."""
    portfolio = get_object_or_404(Portfolio, pk=pk, user=request.user)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{portfolio.name}_holdings.csv"'
    
    writer = csv.writer(response)
    
    # Write headers
    writer.writerow([
        'Symbol', 'Name', 'Asset Type', 'Quantity', 'Average Cost', 
        'Current Price', 'Market Value', 'Gain/Loss', 'Gain/Loss %'
    ])
    
    # Write holdings data
    for holding in portfolio.holdings.filter(is_active=True).select_related('asset'):
        writer.writerow([
            holding.asset.symbol,
            holding.asset.name,
            holding.asset.get_asset_type_display(),
            holding.quantity,
            holding.average_cost,
            holding.asset.current_price,
            holding.current_value,
            holding.gain_loss,
            f'{holding.gain_loss_percentage:.2f}%' if hasattr(holding, 'gain_loss_percentage') else '0.00%'
        ])
    
    return response


class TransactionCreateView(LoginRequiredMixin, CreateView):
    """Create a new transaction for a holding."""
    model = PortfolioTransaction
    form_class = TransactionForm
    template_name = 'portfolios/transaction_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['holding'] = get_object_or_404(Holding, pk=self.kwargs['holding_pk'])
        return kwargs
    
    def form_valid(self, form):
        holding = get_object_or_404(Holding, pk=self.kwargs['holding_pk'])
        form.instance.holding = holding
        
        response = super().form_valid(form)
        
        # Update holding average cost and quantity
        holding.update_from_transactions()
        
        messages.success(self.request, 'Transaction added successfully!')
        return response
    
    def get_success_url(self):
        return reverse('portfolios:detail', 
                      kwargs={'pk': self.object.holding.portfolio.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['holding'] = get_object_or_404(Holding, pk=self.kwargs['holding_pk'])
        return context


# SIP Views
class SIPListView(LoginRequiredMixin, ListView):
    """List all SIPs for the user."""
    template_name = 'portfolios/sip_list.html'
    context_object_name = 'sips'
    paginate_by = 10

    def get_queryset(self):
        return SIP.objects.filter(user=self.request.user).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sips = context['sips']
        
        # Get all user's SIPs for summary statistics (not paginated)
        all_user_sips = SIP.objects.filter(user=self.request.user)
        
        # Calculate summary statistics from all SIPs
        total_invested = sum(sip.total_invested for sip in all_user_sips)
        current_value = sum(sip.current_value for sip in all_user_sips)
        total_returns = current_value - total_invested
        
        context.update({
            'total_invested': total_invested,
            'current_value': current_value,
            'total_returns': total_returns,
            'returns_percentage': (total_returns / total_invested * 100) if total_invested > 0 else 0,
            'active_sips': all_user_sips.filter(status='active').count(),
            'total_sips': all_user_sips.count(),
        })
        return context


class SIPCreateView(LoginRequiredMixin, CreateView):
    """Create a new SIP."""
    model = SIP
    form_class = SIPForm
    template_name = 'portfolios/sip_form.html'
    success_url = reverse_lazy('portfolios:sip_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'SIP "{self.object.name}" created successfully!')
        return response


class SIPDetailView(LoginRequiredMixin, DetailView):
    """View SIP details with all investments."""
    model = SIP
    template_name = 'portfolios/sip_detail.html'
    context_object_name = 'sip'

    def get_queryset(self):
        return SIP.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sip = context['sip']
        
        # Get all investments for this SIP
        investments = sip.investments.all().order_by('-date')
        
        # Update current values for all investments
        for investment in investments:
            investment.calculate_current_value()
        
        # Update SIP returns
        sip.calculate_returns()
        
        # Paginate investments
        paginator = Paginator(investments, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context.update({
            'investments': page_obj,
            'investment_count': investments.count(),
            'next_investment_due': sip.is_due_for_investment,
        })
        return context


class SIPUpdateView(LoginRequiredMixin, UpdateView):
    """Update SIP details."""
    model = SIP
    form_class = SIPForm
    template_name = 'portfolios/sip_form.html'
    
    def get_queryset(self):
        return SIP.objects.filter(user=self.request.user)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'SIP "{self.object.name}" updated successfully!')
        return response
    
    def get_success_url(self):
        return reverse('portfolios:sip_detail', kwargs={'pk': self.object.pk})


class SIPDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a SIP with confirmation."""
    model = SIP
    template_name = 'portfolios/sip_confirm_delete.html'
    context_object_name = 'sip'
    
    def get_queryset(self):
        """Ensure users can only delete their own SIPs."""
        return SIP.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sip = self.get_object()
        
        # Add SIP statistics for confirmation
        context.update({
            'investment_count': sip.investments.count(),
            'total_invested': sip.total_invested,
            'current_value': sip.current_value,
            'total_returns': sip.total_returns,
            'can_delete': True,
        })
        
        # Check if SIP has recent investments (within 30 days)
        from datetime import date, timedelta
        recent_cutoff = date.today() - timedelta(days=30)
        recent_investments = sip.investments.filter(date__gte=recent_cutoff)
        
        if recent_investments.exists():
            context['recent_investments'] = recent_investments
            context['warning_message'] = f"This SIP has {recent_investments.count()} recent investment(s) in the last 30 days."
        
        return context
    
    def delete(self, request, *args, **kwargs):
        sip = self.get_object()
        sip_name = sip.name
        
        # Log the deletion for audit purposes
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"User {request.user.username} deleted SIP: {sip_name} (ID: {sip.id})")
        
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'SIP "{sip_name}" and all its investments have been permanently deleted.')
        
        return response
    
    def get_success_url(self):
        return reverse('portfolios:sip_list')


class SIPInvestmentCreateView(LoginRequiredMixin, CreateView):
    """Add a new investment to a SIP."""
    model = SIPInvestment
    form_class = SIPInvestmentForm
    template_name = 'portfolios/sip_investment_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['sip'] = get_object_or_404(SIP, pk=self.kwargs['sip_pk'], user=self.request.user)
        return kwargs
    
    def form_valid(self, form):
        sip = get_object_or_404(SIP, pk=self.kwargs['sip_pk'], user=self.request.user)
        form.instance.sip = sip
        
        response = super().form_valid(form)
        
        # Update SIP next investment date if this was due
        if sip.is_due_for_investment:
            sip.next_investment_date = sip.get_next_investment_date()
            sip.save(update_fields=['next_investment_date'])
        
        messages.success(self.request, f'Investment of ₹{self.object.amount} recorded for {sip.name}!')
        return response
    
    def get_success_url(self):
        return reverse('portfolios:sip_detail', kwargs={'pk': self.kwargs['sip_pk']})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sip'] = get_object_or_404(SIP, pk=self.kwargs['sip_pk'], user=self.request.user)
        return context


@login_required
def sip_dashboard(request):
    """Enhanced dashboard view showing comprehensive SIP overview and analytics."""
    # Get all user SIPs for calculations
    all_user_sips = SIP.objects.filter(user=request.user).select_related('asset', 'portfolio')
    
    # Convert to list for dashboard display (limited to avoid performance issues)
    user_sips = list(all_user_sips.order_by('-created_at')[:50])  # Limit to 50 for dashboard
    
    # Get SIPs due for investment
    due_sips = [sip for sip in user_sips if sip.is_due_for_investment]
    
    # Calculate comprehensive totals from all SIPs
    total_invested = sum(sip.total_invested for sip in all_user_sips)
    current_value = sum(sip.current_value for sip in all_user_sips)
    total_returns = current_value - total_invested
    
    # Calculate performance metrics
    total_units = sum(sip.total_units for sip in all_user_sips if hasattr(sip, 'total_units'))
    avg_cost = total_invested / total_units if total_units > 0 else Decimal('0')
    current_avg_price = current_value / total_units if total_units > 0 else Decimal('0')
    
    # Top performing SIPs
    top_performers = sorted(
        [sip for sip in user_sips if sip.returns_percentage > 0],
        key=lambda x: x.returns_percentage,
        reverse=True
    )[:5]
    
    # Worst performing SIPs
    worst_performers = sorted(
        [sip for sip in user_sips if sip.returns_percentage < 0],
        key=lambda x: x.returns_percentage
    )[:5]
    
    # Get recent investments with more details
    recent_investments = SIPInvestment.objects.filter(
        sip__user=request.user
    ).select_related('sip', 'sip__asset').order_by('-date')[:15]
    
    # Enhanced monthly investment summary (last 12 months)
    from django.db.models import Sum, Count, Avg
    from datetime import date, timedelta
    import calendar
    
    monthly_data = []
    monthly_stats = []
    current_date = date.today()
    
    for i in range(12):
        year = current_date.year
        month = current_date.month - i
        if month <= 0:
            month += 12
            year -= 1
        
        month_investments = SIPInvestment.objects.filter(
            sip__user=request.user,
            date__year=year,
            date__month=month
        )
        
        month_total = month_investments.aggregate(total=Sum('amount'))['total'] or 0
        month_count = month_investments.count()
        month_avg = month_investments.aggregate(avg=Avg('amount'))['avg'] or 0
        
        monthly_data.append({
            'month': calendar.month_name[month][:3],
            'year': year,
            'amount': float(month_total)
        })
        
        monthly_stats.append({
            'month': f"{calendar.month_name[month][:3]} {year}",
            'total': month_total,
            'count': month_count,
            'average': month_avg
        })
    
    monthly_data.reverse()
    monthly_stats.reverse()
    
    # Asset allocation across SIPs
    asset_allocation = {}
    for sip in all_user_sips:
        asset_type = sip.asset.asset_type
        if asset_type not in asset_allocation:
            asset_allocation[asset_type] = {
                'total_invested': Decimal('0'),
                'current_value': Decimal('0'),
                'count': 0
            }
        asset_allocation[asset_type]['total_invested'] += sip.total_invested
        asset_allocation[asset_type]['current_value'] += sip.current_value
        asset_allocation[asset_type]['count'] += 1
    
    # Calculate XIRR for portfolio (if available)
    portfolio_xirr = None
    try:
        from .utils.calculations import calculate_portfolio_xirr
        if all_user_sips:
            portfolio_xirr = calculate_portfolio_xirr(all_user_sips)
    except ImportError:
        pass
    
    # Calculate next investment amounts
    next_investment_amount = sum(sip.amount for sip in due_sips)
    monthly_commitment = sum(
        sip.amount for sip in all_user_sips 
        if sip.status == 'active' and sip.frequency == 'monthly'
    )
    
    context = {
        'user_sips': user_sips,
        'due_sips': due_sips,
        'total_invested': total_invested,
        'current_value': current_value,
        'total_returns': total_returns,
        'returns_percentage': (total_returns / total_invested * 100) if total_invested > 0 else 0,
        'recent_investments': recent_investments,
        'monthly_data': json.dumps(monthly_data),
        'monthly_stats': monthly_stats[:6],  # Last 6 months
        'active_sips': all_user_sips.filter(status='active').count(),
        'paused_sips': all_user_sips.filter(status='paused').count(),
        'completed_sips': all_user_sips.filter(status='completed').count(),
        'top_performers': top_performers,
        'worst_performers': worst_performers,
        'asset_allocation': asset_allocation,
        'portfolio_xirr': portfolio_xirr,
        'next_investment_amount': next_investment_amount,
        'monthly_commitment': monthly_commitment,
        'total_units': total_units,
        'avg_cost': avg_cost,
        'current_avg_price': current_avg_price,
        'last_updated': timezone.now(),
    }
    
    return render(request, 'portfolios/sip_dashboard.html', context)


@login_required
def update_sip_prices(request):
    """Update NAV prices for all SIP mutual funds."""
    if request.method == 'POST':
        # Get all unique mutual fund assets from user's SIPs
        sip_assets = Asset.objects.filter(
            sips__user=request.user,
            asset_type='mutual_fund'
        ).distinct()
        
        updated_count = 0
        errors = []
        
        # Import SIP service for price updates
        try:
            from .services.price_service import PriceService
            price_service = PriceService()
            
            for asset in sip_assets:
                try:
                    # Use enhanced price service
                    current_price = price_service.get_asset_price(asset.symbol)
                    
                    if current_price and current_price > 0:
                        asset.current_price = current_price
                        asset.price_updated_at = timezone.now()
                        asset.save(update_fields=['current_price', 'price_updated_at'])
                        updated_count += 1
                    else:
                        errors.append(f"No valid price data for {asset.symbol}")
                        
                except Exception as e:
                    errors.append(f"Error updating {asset.symbol}: {str(e)}")
            
        except ImportError:
            # Fallback to basic API service if price service not available
            try:
                from .api_services import market_data_service
                
                for asset in sip_assets:
                    try:
                        current_price = market_data_service.get_current_price(asset.symbol)
                        
                        if current_price and current_price > 0:
                            asset.current_price = current_price
                            asset.price_updated_at = timezone.now()
                            asset.save(update_fields=['current_price', 'price_updated_at'])
                            updated_count += 1
                        else:
                            errors.append(f"No price data for {asset.symbol}")
                            
                    except Exception as e:
                        errors.append(f"Error updating {asset.symbol}: {str(e)}")
                        
            except ImportError:
                # If no API service available, use mock updates for demo
                for asset in sip_assets:
                    try:
                        # Simple price simulation for demo purposes
                        import random
                        current_price = asset.current_price * Decimal(str(random.uniform(0.98, 1.02)))
                        asset.current_price = current_price
                        asset.price_updated_at = timezone.now()
                        asset.save(update_fields=['current_price', 'price_updated_at'])
                        updated_count += 1
                    except Exception as e:
                        errors.append(f"Error updating {asset.symbol}: {str(e)}")
        
        # Update all SIP returns after price updates
        try:
            from .services.sip_service import SIPService
            
            for sip in SIP.objects.filter(user=request.user):
                try:
                    SIPService.update_sip_calculations(sip)
                except Exception as e:
                    errors.append(f"Error updating SIP {sip.name}: {str(e)}")
                    
        except ImportError:
            # Fallback to model methods
            for sip in SIP.objects.filter(user=request.user):
                try:
                    sip.calculate_returns()
                    for investment in sip.investments.all():
                        investment.calculate_current_value()
                except Exception as e:
                    errors.append(f"Error updating SIP {sip.name}: {str(e)}")
        
        # Return JSON response for AJAX calls
        if request.headers.get('Content-Type') == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'updated_count': updated_count,
                'message': f'Updated prices for {updated_count} assets.',
                'errors': errors[:5] if errors else []  # Limit errors in response
            })
        
        # Handle regular form submission
        if updated_count > 0:
            messages.success(request, f'Updated prices for {updated_count} assets.')
        
        if errors:
            messages.warning(request, f'Some errors occurred: {"; ".join(errors[:3])}')
    
    return redirect('portfolios:sip_dashboard')


@login_required
def sip_performance_chart_data(request, pk):
    """API endpoint for SIP performance chart data."""
    sip = get_object_or_404(SIP, pk=pk, user=request.user)
    
    investments = sip.investments.order_by('date')
    chart_data = []
    cumulative_invested = 0
    cumulative_units = 0
    
    for investment in investments:
        cumulative_invested += float(investment.amount)
        cumulative_units += float(investment.units_allocated)
        current_value = cumulative_units * float(sip.asset.current_price)
        
        chart_data.append({
            'date': investment.date.isoformat(),
            'invested': cumulative_invested,
            'value': current_value,
            'units': cumulative_units,
            'nav': float(investment.nav_price)
        })
    
    return JsonResponse({
        'chart_data': chart_data,
        'sip_name': sip.name,
        'asset_name': sip.asset.name,
        'current_nav': float(sip.asset.current_price),
        'total_returns': float(sip.total_returns),
        'returns_percentage': float(sip.returns_percentage)
    })


class SIPHistoryImportView(LoginRequiredMixin, FormView):
    """Import historical SIP investments from CSV."""
    form_class = SIPHistoryImportForm
    template_name = 'portfolios/sip_import_history.html'
    success_url = reverse_lazy('portfolios:sip_dashboard')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        try:
            result = self.process_sip_import(form)
            
            messages.success(
                self.request,
                f"Successfully imported {result['success_count']} SIP investments! "
                f"Created {result['sips_created']} new SIPs."
            )
            
            if result['errors']:
                messages.warning(
                    self.request,
                    f"{result['error_count']} rows had errors. Check the details in your dashboard."
                )
                
        except Exception as e:
            messages.error(self.request, f"Import failed: {str(e)}")
            return self.form_invalid(form)
        
        return super().form_valid(form)
    
    def process_sip_import(self, form):
        """Process CSV file and import SIP data."""
        import csv
        import io
        from datetime import datetime
        from django.db import transaction
        
        try:
            from fuzzywuzzy import fuzz
        except ImportError:
            # Fallback for string matching if fuzzywuzzy is not available
            class FuzzFallback:
                @staticmethod
                def partial_ratio(s1, s2):
                    # Simple substring matching as fallback
                    s1, s2 = s1.lower(), s2.lower()
                    if s1 in s2 or s2 in s1:
                        return 80
                    return 0
            fuzz = FuzzFallback()
        
        csv_file = form.cleaned_data['csv_file']
        portfolio = form.cleaned_data['portfolio']
        create_missing_sips = form.cleaned_data['create_missing_sips']
        update_existing = form.cleaned_data['update_existing']
        
        # Read CSV content
        csv_content = csv_file.read().decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        success_count = 0
        error_count = 0
        sips_created = 0
        errors = []
        
        # Get all available funds for matching
        available_funds = Asset.objects.filter(
            asset_type='mutual_fund', 
            is_active=True
        )
        
        sip_cache = {}  # Cache for created/found SIPs
        
        with transaction.atomic():
            for row_num, row in enumerate(csv_reader, start=2):
                try:
                    # Required fields
                    sip_name = row.get('sip_name', '').strip()
                    fund_name = row.get('fund_name', '').strip()
                    investment_date = row.get('investment_date', '').strip()
                    amount = row.get('amount', '').strip()
                    nav_price = row.get('nav_price', '').strip()
                    
                    if not all([sip_name, fund_name, investment_date, amount, nav_price]):
                        raise ValueError("Missing required fields")
                    
                    # Parse and validate data
                    investment_date = datetime.strptime(investment_date, '%Y-%m-%d').date()
                    amount = Decimal(amount)
                    nav_price = Decimal(nav_price)
                    
                    # Optional fields
                    units = row.get('units', '').strip()
                    frequency = row.get('frequency', 'monthly').strip().lower()
                    transaction_id = row.get('transaction_id', '').strip()
                    
                    # Calculate units if not provided
                    if units:
                        units = Decimal(units)
                    else:
                        units = amount / nav_price
                    
                    # Find matching fund using fuzzy matching
                    matched_fund = self.find_matching_fund(fund_name, available_funds)
                    if not matched_fund:
                        raise ValueError(f"Could not match fund: {fund_name}")
                    
                    # Get or create SIP
                    sip_key = f"{sip_name}_{matched_fund.id}"
                    if sip_key not in sip_cache:
                        sip, created = SIP.objects.get_or_create(
                            name=sip_name,
                            portfolio=portfolio,
                            asset=matched_fund,
                            user=self.request.user,
                            defaults={
                                'amount': amount,
                                'frequency': frequency,
                                'start_date': investment_date,
                                'next_investment_date': investment_date,
                                'status': 'active'
                            }
                        )
                        sip_cache[sip_key] = sip
                        if created:
                            sips_created += 1
                    else:
                        sip = sip_cache[sip_key]
                    
                    # Create or update investment
                    investment, created = SIPInvestment.objects.get_or_create(
                        sip=sip,
                        date=investment_date,
                        defaults={
                            'amount': amount,
                            'nav_price': nav_price,
                            'units_allocated': units,
                            'transaction_id': transaction_id,
                        }
                    )
                    
                    if not created and update_existing:
                        investment.amount = amount
                        investment.nav_price = nav_price
                        investment.units_allocated = units
                        investment.transaction_id = transaction_id
                        investment.save()
                    
                    if created or update_existing:
                        success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    errors.append(f"Row {row_num}: {str(e)}")
            
            # Update all SIP totals and calculations
            for sip in sip_cache.values():
                sip.update_totals()
        
        return {
            'success_count': success_count,
            'error_count': error_count,
            'sips_created': sips_created,
            'errors': errors
        }
    
    def find_matching_fund(self, fund_name, available_funds):
        """Find matching fund using fuzzy string matching."""
        best_match = None
        best_score = 0
        
        for fund in available_funds:
            # Direct name match
            if fund_name.lower() in fund.name.lower() or fund.name.lower() in fund_name.lower():
                return fund
            
            # Fuzzy matching
            score = fuzz.partial_ratio(fund_name.lower(), fund.name.lower())
            if score > best_score and score > 70:  # 70% threshold
                best_score = score
                best_match = fund
        
        return best_match


@login_required
def sip_bulk_import(request, pk):
    """Bulk import investments for a specific SIP."""
    sip = get_object_or_404(SIP, pk=pk, user=request.user)
    
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        
        if not csv_file:
            messages.error(request, 'Please select a CSV file.')
            return redirect('portfolios:sip_detail', pk=pk)
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Please upload a valid CSV file.')
            return redirect('portfolios:sip_detail', pk=pk)
        
        try:
            import csv
            from decimal import Decimal
            from datetime import datetime
            
            # Read and parse CSV
            file_data = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(file_data.splitlines())
            
            success_count = 0
            error_count = 0
            errors = []
            
            for row_num, row in enumerate(csv_reader, start=2):  # Start from 2 since header is row 1
                try:
                    # Parse date
                    date_str = row.get('date', '').strip()
                    if not date_str:
                        raise ValueError("Date is required")
                    
                    # Try different date formats
                    for date_format in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                        try:
                            investment_date = datetime.strptime(date_str, date_format).date()
                            break
                        except ValueError:
                            continue
                    else:
                        raise ValueError(f"Invalid date format: {date_str}")
                    
                    # Parse amount
                    amount_str = row.get('amount', '').strip()
                    if not amount_str:
                        raise ValueError("Amount is required")
                    amount = Decimal(amount_str.replace(',', ''))
                    
                    # Parse NAV price
                    nav_str = row.get('nav_price', '').strip()
                    if not nav_str:
                        raise ValueError("NAV price is required")
                    nav_price = Decimal(nav_str.replace(',', ''))
                    
                    # Parse units (optional)
                    units_str = row.get('units', '').strip()
                    if units_str:
                        units = Decimal(units_str.replace(',', ''))
                    else:
                        units = amount / nav_price  # Calculate units
                    
                    # Parse fees (optional)
                    fees_str = row.get('fees', '').strip()
                    fees = Decimal(fees_str.replace(',', '')) if fees_str else Decimal('0')
                    
                    # Create investment
                    SIPInvestment.objects.create(
                        sip=sip,
                        date=investment_date,
                        amount=amount,
                        nav_price=nav_price,
                        units_allocated=units,
                        fees=fees,
                        current_nav=sip.asset.current_price,
                        notes=f"Imported from CSV"
                    )
                    
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    errors.append(f"Row {row_num}: {str(e)}")
            
            # Update SIP totals
            sip.update_totals()
            
            # Show results
            if success_count > 0:
                messages.success(request, f'Successfully imported {success_count} investments.')
            
            if error_count > 0:
                error_msg = f'{error_count} errors occurred:\n' + '\n'.join(errors[:5])  # Show first 5 errors
                if len(errors) > 5:
                    error_msg += f'\n... and {len(errors) - 5} more errors'
                messages.warning(request, error_msg)
            
        except Exception as e:
            messages.error(request, f'Error processing CSV file: {str(e)}')
    
    return redirect('portfolios:sip_detail', pk=pk)


# Enhanced SIP Management Functions

@login_required
def sip_pause(request, pk):
    """Pause a SIP."""
    sip = get_object_or_404(SIP, pk=pk, user=request.user)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        
        try:
            from .services.sip_service import SIPService
            SIPService.pause_sip(sip, reason)
            messages.success(request, f'SIP "{sip.name}" has been paused.')
        except ImportError:
            # Fallback without service
            sip.status = 'paused'
            if reason:
                sip.notes = f"Paused: {reason}"
            sip.save()
            messages.success(request, f'SIP "{sip.name}" has been paused.')
        except Exception as e:
            messages.error(request, f'Error pausing SIP: {str(e)}')
    
    return redirect('portfolios:sip_detail', pk=pk)


@login_required
def sip_resume(request, pk):
    """Resume a paused SIP."""
    sip = get_object_or_404(SIP, pk=pk, user=request.user)
    
    if request.method == 'POST':
        try:
            from .services.sip_service import SIPService
            SIPService.resume_sip(sip)
            messages.success(request, f'SIP "{sip.name}" has been resumed.')
        except ImportError:
            # Fallback without service
            sip.status = 'active'
            sip.save()
            messages.success(request, f'SIP "{sip.name}" has been resumed.')
        except Exception as e:
            messages.error(request, f'Error resuming SIP: {str(e)}')
    
    return redirect('portfolios:sip_detail', pk=pk)


@login_required
def sip_complete(request, pk):
    """Mark a SIP as completed."""
    sip = get_object_or_404(SIP, pk=pk, user=request.user)
    
    if request.method == 'POST':
        try:
            from .services.sip_service import SIPService
            SIPService.complete_sip(sip)
            messages.success(request, f'SIP "{sip.name}" has been marked as completed.')
        except ImportError:
            # Fallback without service
            sip.status = 'completed'
            sip.save()
            messages.success(request, f'SIP "{sip.name}" has been marked as completed.')
        except Exception as e:
            messages.error(request, f'Error completing SIP: {str(e)}')
    
    return redirect('portfolios:sip_detail', pk=pk)


@login_required
def sip_batch_update(request):
    """Batch update multiple SIPs."""
    if request.method == 'POST':
        action = request.POST.get('action')
        sip_ids = request.POST.getlist('sip_ids')
        
        if not sip_ids:
            messages.error(request, 'Please select at least one SIP.')
            return redirect('portfolios:sip_list')
        
        sips = SIP.objects.filter(id__in=sip_ids, user=request.user)
        success_count = 0
        
        try:
            from .services.sip_service import SIPService
            
            for sip in sips:
                try:
                    if action == 'pause':
                        SIPService.pause_sip(sip)
                    elif action == 'resume':
                        SIPService.resume_sip(sip)
                    elif action == 'update_prices':
                        SIPService.update_sip_calculations(sip)
                    success_count += 1
                except Exception as e:
                    messages.warning(request, f'Error with SIP {sip.name}: {str(e)}')
                    
        except ImportError:
            # Fallback without service
            for sip in sips:
                try:
                    if action == 'pause':
                        sip.status = 'paused'
                        sip.save()
                    elif action == 'resume':
                        sip.status = 'active'
                        sip.save()
                    elif action == 'update_prices':
                        sip.calculate_returns()
                    success_count += 1
                except Exception as e:
                    messages.warning(request, f'Error with SIP {sip.name}: {str(e)}')
        
        if success_count > 0:
            messages.success(request, f'Successfully updated {success_count} SIP(s).')
    
    return redirect('portfolios:sip_list')


@login_required
def process_auto_sips(request):
    """Process automatic SIP investments."""
    if request.method == 'POST':
        try:
            from .services.sip_service import SIPService
            
            # Get due SIPs
            due_sips = SIPService.get_due_sips(request.user)
            processed = 0
            
            for sip in due_sips:
                try:
                    investment = SIPService.process_automatic_sip_investment(sip)
                    if investment:
                        processed += 1
                except Exception as e:
                    messages.warning(request, f'Error processing SIP {sip.name}: {str(e)}')
            
            if processed > 0:
                messages.success(request, f'Successfully processed {processed} automatic SIP investment(s).')
            else:
                messages.info(request, 'No SIPs were due for automatic investment.')
                
        except ImportError:
            messages.error(request, 'Automatic SIP processing service not available.')
        except Exception as e:
            messages.error(request, f'Error processing automatic SIPs: {str(e)}')
    
    return redirect('portfolios:sip_dashboard')


@login_required
def sip_performance_report(request):
    """Generate comprehensive SIP performance report."""
    user_sips = SIP.objects.filter(user=request.user).select_related('asset', 'portfolio')
    
    # Calculate comprehensive performance metrics
    report_data = {
        'total_sips': user_sips.count(),
        'active_sips': user_sips.filter(status='active').count(),
        'paused_sips': user_sips.filter(status='paused').count(),
        'completed_sips': user_sips.filter(status='completed').count(),
        'total_invested': sum(sip.total_invested for sip in user_sips),
        'current_value': sum(sip.current_value for sip in user_sips),
        'total_returns': 0,
        'best_performers': [],
        'worst_performers': [],
        'monthly_performance': [],
    }
    
    report_data['total_returns'] = report_data['current_value'] - report_data['total_invested']
    
    # Get top and worst performers
    sips_with_returns = [(sip, sip.returns_percentage) for sip in user_sips if sip.returns_percentage is not None]
    sips_with_returns.sort(key=lambda x: x[1], reverse=True)
    
    report_data['best_performers'] = sips_with_returns[:5]
    report_data['worst_performers'] = sips_with_returns[-5:]
    
    # Monthly performance data
    from django.db.models import Sum
    from datetime import date
    import calendar
    
    current_date = date.today()
    for i in range(12):
        year = current_date.year
        month = current_date.month - i
        if month <= 0:
            month += 12
            year -= 1
        
        month_investments = SIPInvestment.objects.filter(
            sip__user=request.user,
            date__year=year,
            date__month=month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        report_data['monthly_performance'].append({
            'month': calendar.month_name[month],
            'year': year,
            'amount': month_investments
        })
    
    report_data['monthly_performance'].reverse()
    
    context = {
        'report_data': report_data,
        'user_sips': user_sips,
        'generated_at': timezone.now(),
    }
    
    return render(request, 'portfolios/sip_performance_report.html', context)