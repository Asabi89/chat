from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import User, Profile, Follow

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create a profile when a new user is created
    """
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save the profile when the user is saved
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()

@receiver(post_save, sender=Follow)
def update_follow_counts_on_create(sender, instance, created, **kwargs):
    """
    Update follower and following counts when a follow relationship is created
    """
    if created:
        # Update follower count for the user being followed
        following_profile = instance.following.profile
        following_profile.followers_count = Follow.objects.filter(following=instance.following).count()
        following_profile.save()
        
        # Update following count for the follower
        follower_profile = instance.follower.profile
        follower_profile.following_count = Follow.objects.filter(follower=instance.follower).count()
        follower_profile.save()

@receiver(post_delete, sender=Follow)
def update_follow_counts_on_delete(sender, instance, **kwargs):
    """
    Update follower and following counts when a follow relationship is deleted
    """
    # Update follower count for the user being followed
    following_profile = instance.following.profile
    following_profile.followers_count = Follow.objects.filter(following=instance.following).count()
    following_profile.save()
    
    # Update following count for the follower
    follower_profile = instance.follower.profile
    follower_profile.following_count = Follow.objects.filter(follower=instance.follower).count()
    follower_profile.save()
