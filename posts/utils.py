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

def process_post_text(post):
    """
    Process post caption to extract hashtags and mentions
    """
    from .models import PostTag
    
    # Extract hashtags
    hashtags = extract_hashtags(post.caption)
    if hashtags:
        from search.models import Hashtag
        for tag_name in hashtags:
            tag, created = Hashtag.objects.get_or_create(name=tag_name.lower())
            if created:
                tag.post_count = 1
                tag.save()
            else:
                tag.post_count = F('post_count') + 1
                tag.save()
            
            # Associate hashtag with post
            post.hashtags.add(tag)
    
    # Extract mentions
    mentions = extract_mentions(post.caption)
    if mentions:
        for username in mentions:
            try:
                mentioned_user = User.objects.get(username=username)
                # Create user tag
                PostTag.objects.get_or_create(post=post, user=mentioned_user)
                
                # Create notification
                from notifications.utils import create_notification
                if mentioned_user != post.user:
                    create_notification(
                        recipient=mentioned_user,
                        sender=post.user,
                        notification_type='mention',
                        text=f"{post.user.username} mentioned you in a post",
                        content_id=str(post.id)
                    )
            except User.DoesNotExist:
                pass

def get_trending_posts(days=7, limit=20):
    """
    Get trending posts based on engagement score
    """
    from .models import Post
    from django.utils import timezone
    import datetime
    
    # Get posts from the last X days
    start_date = timezone.now() - datetime.timedelta(days=days)
    
    trending_posts = Post.objects.filter(
        created_at__gte=start_date,
        is_archived=False,
        is_hidden=False
    ).order_by('-engagement_score', '-created_at')[:limit]
    
    return trending_posts

def get_recommended_posts_for_user(user, limit=20):
    """
    Get recommended posts for a user based on their interests and activity
    """
    from .models import Post, Like, SavedPost
    from django.db.models import Count, Q
    
    # Get users that the current user follows
    following = user.following.values_list('following', flat=True)
    
    # Get posts the user has interacted with
    liked_posts = Like.objects.filter(user=user).values_list('post', flat=True)
    saved_posts = SavedPost.objects.filter(user=user).values_list('post', flat=True)
    
    # Get posts from users that are followed by users the current user follows
    # (friends of friends)
    friends_of_friends = User.objects.filter(
        followers__follower__in=following
    ).exclude(
        id__in=following
    ).exclude(
        id=user.id
    ).values_list('id', flat=True)
    
    # Get posts with hashtags the user has interacted with
    hashtags_of_interest = Post.objects.filter(
        id__in=liked_posts
    ).values_list('hashtags__name', flat=True).distinct()
    
    # Get recommended posts
    recommended_posts = Post.objects.filter(
        Q(user__in=friends_of_friends) |  # Posts from friends of friends
        Q(hashtags__name__in=hashtags_of_interest)  # Posts with hashtags of interest
    ).exclude(
        Q(user=user) |  # Exclude own posts
        Q(id__in=liked_posts) |  # Exclude already liked posts
        Q(id__in=saved_posts)  # Exclude already saved posts
    ).filter(
        is_archived=False,
        is_hidden=False
    ).annotate(
        interaction_count=Count('likes') + Count('comments')*2 + Count('saved_by')*3
    ).order_by('-interaction_count', '-created_at')[:limit]
    
    return recommended_posts
