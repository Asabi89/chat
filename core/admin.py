from django.contrib import admin
from django.utils import timezone
from .models import Report, Activity, Feedback, AppSetting

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('reporter', 'content_type', 'report_type', 'created_at', 'is_reviewed', 'action_taken')
    list_filter = ('content_type', 'report_type', 'is_reviewed', 'created_at')
    search_fields = ('reporter__username', 'content_id', 'description', 'action_taken')
    date_hierarchy = 'created_at'
    readonly_fields = ('reporter', 'content_type', 'content_id', 'report_type', 'description', 'created_at')
    
    actions = ['mark_as_reviewed', 'mark_as_no_action']
    
    def mark_as_reviewed(self, request, queryset):
        queryset.update(is_reviewed=True, reviewed_at=timezone.now())
    mark_as_reviewed.short_description = "Mark selected reports as reviewed"
    
    def mark_as_no_action(self, request, queryset):
        queryset.update(is_reviewed=True, reviewed_at=timezone.now(), action_taken="No action required")
    mark_as_no_action.short_description = "Mark selected reports as reviewed with no action"

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'content_id', 'ip_address', 'created_at')
    list_filter = ('activity_type', 'created_at')
    search_fields = ('user__username', 'content_id', 'ip_address', 'user_agent')
    date_hierarchy = 'created_at'
    readonly_fields = ('user', 'activity_type', 'content_id', 'ip_address', 'user_agent', 'created_at')

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'feedback_type', 'subject', 'created_at', 'is_resolved')
    list_filter = ('feedback_type', 'is_resolved', 'created_at')
    search_fields = ('user__username', 'subject', 'message', 'response')
    date_hierarchy = 'created_at'
    readonly_fields = ('user', 'feedback_type', 'subject', 'message', 'screenshot', 'created_at')
    
    actions = ['mark_as_resolved']
    
    def mark_as_resolved(self, request, queryset):
        queryset.update(is_resolved=True, resolved_at=timezone.now())
    mark_as_resolved.short_description = "Mark selected feedback as resolved"

@admin.register(AppSetting)
class AppSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'value_preview', 'is_public', 'updated_at')
    list_filter = ('is_public', 'updated_at')
    search_fields = ('key', 'value', 'description')
    readonly_fields = ('updated_at',)
    
    def value_preview(self, obj):
        if len(obj.value) > 50:
            return f"{obj.value[:50]}..."
        return obj.value
    value_preview.short_description = 'Value'
