from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

from .models import Notification, NotificationSetting
from accounts.models import User, Follow

@receiver(post_save, sender=Notification)
def send_notification_email(sender, instance, created, **kwargs):
    """
    Send email notification if user has enabled email notifications for this type
    """
    if not created:
        return
    
    # Get notification settings for the recipient
    try:
        notification_settings = instance.recipient.notification_settings
    except NotificationSetting.DoesNotExist:
        # Create default settings if they don't exist
        notification_settings = NotificationSetting.objects.create(user=instance.recipient)
    
    # Check if email notifications are enabled for this type
    should_send_email = False
    
    if instance.notification_type == 'like' and notification_settings.email_likes:
        should_send_email = True
    elif instance.notification_type == 'comment' and notification_settings.email_comments:
        should_send_email = True
    elif instance.notification_type in ['follow', 'follow_request'] and notification_settings.email_follows:
        should_send_email = True
    elif instance.notification_type == 'message' and notification_settings.email_messages:
        should_send_email = True
    elif instance.notification_type == 'system' and notification_settings.email_system:
        should_send_email = True
    
    if should_send_email:
        # Prepare email content
        subject = f'NoChat: New {instance.get_notification_type_display()}'
        
        context = {
            'recipient': instance.recipient,
            'notification': instance,
            'sender': instance.sender,
            'site_url': settings.SITE_URL,
        }
        
        html_message = render_to_string('notifications/email/notification_email.html', context)
        plain_message = render_to_string('notifications/email/notification_email.txt', context)
        
        # Send email
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [instance.recipient.email],
            html_message=html_message,
            fail_silently=True,
        )

@receiver(post_save, sender=User)
def create_notification_settings(sender, instance, created, **kwargs):
    """
    Create notification settings for new users
    """
    if created:
        NotificationSetting.objects.create(user=instance)

# Example signal handlers for creating notifications

@receiver(post_save, sender=Follow)
def create_follow_notification(sender, instance, created, **kwargs):
    """
    Create a notification when a user follows another user
    """
    if created:
        # Create follow notification
        Notification.objects.create(
            recipient=instance.following,
            sender=instance.follower,
            notification_type='follow',
            text=f"{instance.follower.username} started following you"
        )
