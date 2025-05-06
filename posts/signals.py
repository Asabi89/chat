from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Post, Like, Comment, SavedPost
from .utils import process_post_text

@receiver(post_save, sender=Post)
def post_created_or_updated(sender, instance, created, **kwargs):
    """
    Signal handler for when a post is created or updated
    """
    if created:
        # Process post text for hashtags and mentions
        process_post_text(instance)
        
        # Update user's post count
        profile = instance.user.profile
        profile.posts_count += 1
        profile.save(update_fields=['posts_count'])

@receiver(post_delete, sender=Post)
def post_deleted(sender, instance, **kwargs):
    """
    Signal handler for when a post is deleted
    """
    # Update user's post count
    profile = instance.user.profile
    profile.posts_count = max(0, profile.posts_count - 1)  # Ensure it doesn't go below 0
    profile.save(update_fields=['posts_count'])

@receiver(post_save, sender=Like)
def like_created(sender, instance, created, **kwargs):
    """
    Signal handler for when a like is created
    """
    if created:
        # Update post's engagement score
        instance.post.calculate_engagement_score()

@receiver(post_delete, sender=Like)
def like_deleted(sender, instance, **kwargs):
    """
    Signal handler for when a like is deleted
    """
    # Update post's engagement score
    instance.post.calculate_engagement_score()

@receiver(post_save, sender=Comment)
def comment_created(sender, instance, created, **kwargs):
    """
    Signal handler for when a comment is created
    """
    if created:
        # Update post's engagement score
        instance.post.calculate_engagement_score()

@receiver(post_delete, sender=Comment)
def comment_deleted(sender, instance, **kwargs):
    """
    Signal handler for when a comment is deleted
    """
    # Update post's engagement score
    instance.post.calculate_engagement_score()

@receiver(post_save, sender=SavedPost)
def saved_post_created(sender, instance, created, **kwargs):
    """
    Signal handler for when a post is saved
    """
    if created:
        # Update post's engagement score
        instance.post.calculate_engagement_score()

@receiver(post_delete, sender=SavedPost)
def saved_post_deleted(sender, instance, **kwargs):
    """
    Signal handler for when a saved post is deleted
    """
    # Update post's engagement score
    instance.post.calculate_engagement_score()
