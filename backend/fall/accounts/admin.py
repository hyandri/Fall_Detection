from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for UserProfile"""
    list_display = ('user', 'user_type', 'created_at', 'updated_at')
    list_filter = ('user_type', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'user_type')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

