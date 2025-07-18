from django.contrib import admin
from .models import Tag, PromptCategory, WritingPrompt
from .models_tracker import WritingGoal, WritingSession

class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

class PromptCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

class WritingPromptAdmin(admin.ModelAdmin):
    list_display = ('text_preview', 'category', 'difficulty', 'prompt_type', 'active')
    list_filter = ('category', 'difficulty', 'prompt_type', 'active', 'tags')
    search_fields = ('text',)
    filter_horizontal = ('tags',)
    
    def text_preview(self, obj):
        return obj.text[:50] + ('...' if len(obj.text) > 50 else '')
    text_preview.short_description = 'Prompt'

class WritingGoalAdmin(admin.ModelAdmin):
    list_display = ('user', 'goal_type', 'target_value', 'frequency', 'start_date', 'end_date', 'active')
    list_filter = ('goal_type', 'frequency', 'active', 'start_date')
    search_fields = ('user__username', 'notes')
    date_hierarchy = 'start_date'
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Goal Details', {
            'fields': ('goal_type', 'target_value', 'frequency', 'start_date', 'end_date', 'active')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_at', 'updated_at')
        }),
    )

class WritingSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'minutes_spent', 'word_count', 'mood', 'prompt_preview')
    list_filter = ('date', 'mood')
    search_fields = ('user__username', 'notes')
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Session Details', {
            'fields': ('date', 'minutes_spent', 'word_count', 'mood', 'prompt_used')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_at', 'updated_at')
        }),
    )
    
    def prompt_preview(self, obj):
        if obj.prompt_used:
            return obj.prompt_used.text[:30] + ('...' if len(obj.prompt_used.text) > 30 else '')
        return '—'
    prompt_preview.short_description = 'Prompt Used'

admin.site.register(Tag, TagAdmin)
admin.site.register(PromptCategory, PromptCategoryAdmin)
admin.site.register(WritingPrompt, WritingPromptAdmin)
admin.site.register(WritingGoal, WritingGoalAdmin)
admin.site.register(WritingSession, WritingSessionAdmin)
