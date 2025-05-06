from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from posts.models import Post
from reels.models import Reel
from .utils import process_hashtags, update_trending_hashtag
from .models import PostHashtag, ReelHashtag, Hashtag

@receiver(post_save, sender=Post)
def post_created_or_updated(sender, instance, created, **kwargs):
    """
    Signal handler for when a post is created or updated
    """
    # Process hashtags in caption
    process_hashtags(instance.caption, instance, 'post')

@receiver(post_save, sender=Reel)
def reel_created_or_updated(sender, instance, created, **kwargs):
    """
    Signal handler for when a reel is created or updated
    """
    # Process hashtags in caption
    process_hashtags(instance.caption, instance, 'reel')

@receiver(post_delete, sender=PostHashtag)
def post_hashtag_deleted(sender, instance, **kwargs):
    """
    Signal handler for when a post hashtag is deleted
    """
    # Decrement post count for hashtag
    hashtag = instance.hashtag
    hashtag.post_count = max(0, hashtag.post_count - 1)
    hashtag.save()
    
    # Update trending data
    update_trending_hashtag(hashtag)

@receiver(post_delete, sender=ReelHashtag)
def reel_hashtag_deleted(sender, instance, **kwargs):
    """
    Signal handler for when a reel hashtag is deleted
    """
    # Decrement post count for hashtag
    hashtag = instance.hashtag
    hashtag.post_count = max(0, hashtag.post_count - 1)
    hashtag.save()
    
    # Update trending data
    update_trending_hashtag(hashtag)
