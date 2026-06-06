from django.contrib import admin
from .models import ExperimentWeek, ExperimentGoal, MilestoneReflection, LiveItListItem


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


@admin.register(LiveItListItem)
class LiveItListItemAdmin(admin.ModelAdmin):
    list_display = ("user", "item_text", "is_living_it", "created")
    list_filter = ("is_living_it",)
    search_fields = ("user__email", "item_text")
