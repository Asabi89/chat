from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.db.models import Q, F, Count
from django.core.paginator import Paginator
from django.utils import timezone
from django.urls import reverse
from django.contrib import messages

from .models import Reel, ReelLike, ReelComment, ReelCommentLike, SavedReel
from .forms import ReelForm, ReelCommentForm
from accounts.models import User, Follow, BlockedUser
from notifications.utils import create_notification

import re
import json
from datetime import timedelta

@login_required
def reels_feed_view(request):
    """
    View for reels feed
    """
    # Get users that the current user follows
    following = Follow.objects.filter(follower=request.user).values_list('following', flat=True)
    
    # Get blocked users
    blocked_users = BlockedUser.objects.filter(
        Q(user=request.user) | Q(blocked_user=request.user)
    ).values_list('user', 'blocked_user')
    
    blocked_ids = set()
    for user_id, blocked_id in blocked_users:
        if user_id == request.user.id:
            blocked_ids.add(blocked_id)
        else:
            blocked_ids.add(user_id)
    
    # Get reels from followed users and trending reels
    followed_reels = Reel.objects.filter(
        user__in=following,
        is_archived=False,
        is_hidden=False
    ).exclude(
        user__in=blocked_ids
    )
    
    # Get trending reels from the last 7 days
    week_ago = timezone.now() - timedelta(days=7)
    trending_reels = Reel.objects.filter(
        created_at__gte=week_ago,
        is_archived=False,
        is_hidden=False
    ).exclude(
        user__in=blocked_ids
    ).exclude(
        id__in=followed_reels.values_list('id', flat=True)
    ).order_by('-engagement_score')[:50]
    
    # Combine and shuffle reels
    from itertools import chain
    from random import shuffle
    
    reels_list = list(chain(followed_reels, trending_reels))
    shuffle(reels_list)
    
    # Check which reels are liked by the current user
    liked_reels = ReelLike.objects.filter(
        user=request.user
    ).values_list('reel_id', flat=True)
    
    # Check which reels are saved by the current user
    saved_reels = SavedReel.objects.filter(
        user=request.user
    ).values_list('reel_id', flat=True)
    
    context = {
        'reels': reels_list,
        'liked_reels': liked_reels,
        'saved_reels': saved_reels,
    }
    
    # For AJAX requests, return JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        start = int(request.GET.get('start', 0))
        end = start + 5  # Load 5 reels at a time
        
        reels_data = []
        for reel in reels_list[start:end]:
            reels_data.append({
                'id': str(reel.id),
                'user': {
                    'username': reel.user.username,
                    'profile_picture': reel.user.profile_picture.url,
                },
                'video': reel.video.url,
                'thumbnail': reel.thumbnail.url if reel.thumbnail else '',
                'caption': reel.caption,
                'audio_track': reel.audio_track,
                'audio_artist': reel.audio_artist,
                'duration': reel.duration,
                'created_at': reel.created_at.isoformat(),
                'views_count': reel.views_count,
                'likes_count': reel.likes_count,
                'comments_count': reel.comments_count,
                'is_liked': str(reel.id) in liked_reels,
                'is_saved': str(reel.id) in saved_reels,
            })
        
        return JsonResponse({
            'reels': reels_data,
            'has_more': end < len(reels_list),
        })
    
    return render(request, 'reels/feed.html', context)

@login_required
def create_reel_view(request):
    """
    View for creating a new reel
    """
    if request.method == 'POST':
        form = ReelForm(request.POST, request.FILES)
        if form.is_valid():
            # Create reel
            reel = form.save(commit=False)
            reel.user = request.user
            
            # Process video duration (would require a video processing library)
            # For now, we'll set a default duration
            reel.duration = 30  # Default 30 seconds
            
            # Generate thumbnail (would require a video processing library)
            # For now, we'll leave it blank
            
            reel.save()
            
            # Update user's profile
            profile = request.user.profile
            profile.save()
            
            messages.success(request, "Your reel has been posted!")
            return redirect('reels:detail', pk=reel.pk)
    else:
        form = ReelForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'reels/create_reel.html', context)

