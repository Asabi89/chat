from django.db import models
from accounts.models import User
import uuid

class Conversation(models.Model):
    """
    Model for conversations between users
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_group_chat = models.BooleanField(default=False)
    group_name = models.CharField(max_length=100, blank=True)
    group_avatar = models.ImageField(upload_to='uploads/group_avatars/', blank=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def get_other_participant(self, user):
        """Get the other participant in a one-on-one conversation"""
        if not self.is_group_chat:
            return self.participants.exclude(id=user.id).first()
        return None
    
    def __str__(self):
        if self.is_group_chat and self.group_name:
            return f"Group: {self.group_name}"
        participants_str = ", ".join([user.username for user in self.participants.all()[:3]])
        if self.participants.count() > 3:
            participants_str += f" and {self.participants.count() - 3} more"
        return f"Conversation between {participants_str}"


class Message(models.Model):
    """
    Model for individual messages in a conversation
    """
    MESSAGE_TYPES = (
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('file', 'File'),
        ('location', 'Location'),
        ('post', 'Post Share'),
        ('reel', 'Reel Share'),
        ('story', 'Story Share'),
        ('profile', 'Profile Share'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    text = models.TextField(blank=True)
    file = models.FileField(upload_to='uploads/messages/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    # For sharing content
    shared_content_id = models.CharField(max_length=100, blank=True)
    
    # For location sharing
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        if self.message_type == 'text':
            preview = self.text[:30] + "..." if len(self.text) > 30 else self.text
            return f"Message from {self.sender.username}: {preview}"
        return f"{self.get_message_type_display()} from {self.sender.username}"


class MessageRead(models.Model):
    """
    Model to track when messages are read by participants
    """
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='read_by')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='read_messages')
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('message', 'user')
    
    def __str__(self):
        return f"Message {self.message.id} read by {self.user.username}"


class MessageReaction(models.Model):
    """
    Model for reactions to messages
    """
    REACTION_TYPES = (
        ('like', '👍'),
        ('love', '❤️'),
        ('laugh', '😂'),
        ('wow', '😮'),
        ('sad', '😢'),
        ('angry', '😡'),
    )
    
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='message_reactions')
    reaction_type = models.CharField(max_length=10, choices=REACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('message', 'user')
    
    def __str__(self):
        return f"{self.user.username} reacted to message with {self.get_reaction_type_display()}"
