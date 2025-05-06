from .models import Notification

def notifications(request):
    """
    Context processor to add notification data to all templates
    """
    context = {}
    
    if request.user.is_authenticated:
        # Add unread notification count
        context['unread_notifications_count'] = getattr(
            request, 'unread_notifications_count', 
            Notification.objects.filter(recipient=request.user, is_read=False).count()
        )
        
        # Add recent notifications
        context['recent_notifications'] = Notification.objects.filter(
            recipient=request.user
        ).order_by('-created_at')[:5]
    
    return context
