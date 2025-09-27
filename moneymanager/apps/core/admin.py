from django.contrib import admin
from .models import FamilyGroup, FamilyGroupMembership, Category


@admin.register(FamilyGroup)
class FamilyGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'created_at', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'created_by__username']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(FamilyGroupMembership)
class FamilyGroupMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'family_group', 'role', 'joined_at', 'is_active']
    list_filter = ['role', 'is_active', 'joined_at']
    search_fields = ['user__username', 'family_group__name']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category_type', 'parent', 'family_group', 'is_system_category']
    list_filter = ['category_type', 'is_system_category', 'created_at']
    search_fields = ['name']
    ordering = ['category_type', 'name']