from django.db import models
from accounts.models import User

class Report(models.Model):
    """
    Model for user reports on content
    """
    REPORT_TYPES = (
        ('spam', 'Spam'),
        ('nudity', 'Nudity or sexual activity'),
        ('hate_speech', 'Hate speech or symbols'),
        ('violence', 'Violence or dangerous organizations'),
        ('illegal', 'Sale of illegal goods'),
        ('bullying', 'Bullying or harassment'),
        ('intellectual_property', 'Intellectual property violation'),
        ('suicide', 'Suicide or self-injury'),
        ('eating_disorders', 'Eating disorders'),
        ('scam', 'Scam or fraud'),
        ('false_information', 'False information'),
        ('other', 'Other'),
    )
    
    CONTENT_TYPES = (
        ('post', 'Post'),
        ('comment', 'Comment'),
        ('story', 'Story'),
        ('reel', 'Reel'),
        ('message', 'Message'),
        ('user', 'User Profile'),
    )
    
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPES)
    content_id = models.CharField(max_length=100)
    report_type = models.CharField(max_length=30, choices=REPORT_TYPES)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_reviewed = models.BooleanField(default=False)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    action_taken = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return f"Report by {self.reporter.username} for {self.content_type} ({self.report_type})"

class Activity(models.Model):
    """
    Model to track user activity for analytics
    """
    ACTIVITY_TYPES = (
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('post_create', 'Create Post'),
        ('post_view', 'View Post'),
        ('post_like', 'Like Post'),
        ('post_comment', 'Comment on Post'),
        ('post_share', 'Share Post'),
        ('story_create', 'Create Story'),
        ('story_view', 'View Story'),
        ('reel_create', 'Create Reel'),
        ('reel_view', 'View Reel'),
        ('profile_view', 'View Profile'),
        ('follow', 'Follow User'),
        ('unfollow', 'Unfollow User'),
        ('message_send', 'Send Message'),
        ('search', 'Search'),
        ('notification_click', 'Click Notification'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    content_id = models.CharField(max_length=100, blank=True)  # ID of related content if applicable
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Activities'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()} at {self.created_at}"


class Feedback(models.Model):
    """
    Model for user feedback and bug reports
    """
    FEEDBACK_TYPES = (
        ('bug', 'Bug Report'),
        ('feature', 'Feature Request'),
        ('content', 'Content Issue'),
        ('account', 'Account Issue'),
        ('other', 'Other'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedback')
    feedback_type = models.CharField(max_length=10, choices=FEEDBACK_TYPES)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    screenshot = models.ImageField(upload_to='uploads/feedback/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    response = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.get_feedback_type_display()} from {self.user.username}: {self.subject}"


class AppSetting(models.Model):
    """
    Model for application-wide settings
    """
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)  # Whether this setting is visible to regular users
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.key
