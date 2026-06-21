# bots/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import BotProduct, BotAccess, BotKnowledge

class BotKnowledgeInline(admin.TabularInline):
    model = BotKnowledge
    extra = 1
    fields = ['title', 'knowledge_file', 'order']


@admin.register(BotProduct)
class BotProductAdmin(admin.ModelAdmin):
    list_display = ['product', 'bot_name', 'model', 'message_limit', 'access_days', 'is_active']
    list_filter = ['is_active', 'model']
    search_fields = ['product__title', 'bot_name']
    readonly_fields = ['created', 'updated', 'knowledge_size']
    inlines = [BotKnowledgeInline]

    fieldsets = (
        ('Product', {
            'fields': ('product', 'bot_name', 'is_active')
        }),
        ('Bot Configuration', {
            'fields': ('welcome_message', 'system_prompt'),
            'classes': ('wide',)
        }),
        ('Model & cost', {
            'fields': ('model', 'max_tokens', 'knowledge_size'),
            'description': (
                'Haiku costs about a third of Sonnet to run and is well suited to '
                'answering from a workbook PDF. The knowledge size below is sent on every '
                "message — keep it small (ideally one PDF) to keep costs down and to stay "
                "inside the model's context window."
            ),
        }),
        ('Access Settings', {
            'fields': ('message_limit', 'access_days')
        }),
        ('Timestamps', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )

    def knowledge_size(self, obj):
        """Estimate the token size of the attached PDFs and warn if large."""
        if obj is None or not obj.pk:
            return "Save the bot first; attached files are then measured here."
        try:
            from pypdf import PdfReader
        except Exception:
            return "Install pypdf to see the size estimate."
        chars = 0
        files = 0
        for kf in obj.knowledge_files.all():
            try:
                reader = PdfReader(kf.knowledge_file.path)
                chars += sum(len(p.extract_text() or "") for p in reader.pages)
                files += 1
            except Exception:
                continue
        tokens = chars // 4
        if tokens < 25_000:
            colour, note = "green", "good — cheap and well within the context window"
        elif tokens < 100_000:
            colour, note = "orange", "getting large — consider fewer / shorter PDFs"
        else:
            colour, note = "red", "too large — likely to exceed the context window and cost a lot per message"
        return format_html(
            '<strong style="color:{}">~{} tokens</strong> across {} file(s) — {}',
            colour, f"{tokens:,}", files, note,
        )
    knowledge_size.short_description = "Knowledge size (sent every message)"


@admin.register(BotAccess)
class BotAccessAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'bot_product', 'message_count', 'messages_remaining_display',
        'days_remaining_display', 'has_access_display', 'created'
    ]
    list_filter = ['bot_product']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created', 'last_used', 'message_count']
    fields = ['user', 'bot_product', 'message_count', 'bonus_messages', 'access_expires']
    
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