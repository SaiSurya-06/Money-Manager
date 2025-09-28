"""
Enhanced Views with Service Layer Integration
Production-level views with proper error handling and security.
"""
import json
import logging
from typing import Dict, Any, Optional
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, FormView
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from django.http import JsonResponse, HttpResponse, Http404
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.utils import timezone
from decimal import Decimal

from .models import Portfolio, SIP, Asset
from .forms import PortfolioForm, SIPForm, SIPInvestmentForm
from .services import PortfolioService, SIPService, PriceService
from .exceptions import (
    PortfolioError, SIPError, ValidationError, 
    PriceDataError, BusinessRuleError
)
from .utils.validators import InvestmentValidator
from .constants import DEFAULT_PAGINATION, CACHE_TIMEOUTS

logger = logging.getLogger(__name__)


class SecureViewMixin:
    """Mixin for enhanced security in views."""
    
    def dispatch(self, request, *args, **kwargs):
        """Add security headers and logging."""
        try:
            response = super().dispatch(request, *args, **kwargs)
            
            # Add security headers
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
            response['X-XSS-Protection'] = '1; mode=block'
            
            return response
        except Exception as e:
            logger.error(f"View error in {self.__class__.__name__}: {str(e)}", 
                        exc_info=True, extra={'user': request.user.id if request.user.is_authenticated else None})
            raise


class ErrorHandlingMixin:
    """Mixin for consistent error handling."""
    
    def handle_service_error(self, e: Exception, default_message: str = "An error occurred"):
        """Handle service layer errors consistently."""
        if isinstance(e, ValidationError):
            messages.error(self.request, str(e))
        elif isinstance(e, BusinessRuleError):
            messages.warning(self.request, str(e))
        elif isinstance(e, (PortfolioError, SIPError, PriceDataError)):
            messages.error(self.request, str(e))
        else:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            messages.error(self.request, default_message)


class EnhancedPortfolioListView(SecureViewMixin, ErrorHandlingMixin, LoginRequiredMixin, ListView):
    """Enhanced portfolio list with service layer."""
    model = Portfolio
    template_name = 'portfolios/enhanced_portfolio_list.html'
    context_object_name = 'portfolios'
    paginate_by = DEFAULT_PAGINATION['portfolio_list']

    def get_queryset(self):
        """Get user's portfolios with optimizations."""
        try:
            return PortfolioService.get_user_portfolios(self.request.user)
        except PortfolioError as e:
            self.handle_service_error(e, "Failed to load portfolios")
            return Portfolio.objects.none()

    def get_context_data(self, **kwargs):
        """Add dashboard data to context."""
        context = super().get_context_data(**kwargs)
        
        try:
            # Get portfolio summary
            summary = PortfolioService.get_portfolio_summary(self.request.user)
            context.update(summary)
            
        except PortfolioError as e:
            self.handle_service_error(e)
            
        return context


class EnhancedPortfolioCreateView(SecureViewMixin, ErrorHandlingMixin, LoginRequiredMixin, CreateView):
    """Enhanced portfolio creation with service layer."""
    model = Portfolio
    form_class = PortfolioForm
    template_name = 'portfolios/enhanced_portfolio_form.html'
    success_url = reverse_lazy('portfolios:enhanced_list')

    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        """Create portfolio using service layer."""
        try:
            portfolio = PortfolioService.create_portfolio(
                user=self.request.user,
                name=form.cleaned_data['name'],
                description=form.cleaned_data.get('description', '')
            )
            
            messages.success(
                self.request, 
                f'Portfolio "{portfolio.name}" created successfully!'
            )
            
            # Store created object for success_url
            self.object = portfolio
            return redirect(self.get_success_url())
            
        except (ValidationError, PortfolioError) as e:
            self.handle_service_error(e, "Failed to create portfolio")
            return self.form_invalid(form)


class EnhancedPortfolioDetailView(SecureViewMixin, ErrorHandlingMixin, LoginRequiredMixin, DetailView):
    """Enhanced portfolio detail with performance metrics."""
    model = Portfolio
    template_name = 'portfolios/enhanced_portfolio_detail.html'
    context_object_name = 'portfolio'

    def get_queryset(self):
        """Ensure user can only access their portfolios."""
        return Portfolio.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        """Add comprehensive portfolio data."""
        context = super().get_context_data(**kwargs)
        portfolio = self.object
        
        try:
            # Update portfolio values
            PortfolioService.update_portfolio_values(portfolio)
            
            # Get performance metrics
            performance = PortfolioService.get_portfolio_performance(portfolio)
            context['performance'] = performance
            
            # Get asset allocation
            allocation = PortfolioService.get_asset_allocation(portfolio)
            context['allocation'] = allocation
            
            # Get holdings with pagination
            holdings = portfolio.holdings.filter(is_active=True).select_related('asset')
            paginator = Paginator(holdings, 10)
            page_number = self.request.GET.get('page')
            context['holdings'] = paginator.get_page(page_number)
            
            # Check if rebalancing needed
            context['needs_rebalancing'] = portfolio.check_rebalancing_needed()
            
        except PortfolioError as e:
            self.handle_service_error(e)
            
        return context


