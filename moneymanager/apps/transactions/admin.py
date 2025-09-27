from django.contrib import admin
from .models import Account, Transaction, RecurringTransaction, TransactionTag


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'account_type', 'bank_name', 'current_balance', 'owner', 'is_active']
    list_filter = ['account_type', 'is_active', 'include_in_totals', 'created_at']
    search_fields = ['name', 'bank_name', 'owner__username']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['description', 'amount', 'transaction_type', 'category', 'account', 'date', 'user']
    list_filter = ['transaction_type', 'date', 'is_active', 'created_at']
    search_fields = ['description', 'notes', 'user__username']
    date_hierarchy = 'date'
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['user', 'account', 'to_account', 'from_account']


@admin.register(RecurringTransaction)
class RecurringTransactionAdmin(admin.ModelAdmin):
    list_display = ['name', 'amount', 'frequency', 'next_due_date', 'user', 'is_active']
    list_filter = ['frequency', 'transaction_type', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'user__username']
    date_hierarchy = 'next_due_date'


@admin.register(TransactionTag)
class TransactionTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'family_group']
    list_filter = ['created_at']
    search_fields = ['name']