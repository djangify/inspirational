from django.contrib import admin
from django.utils.html import format_html

from .models import (
    ExperimentWeek,
    ExperimentGoal,
    MilestoneReflection,
    AliveListItem,
    HostedTool,
)


@admin.register(ExperimentWeek)
class ExperimentWeekAdmin(admin.ModelAdmin):
    list_display = (
        "week_date",
        "week_number",
        "blog_posts_rewritten",
        "pinterest_pins",
        "revenue_this_week",
        "is_published",
    )
    list_filter = ("is_published", "is_milestone")
    list_editable = ("is_published",)
    ordering = ("-week_date",)


@admin.register(ExperimentGoal)
class ExperimentGoalAdmin(admin.ModelAdmin):
    list_display = ("milestone", "goal_text", "is_achieved")
    list_filter = ("milestone", "is_achieved")
    list_editable = ("is_achieved",)
    ordering = ("milestone", "order")


@admin.register(MilestoneReflection)
class MilestoneReflectionAdmin(admin.ModelAdmin):
    list_display = ("milestone", "published_date")


@admin.register(AliveListItem)
class AliveListItemAdmin(admin.ModelAdmin):
    list_display = ("user", "item_text", "is_living_it", "created")
    list_filter = ("is_living_it",)
    search_fields = ("user__email", "item_text")


@admin.register(HostedTool)
class HostedToolAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "published", "view_link", "updated")
    list_filter = ("published",)
    list_editable = ("published",)
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created", "updated")

    fieldsets = (
        (
            None,
            {
                "fields": ("title", "slug", "html_file", "description", "published"),
                "description": (
                    "Upload the single .html file Claude gives you, then save — "
                    "your tool goes live at /tools/&lt;slug&gt;/. "
                    "There is no limit on how many tools you can host. "
                    "Note: tools run in an isolated sandbox, so they cannot use "
                    "browser localStorage or call your logged-in pages — keep all "
                    "state in memory inside the artifact."
                ),
            },
        ),
        (
            "Info",
            {
                "fields": ("created", "updated"),
                "classes": ("collapse",),
            },
        ),
    )

    def view_link(self, obj):
        if not obj.pk:
            return "—"
        url = obj.get_absolute_url()
        if not obj.published:
            url = f"{url}?preview=1"
        return format_html('<a href="{}" target="_blank">View</a>', url)

    view_link.short_description = "Live page"