class EnhancedSIPListView(SecureViewMixin, ErrorHandlingMixin, LoginRequiredMixin, ListView):
    """Enhanced SIP list with comprehensive data."""
    model = SIP
    template_name = 'portfolios/enhanced_sip_list.html'
    context_object_name = 'sips'
    paginate_by = DEFAULT_PAGINATION['sip_list']

    def get_queryset(self):
        """Get user's SIPs with filtering."""
        try:
            status = self.request.GET.get('status')
            portfolio_id = self.request.GET.get('portfolio')
            
            # Get portfolio filter if provided
            portfolio = None
            if portfolio_id:
                try:
                    portfolio = Portfolio.objects.get(
                        id=portfolio_id, 
                        user=self.request.user
                    )
                except Portfolio.DoesNotExist:
                    pass
            
            return SIPService.get_user_sips(
                user=self.request.user,
                status=status,
                portfolio=portfolio
            )
            
        except SIPError as e:
            self.handle_service_error(e, "Failed to load SIPs")
            return SIP.objects.none()

    def get_context_data(self, **kwargs):
        """Add SIP dashboard data."""
        context = super().get_context_data(**kwargs)
        
        try:
            # Get SIP dashboard data
            dashboard_data = SIPService.get_sip_dashboard_data(self.request.user)
            context.update(dashboard_data)
            
            # Get user's portfolios for filtering
            context['portfolios'] = PortfolioService.get_user_portfolios(self.request.user)
            
            # Current filters
            context['current_status'] = self.request.GET.get('status', '')
            context['current_portfolio'] = self.request.GET.get('portfolio', '')
            
        except (SIPError, PortfolioError) as e:
            self.handle_service_error(e)
            
        return context


class EnhancedSIPCreateView(SecureViewMixin, ErrorHandlingMixin, LoginRequiredMixin, CreateView):
    """Enhanced SIP creation with validation."""
    model = SIP
    form_class = SIPForm
    template_name = 'portfolios/enhanced_sip_form.html'
    success_url = reverse_lazy('portfolios:enhanced_sip_list')

    def get_form_kwargs(self):
        """Pass user to form."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Create SIP using service layer."""
        try:
            sip = SIPService.create_sip(
                user=self.request.user,
                portfolio=form.cleaned_data['portfolio'],
                asset=form.cleaned_data['asset'],
                name=form.cleaned_data['name'],
                amount=form.cleaned_data['amount'],
                frequency=form.cleaned_data['frequency'],
                start_date=form.cleaned_data['start_date'],
                end_date=form.cleaned_data.get('end_date'),
                auto_invest=form.cleaned_data.get('auto_invest', False)
            )
            
            messages.success(
                self.request,
                f'SIP "{sip.name}" created successfully!'
            )
            
            self.object = sip
            return redirect(self.get_success_url())
            
        except (ValidationError, SIPError) as e:
            self.handle_service_error(e, "Failed to create SIP")
            return self.form_invalid(form)


class EnhancedSIPDetailView(SecureViewMixin, ErrorHandlingMixin, LoginRequiredMixin, DetailView):
    """Enhanced SIP detail with performance metrics."""
    model = SIP
    template_name = 'portfolios/enhanced_sip_detail.html'
    context_object_name = 'sip'

    def get_queryset(self):
        """Ensure user can only access their SIPs."""
        return SIP.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        """Add comprehensive SIP data."""
        context = super().get_context_data(**kwargs)
        sip = self.object
        
        try:
            # Get performance metrics
            performance = SIPService.get_sip_performance_metrics(sip)
            context['performance'] = performance
            
            # Get investments with pagination
            investments = sip.investments.all().order_by('-date')
            paginator = Paginator(investments, DEFAULT_PAGINATION['investment_list'])
            page_number = self.request.GET.get('page')
            context['investments'] = paginator.get_page(page_number)
            
            # Calculate XIRR
            context['xirr'] = SIPService.calculate_sip_xirr(sip)
            
            # Check if due for investment
            context['is_due'] = sip.is_due_for_investment
            
        except SIPError as e:
            self.handle_service_error(e)
            
        return context


