from django.contrib import admin
from .models import Administrator, Contact, ViewerProfile, FallAlert


@admin.register(Administrator)
class AdministratorAdmin(admin.ModelAdmin):
    list_display = ('email', 'phone_number')
    search_fields = ('email', 'phone_number')


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone_number', 'whatsapp_enabled', 'email_enabled')
    list_filter = ('whatsapp_enabled', 'email_enabled')
    search_fields = ('name', 'email', 'phone_number')


@admin.register(ViewerProfile)
class ViewerProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'setup_user', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at', 'setup_user')
    search_fields = ('name', 'email', 'setup_user__username', 'setup_user__email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'setup_user', 'name', 'email', 'phone_number')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(FallAlert)
class FallAlertAdmin(admin.ModelAdmin):
    list_display = ('id', 'setup_user', 'viewer', 'status', 'timestamp', 'confidence', 'whatsapp_sent', 'confirmed_by')
    list_filter = ('status', 'whatsapp_sent', 'timestamp', 'setup_user')
    search_fields = ('setup_user__username', 'viewer__name', 'viewer__email')
    readonly_fields = ('timestamp', 'confirmed_at')
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Alert Information', {
            'fields': ('setup_user', 'viewer', 'timestamp', 'status')
        }),
        ('Detection Details', {
            'fields': ('confidence', 'consecutive_frames', 'snapshot_path', 'detection_info')
        }),
        ('Notification', {
            'fields': ('whatsapp_sent',)
        }),
        ('Confirmation', {
            'fields': ('confirmed_by', 'confirmed_at')
        }),
    )
