from django.contrib import admin
from .models import Story, StoryView, StoryReaction, StoryHighlight, HighlightStory

@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'story_type', 'created_at', 'expires_at', 'views_count', 'is_hidden')
    list_filter = ('story_type', 'created_at', 'is_hidden')
    search_fields = ('user__username', 'caption', 'location')
    readonly_fields = ('id', 'created_at', 'views_count')
    date_hierarchy = 'created_at'

@admin.register(StoryView)
class StoryViewAdmin(admin.ModelAdmin):
    list_display = ('story', 'user', 'viewed_at')
    list_filter = ('viewed_at',)
    search_fields = ('user__username', 'story__user__username')
    date_hierarchy = 'viewed_at'

@admin.register(StoryReaction)
class StoryReactionAdmin(admin.ModelAdmin):
    list_display = ('story', 'user', 'reaction_type', 'custom_message', 'created_at')
    list_filter = ('reaction_type', 'created_at')
    search_fields = ('user__username', 'story__user__username', 'custom_message')
    date_hierarchy = 'created_at'

@admin.register(StoryHighlight)
class StoryHighlightAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('title', 'user__username')
    date_hierarchy = 'created_at'

@admin.register(HighlightStory)
class HighlightStoryAdmin(admin.ModelAdmin):
    list_display = ('highlight', 'story', 'order')
    list_filter = ('highlight__user',)
    search_fields = ('highlight__title', 'highlight__user__username', 'story__id')
