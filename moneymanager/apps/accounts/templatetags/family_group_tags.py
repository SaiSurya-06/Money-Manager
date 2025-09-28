from django import template
from django.contrib.auth import get_user_model

register = template.Library()

User = get_user_model()


@register.filter
def is_family_group_admin(user, family_group):
    """Template filter to check if user is admin of a family group."""
    if not user or not family_group:
        return False
    return user.is_family_group_admin(family_group)


@register.filter
def can_access_family_group(user, family_group):
    """Template filter to check if user can access a family group."""
    if not user or not family_group:
        return False
    return user.can_access_family_group(family_group)


@register.simple_tag
def user_family_role(user, family_group):
    """Template tag to get user's role in a family group."""
    if not user or not family_group:
        return None
    
    from moneymanager.apps.core.models import FamilyGroupMembership
    try:
        membership = FamilyGroupMembership.objects.get(
            user=user,
            family_group=family_group,
            is_active=True
        )
        return membership.get_role_display()
    except FamilyGroupMembership.DoesNotExist:
        return None


@register.filter
def get_owner_name(obj):
    """Get the name of the owner of an object."""
    if hasattr(obj, 'user') and obj.user:
        return obj.user.display_name
    elif hasattr(obj, 'owner') and obj.owner:
        return obj.owner.display_name
    return "Unknown"


@register.filter
def get_owner_badge_class(obj, current_user):
    """Get the CSS class for the owner badge."""
    owner = None
    if hasattr(obj, 'user') and obj.user:
        owner = obj.user
    elif hasattr(obj, 'owner') and obj.owner:
        owner = obj.owner
    
    if owner == current_user:
        return "badge bg-primary"
    else:
        return "badge bg-secondary"


@register.filter
def sum_account_balances(accounts):
    """Calculate the total balance of all accounts."""
    from decimal import Decimal
    if not accounts:
        return Decimal('0.00')
    
    total = Decimal('0.00')
    for account in accounts:
        if hasattr(account, 'current_balance') and account.current_balance:
            total += account.current_balance
    return total


@register.simple_tag
def family_admin_indicator(user, family_group):
    """Show an indicator if the user can see all family data."""
    from django.utils.safestring import mark_safe
    
    if not user or not family_group:
        return ""
    
    if user.is_family_group_admin(family_group):
        return mark_safe('<i class="bi bi-shield-check text-warning me-1" title="You can see all family transactions and portfolios"></i>')
    return ""