@login_required
def reel_detail_view(request, pk):
    """
    View for reel detail
    """
    reel = get_object_or_404(Reel, pk=pk)
    
    # Check if reel is archived or hidden
    if reel.is_archived and reel.user != request.user:
        return HttpResponseForbidden("This reel is no longer available")
    
    if reel.is_hidden:
        return HttpResponseForbidden("This reel has been removed")
    
    # Check if user is blocked
    is_blocked = BlockedUser.objects.filter(
        (Q(user=request.user) & Q(blocked_user=reel.user)) | 
        (Q(user=reel.user) & Q(blocked_user=request.user))
    ).exists()
    
    if is_blocked:
        return HttpResponseForbidden("You cannot view this reel")
    
    # Increment view count
    if request.user != reel.user:
        reel.views_count = F('views_count') + 1
        reel.save()
        reel.refresh_from_db()
        
        # Update engagement score
        reel.calculate_engagement_score()
    
    # Get comments
    comments = ReelComment.objects.filter(reel=reel, parent=None).select_related('user')
    
    # Check if reel is liked by current user
    is_liked = ReelLike.objects.filter(user=request.user, reel=reel).exists()
    
    # Check if reel is saved by current user
    is_saved = SavedReel.objects.filter(user=request.user, reel=reel).exists()
    
    context = {
        'reel': reel,
        'comments': comments,
        'is_liked': is_liked,
        'is_saved': is_saved,
        'comment_form': ReelCommentForm(),
    }
    
    return render(request, 'reels/reel_detail.html', context)

@login_required
def edit_reel_view(request, pk):
    """
    View for editing a reel
    """
    reel = get_object_or_404(Reel, pk=pk)
    
    # Check if user is the reel owner
    if reel.user != request.user:
        return HttpResponseForbidden("You cannot edit this reel")
    
    if request.method == 'POST':
        form = ReelForm(request.POST, instance=reel)
        if form.is_valid():
            form.save()
            messages.success(request, "Reel updated successfully")
            return redirect('reels:detail', pk=reel.pk)
    else:
        form = ReelForm(instance=reel)
    
    context = {
        'form': form,
        'reel': reel,
    }
    
    return render(request, 'reels/edit_reel.html', context)

@login_required
def delete_reel_view(request, pk):
    """
    View for deleting a reel
    """
    reel = get_object_or_404(Reel, pk=pk)
    
    # Check if user is the reel owner
    if reel.user != request.user:
        return HttpResponseForbidden("You cannot delete this reel")
    
    if request.method == 'POST':
        # Archive reel instead of deleting
        reel.is_archived = True
        reel.save()
        
        messages.success(request, "Reel deleted successfully")
        return redirect('accounts:profile', username=request.user.username)
    
    context = {
        'reel': reel,
    }
    
    return render(request, 'reels/delete_reel.html', context)

@login_required
@require_POST
def like_reel_view(request, pk):
    """
    AJAX view for liking/unliking a reel
    """
    reel = get_object_or_404(Reel, pk=pk)
    
    # Check if user is blocked
    is_blocked = BlockedUser.objects.filter(
        (Q(user=request.user) & Q(blocked_user=reel.user)) | 
        (Q(user=reel.user) & Q(blocked_user=request.user))
    ).exists()
    
    if is_blocked:
        return JsonResponse({'status': 'error', 'message': 'You cannot interact with this reel'})
    
    # Check if reel is already liked
    like, created = ReelLike.objects.get_or_create(user=request.user, reel=reel)
    
    if created:
        # Increment like count
        reel.likes_count = F('likes_count') + 1
        reel.save()
        reel.refresh_from_db()
        
        # Create notification for reel owner
        if reel.user != request.user:
            create_notification(
                recipient=reel.user,
                sender=request.user,
                notification_type='reel_like',
                text=f"{request.user.username} liked your reel",
                content_id=str(reel.id)
            )
        
        # Update engagement score
        reel.calculate_engagement_score()
        
        return JsonResponse({
            'status': 'success', 
            'action': 'liked',
            'likes_count': reel.likes_count
        })
    else:
        # Unlike reel
        like.delete()
        
        # Decrement like count
        reel.likes_count = F('likes_count') - 1
        reel.save()
        reel.refresh_from_db()
        
        # Update engagement score
        reel.calculate_engagement_score()
        
        return JsonResponse({
            'status': 'success', 
            'action': 'unliked',
            'likes_count': reel.likes_count
        })

@login_required
@require_POST
def save_reel_view(request, pk):
    """
    AJAX view for saving/unsaving a reel
    """
    reel = get_object_or_404(Reel, pk=pk)
    
    # Check if reel is already saved
    saved, created = SavedReel.objects.get_or_create(user=request.user, reel=reel)
    
    if created:
        return JsonResponse({
            'status': 'success', 
            'action': 'saved'
        })
    else:
        # Unsave reel
        saved.delete()
        
        return JsonResponse({
            'status': 'success', 
            'action': 'unsaved'
        })

