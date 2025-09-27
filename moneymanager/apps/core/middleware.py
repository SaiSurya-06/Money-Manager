from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from .models import FamilyGroup, FamilyGroupMembership
import logging

logger = logging.getLogger(__name__)


class FamilyGroupMiddleware(MiddlewareMixin):
    """Middleware to set current family group for authenticated users."""

    def process_request(self, request):
        # Initialize defaults
        request.family_groups = FamilyGroup.objects.none()
        request.current_family_group = None

        if not isinstance(request.user, AnonymousUser) and request.user.is_authenticated:
            try:
                # Cache key for user's family groups
                cache_key = f"user_family_groups_{request.user.id}"
                family_groups = cache.get(cache_key)

                if family_groups is None:
                    # Get the user's active family groups
                    family_groups = FamilyGroup.objects.filter(
                        members=request.user,
                        is_active=True,
                        familygroupmembership__is_active=True
                    ).distinct().select_related().prefetch_related('members')

                    # Cache for 5 minutes
                    cache.set(cache_key, family_groups, 300)

                request.family_groups = family_groups

                # Set current family group from session or use first available
                current_family_group_id = request.session.get('current_family_group_id')
                current_family_group = None

                if current_family_group_id:
                    try:
                        # Convert to UUID if it's a string
                        import uuid
                        if isinstance(current_family_group_id, str):
                            current_family_group_id = uuid.UUID(current_family_group_id)

                        current_family_group = family_groups.get(id=current_family_group_id)
                    except (FamilyGroup.DoesNotExist, ValueError, TypeError):
                        # Invalid UUID or family group not found
                        current_family_group = family_groups.first() if family_groups.exists() else None
                        logger.warning(f"Invalid family group ID in session for user {request.user.id}")
                else:
                    current_family_group = family_groups.first() if family_groups.exists() else None

                request.current_family_group = current_family_group

                # Update session if needed
                if current_family_group:
                    request.session['current_family_group_id'] = str(current_family_group.id)
                elif 'current_family_group_id' in request.session:
                    request.session.pop('current_family_group_id', None)

            except Exception as e:
                logger.error(f"Error in FamilyGroupMiddleware for user {request.user.id}: {str(e)}")
                # Ensure defaults are set even on error
                request.family_groups = FamilyGroup.objects.none()
                request.current_family_group = None

    def process_response(self, request, response):
        """Clear family group cache if needed."""
        if hasattr(request, '_clear_family_group_cache') and request._clear_family_group_cache:
            cache_key = f"user_family_groups_{request.user.id}"
            cache.delete(cache_key)
        return response