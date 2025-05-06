# This file would be used with Celery or another task queue
# for handling asynchronous notification processing

from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

from .models import Notification, NotificationSetting
from .utils import create_notification, bulk_create_notifications

@shared_task
def send_notification_email_task(notification_id):
    """
    Task to send an email notification asynchronously
    """
    try:
        notification = Notification.objects.get(id=notification_id)
        
        # Check if email notifications are enabled for this type
        try:
            notification_settings = notification.recipient.notification_settings
            should_send_email = False
            
            if notification.notification_type == 'like' and notification_settings.email_likes:
                should_send_email = True
            elif notification.notification_type == 'comment' and notification_settings.email_comments:
                should_send_email = True
            elif notification.notification_type in ['follow', 'follow_request'] and notification_settings.email_follows:
                should_send_email = True
            elif notification.notification_type == 'message' and notification_settings.email_messages:
                should_send_email = True
            elif notification.notification_type == 'system' and notification_settings.email_system:
                should_send_email = True
            
            if should_send_email:
                # Prepare email content
                subject = f'NoChat: New {notification.get_notification_type_display()}'
                
                context = {
                    'recipient': notification.recipient,
                    'notification': notification,
                    'sender': notification.sender,
                    'site_url': settings.SITE_URL,
                }
                
                html_message = render_to_string('notifications/email/notification_email.html', context)
                plain_message = render_to_string('notifications/email/notification_email.txt', context)
                
                # Send email
                send_mail(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [notification.recipient.email],
                    html_message=html_message,
                    fail_silently=True,
                )
                
        except NotificationSetting.DoesNotExist:
            # No settings, don't send email
            pass
            
    except Notification.DoesNotExist:
        # Notification doesn't exist, nothing to do
        pass

@shared_task
def clean_old_notifications_task():
    """
    Task to clean up old read notifications
    """
    from django.utils import timezone
    import datetime
    
    # Delete read notifications older than 90 days
    cutoff_date = timezone.now() - datetime.timedelta(days=90)
    Notification.objects.filter(is_read=True, created_at__lt=cutoff_date).delete()

@shared_task
def create_bulk_notifications_task(recipient_ids, notification_type, text, sender_id=None, content_id=''):
    """
    Task to create notifications for multiple recipients asynchronously
    """
    from accounts.models import User
    
    # Get recipients
    recipients = User.objects.filter(id__in=recipient_ids)
    
    # Get sender if provided
    sender = None
    if sender_id:
        try:
            sender = User.objects.get(id=sender_id)
        except User.DoesNotExist:
            pass
    
    # Create notifications
    bulk_create_notifications(recipients, notification_type, text, sender, content_id)
