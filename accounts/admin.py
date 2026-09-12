from django.contrib import admin

from .models import Profile, Transaction


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('account_number', 'user', 'balance', 'is_frozen', 'created_at')
    list_filter = ('is_frozen',)
    search_fields = ('account_number', 'user__username', 'user__email')
    readonly_fields = ('account_number', 'created_at')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('kind', 'from_account', 'to_account', 'amount', 'status', 'created_at')
    list_filter = ('kind', 'status')
    search_fields = ('from_account__account_number', 'to_account__account_number')
    readonly_fields = ('created_at',)
