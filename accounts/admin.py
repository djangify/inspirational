# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import MemberResource, UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'

# Extend the existing UserAdmin to include profile information
class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_favourite_count')
    
    def get_favourite_count(self, obj):
        return obj.profile.favourite_prompts.count()
    get_favourite_count.short_description = 'Favourite Prompts'

# Re-register UserAdmin with our custom version
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Register the UserProfile model directly as well
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_email', 'get_favourite_count')
    search_fields = ('user__username', 'user__email')
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'
    
    def get_favourite_count(self, obj):
        return obj.favourite_prompts.count()
    get_favourite_count.short_description = 'Favourite Prompts'


@admin.register(MemberResource)
class MemberResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'description')