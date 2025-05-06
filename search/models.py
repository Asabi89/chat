from django.db import models
from accounts.models import User

class Hashtag(models.Model):
    """
    Model for hashtags
    """
    name = models.CharField(max_length=100, unique=True)
    post_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-post_count']
    
    def __str__(self):
        return f"#{self.name}"


class PostHashtag(models.Model):
    """
    Model to associate hashtags with posts
    """
    post = models.ForeignKey('posts.Post', on_delete=models.CASCADE, related_name='hashtags')
    hashtag = models.ForeignKey(Hashtag, on_delete=models.CASCADE, related_name='posts')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('post', 'hashtag')
    
    def __str__(self):
        return f"#{self.hashtag.name} on post {self.post.id}"


class ReelHashtag(models.Model):
    """
    Model to associate hashtags with reels
    """
    reel = models.ForeignKey('reels.Reel', on_delete=models.CASCADE, related_name='hashtags')
    hashtag = models.ForeignKey(Hashtag, on_delete=models.CASCADE, related_name='reels')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('reel', 'hashtag')
    
    def __str__(self):
        return f"#{self.hashtag.name} on reel {self.reel.id}"


class SearchHistory(models.Model):
    """
    Model to track user search history
    """
    SEARCH_TYPES = (
        ('user', 'User'),
        ('hashtag', 'Hashtag'),
        ('location', 'Location'),
        ('general', 'General'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_history')
    query = models.CharField(max_length=255)
    search_type = models.CharField(max_length=10, choices=SEARCH_TYPES, default='general')
    result_id = models.CharField(max_length=100, blank=True)  # ID of the selected result if any
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Search histories'
    
    def __str__(self):
        return f"{self.user.username} searched for '{self.query}'"


class TrendingHashtag(models.Model):
    """
    Model for trending hashtags
    """
    hashtag = models.ForeignKey(Hashtag, on_delete=models.CASCADE, related_name='trending_records')
    post_count_24h = models.PositiveIntegerField(default=0)
    view_count_24h = models.PositiveIntegerField(default=0)
    engagement_score = models.FloatField(default=0.0)
    date = models.DateField(auto_now_add=True)
    
    class Meta:
        ordering = ['-engagement_score']
        unique_together = ('hashtag', 'date')
    
    def __str__(self):
        return f"Trending: #{self.hashtag.name} on {self.date}"
