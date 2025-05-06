from django.utils import timezone
from .models import Hashtag, TrendingHashtag
import re

class HashtagViewTrackingMiddleware:
    """
    Middleware to track hashtag views
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Check if this is a hashtag view
        if request.path.startswith('/search/hashtag/') and request.user.is_authenticated:
            path_parts = request.path.split('/')
            if len(path_parts) >= 4 and path_parts[3]:
                try:
                    # Get hashtag name from URL
                    hashtag_name = path_parts[3]
                    
                    # Store view in session to prevent duplicate counts
                    session_key = f'viewed_hashtag_{hashtag_name}'
                    if not request.session.get(session_key):
                        try:
                            # Get hashtag
                            hashtag = Hashtag.objects.get(name=hashtag_name)
                            
                            # Update trending data
                            trending, created = TrendingHashtag.objects.get_or_create(
                                hashtag=hashtag,
                                date=timezone.now().date()
                            )
                            
                            # Increment view count
                            trending.view_count_24h += 1
                            
                            # Update engagement score
                            trending.engagement_score = (trending.post_count_24h * 1.0) + (trending.view_count_24h * 0.1)
                            
                            trending.save()
                            
                            # Set session flag to prevent duplicate counts
                            request.session[session_key] = True
                            request.session.set_expiry(3600)  # Expire after 1 hour
                        except Hashtag.DoesNotExist:
                            pass
                except:
                    pass
        
        return response
