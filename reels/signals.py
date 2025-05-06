from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Reel, ReelLike, ReelComment, SavedReel
from .utils import process_reel_caption

@receiver(post_save, sender=Reel)
def reel_created_or_updated(sender, instance, created, **kwargs):
    """
    Signal handler for when a reel is created or updated
    """
    if created:
        # Process reel caption for hashtags and mentions
        process_reel_caption(instance)

@receiver(post_save, sender=ReelLike)
def reel_like_created(sender, instance, created, **kwargs):
    """
    Signal handler for when a reel like is created
    """
    if created:
        # Update reel's engagement score
        instance.reel.calculate_engagement_score()

@receiver(post_delete, sender=ReelLike)
def reel_like_deleted(sender, instance, **kwargs):
    """
    Signal handler for when a reel like is deleted
    """
    # Update reel's engagement score
    instance.reel.calculate_engagement_score()

@receiver(post_save, sender=ReelComment)
def reel_comment_created(sender, instance, created, **kwargs):
    """
    Signal handler for when a reel comment is created
    """
    if created:
        # Update reel's engagement score
        instance.reel.calculate_engagement_score()

@receiver(post_delete, sender=ReelComment)
def reel_comment_deleted(sender, instance, **kwargs):
    """
    Signal handler for when a reel comment is deleted
    """
    # Update reel's engagement score
    instance.reel.calculate_engagement_score()

@receiver(post_save, sender=SavedReel)
def saved_reel_created(sender, instance, created, **kwargs):
    """
    Signal handler for when a reel is saved
    """
    if created:
        # Update reel's engagement score
        instance.reel.calculate_engagement_score()

@receiver(post_delete, sender=SavedReel)
def saved_reel_deleted(sender, instance, **kwargs):
    """
    Signal handler for when a saved reel is deleted
    """
    # Update reel's engagement score
    instance.reel.calculate_engagement_score()