@login_required
@require_POST
def add_comment_view(request, pk):
    """
    View for adding a comment to a reel
    """
    reel = get_object_or_404(Reel, pk=pk)
    
    # Check if user is blocked
    is_blocked = BlockedUser.objects.filter(
        (Q(user=request.user) & Q(blocked_user=reel.user)) | 
        (Q(user=reel.user) & Q(blocked_user=request.user))
    ).exists()
    
    if is_blocked:
        return JsonResponse({'status': 'error', 'message': 'You cannot comment on this reel'})
    
    form = ReelCommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.user = request.user
        comment.reel = reel
        
        # Check for parent comment (reply)
        parent_id = request.POST.get('parent_id')
        if parent_id:
            try:
                
                parent_comment = ReelComment.objects.get(id=parent_id, reel=reel)
                comment.parent = parent_comment
            except ReelComment.DoesNotExist:
                pass
        
        comment.save()
        
        # Increment comment count
        reel.comments_count = F('comments_count') + 1
        reel.save()
        reel.refresh_from_db()
        
        # Update engagement score
        reel.calculate_engagement_score()
        
        # Create notification for reel owner
        if reel.user != request.user:
            create_notification(
                recipient=reel.user,
                sender=request.user,
                notification_type='reel_comment',
                text=f"{request.user.username} commented on your reel",
                content_id=str(reel.id)
            )
        
        # Create notification for parent comment owner (if reply)
        if comment.parent and comment.parent.user != request.user and comment.parent.user != reel.user:
            create_notification(
                recipient=comment.parent.user,
                sender=request.user,
                notification_type='reel_comment_reply',
                text=f"{request.user.username} replied to your comment",
                content_id=str(reel.id)
            )
        
        # Process mentions in comment
        mentions = re.findall(r'@(\w+)', comment.text)
        for username in mentions:
            try:
                mentioned_user = User.objects.get(username=username)
                # Don't notify yourself or users already notified
                if mentioned_user != request.user and mentioned_user != reel.user and (not comment.parent or mentioned_user != comment.parent.user):
                    create_notification(
                        recipient=mentioned_user,
                        sender=request.user,
                        notification_type='mention',
                        text=f"{request.user.username} mentioned you in a comment",
                        content_id=str(reel.id)
                    )
            except User.DoesNotExist:
                pass
        
        # For AJAX requests, return comment data
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'comment': {
                    'id': comment.id,
                    'user': {
                        'username': comment.user.username,
                        'profile_picture': comment.user.profile_picture.url,
                    },
                    'text': comment.text,
                    'created_at': comment.created_at.isoformat(),
                    'likes_count': 0,
                    'is_parent': comment.parent is None,
                    'parent_id': str(comment.parent.id) if comment.parent else None,
                },
                'comments_count': reel.comments_count
            })
        
        return redirect('reels:detail', pk=reel.pk)
    
    # If form is invalid
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'error',
            'errors': form.errors
        }, status=400)
    
    messages.error(request, "Error adding comment")
    return redirect('reels:detail', pk=reel.pk)

@login_required
@require_POST
def delete_comment_view(request, pk):
    """
    View for deleting a comment
    """
    comment = get_object_or_404(ReelComment, pk=pk)
    
    # Check if user is the comment owner or reel owner
    if comment.user != request.user and comment.reel.user != request.user:
        return HttpResponseForbidden("You cannot delete this comment")
    
    reel = comment.reel
    
    # Delete comment
    comment.delete()
    
    # Decrement comment count
    reel.comments_count = F('comments_count') - 1
    reel.save()
    reel.refresh_from_db()
    
    # Update engagement score
    reel.calculate_engagement_score()
    
    # For AJAX requests
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'comments_count': reel.comments_count
        })
    
    messages.success(request, "Comment deleted successfully")
    return redirect('reels:detail', pk=reel.pk)

@login_required
@require_POST
def like_comment_view(request, pk):
    """
    AJAX view for liking/unliking a comment
    """
    comment = get_object_or_404(ReelComment, pk=pk)
    
    # Check if user is blocked
    is_blocked = BlockedUser.objects.filter(
        (Q(user=request.user) & Q(blocked_user=comment.user)) | 
        (Q(user=comment.user) & Q(blocked_user=request.user))
    ).exists()
    
    if is_blocked:
        return JsonResponse({'status': 'error', 'message': 'You cannot interact with this comment'})
    
    # Check if comment is already liked
    like, created = ReelCommentLike.objects.get_or_create(user=request.user, comment=comment)
    
    if created:
        # Increment like count
        comment.likes_count = F('likes_count') + 1
        comment.save()
        comment.refresh_from_db()
        
        # Create notification for comment owner
        if comment.user != request.user:
            create_notification(
                recipient=comment.user,
                sender=request.user,
                notification_type='reel_comment_like',
                text=f"{request.user.username} liked your comment",
                content_id=str(comment.reel.id)
            )
        
        return JsonResponse({
            'status': 'success', 
            'action': 'liked',
            'likes_count': comment.likes_count
        })
    else:
        # Unlike comment
        like.delete()
        
        # Decrement like count
        comment.likes_count = F('likes_count') - 1
        comment.save()
        comment.refresh_from_db()
        
        return JsonResponse({
            'status': 'success', 
            'action': 'unliked',
            'likes_count': comment.likes_count
        })

