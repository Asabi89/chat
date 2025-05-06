import re
from django.utils import timezone
from django.db.models import F, Count, Q
import datetime

def extract_hashtags(text):
    """
    Extract hashtags from text
    Returns a list of hashtags without the # symbol
    """
    hashtag_pattern = r'#(\w+)'
    return re.findall(hashtag_pattern, text)

def process_hashtags(text, content_obj, content_type):
    """
    Process text to extract and save hashtags
    content_type should be 'post' or 'reel'
    """
    from .models import Hashtag, PostHashtag, ReelHashtag
    
    # Extract hashtags
    hashtags = extract_hashtags(text)
    
    if not hashtags:
        return
    
    for tag_name in hashtags:
        # Get or create hashtag
        tag, created = Hashtag.objects.get_or_create(name=tag_name.lower())
        
        # Increment post count
        tag.post_count = F('post_count') + 1
        tag.save()
        
        # Associate hashtag with content
        if content_type == 'post':
            PostHashtag.objects.get_or_create(post=content_obj, hashtag=tag)
            
            # Update trending data
            update_trending_hashtag(tag)
        elif content_type == 'reel':
            ReelHashtag.objects.get_or_create(reel=content_obj, hashtag=tag)
            
            # Update trending data
            update_trending_hashtag(tag)

def update_trending_hashtag(hashtag):
    """
    Update trending hashtag data
    """
    from .models import TrendingHashtag, PostHashtag, ReelHashtag
    
    # Get today's date
    today = timezone.now().date()
    
    # Get or create trending record
    trending, created = TrendingHashtag.objects.get_or_create(
        hashtag=hashtag,
        date=today
    )
    
    # Get 24h post count
    yesterday = timezone.now() - datetime.timedelta(days=1)
    
    post_count = PostHashtag.objects.filter(
        hashtag=hashtag,
        created_at__gte=yesterday
    ).count()
    
    reel_count = ReelHashtag.objects.filter(
        hashtag=hashtag,
        created_at__gte=yesterday
    ).count()
    
    # Update trending record
    trending.post_count_24h = post_count + reel_count
    
    # Calculate engagement score
    # Formula: post_count_24h * 1.0 + view_count_24h * 0.1
    trending.engagement_score = (post_count + reel_count) * 1.0 + trending.view_count_24h * 0.1
    
    trending.save()

def get_trending_hashtags(limit=10):
    """
    Get trending hashtags
    """
    from .models import TrendingHashtag
    
    # Get today's date
    today = timezone.now().date()
    
    # Get trending hashtags
    trending = TrendingHashtag.objects.filter(
        date=today
    ).select_related('hashtag').order_by('-engagement_score')[:limit]
    
    return trending

def get_related_hashtags(hashtag, limit=10):
    """
    Get related hashtags based on co-occurrence in posts
    """
    from .models import Hashtag, PostHashtag
    
    # Get posts with this hashtag
    posts_with_hashtag = PostHashtag.objects.filter(
        hashtag=hashtag
    ).values_list('post', flat=True)
    
    # Get other hashtags used in these posts
    related_hashtags = PostHashtag.objects.filter(
        post__in=posts_with_hashtag
    ).exclude(
        hashtag=hashtag
    ).values('hashtag').annotate(
        count=Count('hashtag')
    ).order_by('-count')[:limit]
    
    # Get the actual hashtag objects
    hashtag_ids = [item['hashtag'] for item in related_hashtags]
    return Hashtag.objects.filter(id__in=hashtag_ids)
