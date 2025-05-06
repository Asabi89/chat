import re
from django.db.models import F
from accounts.models import User

def extract_hashtags(text):
    """
    Extract hashtags from text
    Returns a list of hashtags without the # symbol
    """
    hashtag_pattern = r'#(\w+)'
    return re.findall(hashtag_pattern, text)

def extract_mentions(text):
    """
    Extract mentions from text
    Returns a list of usernames without the @ symbol
    """
    mention_pattern = r'@(\w+)'
    return re.findall(mention_pattern, text)

def process_reel_caption(reel):
    """
    Process reel caption to extract hashtags and mentions
    """
    # Extract hashtags
    hashtags = extract_hashtags(reel.caption)
    if hashtags:
        from search.models import Hashtag
        for tag_name in hashtags:
            tag, created = Hashtag.objects.get_or_create(name=tag_name.lower())
            if created:
                tag.reel_count = 1
                tag.save()
            else:
                tag.reel_count = F('reel_count') + 1
                tag.save()
    
    # Extract mentions
    mentions = extract_mentions(reel.caption)
    if mentions:
        for username in mentions:
            try:
                mentioned_user = User.objects.get(username=username)
                
                # Create notification
                from notifications.utils import create_notification
                if mentioned_user != reel.user:
                    create_notification(
                        recipient=mentioned_user,
                        sender=reel.user,
                        notification_type='mention',
                        text=f"{reel.user.username} mentioned you in a reel",
                        content_id=str(reel.id)
                    )
            except User.DoesNotExist:
                pass

def get_trending_reels(days=7, limit=20):
    """
    Get trending reels based on engagement score
    """
    from .models import Reel
    from django.utils import timezone
    import datetime
    
    # Get reels from the last X days
    start_date = timezone.now() - datetime.timedelta(days=days)
    
    trending_reels = Reel.objects.filter(
        created_at__gte=start_date,
        is_archived=False,
        is_hidden=False
    ).order_by('-engagement_score', '-created_at')[:limit]
    
    return trending_reels

def get_recommended_reels_for_user(user, limit=20):
    """
    Get recommended reels for a user based on their interests and activity
    """
    from .models import Reel, ReelLike, SavedReel
    from django.db.models import Count, Q
    
    # Get users that the current user follows
    following = user.following.values_list('following', flat=True)
    
    # Get reels the user has interacted with
    liked_reels = ReelLike.objects.filter(user=user).values_list('reel', flat=True)
    saved_reels = SavedReel.objects.filter(user=user).values_list('reel', flat=True)
    
    # Get reels from users that are followed by users the current user follows
    # (friends of friends)
    friends_of_friends = User.objects.filter(
        followers__follower__in=following
    ).exclude(
        id__in=following
    ).exclude(
        id=user.id
    ).values_list('id', flat=True)
    
    # Get recommended reels
    recommended_reels = Reel.objects.filter(
        Q(user__in=friends_of_friends) |  # Reels from friends of friends
        Q(audio_track__in=Reel.objects.filter(id__in=liked_reels).values_list('audio_track', flat=True).distinct())  # Reels with same audio
    ).exclude(
        Q(user=user) |  # Exclude own reels
        Q(id__in=liked_reels) |  # Exclude already liked reels
        Q(id__in=saved_reels)  # Exclude already saved reels
    ).filter(
        is_archived=False,
        is_hidden=False
    ).annotate(
        interaction_count=Count('likes') + Count('comments')*2 + Count('saved_by')*3
    ).order_by('-interaction_count', '-created_at')[:limit]
    
    return recommended_reels
