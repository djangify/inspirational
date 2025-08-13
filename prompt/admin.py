from django.contrib import admin
from .models import Tag, PromptCategory, WritingPrompt
from .models_tracker import WritingGoal, WritingSession
from .models import WritingStyle


class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(PromptCategory)
class PromptCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "sub_category", "slug")
    list_filter = ("sub_category",)
    search_fields = ("name", "sub_category")
    fields = ("name", "sub_category", "slug", "description")


@admin.register(WritingPrompt)
class WritingPromptAdmin(admin.ModelAdmin):
    # exclude = ("prompt_type",)  # hides prompt_type from admin
    list_display = ("text", "category", "created_at", "active")
    list_filter = ("category", "writing_styles", "tags", "active")
    search_fields = ("text",)
    filter_horizontal = ("writing_styles", "tags")
    exclude = ("prompt_type",)

    def text_preview(self, obj):
        return obj.text[:50] + ("..." if len(obj.text) > 50 else "")

    text_preview.short_description = "Prompt"


@admin.register(WritingStyle)
class WritingStyleAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


class WritingGoalAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "goal_label",  # show label if set
        "goal_type",
        "target_value",
        "frequency",
        "start_date",
        "end_date",
        "active",
    )
    list_filter = ("goal_type", "frequency", "active", "start_date")
    search_fields = ("user__username", "goal_label", "notes")
    date_hierarchy = "start_date"
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("User Information", {"fields": ("user",)}),
        (
            "Goal Details",
            {
                "fields": (
                    "goal_label",  # NEW
                    "goal_type",
                    "target_value",
                    "frequency",
                    "start_date",
                    "end_date",
                    "active",
                )
            },
        ),
        ("Additional Information", {"fields": ("notes", "created_at", "updated_at")}),
    )


class WritingSessionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "goal",  # NEW
        "date",
        "minutes_spent",
        "word_count",
        "mood",
        "prompt_preview",
    )
    list_filter = ("goal", "mood", "date")  # include goal for quick filtering
    search_fields = (
        "user__username",
        "goal__goal_label",  # search by goal label
        "notes",
        "prompt_used",
    )
    list_select_related = ("user", "goal")
    date_hierarchy = "date"
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("User & Goal", {"fields": ("user", "goal")}),  # put goal near user
        (
            "Session Details",
            {"fields": ("date", "minutes_spent", "word_count", "mood", "prompt_used")},
        ),
        ("Additional Information", {"fields": ("notes", "created_at", "updated_at")}),
    )

    @admin.display(description="Prompt Used")
    def prompt_preview(self, obj):
        s = obj.prompt_used or ""
        return (s[:30] + "...") if len(s) > 30 else s


admin.site.register(Tag, TagAdmin)

admin.site.register(WritingGoal, WritingGoalAdmin)
admin.site.register(WritingSession, WritingSessionAdmin)