class EnhancedSIPInvestmentCreateView(SecureViewMixin, ErrorHandlingMixin, LoginRequiredMixin, CreateView):
    """Enhanced SIP investment creation."""
    model = SIPInvestment
    form_class = SIPInvestmentForm
    template_name = 'portfolios/enhanced_sip_investment_form.html'

    def get_sip(self):
        """Get the SIP for this investment."""
        sip_id = self.kwargs['sip_pk']
        return get_object_or_404(
            SIP,
            pk=sip_id,
            user=self.request.user
        )

    def get_form_kwargs(self):
        """Pass SIP to form."""
        kwargs = super().get_form_kwargs()
        kwargs['sip'] = self.get_sip()
        return kwargs

    def form_valid(self, form):
        """Create investment using service layer."""
        try:
            sip = self.get_sip()
            
            investment = SIPService.create_sip_investment(
                sip=sip,
                amount=form.cleaned_data['amount'],
                nav_price=form.cleaned_data['nav_price'],
                investment_date=form.cleaned_data['date'],
                transaction_id=form.cleaned_data.get('transaction_id', ''),
                fees=form.cleaned_data.get('fees', Decimal('0')),
                notes=form.cleaned_data.get('notes', '')
            )
            
            messages.success(
                self.request,
                f'Investment of ₹{investment.amount} recorded successfully!'
            )
            
            return redirect('portfolios:enhanced_sip_detail', pk=sip.pk)
            
        except (ValidationError, SIPError) as e:
            self.handle_service_error(e, "Failed to record investment")
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        """Add SIP context."""
        context = super().get_context_data(**kwargs)
        context['sip'] = self.get_sip()
        return context

    def get_success_url(self):
        """Redirect to SIP detail."""
        return reverse('portfolios:enhanced_sip_detail', kwargs={'pk': self.get_sip().pk})


@login_required
def enhanced_price_update_view(request):
    """Enhanced price update with better error handling."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Get user's assets
        user_portfolios = Portfolio.objects.filter(user=request.user, is_active=True)
        user_sips = SIP.objects.filter(user=request.user, status='active')
        
        # Collect unique assets
        asset_ids = set()
        for portfolio in user_portfolios:
            asset_ids.update(portfolio.holdings.filter(is_active=True).values_list('asset_id', flat=True))
        
        for sip in user_sips:
            asset_ids.add(sip.asset_id)
        
        assets = Asset.objects.filter(id__in=asset_ids)
        
        # Update prices using service
        results = PriceService.update_asset_prices(list(assets))
        
        # Update portfolio values
        for portfolio in user_portfolios:
            PortfolioService.update_portfolio_values(portfolio)
        
        # Update SIP calculations
        for sip in user_sips:
            SIPService.update_sip_calculations(sip)
        
        return JsonResponse({
            'success': True,
            'message': f"Updated {results['success_count']} assets successfully",
            'updated_count': results['success_count'],
            'error_count': results['error_count'],
            'errors': results['errors'][:5]  # Limit errors shown
        })
        
    except Exception as e:
        logger.error(f"Price update failed: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': 'Price update failed',
            'message': str(e)
        }, status=500)


@login_required
def enhanced_dashboard_view(request):
    """Enhanced dashboard with comprehensive data."""
    try:
        # Get portfolio summary
        portfolio_summary = PortfolioService.get_portfolio_summary(request.user)
        
        # Get SIP dashboard data
        sip_summary = SIPService.get_sip_dashboard_data(request.user)
        
        # Get due SIPs
        due_sips = SIPService.get_due_sips(request.user)
        
        # Get recent activity (this would need to be implemented)
        recent_activity = []  # Placeholder
        
        context = {
            'portfolio_summary': portfolio_summary,
            'sip_summary': sip_summary,
            'due_sips': due_sips,
            'recent_activity': recent_activity,
        }
        
        return render(request, 'portfolios/enhanced_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}", exc_info=True)
        messages.error(request, "Failed to load dashboard data")
        return render(request, 'portfolios/enhanced_dashboard.html', {})


@method_decorator(cache_page(CACHE_TIMEOUTS['price_data']), name='get')
class EnhancedAssetPriceAPI(SecureViewMixin, LoginRequiredMixin, ListView):
    """API endpoint for asset prices."""
    
    def get(self, request, *args, **kwargs):
        """Get current asset price."""
        symbol = request.GET.get('symbol')
        asset_type = request.GET.get('type', 'stock')
        
        if not symbol:
            return JsonResponse({'error': 'Symbol required'}, status=400)
        
        try:
            # Validate inputs
            symbol = InvestmentValidator.validate_symbol(symbol)
            
            # Get price
            price = PriceService.get_current_price(symbol, asset_type)
            
            return JsonResponse({
                'symbol': symbol,
                'price': float(price),
                'currency': 'INR',
                'timestamp': timezone.now().isoformat()
            })
            
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except PriceDataError as e:
            return JsonResponse({'error': str(e)}, status=404)
        except Exception as e:
            logger.error(f"Price API error: {str(e)}")
            return JsonResponse({'error': 'Internal server error'}, status=500)


@login_required
def process_due_sips_view(request):
    """Manual trigger for processing due SIPs."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        due_sips = SIPService.get_due_sips(request.user)
        processed_count = 0
        errors = []
        
        for sip in due_sips:
            try:
                SIPService.process_automatic_sip_investment(sip)
                processed_count += 1
            except Exception as e:
                error_msg = f"Failed to process {sip.name}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        return JsonResponse({
            'success': True,
            'processed_count': processed_count,
            'total_due': len(due_sips),
            'errors': errors
        })
        
    except Exception as e:
        logger.error(f"SIP processing error: {str(e)}")
        return JsonResponse({
            'error': 'Failed to process SIPs',
            'message': str(e)
        }, status=500)