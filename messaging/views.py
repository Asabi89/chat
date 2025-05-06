from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q, Max, Count, Exists, OuterRef
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib import messages

from .models import Conversation, Message, MessageRead, MessageReaction
from .forms import MessageForm, ConversationForm
from accounts.models import User, BlockedUser

@login_required
def inbox_view(request):
    """
    View to display user's conversations
    """
    # Get all conversations the user is part of
    conversations = Conversation.objects.filter(
        participants=request.user
    ).annotate(
        last_message_time=Max('messages__created_at'),
        unread_count=Count(
            'messages',
            filter=~Q(messages__read_by__user=request.user) & ~Q(messages__sender=request.user)
        )
    ).order_by('-last_message_time')
    
    return {
        'conversations': conversations,
    }

@login_required
def conversation_view(request, conversation_id):
    """
    View to display a specific conversation
    """
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Check if user is a participant
    if request.user not in conversation.participants.all():
        return HttpResponseForbidden("You are not a participant in this conversation")
    
    # Get messages for this conversation
    messages_queryset = Message.objects.filter(conversation=conversation).order_by('created_at')
    
    # Paginate messages
    paginator = Paginator(messages_queryset, 50)  # 50 messages per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Mark unread messages as read
    unread_messages = messages_queryset.filter(
        ~Q(sender=request.user) & ~Q(read_by__user=request.user)
    )
    
    for message in unread_messages:
        MessageRead.objects.get_or_create(message=message, user=request.user)
    
    # Create form for new message
    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.save()
            
            # Update conversation's updated_at time
            conversation.save()  # This will update the updated_at field via auto_now
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message_id': str(message.id),
                    'message_type': message.message_type,
                    'text': message.text,
                    'file_url': message.file.url if message.file else None,
                    'created_at': message.created_at.isoformat(),
                    'sender': {
                        'id': request.user.id,
                        'username': request.user.username,
                        'profile_picture': request.user.profile_picture.url,
                    }
                })
            
            return redirect('messaging:conversation', conversation_id=conversation.id)
    else:
        form = MessageForm()
    
    context = {
        'conversation': conversation,
        'messages': page_obj,
        'form': form,
    }
    
    return context

@login_required
def create_conversation_view(request):
    """
    View to create a new conversation
    """
    if request.method == 'POST':
        form = ConversationForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            conversation = form.save(commit=False)
            conversation.save()
            
            # Add current user and selected participants
            conversation.participants.add(request.user, *form.cleaned_data['participants'])
            
            # Create initial message if provided
            initial_message = request.POST.get('initial_message')
            if initial_message:
                Message.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    message_type='text',
                    text=initial_message
                )
            
            messages.success(request, "Conversation created successfully")
            return redirect('messaging:conversation', conversation_id=conversation.id)
    else:
        form = ConversationForm(user=request.user)
    
    context = {
        'form': form,
    }
    
    return context

@login_required
def direct_message_view(request, username):
    """
    View to start or continue a direct message with a specific user
    """
    recipient = get_object_or_404(User, username=username)
    
    # Check if users have blocked each other
    if BlockedUser.objects.filter(
        Q(user=request.user, blocked_user=recipient) | 
        Q(user=recipient, blocked_user=request.user)
    ).exists():
        messages.error(request, "You cannot message this user")
        return redirect('messaging:inbox')
    
    # Check if a conversation already exists between these users
    conversation = Conversation.objects.filter(
        participants=request.user,
        is_group_chat=False
    ).filter(
        participants=recipient
    ).annotate(
        participants_count=Count('participants')
    ).filter(
        participants_count=2
    ).first()
    
    # If no conversation exists, create one
    if not conversation:
        conversation = Conversation.objects.create(is_group_chat=False)
        conversation.participants.add(request.user, recipient)
    
    return redirect('messaging:conversation', conversation_id=conversation.id)

