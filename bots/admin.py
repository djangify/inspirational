# bots/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import BotProduct, BotAccess


@admin.register(BotProduct)
class BotProductAdmin(admin.ModelAdmin):
    list_display = ['product', 'bot_name', 'message_limit', 'access_days', 'is_active']
    list_filter = ['is_active']
    search_fields = ['product__title', 'bot_name']
    readonly_fields = ['created', 'updated']

    fieldsets = (
        ('Product', {
            'fields': ('product', 'bot_name', 'is_active')
        }),
        ('Bot Configuration', {
            'fields': ('welcome_message', 'system_prompt'),
            'classes': ('wide',)
        }),
        ('Access Settings', {
            'fields': ('message_limit', 'access_days')
        }),
        ('Timestamps', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BotAccess)
class BotAccessAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'bot_product', 'message_count', 'messages_remaining_display',
        'days_remaining_display', 'has_access_display', 'created'
    ]
    list_filter = ['bot_product']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created', 'last_used', 'message_count']
    
    def messages_remaining_display(self, obj):
        remaining = obj.messages_remaining
        if remaining < 20:
            return format_html('<span style="color: red;">{}</span>', remaining)
        return remaining
    messages_remaining_display.short_description = 'Messages Left'

    def days_remaining_display(self, obj):
        days = obj.days_remaining
        if days == 0:
            return format_html('<span style="color: red;">Expired</span>')
        if days < 7:
            return format_html('<span style="color: orange;">{} days</span>', days)
        return f'{days} days'
    days_remaining_display.short_description = 'Days Left'

    def has_access_display(self, obj):
        if obj.has_access:
            return format_html('<span style="color: green;">✓ Active</span>')
        return format_html('<span style="color: red;">✗ Inactive</span>')
    has_access_display.short_description = 'Access'

    actions = ['extend_access_30_days']

    def extend_access_30_days(self, request, queryset):
        from django.utils import timezone
        from datetime import timedelta
        for access in queryset:
            if access.is_expired:
                access.access_expires = timezone.now() + timedelta(days=30)
            else:
                access.access_expires += timedelta(days=30)
            access.save()
        self.message_user(request, f'{queryset.count()} access records extended by 30 days.')
    extend_access_30_days.short_description = 'Extend access by 30 days'