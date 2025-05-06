from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Profile, Follow, BlockedUser

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'bio', 'website', 'phone_number', 'profile_picture')}),
        ('Account settings', {'fields': ('is_private', 'is_verified', 'show_activity_status', 'allow_sharing', 'allow_mentions')}),
        ('Interests', {'fields': ('interests',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_private', 'is_verified', 'is_staff')
    list_filter = ('is_private', 'is_verified', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    inlines = [ProfileInline]

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'followers_count', 'following_count', 'posts_count', 'profile_views', 'last_active')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('followers_count', 'following_count', 'posts_count', 'profile_views', 'last_active')

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'following', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('follower__username', 'following__username')
    date_hierarchy = 'created_at'

@admin.register(BlockedUser)
class BlockedUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'blocked_user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'blocked_user__username')
    date_hierarchy = 'created_at'
