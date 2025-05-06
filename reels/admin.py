from django.contrib import admin
from .models import Reel, ReelLike, ReelComment, ReelCommentLike, SavedReel

@admin.register(Reel)
class ReelAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'views_count', 'likes_count', 'comments_count', 'shares_count')
    list_filter = ('created_at', 'is_archived', 'is_hidden')
    search_fields = ('user__username', 'caption', 'audio_track', 'audio_artist')
    readonly_fields = ('id', 'created_at', 'views_count', 'likes_count', 'comments_count', 'shares_count', 'engagement_score')
    date_hierarchy = 'created_at'

@admin.register(ReelComment)
class ReelCommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'reel', 'parent', 'created_at', 'likes_count')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'text', 'reel__user__username')
    readonly_fields = ('created_at', 'likes_count')

@admin.register(ReelLike)
class ReelLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'reel', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'reel__user__username')

@admin.register(ReelCommentLike)
class ReelCommentLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'comment', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'comment__user__username')

@admin.register(SavedReel)
class SavedReelAdmin(admin.ModelAdmin):
    list_display = ('user', 'reel', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'reel__user__username')
