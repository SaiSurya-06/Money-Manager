from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid


class User(AbstractUser):
    """Custom user model with additional fields for MoneyManager."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=150)
    last_name = models.CharField(_('last name'), max_length=150)
    phone_number = models.CharField(_('phone number'), max_length=20, blank=True)
    date_of_birth = models.DateField(_('date of birth'), null=True, blank=True)
    avatar = models.ImageField(_('avatar'), upload_to='avatars/', null=True, blank=True)
    timezone = models.CharField(
        _('timezone'),
        max_length=50,
        default='UTC',
        help_text=_('User timezone for date/time display')
    )
    preferred_currency = models.CharField(
        _('preferred currency'),
        max_length=3,
        default='USD',
        help_text=_('User preferred currency code (ISO 4217)')
    )
    is_email_verified = models.BooleanField(_('email verified'), default=False)
    email_verification_token = models.CharField(max_length=100, blank=True)
    password_reset_token = models.CharField(max_length=100, blank=True)
    last_login_ip = models.GenericIPAddressField(_('last login IP'), null=True, blank=True)
    created_at = models.DateTimeField(_('date created'), auto_now_add=True)
    updated_at = models.DateTimeField(_('date updated'), auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        db_table = 'accounts_user'
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f'{self.first_name} {self.last_name}'
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name

    @property
    def display_name(self):
        """Return display name for UI."""
        if self.get_full_name():
            return self.get_full_name()
        return self.username

    def get_active_family_groups(self):
        """Get user's active family groups."""
        from moneymanager.apps.core.models import FamilyGroup
        return FamilyGroup.objects.filter(
            members=self,
            is_active=True,
            familygroupmembership__is_active=True
        ).distinct()

    def is_family_group_admin(self, family_group):
        """Check if user is admin of the given family group."""
        from moneymanager.apps.core.models import FamilyGroupMembership
        try:
            membership = FamilyGroupMembership.objects.get(
                user=self,
                family_group=family_group,
                is_active=True
            )
            return membership.role == 'admin'
        except FamilyGroupMembership.DoesNotExist:
            return False

    def can_access_family_group(self, family_group):
        """Check if user can access the given family group."""
        from moneymanager.apps.core.models import FamilyGroupMembership
        return FamilyGroupMembership.objects.filter(
            user=self,
            family_group=family_group,
            is_active=True
        ).exists()


class UserProfile(models.Model):
    """Extended user profile for additional settings."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(_('bio'), max_length=500, blank=True)
    location = models.CharField(_('location'), max_length=100, blank=True)
    website = models.URLField(_('website'), blank=True)

    # Notification settings
    email_notifications = models.BooleanField(_('email notifications'), default=True)
    push_notifications = models.BooleanField(_('push notifications'), default=True)
    budget_alerts = models.BooleanField(_('budget alerts'), default=True)
    transaction_alerts = models.BooleanField(_('transaction alerts'), default=False)

    # Privacy settings
    profile_visibility = models.CharField(
        _('profile visibility'),
        max_length=20,
        choices=[
            ('public', _('Public')),
            ('family', _('Family Only')),
            ('private', _('Private')),
        ],
        default='family'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts_user_profile'
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')

    def __str__(self):
        return f"{self.user.display_name}'s Profile"