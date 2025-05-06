from django.db import models
from accounts.models import User
import uuid

class Notification(models.Model):
    """
    Model for user notifications
    """
    NOTIFICATION_TYPES = (
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('follow', 'Follow'),
        ('mention', 'Mention'),
        ('tag', 'Tag'),
        ('message', 'Message'),
        ('comment_like', 'Comment Like'),
        ('follow_request', 'Follow Request'),
        ('story_view', 'Story View'),
        ('story_reaction', 'Story Reaction'),
        ('post_share', 'Post Share'),
        ('reel_like', 'Reel Like'),
        ('reel_comment', 'Reel Comment'),
        ('system', 'System Notification'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications', null=True, blank=True)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    content_id = models.CharField(max_length=100, blank=True)  # ID of the related content (post, comment, etc.)
    text = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        if self.sender:
            return f"{self.notification_type} notification from {self.sender.username} to {self.recipient.username}"
        return f"{self.notification_type} notification to {self.recipient.username}"


class NotificationSetting(models.Model):
    """
    Model for user notification preferences
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_settings')
    
    # Push notifications
    likes = models.BooleanField(default=True)
    comments = models.BooleanField(default=True)
    comment_likes = models.BooleanField(default=True)
    follows = models.BooleanField(default=True)
    follow_requests = models.BooleanField(default=True)
    messages = models.BooleanField(default=True)
    mentions = models.BooleanField(default=True)
    tags = models.BooleanField(default=True)
    story_views = models.BooleanField(default=False)
    story_reactions = models.BooleanField(default=True)
    post_shares = models.BooleanField(default=True)
    
    # Email notifications
    email_likes = models.BooleanField(default=False)
    email_comments = models.BooleanField(default=False)
    email_follows = models.BooleanField(default=True)
    email_messages = models.BooleanField(default=False)
    email_system = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Notification settings for {self.user.username}"
