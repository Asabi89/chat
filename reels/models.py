from django.db import models
from django.urls import reverse
from accounts.models import User
import uuid

class Reel(models.Model):
    """
    Model for short-form video content (Reels)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reels')
    video = models.FileField(upload_to='uploads/reels/')
    thumbnail = models.ImageField(upload_to='uploads/reels/thumbnails/', blank=True)
    caption = models.TextField(blank=True, max_length=2200)
    
    # For music/audio
    audio_track = models.CharField(max_length=255, blank=True)
    audio_artist = models.CharField(max_length=255, blank=True)
    
    # Metadata
    duration = models.PositiveIntegerField(default=0)  # in seconds
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Engagement metrics
    views_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    shares_count = models.PositiveIntegerField(default=0)
    
    # For algorithm
    engagement_score = models.FloatField(default=0.0)
    
    # Moderation
    is_archived = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        
    def get_absolute_url(self):
        return reverse('reels:detail', kwargs={'pk': self.pk})
    
    def calculate_engagement_score(self):
        """Calculate engagement score for recommendation algorithm"""
        # Formula: (likes + comments*2 + shares*3) / views if views > 0 else 0
        if self.views_count > 0:
            self.engagement_score = (self.likes_count + self.comments_count*2 + self.shares_count*3) / self.views_count
        else:
            self.engagement_score = 0
        self.save(update_fields=['engagement_score'])
        
    def __str__(self):
        return f"Reel by {self.user.username} on {self.created_at.strftime('%Y-%m-%d')}"


class ReelLike(models.Model):
    """
    Model for reel likes
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reel_likes')
    reel = models.ForeignKey(Reel, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'reel')
        
    def __str__(self):
        return f"{self.user.username} likes reel {self.reel.id}"


class ReelComment(models.Model):
    """
    Model for reel comments
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reel_comments')
    reel = models.ForeignKey(Reel, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    text = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Engagement metrics
    likes_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['created_at']
        
    def __str__(self):
        return f"Comment by {self.user.username} on reel {self.reel.id}"

class ReelCommentLike(models.Model):
    """
    Model for reel comment likes
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reel_comment_likes')
    comment = models.ForeignKey(ReelComment, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'comment')
        
    def __str__(self):
        return f"{self.user.username} likes comment {self.comment.id} on reel"


class SavedReel(models.Model):
    """
    Model for saved reels
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_reels')
    reel = models.ForeignKey(Reel, on_delete=models.CASCADE, related_name='saved_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'reel')
        
    def __str__(self):
        return f"{self.user.username} saved reel {self.reel.id}"
