from django.contrib import admin
from .models import Budget, BudgetCategory, BudgetGoal, BudgetAlert


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['name', 'period', 'total_budget', 'spent_amount', 'user', 'is_active']
    list_filter = ['period', 'is_active', 'created_at']
    search_fields = ['name', 'user__username']
    readonly_fields = ['id', 'spent_amount', 'remaining_amount', 'created_at', 'updated_at']
    date_hierarchy = 'start_date'


@admin.register(BudgetCategory)
class BudgetCategoryAdmin(admin.ModelAdmin):
    list_display = ['budget', 'category', 'allocated_amount', 'spent_amount']
    list_filter = ['budget__period', 'category__category_type']
    search_fields = ['budget__name', 'category__name']


@admin.register(BudgetGoal)
class BudgetGoalAdmin(admin.ModelAdmin):
    list_display = ['name', 'goal_type', 'target_amount', 'current_amount', 'target_date', 'is_achieved']
    list_filter = ['goal_type', 'priority', 'is_achieved', 'is_active']
    search_fields = ['name', 'user__username']
    date_hierarchy = 'target_date'


@admin.register(BudgetAlert)
class BudgetAlertAdmin(admin.ModelAdmin):
    list_display = ['alert_type', 'user', 'is_read', 'created_at']
    list_filter = ['alert_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'message']