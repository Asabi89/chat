from django.contrib import admin
from .models import Hashtag, PostHashtag, ReelHashtag, SearchHistory, TrendingHashtag

@admin.register(Hashtag)
class HashtagAdmin(admin.ModelAdmin):
    list_display = ('name', 'post_count', 'created_at')
    search_fields = ('name',)
    list_filter = ('created_at',)
    readonly_fields = ('post_count',)
    ordering = ('-post_count',)

@admin.register(PostHashtag)
class PostHashtagAdmin(admin.ModelAdmin):
    list_display = ('hashtag', 'post', 'created_at')
    search_fields = ('hashtag__name', 'post__id')
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'

@admin.register(ReelHashtag)
class ReelHashtagAdmin(admin.ModelAdmin):
    list_display = ('hashtag', 'reel', 'created_at')
    search_fields = ('hashtag__name', 'reel__id')
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'

@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'query', 'search_type', 'created_at')
    search_fields = ('user__username', 'query')
    list_filter = ('search_type', 'created_at')
    date_hierarchy = 'created_at'

@admin.register(TrendingHashtag)
class TrendingHashtagAdmin(admin.ModelAdmin):
    list_display = ('hashtag', 'post_count_24h', 'view_count_24h', 'engagement_score', 'date')
    search_fields = ('hashtag__name',)
    list_filter = ('date',)
    date_hierarchy = 'date'
    readonly_fields = ('post_count_24h', 'view_count_24h', 'engagement_score')
