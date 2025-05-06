from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from posts.models import Post
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """
    Custom User model for NoChat
    """
    email = models.EmailField(_('email address'), unique=True)
    bio = models.TextField(blank=True, max_length=500)
    website = models.URLField(blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    profile_picture = models.ImageField(upload_to='uploads/profile_pics', default='default_profile.png')
    is_private = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)  # For blue badge verification
    
    # Add reference to the post created when profile picture is updated
    profile_picture_post = models.ForeignKey('posts.Post', on_delete=models.SET_NULL, null=True, blank=True, related_name='profile_picture_of')
    
    # Additional fields for user settings
    show_activity_status = models.BooleanField(default=True)
    allow_sharing = models.BooleanField(default=True)
    allow_mentions = models.BooleanField(default=True)
    
    # For recommendation algorithm
    interests = models.ManyToManyField('search.Hashtag', blank=True, related_name='interested_users')
    
    def get_absolute_url(self):
        return reverse('accounts:profile', kwargs={'username': self.username})
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}" if self.first_name and self.last_name else self.username
    
    def __str__(self):
        return self.username



class Profile(models.Model):
    """
    Extended profile information for users
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    followers_count = models.PositiveIntegerField(default=0)
    following_count = models.PositiveIntegerField(default=0)
    posts_count = models.PositiveIntegerField(default=0)
    
    # For analytics
    profile_views = models.PositiveIntegerField(default=0)
    last_active = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s profile"


class Follow(models.Model):
    """
    Model to track follower/following relationships
    """
    follower = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    following = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('follower', 'following')
        
    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


class BlockedUser(models.Model):
    """
    Model to track blocked users
    """
    user = models.ForeignKey(User, related_name='user_blocks', on_delete=models.CASCADE)
    blocked_user = models.ForeignKey(User, related_name='blocked_by', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'blocked_user')
        
    def __str__(self):
        return f"{self.user.username} blocked {self.blocked_user.username}"
