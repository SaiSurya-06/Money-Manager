from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json

from .models import User, UserProfile
from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm, FamilyGroupCreationForm
from moneymanager.apps.core.models import FamilyGroup, FamilyGroupMembership


class SignUpView(CreateView):
    """User registration view."""
    model = User
    form_class = CustomUserCreationForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Account created successfully! Please log in.')
        return response


def login_view(request):
    """Custom login view."""
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Update last login IP
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')

            user.last_login_ip = ip
            user.save(update_fields=['last_login_ip'])

            messages.success(request, f'Welcome back, {user.get_short_name()}!')

            next_url = request.GET.get('next', 'dashboard:home')
            return redirect(next_url)
    else:
        form = CustomAuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """Custom logout view."""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('accounts:login')


class ProfileView(LoginRequiredMixin, DetailView):
    """User profile view."""
    model = User
    template_name = 'accounts/profile.html'
    context_object_name = 'profile_user'

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['family_groups'] = self.request.user.get_active_family_groups()
        # Ensure user has a profile
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        context['profile'] = profile
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Update user profile view."""
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'accounts/profile_update.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Profile updated successfully!')
        return response


@login_required
def family_group_create(request):
    """Create a new family group."""
    if request.method == 'POST':
        form = FamilyGroupCreationForm(request.POST)
        if form.is_valid():
            # Create the family group
            family_group = FamilyGroup.objects.create(
                name=form.cleaned_data['name'],
                created_by=request.user
            )

            # Add the creator as admin
            FamilyGroupMembership.objects.create(
                user=request.user,
                family_group=family_group,
                role='admin'
            )

            # Set as current family group
            request.session['current_family_group_id'] = str(family_group.id)

            messages.success(request, f'Family group "{family_group.name}" created successfully!')
            return redirect('accounts:family_groups')
    else:
        form = FamilyGroupCreationForm()

    return render(request, 'accounts/family_group_create.html', {'form': form})


@login_required
def family_groups_list(request):
    """List user's family groups."""
    family_groups = request.user.get_active_family_groups()
    
    # Add admin status for each group
    groups_with_admin_status = []
    for group in family_groups:
        groups_with_admin_status.append({
            'group': group,
            'is_admin': request.user.is_family_group_admin(group),
            'membership': group.familygroupmembership_set.filter(user=request.user, is_active=True).first()
        })
    
    return render(request, 'accounts/family_groups.html', {
        'family_groups': family_groups,
        'groups_with_admin_status': groups_with_admin_status
    })


@login_required
def family_group_detail(request, group_id):
    """Family group detail view."""
    family_group = get_object_or_404(FamilyGroup, id=group_id)

    # Check if user can access this family group
    if not request.user.can_access_family_group(family_group):
        messages.error(request, 'You do not have access to this family group.')
        return redirect('accounts:family_groups')

    memberships = FamilyGroupMembership.objects.filter(
        family_group=family_group,
        is_active=True
    ).select_related('user')

    is_admin = request.user.is_family_group_admin(family_group)

    return render(request, 'accounts/family_group_detail.html', {
        'family_group': family_group,
        'memberships': memberships,
        'is_admin': is_admin
    })


@login_required
@require_POST
def switch_family_group(request):
    """Switch current family group via AJAX."""
    try:
        data = json.loads(request.body)
        group_id = data.get('group_id')

        if group_id:
            try:
                family_group = get_object_or_404(FamilyGroup, id=group_id)

                # Check if user can access this family group
                if request.user.can_access_family_group(family_group):
                    request.session['current_family_group_id'] = str(family_group.id)

                    # Mark for cache clearing
                    request._clear_family_group_cache = True

                    return JsonResponse({
                        'success': True,
                        'group_name': family_group.name,
                        'group_id': str(family_group.id)
                    })
                else:
                    return JsonResponse({'success': False, 'error': 'Access denied to this family group'})
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Invalid group ID format'})
        else:
            # Clear current family group (switch to personal)
            request.session.pop('current_family_group_id', None)
            request._clear_family_group_cache = True

            return JsonResponse({
                'success': True,
                'group_name': 'Personal',
                'group_id': None
            })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'})


@login_required
@require_POST
def invite_member(request, group_id):
    """Invite a member to family group."""
    family_group = get_object_or_404(FamilyGroup, id=group_id)
    
    # Check if this is an AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '')

    # Check if user is admin
    if not request.user.is_family_group_admin(family_group):
        if is_ajax:
            return JsonResponse({'success': False, 'error': 'You must be an admin to invite members.'})
        messages.error(request, 'You must be an admin to invite members.')
        return redirect('accounts:family_group_detail', group_id=group_id)

    email = request.POST.get('email')
    role = request.POST.get('role', 'member')

    try:
        invited_user = User.objects.get(email=email)

        # Check if user is already a member
        if FamilyGroupMembership.objects.filter(
            user=invited_user,
            family_group=family_group,
            is_active=True
        ).exists():
            if is_ajax:
                return JsonResponse({'success': False, 'error': 'User is already a member of this group.'})
            messages.warning(request, 'User is already a member of this group.')
        else:
            # Add user to family group
            FamilyGroupMembership.objects.create(
                user=invited_user,
                family_group=family_group,
                role=role
            )
            if is_ajax:
                return JsonResponse({'success': True, 'message': f'{invited_user.display_name} has been added to the group.'})
            messages.success(request, f'{invited_user.display_name} has been added to the group.')

    except User.DoesNotExist:
        if is_ajax:
            return JsonResponse({'success': False, 'error': 'User with this email does not exist.'})
        messages.error(request, 'User with this email does not exist.')

    return redirect('accounts:family_group_detail', group_id=group_id)


@login_required
@require_POST
def remove_member(request, group_id, user_id):
    """Remove a member from family group."""
    family_group = get_object_or_404(FamilyGroup, id=group_id)
    member_user = get_object_or_404(User, id=user_id)
    
    # Check if this is an AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '')

    # Check if user is admin
    if not request.user.is_family_group_admin(family_group):
        if is_ajax:
            return JsonResponse({'success': False, 'error': 'You must be an admin to remove members.'})
        messages.error(request, 'You must be an admin to remove members.')
        return redirect('accounts:family_group_detail', group_id=group_id)

    # Prevent removing the creator
    if member_user == family_group.created_by:
        if is_ajax:
            return JsonResponse({'success': False, 'error': 'Cannot remove the group creator.'})
        messages.error(request, 'Cannot remove the group creator.')
        return redirect('accounts:family_group_detail', group_id=group_id)

    try:
        membership = FamilyGroupMembership.objects.get(
            user=member_user,
            family_group=family_group,
            is_active=True
        )
        membership.is_active = False
        membership.save()

        if is_ajax:
            return JsonResponse({'success': True, 'message': f'{member_user.display_name} has been removed from the group.'})
        messages.success(request, f'{member_user.display_name} has been removed from the group.')

    except FamilyGroupMembership.DoesNotExist:
        if is_ajax:
            return JsonResponse({'success': False, 'error': 'Membership not found.'})
        messages.error(request, 'Membership not found.')

    return redirect('accounts:family_group_detail', group_id=group_id)