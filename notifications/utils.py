from django.db.models import Q
from .models import Notification, NotificationSetting

def create_notification(recipient, notification_type, text, sender=None, content_id=''):
    """
    Utility function to create a notification with checks for user preferences
    
    Args:
        recipient: User object who will receive the notification
        notification_type: Type of notification (from NOTIFICATION_TYPES)
        text: Text content of the notification
        sender: User object who triggered the notification (optional)
        content_id: ID of related content (post, comment, etc.) (optional)
    
    Returns:
        Notification object if created, None otherwise
    """
    # Don't send notifications to yourself
    if sender and sender == recipient:
        return None
    
    # Check if user has enabled this type of notification
    try:
        settings = recipient.notification_settings
        
        # Check notification preferences based on type
        if notification_type == 'like' and not settings.likes:
            return None
        elif notification_type == 'comment' and not settings.comments:
            return None
        elif notification_type == 'comment_like' and not settings.comment_likes:
            return None
        elif notification_type == 'follow' and not settings.follows:
            return None
        elif notification_type == 'follow_request' and not settings.follow_requests:
            return None
        elif notification_type == 'message' and not settings.messages:
            return None
        elif notification_type == 'mention' and not settings.mentions:
            return None
        elif notification_type == 'tag' and not settings.tags:
            return None
        elif notification_type == 'story_view' and not settings.story_views:
            return None
        elif notification_type == 'story_reaction' and not settings.story_reactions:
            return None
        elif notification_type == 'post_share' and not settings.post_shares:
            return None
        
    except NotificationSetting.DoesNotExist:
        # If settings don't exist, create with defaults
        NotificationSetting.objects.create(user=recipient)
    
    # Create the notification
    notification = Notification.objects.create(
        recipient=recipient,
        sender=sender,
        notification_type=notification_type,
        text=text,
        content_id=content_id
    )
    
    # In a real app, you might want to send a real-time notification here
    # using channels or another mechanism
    
    return notification

def get_notification_url(notification):
    """
    Generate the appropriate URL for a notification based on its type and content
    
    Args:
        notification: Notification object
    
    Returns:
        URL string for the notification
    """
    notification_type = notification.notification_type
    content_id = notification.content_id
    
    if notification_type in ['like', 'comment', 'comment_like', 'post_share']:
        # Post-related notifications
        return f'/posts/{content_id}/'
    
    elif notification_type in ['follow', 'follow_request']:
        # User profile notifications
        if notification.sender:
            return f'/accounts/profile/{notification.sender.username}/'
        return '/'
    
    elif notification_type == 'message':
        # Message notifications
        return f'/messaging/conversation/{content_id}/'
    
    elif notification_type in ['mention', 'tag']:
        # Could be post or comment
        if '/' in content_id:
            parts = content_id.split('/')
            if parts[0] == 'post':
                return f'/posts/{parts[1]}/'
            elif parts[0] == 'comment':
                return f'/posts/{parts[1]}/#comment-{parts[2]}'
        return '/'
    
    elif notification_type in ['story_view', 'story_reaction']:
        # Story notifications
        return f'/stories/{content_id}/'
    
    elif notification_type == 'reel_like' or notification_type == 'reel_comment':
        # Reel notifications
        return f'/reels/{content_id}/'
    
    # Default for system notifications
    return '/'

def bulk_create_notifications(recipients, notification_type, text, sender=None, content_id=''):
    """
    Create notifications for multiple recipients efficiently
    
    Args:
        recipients: QuerySet or list of User objects
        notification_type: Type of notification
        text: Text content of the notification
        sender: User who triggered the notification (optional)
        content_id: ID of related content (optional)
    
    Returns:
        List of created Notification objects
    """
    # Filter recipients based on their notification settings
    if notification_type == 'like':
        recipients = recipients.filter(notification_settings__likes=True)
    elif notification_type == 'comment':
        recipients = recipients.filter(notification_settings__comments=True)
    elif notification_type == 'comment_like':
        recipients = recipients.filter(notification_settings__comment_likes=True)
    elif notification_type == 'follow':
        recipients = recipients.filter(notification_settings__follows=True)
    elif notification_type == 'follow_request':
        recipients = recipients.filter(notification_settings__follow_requests=True)
    elif notification_type == 'message':
        recipients = recipients.filter(notification_settings__messages=True)
    elif notification_type == 'mention':
        recipients = recipients.filter(notification_settings__mentions=True)
    elif notification_type == 'tag':
        recipients = recipients.filter(notification_settings__tags=True)
    elif notification_type == 'story_view':
        recipients = recipients.filter(notification_settings__story_views=True)
    elif notification_type == 'story_reaction':
        recipients = recipients.filter(notification_settings__story_reactions=True)
    elif notification_type == 'post_share':
        recipients = recipients.filter(notification_settings__post_shares=True)
    
    # Don't send notifications to the sender
    if sender:
        recipients = recipients.exclude(id=sender.id)
    
    # Create notifications in bulk
    notifications = [
        Notification(
            recipient=recipient,
            sender=sender,
            notification_type=notification_type,
            text=text,
            content_id=content_id
        )
        for recipient in recipients
    ]
    
    if notifications:
        return Notification.objects.bulk_create(notifications)
    
    return []
