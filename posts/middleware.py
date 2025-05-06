from django.utils import timezone
from accounts.models import Profile
import datetime

class UserActivityMiddleware:
    """
    Middleware to track user activity and update last_active timestamp
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Update last_active for authenticated users
        if request.user.is_authenticated:
            # Only update if it's been more than 5 minutes since last update
            # to avoid too many database writes
            now = timezone.now()
            try:
                profile = request.user.profile
                if not profile.last_active or (now - profile.last_active) > datetime.timedelta(minutes=5):
                    profile.last_active = now
                    profile.save(update_fields=['last_active'])
            except Profile.DoesNotExist:
                pass
        
        return response
