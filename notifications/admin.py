from django.contrib import admin
from .models import Notification, NotificationSetting

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'notification_type', 'recipient', 'sender', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('recipient__username', 'sender__username', 'text')
    readonly_fields = ('id', 'created_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('id', 'notification_type', 'recipient', 'sender')
        }),
        ('Content', {
            'fields': ('text', 'content_id')
        }),
        ('Status', {
            'fields': ('is_read', 'created_at')
        }),
    )

@admin.register(NotificationSetting)
class NotificationSettingAdmin(admin.ModelAdmin):
    list_display = ('user', 'messages', 'likes', 'comments', 'follows')
    search_fields = ('user__username',)
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Push Notifications', {
            'fields': (
                'likes', 'comments', 'comment_likes', 'follows', 'follow_requests',
                'messages', 'mentions', 'tags', 'story_views', 'story_reactions', 'post_shares'
            )
        }),
        ('Email Notifications', {
            'fields': (
                'email_likes', 'email_comments', 'email_follows', 'email_messages', 'email_system'
            )
        }),
    )
