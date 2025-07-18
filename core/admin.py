from django.contrib import admin
from .models import SupportMessage


@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "submitted_at")
    list_filter = ("submitted_at",)
    search_fields = ("name", "email", "subject", "message")
