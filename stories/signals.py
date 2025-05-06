from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
import datetime

from .models import Story, StoryView

@receiver(pre_save, sender=Story)
def set_story_expiration(sender, instance, **kwargs):
    """
    Set story expiration time if not already set
    """
    if not instance.expires_at:
        instance.expires_at = timezone.now() + datetime.timedelta(hours=24)

@receiver(post_save, sender=StoryView)
def update_story_view_count(sender, instance, created, **kwargs):
    """
    Update story view count when a new view is recorded
    """
    if created:
        story = instance.story
        story.views_count = StoryView.objects.filter(story=story).count()
        story.save(update_fields=['views_count'])