@login_required
def message_reaction_view(request, message_id):
    """
    AJAX view to add/remove a reaction to a message
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    
    message = get_object_or_404(Message, id=message_id)
    
    # Check if user is a participant in the conversation
    if request.user not in message.conversation.participants.all():
        return JsonResponse({'status': 'error', 'message': 'Not authorized'}, status=403)
    
    reaction_type = request.POST.get('reaction_type')
    if not reaction_type or reaction_type not in dict(MessageReaction.REACTION_TYPES):
        return JsonResponse({'status': 'error', 'message': 'Invalid reaction type'}, status=400)
    
    # Check if reaction already exists
    existing_reaction = MessageReaction.objects.filter(
        message=message,
        user=request.user
    ).first()
    
    if existing_reaction and existing_reaction.reaction_type == reaction_type:
        # Remove reaction if it's the same type
        existing_reaction.delete()
        action = 'removed'
    else:
        # Update or create reaction
        if existing_reaction:
            existing_reaction.reaction_type = reaction_type
            existing_reaction.save()
            action = 'updated'
        else:
            MessageReaction.objects.create(
                message=message,
                user=request.user,
                reaction_type=reaction_type
            )
            action = 'added'
    
    # Get updated reactions for this message
    reactions = MessageReaction.objects.filter(message=message).values('reaction_type').annotate(
        count=Count('reaction_type')
    )
    
    reaction_data = {}
    for r in reactions:
        reaction_data[r['reaction_type']] = r['count']
    
    return JsonResponse({
        'status': 'success',
        'action': action,
        'message_id': str(message.id),
        'reactions': reaction_data
    })

@login_required
def delete_message_view(request, message_id):
    """
    AJAX view to delete a message
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    
    message = get_object_or_404(Message, id=message_id)
    
    # Only the sender can delete their message
    if message.sender != request.user:
        return JsonResponse({'status': 'error', 'message': 'Not authorized'}, status=403)
    
    # Delete the message
    message.delete()
    
    return JsonResponse({
        'status': 'success',
        'message': 'Message deleted successfully'
    })

@login_required
def edit_message_view(request, message_id):
    """
    AJAX view to edit a message
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    
    message = get_object_or_404(Message, id=message_id)
    
    # Only the sender can edit their message
    if message.sender != request.user:
        return JsonResponse({'status': 'error', 'message': 'Not authorized'}, status=403)
    
    # Only text messages can be edited
    if message.message_type != 'text':
        return JsonResponse({'status': 'error', 'message': 'Only text messages can be edited'}, status=400)
    
    new_text = request.POST.get('text')
    if not new_text:
        return JsonResponse({'status': 'error', 'message': 'Message text cannot be empty'}, status=400)
    
    # Update the message
    message.text = new_text
    message.is_edited = True
    message.edited_at = timezone.now()
    message.save()
    
    return JsonResponse({
        'status': 'success',
        'message_id': str(message.id),
        'text': message.text,
        'edited_at': message.edited_at.isoformat()
    })

@login_required
def leave_group_view(request, conversation_id):
    """
    View to leave a group conversation
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Check if user is a participant
    if request.user not in conversation.participants.all():
        return JsonResponse({'status': 'error', 'message': 'Not a participant'}, status=403)
    
    # Check if it's a group chat
    if not conversation.is_group_chat:
        return JsonResponse({'status': 'error', 'message': 'Not a group conversation'}, status=400)
    
    # Remove user from participants
    conversation.participants.remove(request.user)
    
    # Add system message about user leaving
    Message.objects.create(
        conversation=conversation,
        sender=request.user,
        message_type='text',
        text=f"{request.user.username} has left the group"
    )
    
    return JsonResponse({
        'status': 'success',
        'message': 'You have left the group'
    })

