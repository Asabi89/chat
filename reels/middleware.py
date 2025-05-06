from django.utils import timezone
from .models import Reel
import datetime

class ReelViewTrackingMiddleware:
    """
    Middleware to track reel views
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Check if this is a reel detail view
        if request.path.startswith('/reels/') and request.user.is_authenticated:
            path_parts = request.path.split('/')
            if len(path_parts) >= 3 and path_parts[2]:
                try:
                    # Try to get reel ID from path
                    reel_id = path_parts[2]
                    
                    # Store view in session to prevent duplicate counts
                    session_key = f'viewed_reel_{reel_id}'
                    if not request.session.get(session_key):
                        try:
                            reel = Reel.objects.get(pk=reel_id)
                            
                            # Don't count views from the reel owner
                            if request.user != reel.user:
                                # Set session flag to prevent duplicate counts
                                request.session[session_key] = True
                                request.session.set_expiry(3600)  # Expire after 1 hour
                        except Reel.DoesNotExist:
                            pass
                except:
                    pass
        
        return response
