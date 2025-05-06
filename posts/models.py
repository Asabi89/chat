from django.db import models
from django.urls import reverse

import uuid

class Post(models.Model):
    """
    Model for user posts (images, videos, or carousels)
    """
    POST_TYPES = (
        ('image', 'Image'),
        ('video', 'Video'),
        ('carousel', 'Carousel'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='posts')
    caption = models.TextField(blank=True, max_length=2200)
    location = models.CharField(max_length=100, blank=True)
    post_type = models.CharField(max_length=10, choices=POST_TYPES, default='image')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Engagement metrics
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    saves_count = models.PositiveIntegerField(default=0)
    views_count = models.PositiveIntegerField(default=0)
    
    # For algorithm
    engagement_score = models.FloatField(default=0.0)
    
    # Moderation
    is_archived = models.BooleanField(default=False)  # User archived their post
    is_hidden = models.BooleanField(default=False)    # Admin hid the post
    
    class Meta:
        ordering = ['-created_at']
        
    def get_absolute_url(self):
        return reverse('posts:detail', kwargs={'pk': self.pk})
    
    def calculate_engagement_score(self):
        """Calculate engagement score for recommendation algorithm"""
        # Simple formula: (likes + comments*2 + saves*3) / views if views > 0 else 0
        if self.views_count > 0:
            self.engagement_score = (self.likes_count + self.comments_count*2 + self.saves_count*3) / self.views_count
        else:
            self.engagement_score = 0
        self.save(update_fields=['engagement_score'])
        
    def __str__(self):
        return f"Post by {self.user.username} on {self.created_at.strftime('%Y-%m-%d')}"


class Media(models.Model):
    """
    Model for media files associated with posts (for carousel posts)
    """
    MEDIA_TYPES = (
        ('image', 'Image'),
        ('video', 'Video'),
    )
    
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='media_files')
    file = models.FileField(upload_to='uploads/posts/')
    media_type = models.CharField(max_length=5, choices=MEDIA_TYPES)
    order = models.PositiveSmallIntegerField(default=0)  # For ordering in carousel
    
    class Meta:
        ordering = ['order']
        
    def __str__(self):
        return f"Media {self.id} for post {self.post.id}"


class Like(models.Model):
    """
    Model for post likes
    """
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'post')
        
    def __str__(self):
        return f"{self.user.username} likes post {self.post.id}"


class Comment(models.Model):
    """
    Model for post comments
    """
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='comments')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    text = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Engagement metrics
    likes_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['created_at']
        
    def __str__(self):
        return f"Comment by {self.user.username} on post {self.post.id}"


class CommentLike(models.Model):
    """
    Model for comment likes
    """
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='comment_likes')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'comment')
        
    def __str__(self):
        return f"{self.user.username} likes comment {self.comment.id}"


class SavedPost(models.Model):
    """
    Model for saved posts
    """
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='saved_posts')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='saved_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'post')
        
    def __str__(self):
        return f"{self.user.username} saved post {self.post.id}"


class PostTag(models.Model):
    """
    Model for user tags in posts
    """
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='user_tags')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='tagged_in')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('post', 'user')
        
    def __str__(self):
        return f"{self.user.username} tagged in post {self.post.id}"