@login_required
def add_participants_view(request, conversation_id):
    """
    View to add participants to a group conversation
    """
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
        # Check if user is a participant
    if request.user not in conversation.participants.all():
        return HttpResponseForbidden("You are not a participant in this conversation")
    
    # Check if it's a group chat
    if not conversation.is_group_chat:
        return HttpResponseForbidden("This is not a group conversation")
    
    if request.method == 'POST':
        user_ids = request.POST.getlist('user_ids')
        
        if not user_ids:
            return JsonResponse({'status': 'error', 'message': 'No users selected'}, status=400)
        
        # Get users from IDs
        users_to_add = User.objects.filter(id__in=user_ids)
        
        # Check for blocked users
        blocked_users = []
        for user in users_to_add:
            if BlockedUser.objects.filter(
                Q(user=request.user, blocked_user=user) | 
                Q(user=user, blocked_user=request.user)
            ).exists():
                blocked_users.append(user.username)
        
        if blocked_users:
            return JsonResponse({
                'status': 'error', 
                'message': f"Cannot add users: {', '.join(blocked_users)}"
            }, status=400)
        
        # Add users to conversation
        current_participants = set(conversation.participants.all().values_list('id', flat=True))
        added_users = []
        
        for user in users_to_add:
            if user.id not in current_participants:
                conversation.participants.add(user)
                added_users.append(user.username)
        
        if added_users:
            # Add system message about users being added
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                message_type='text',
                text=f"{request.user.username} added {', '.join(added_users)} to the group"
            )
            
            return JsonResponse({
                'status': 'success',
                'message': f"Added users: {', '.join(added_users)}"
            })
        else:
            return JsonResponse({
                'status': 'info',
                'message': "All selected users are already in the group"
            })
    
    # Get users who can be added (not blocked, not already in the conversation)
    current_participants = conversation.participants.all()
    
    blocked_users = User.objects.filter(
        Q(user_blocks__blocked_user=request.user) | 
        Q(blocked_by__user=request.user)
    ).distinct()
    
    available_users = User.objects.exclude(
        Q(id__in=current_participants.values_list('id', flat=True)) | 
        Q(id__in=blocked_users.values_list('id', flat=True))
    )
    
    context = {
        'conversation': conversation,
        'available_users': available_users,
    }
    
    return context

@login_required
def edit_group_view(request, conversation_id):
    """
    View to edit group conversation details
    """
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Check if user is a participant
    if request.user not in conversation.participants.all():
        return HttpResponseForbidden("You are not a participant in this conversation")
    
    # Check if it's a group chat
    if not conversation.is_group_chat:
        return HttpResponseForbidden("This is not a group conversation")
    
    if request.method == 'POST':
        group_name = request.POST.get('group_name')
        
        if not group_name:
            return JsonResponse({'status': 'error', 'message': 'Group name cannot be empty'}, status=400)
        
        # Update group name
        old_name = conversation.group_name
        conversation.group_name = group_name
        
        # Update group avatar if provided
        if 'group_avatar' in request.FILES:
            conversation.group_avatar = request.FILES['group_avatar']
        
        conversation.save()
        
        # Add system message about group name change
        if old_name != group_name:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                message_type='text',
                text=f"{request.user.username} changed the group name to '{group_name}'"
            )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Group details updated successfully',
            'group_name': conversation.group_name,
            'group_avatar': conversation.group_avatar.url if conversation.group_avatar else None
        })
    
    context = {
        'conversation': conversation,
    }
    
    return context
@login_required
def mark_conversation_read_view(request, conversation_id):
    """AJAX view to mark all messages in a conversation as read"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Check if user is a participant
    if request.user not in conversation.participants.all():
        return JsonResponse({'status': 'error', 'message': 'Not a participant'}, status=403)
    
    # Get all unread messages in this conversation
    unread_messages = Message.objects.filter(
        conversation=conversation
    ).exclude(
        sender=request.user
    ).exclude(
        read_by__user=request.user
    )
    
    # Mark all as read
    for message in unread_messages:
        MessageRead.objects.get_or_create(message=message, user=request.user)
    
    return JsonResponse({
        'status': 'success',
        'message': 'All messages marked as read',
        'count': unread_messages.count()
    })
    
@login_required
def unread_count_view(request):
    """AJAX view to get the count of unread messages"""
    # Count unread messages across all conversations
    unread_count = Message.objects.filter(
        conversation__participants=request.user
    ).exclude(
        sender=request.user
    ).exclude(
        read_by__user=request.user
    ).count()
    
    return JsonResponse({'unread_count': unread_count})