@login_required
def user_reels_view(request, username):
    """
    View for displaying a user's reels
    """
    user = get_object_or_404(User, username=username)
    
    # Check if user is blocked
    is_blocked = BlockedUser.objects.filter(
        (Q(user=request.user) & Q(blocked_user=user)) | 
        (Q(user=user) & Q(blocked_user=request.user))
    ).exists()
    
    if is_blocked:
        return HttpResponseForbidden("You cannot view this user's reels")
    
    # Check if profile is private and user is not following
    if user.is_private and user != request.user:
        is_following = Follow.objects.filter(follower=request.user, following=user).exists()
        if not is_following:
            return HttpResponseForbidden("This account is private")
    
    # Get user's reels
    reels = Reel.objects.filter(
        user=user,
        is_archived=False,
        is_hidden=False
    ).order_by('-created_at')
    
    # Paginate reels
    paginator = Paginator(reels, 12)  # Show in grid layout
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'profile_user': user,
        'reels': page_obj,
    }
    
    # For AJAX requests, return JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        reel_data = []
        for reel in page_obj:
            reel_data.append({
                'id': str(reel.id),
                'thumbnail': reel.thumbnail.url if reel.thumbnail else '',
                'views_count': reel.views_count,
                'likes_count': reel.likes_count,
            })
        
        return JsonResponse({
            'reels': reel_data,
            'has_next': page_obj.has_next(),
        })
    
    return render(request, 'reels/user_reels.html', context)

@login_required
def saved_reels_view(request):
    """
    View for displaying a user's saved reels
    """
    # Get saved reels
    saved = SavedReel.objects.filter(user=request.user).order_by('-created_at')
    
    # Get the actual reels
    reels = Reel.objects.filter(
        id__in=saved.values_list('reel_id', flat=True),
        is_archived=False,
        is_hidden=False
    ).select_related('user')
    
    # Paginate reels
    paginator = Paginator(reels, 12)  # Show in grid layout
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'reels': page_obj,
    }
    
    # For AJAX requests, return JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        reel_data = []
        for reel in page_obj:
            reel_data.append({
                'id': str(reel.id),
                'user': {
                    'username': reel.user.username,
                },
                'thumbnail': reel.thumbnail.url if reel.thumbnail else '',
                'views_count': reel.views_count,
                'likes_count': reel.likes_count,
            })
        
        return JsonResponse({
            'reels': reel_data,
            'has_next': page_obj.has_next(),
        })
    
    return render(request, 'reels/saved_reels.html', context)

@login_required
@require_POST
def share_reel_view(request, pk):
    """
    AJAX view for sharing a reel
    """
    reel = get_object_or_404(Reel, pk=pk)
    
    # Increment share count
    reel.shares_count = F('shares_count') + 1
    reel.save()
    reel.refresh_from_db()
    
    # Update engagement score
    reel.calculate_engagement_score()
    
    # Get share destination (DM, external, etc.)
    share_type = request.POST.get('share_type', 'external')
    
    if share_type == 'message':
        # Handle sharing to direct messages
        recipient_username = request.POST.get('recipient')
        try:
            recipient = User.objects.get(username=recipient_username)
            
            # Create a conversation and message
            from messaging.models import Conversation, Message
            
            # Find or create conversation
            conversation = None
            for conv in request.user.conversations.all():
                if not conv.is_group_chat and conv.participants.count() == 2:
                    if recipient in conv.participants.all():
                        conversation = conv
                        break
            
            if not conversation:
                conversation = Conversation.objects.create(is_group_chat=False)
                conversation.participants.add(request.user, recipient)
            
            # Create message with reel share
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                message_type='reel',
                text=f"Shared a reel",
                shared_content_id=str(reel.id)
            )
            
            return JsonResponse({
                'status': 'success',
                'action': 'shared_dm',
                'shares_count': reel.shares_count
            })
            
        except User.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'User not found'
            }, status=400)
    
    # Default external share
    return JsonResponse({
        'status': 'success',
        'action': 'shared_external',
        'shares_count': reel.shares_count
    })

                
            
