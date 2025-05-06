from django.contrib import admin
from .models import Post, Media, Like, Comment, CommentLike, SavedPost, PostTag

class MediaInline(admin.TabularInline):
    model = Media
    extra = 1

class PostTagInline(admin.TabularInline):
    model = PostTag
    extra = 1

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'post_type', 'created_at', 'likes_count', 'comments_count', 'views_count')
    list_filter = ('post_type', 'created_at', 'is_archived', 'is_hidden')
    search_fields = ('user__username', 'caption', 'location')
    readonly_fields = ('id', 'created_at', 'updated_at', 'likes_count', 'comments_count', 'saves_count', 'views_count', 'engagement_score')
    inlines = [MediaInline, PostTagInline]
    date_hierarchy = 'created_at'

@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'media_type', 'order')
    list_filter = ('media_type',)
    search_fields = ('post__user__username',)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'post', 'parent', 'created_at', 'likes_count')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'text', 'post__user__username')
    readonly_fields = ('created_at', 'updated_at', 'likes_count')

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'post__user__username')

@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'comment', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'comment__user__username')

@admin.register(SavedPost)
class SavedPostAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'post__user__username')

@admin.register(PostTag)
class PostTagAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'post__user__username')
