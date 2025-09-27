from django.db import models
from django.contrib.auth import get_user_model
import uuid


class TimeStampedModel(models.Model):
    """Abstract base model with created and updated timestamps."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class FamilyGroup(TimeStampedModel):
    """Model to represent a family group for shared financial management."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='created_family_groups'
    )
    members = models.ManyToManyField(
        'accounts.User',
        through='FamilyGroupMembership',
        related_name='family_groups'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'core_family_group'
        ordering = ['name']

    def __str__(self):
        return self.name


class FamilyGroupMembership(TimeStampedModel):
    """Through model for FamilyGroup and User relationship."""
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('member', 'Member'),
        ('viewer', 'Viewer'),
    ]

    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    family_group = models.ForeignKey(FamilyGroup, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'core_family_group_membership'
        unique_together = ['user', 'family_group']

    def __str__(self):
        return f"{self.user.username} - {self.family_group.name} ({self.role})"


class Category(TimeStampedModel):
    """Model for transaction categories."""
    CATEGORY_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('transfer', 'Transfer'),
    ]

    name = models.CharField(max_length=100)
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPES)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories'
    )
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=7, default='#007bff')
    is_system_category = models.BooleanField(default=False)
    family_group = models.ForeignKey(
        FamilyGroup,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='categories'
    )

    class Meta:
        db_table = 'core_category'
        ordering = ['category_type', 'name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name