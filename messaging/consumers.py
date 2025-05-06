import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Conversation, Message, MessageRead
from accounts.models import User

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        
        # Anonymous users can't connect
        if self.user.is_anonymous:
            await self.close()
            return
        
        # Get conversation ID from URL route
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.conversation_group_name = f'chat_{self.conversation_id}'
        
        # Check if user is a participant in this conversation
        is_participant = await self.is_conversation_participant()
        if not is_participant:
            await self.close()
            return
        
        # Join the conversation group
        await self.channel_layer.group_add(
            self.conversation_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send user online status to the group
        await self.channel_layer.group_send(
            self.conversation_group_name,
            {
                'type': 'user_online',
                'user_id': self.user.id,
                'username': self.user.username,
                'timestamp': timezone.now().isoformat(),
            }
        )
    
    async def disconnect(self, close_code):
        # Leave the conversation group
        if hasattr(self, 'conversation_group_name'):
            await self.channel_layer.group_discard(
                self.conversation_group_name,
                self.channel_name
            )
            
            # Send user offline status to the group
            await self.channel_layer.group_send(
                self.conversation_group_name,
                {
                    'type': 'user_offline',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'timestamp': timezone.now().isoformat(),
                }
            )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'message')
        
        if message_type == 'message':
            # Handle new message
            content = data.get('content', '').strip()
            message_format = data.get('format', 'text')
            
            if content or message_format != 'text':
                # Save message to database
                message = await self.save_message(content, message_format, data)
                
                # Send message to the conversation group
                await self.channel_layer.group_send(
                    self.conversation_group_name,
                    {
                        'type': 'chat_message',
                        'message_id': str(message.id),
                        'sender_id': self.user.id,
                        'sender_username': self.user.username,
                        'sender_profile_picture': self.user.profile_picture.url,
                        'content': content,
                        'format': message_format,
                        'timestamp': message.created_at.isoformat(),
                        'extra_data': data.get('extra_data', {}),
                    }
                )
        
        elif message_type == 'typing':
            # Handle typing indicator
            is_typing = data.get('is_typing', False)
            
            # Send typing status to the conversation group
            await self.channel_layer.group_send(
                self.conversation_group_name,
                {
                    'type': 'user_typing',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'is_typing': is_typing,
                }
            )
        
        elif message_type == 'read':
            # Handle message read status
            message_id = data.get('message_id')
            if message_id:
                # Mark message as read in database
                await self.mark_message_read(message_id)
                
                # Send read status to the conversation group
                await self.channel_layer.group_send(
                    self.conversation_group_name,
                    {
                        'type': 'message_read',
                        'message_id': message_id,
                        'user_id': self.user.id,
                        'username': self.user.username,
                        'timestamp': timezone.now().isoformat(),
                    }
                )
    
    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message_id': event['message_id'],
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'sender_profile_picture': event['sender_profile_picture'],
            'content': event['content'],
            'format': event['format'],
            'timestamp': event['timestamp'],
            'extra_data': event.get('extra_data', {}),
        }))
    
    async def user_typing(self, event):
        # Send typing status to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_typing': event['is_typing'],
        }))
    
    async def message_read(self, event):
        # Send read status to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'read',
            'message_id': event['message_id'],
            'user_id': event['user_id'],
            'username': event['username'],
            'timestamp': event['timestamp'],
        }))
    
    async def user_online(self, event):
        # Send online status to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'status',
            'status': 'online',
            'user_id': event['user_id'],
            'username': event['username'],
            'timestamp': event['timestamp'],
        }))
    
    async def user_offline(self, event):
        # Send offline status to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'status',
            'status': 'offline',
            'user_id': event['user_id'],
            'username': event['username'],
            'timestamp': event['timestamp'],
        }))
    
    @database_sync_to_async
    def is_conversation_participant(self):
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            return conversation.participants.filter(id=self.user.id).exists()
        except Conversation.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, content, message_format, data):
        conversation = Conversation.objects.get(id=self.conversation_id)
        
        # Create message
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            message_type=message_format,
            text=content if message_format == 'text' else '',
        )
        
        # Handle additional data based on message type
        if message_format == 'location':
            message.latitude = data.get('latitude')
            message.longitude = data.get('longitude')
        elif message_format in ['post', 'reel', 'story', 'profile']:
            message.shared_content_id = data.get('content_id', '')
        
        # Save file if provided (for image, video, audio, file types)
        if 'file_data' in data and message_format in ['image', 'video', 'audio', 'file']:
            # Note: In a real implementation, you would need to handle file uploads differently
            # This is a placeholder for the concept
            pass
        
        message.save()
        
        # Update conversation's updated_at time
        conversation.save()  # This will update the updated_at field via auto_now
        
        return message
    
    @database_sync_to_async
    def mark_message_read(self, message_id):
        try:
            message = Message.objects.get(id=message_id)
            # Only mark as read if user is not the sender
            if message.sender.id != self.user.id:
                MessageRead.objects.get_or_create(message=message, user=self.user)
            return True
        except Message.DoesNotExist:
            return False
