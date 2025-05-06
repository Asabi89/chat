from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Message, MessageRead, Conversation
from django.utils import timezone

@receiver(post_save, sender=Message)
def update_conversation_timestamp(sender, instance, created, **kwargs):
    """
    Update the conversation's updated_at timestamp when a new message is created
    """
    if created:
        conversation = instance.conversation
        conversation.updated_at = timezone.now()
        conversation.save(update_fields=['updated_at'])

@receiver(post_save, sender=MessageRead)
def notify_message_read(sender, instance, created, **kwargs):
    """
    Notify when a message is read
    This is a placeholder for potential real-time notifications
    """
    if created:
        # In a real implementation, you might want to send a notification
        # to the message sender that their message has been read
        pass
