from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from .models import Notification

class NotificationMiddleware(MiddlewareMixin):
    """
    Middleware to add unread notification count to request
    """
    def process_request(self, request):
        if request.user.is_authenticated:
            # Add unread notification count to request
            request.unread_notifications_count = Notification.objects.filter(
                recipient=request.user,
                is_read=False
            ).count()
