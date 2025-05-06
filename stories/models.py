from django.db import models
from django.urls import reverse
from accounts.models import User
import uuid

class Story(models.Model):
    """
    Model for user stories (24-hour content)
    """
    STORY_TYPES = (
        ('image', 'Image'),
        ('video', 'Video'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories')
    file = models.FileField(upload_to='uploads/stories/')
    story_type = models.CharField(max_length=5, choices=STORY_TYPES)
    caption = models.TextField(blank=True, max_length=500)
    location = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # 24 hours after creation
    
    # For music/audio
    music_track = models.CharField(max_length=255, blank=True)
    music_artist = models.CharField(max_length=255, blank=True)
    
    # Engagement metrics
    views_count = models.PositiveIntegerField(default=0)
    
    # Moderation
    is_hidden = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Stories'
        
    def get_absolute_url(self):
        return reverse('stories:view', kwargs={'pk': self.pk})
    
    def __str__(self):
        return f"Story by {self.user.username} on {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class StoryView(models.Model):
    """
    Model to track who viewed a story
    """
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='viewed_stories')
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('story', 'user')
        
    def __str__(self):
        return f"{self.user.username} viewed story {self.story.id}"


class StoryReaction(models.Model):
    """
    Model for reactions to stories
    """
    REACTION_TYPES = (
        ('like', '❤️'),
        ('laugh', '😂'),
        ('wow', '😮'),
        ('sad', '😢'),
        ('custom', 'Custom'),
    )
    
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='story_reactions')
    reaction_type = models.CharField(max_length=10, choices=REACTION_TYPES)
    custom_message = models.CharField(max_length=100, blank=True)  # For custom reactions
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} reacted to story {self.story.id} with {self.get_reaction_type_display()}"


class StoryHighlight(models.Model):
    """
    Model for story highlights (collections of past stories)
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='highlights')
    title = models.CharField(max_length=50)
    cover_image = models.ImageField(upload_to='uploads/highlights/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Highlight '{self.title}' by {self.user.username}"


class HighlightStory(models.Model):
    """
    Model to associate stories with highlights
    """
    highlight = models.ForeignKey(StoryHighlight, on_delete=models.CASCADE, related_name='stories')
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='in_highlights')
    order = models.PositiveSmallIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
        unique_together = ('highlight', 'story')
        
    def __str__(self):
        return f"Story {self.story.id} in highlight '{self.highlight.title}'"
