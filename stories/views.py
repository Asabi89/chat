from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.utils import timezone
from django.db.models import Q, F, Count
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied

from .models import Story, StoryView, StoryReaction, StoryHighlight, HighlightStory
from .forms import StoryForm, StoryHighlightForm, HighlightStoryFormSet
from accounts.models import User, Follow, BlockedUser

import datetime

@login_required
def story_feed(request):
    """
    View for displaying stories from followed users
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
    
    # Get active stories from followed users
    now = timezone.now()
    
    # First get users with active stories
    users_with_stories = User.objects.filter(
        id__in=following,
        stories__expires_at__gt=now,
        stories__is_hidden=False
    ).exclude(
        id__in=blocked_ids
    ).annotate(
        story_count=Count('stories', filter=Q(stories__expires_at__gt=now, stories__is_hidden=False))
    ).filter(
        story_count__gt=0
    ).distinct()
    
    # Get stories for each user
    user_stories = []
    for user in users_with_stories:
        stories = Story.objects.filter(
            user=user,
            expires_at__gt=now,
            is_hidden=False
        ).order_by('created_at')
        
        # Check which stories the current user has viewed
        viewed_story_ids = StoryView.objects.filter(
            user=request.user,
            story__in=stories
        ).values_list('story_id', flat=True)
        
        # Add viewed status to each story
        stories_with_status = []
        for story in stories:
            stories_with_status.append({
                'story': story,
                'viewed': story.id in viewed_story_ids
            })
        
        # Only add to the feed if there are stories
        if stories_with_status:
            user_stories.append({
                'user': user,
                'stories': stories_with_status,
                'has_unviewed': any(not s['viewed'] for s in stories_with_status)
            })
    
    # Sort users with unviewed stories first
    user_stories.sort(key=lambda x: (not x['has_unviewed'], x['stories'][0]['story'].created_at), reverse=True)
    
    # Get current user's active stories
    my_stories = Story.objects.filter(
        user=request.user,
        expires_at__gt=now,
        is_hidden=False
    ).order_by('created_at')
    
    # For AJAX requests, return JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        users_data = []
        for user_data in user_stories:
            user = user_data['user']
            stories_data = []
            
            for story_data in user_data['stories']:
                story = story_data['story']
                stories_data.append({
                    'id': str(story.id),
                    'type': story.story_type,
                    'file_url': story.file.url,
                    'caption': story.caption,
                    'created_at': story.created_at.isoformat(),
                    'expires_at': story.expires_at.isoformat(),
                    'viewed': story_data['viewed'],
                })
            
            users_data.append({
                'id': user.id,
                'username': user.username,
                'profile_picture': user.profile_picture.url,
                'is_verified': user.is_verified,
                'stories': stories_data,
                'has_unviewed': user_data['has_unviewed'],
            })
        
        my_stories_data = []
        for story in my_stories:
            my_stories_data.append({
                'id': str(story.id),
                'type': story.story_type,
                'file_url': story.file.url,
                'caption': story.caption,
                'created_at': story.created_at.isoformat(),
                'expires_at': story.expires_at.isoformat(),
                'views_count': story.views_count,
            })
        
        return JsonResponse({
            'user_stories': users_data,
            'my_stories': my_stories_data,
        })
    
    context = {
        'user_stories': user_stories,
        'my_stories': my_stories,
    }
    
    return render(request, 'stories/feed.html', context)

@login_required
def view_story(request, pk):
    """
    View a specific story
    """
    story = get_object_or_404(Story, pk=pk)
    
    # Check if story is expired
    if story.expires_at < timezone.now():
        raise Http404("Story has expired")
    
    # Check if story is hidden
    if story.is_hidden:
        raise Http404("Story not found")
    
    # Check if user is blocked
    is_blocked = BlockedUser.objects.filter(
        (Q(user=request.user) & Q(blocked_user=story.user)) |
        (Q(user=story.user) & Q(blocked_user=request.user))
    ).exists()
    
    if is_blocked:
        raise Http404("Story not found")
    
    # Record view if not already viewed
    if request.user != story.user:
        view, created = StoryView.objects.get_or_create(
            story=story,
            user=request.user
        )
        
        if created:
            # Increment view count
            story.views_count = F('views_count') + 1
            story.save(update_fields=['views_count'])
    
    # Get reactions for this story
    reactions = StoryReaction.objects.filter(story=story)
    
    # Get user's reaction if any
    user_reaction = None
    if request.user.is_authenticated:
        try:
            user_reaction = StoryReaction.objects.get(story=story, user=request.user)
        except StoryReaction.DoesNotExist:
            pass
    
    # Get next and previous stories from the same user
    now = timezone.now()
    next_story = Story.objects.filter(
        user=story.user,
        created_at__gt=story.created_at,
        expires_at__gt=now,
        is_hidden=False
    ).order_by('created_at').first()
    
    prev_story = Story.objects.filter(
        user=story.user,
        created_at__lt=story.created_at,
        expires_at__gt=now,
        is_hidden=False
    ).order_by('-created_at').first()
    
    # For AJAX requests, return JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        reactions_data = []
        for reaction in reactions:
            reactions_data.append({
                'id': reaction.id,
                'user': {
                    'id': reaction.user.id,
                    'username': reaction.user.username,
                    'profile_picture': reaction.user.profile_picture.url,
                },
                'reaction_type': reaction.reaction_type,
                'custom_message': reaction.custom_message,
                'created_at': reaction.created_at.isoformat(),
            })
        
        user_reaction_data = None
        if user_reaction:
            user_reaction_data = {
                'id': user_reaction.id,
                'reaction_type': user_reaction.reaction_type,
                'custom_message': user_reaction.custom_message,
            }
        
        next_story_data = None
        if next_story:
            next_story_data = {
                'id': str(next_story.id),
            }
        
        prev_story_data = None
        if prev_story:
            prev_story_data = {
                'id': str(prev_story.id),
            }
        
        return JsonResponse({
            'story': {
                'id': str(story.id),
                'user': {
                    'id': story.user.id,
                    'username': story.user.username,
                    'profile_picture': story.user.profile_picture.url,
                    'is_verified': story.user.is_verified,
                },
                'file_url': story.file.url,
                'story_type': story.story_type,
                'caption': story.caption,
                'location': story.location,
                'created_at': story.created_at.isoformat(),
                'expires_at': story.expires_at.isoformat(),
                'music_track': story.music_track,
                'music_artist': story.music_artist,
                'views_count': story.views_count,
            },
            'reactions': reactions_data,
            'user_reaction': user_reaction_data,
            'next_story': next_story_data,
            'prev_story': prev_story_data,
        })
    
    context = {
        'story': story,
        'reactions': reactions,
        'user_reaction': user_reaction,
        'next_story': next_story,
        'prev_story': prev_story,
    }
    
    return render(request, 'stories/view.html', context)

@login_required
def create_story(request):
    """
    Create a new story
    """
    if request.method == 'POST':
        form = StoryForm(request.POST, request.FILES)
        if form.is_valid():
            story = form.save(commit=False)
            story.user = request.user
            
            # Set expiration time (24 hours from now)
            story.expires_at = timezone.now() + datetime.timedelta(hours=24)
            
            story.save()
            
            # For AJAX requests, return JSON
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'story_id': str(story.id),
                    'redirect_url': story.get_absolute_url(),
                })
            
            return redirect(story.get_absolute_url())
    else:
        form = StoryForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'stories/create.html', context)

@login_required
def delete_story(request, pk):
    """
    Delete a story
    """
    story = get_object_or_404(Story, pk=pk)
    
    # Check if user is the owner
    if request.user != story.user:
        raise PermissionDenied("You don't have permission to delete this story")
    
    if request.method == 'POST':
        story.delete()
        
        # For AJAX requests, return JSON
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
            })
        
        return redirect('stories:feed')
    
    context = {
        'story': story,
    }
    
    return render(request, 'stories/delete.html', context)

@login_required
@require_POST
def react_to_story(request, pk):
    """
    React to a story
    """
    story = get_object_or_404(Story, pk=pk)
    
    # Check if story is expired
    if story.expires_at < timezone.now():
        return JsonResponse({
            'success': False,
            'error': 'Story has expired',
        }, status=400)
    
    # Check if story is hidden
    if story.is_hidden:
        return JsonResponse({
            'success': False,
            'error': 'Story not found',
        }, status=404)
    
    # Check if user is blocked
    is_blocked = BlockedUser.objects.filter(
        (Q(user=request.user) & Q(blocked_user=story.user)) |
        (Q(user=story.user) & Q(blocked_user=request.user))
    ).exists()
    
    if is_blocked:
        return JsonResponse({
            'success': False,
            'error': 'Story not found',
        }, status=404)
    
    reaction_type = request.POST.get('reaction_type')
    custom_message = request.POST.get('custom_message', '')
    
    # Validate reaction type
    valid_reaction_types = [choice[0] for choice in StoryReaction.REACTION_TYPES]
    if reaction_type not in valid_reaction_types:
        return JsonResponse({
            'success': False,
            'error': 'Invalid reaction type',
        }, status=400)
    
    # Create or update reaction
    reaction, created = StoryReaction.objects.update_or_create(
        story=story,
        user=request.user,
        defaults={
            'reaction_type': reaction_type,
            'custom_message': custom_message if reaction_type == 'custom' else '',
        }
    )
    
    return JsonResponse({
        'success': True,
        'reaction': {
            'id': reaction.id,
            'reaction_type': reaction.reaction_type,
            'custom_message': reaction.custom_message,
            'created_at': reaction.created_at.isoformat(),
        },
    })

@login_required
@require_POST
def delete_reaction(request, pk):
    """
    Delete a reaction to a story
    """
    story = get_object_or_404(Story, pk=pk)
    
    # Delete the reaction
    try:
        reaction = StoryReaction.objects.get(story=story, user=request.user)
        reaction.delete()
        
        return JsonResponse({
            'success': True,
        })
    except StoryReaction.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Reaction not found',
        }, status=404)

@login_required
def story_viewers(request, pk):
    """
    View list of users who viewed a story
    """
    story = get_object_or_404(Story, pk=pk)
    
    # Check if user is the owner
    if request.user != story.user:
        raise PermissionDenied("You don't have permission to view this information")
    
    # Get viewers
    viewers = StoryView.objects.filter(story=story).select_related('user').order_by('-viewed_at')
    
    # For AJAX requests, return JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        viewers_data = []
        for view in viewers:
            viewers_data.append({
                'id': view.id,
                'user': {
                    'id': view.user.id,
                    'username': view.user.username,
                    'profile_picture': view.user.profile_picture.url,
                    'is_verified': view.user.is_verified,
                },
                'viewed_at': view.viewed_at.isoformat(),
            })
        
        return JsonResponse({
            'viewers': viewers_data,
            'total_count': viewers.count(),
        })
    
    context = {
        'story': story,
        'viewers': viewers,
    }
    
    return render(request, 'stories/viewers.html', context)

@login_required
def user_stories(request, username):
    """
    View all active stories from a specific user
    """
    user = get_object_or_404(User, username=username)
    
    # Check if user is blocked
    is_blocked = BlockedUser.objects.filter(
        (Q(user=request.user) & Q(blocked_user=user)) |
        (Q(user=user) & Q(blocked_user=request.user))
    ).exists()
    
    if is_blocked:
        raise Http404("User not found")
    
    # Check if user has a private account and current user is not following
    if user.is_private and user != request.user:
        is_following = Follow.objects.filter(follower=request.user, following=user).exists()
        if not is_following:
            raise PermissionDenied("This account is private")
    
    # Get active stories
    now = timezone.now()
    stories = Story.objects.filter(
        user=user,
        expires_at__gt=now,
        is_hidden=False
    ).order_by('created_at')
    
    # Check which stories the current user has viewed
    viewed_story_ids = StoryView.objects.filter(
        user=request.user,
        story__in=stories
    ).values_list('story_id', flat=True)
    
    # Add viewed status to each story
    stories_with_status = []
    for story in stories:
        stories_with_status.append({
            'story': story,
            'viewed': story.id in viewed_story_ids
        })
    
    # For AJAX requests, return JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        stories_data = []
        for story_data in stories_with_status:
            story = story_data['story']
            stories_data.append({
                'id': str(story.id),
                'type': story.story_type,
                'file_url': story.file.url,
                'caption': story.caption,
                'created_at': story.created_at.isoformat(),
                'expires_at': story.expires_at.isoformat(),
                'viewed': story_data['viewed'],
            })
        
        return JsonResponse({
            'user': {
                'id': user.id,
                'username': user.username,
                'profile_picture': user.profile_picture.url,
                'is_verified': user.is_verified,
            },
            'stories': stories_data,
        })
    
    context = {
        'profile_user': user,
        'stories': stories_with_status,
    }
    
    return render(request, 'stories/user_stories.html', context)

@login_required
def highlights(request, username):
    """
    View story highlights for a user
    """
    user = get_object_or_404(User, username=username)
    
    # Check if user is blocked
    is_blocked = BlockedUser.objects.filter(
        (Q(user=request.user) & Q(blocked_user=user)) |
        (Q(user=user) & Q(blocked_user=request.user))
    ).exists()
    
    if is_blocked:
        raise Http404("User not found")
    
    # Check if user has a private account and current user is not following
    if user.is_private and user != request.user:
        is_following = Follow.objects.filter(follower=request.user, following=user).exists()
        if not is_following:
            raise PermissionDenied("This account is private")
    
    # Get highlights
    highlights = StoryHighlight.objects.filter(user=user).order_by('-updated_at')
    
    # For AJAX requests, return JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        highlights_data = []
        for highlight in highlights:
            # Get stories in this highlight
            highlight_stories = HighlightStory.objects.filter(
                highlight=highlight
            ).select_related('story').order_by('order')
            
            stories_data = []
            for hs in highlight_stories:
                story = hs.story
                stories_data.append({
                    'id': str(story.id),
                    'type': story.story_type,
                    'file_url': story.file.url,
                    'caption': story.caption,
                })
            
            highlights_data.append({
                'id': highlight.id,
                'title': highlight.title,
                'cover_image': highlight.cover_image.url if highlight.cover_image else None,
                'created_at': highlight.created_at.isoformat(),
                'updated_at': highlight.updated_at.isoformat(),
                'stories_count': highlight_stories.count(),
                'stories': stories_data,
            })
        
        return JsonResponse({
            'user': {
                'id': user.id,
                'username': user.username,
                'profile_picture': user.profile_picture.url,
                'is_verified': user.is_verified,
            },
            'highlights': highlights_data,
        })
    
    context = {
        'profile_user': user,
        'highlights': highlights,
    }
    
    return render(request, 'stories/highlights.html', context)

@login_required
def view_highlight(request, username, pk):
    """
    View a specific highlight
    """
    user = get_object_or_404(User, username=username)
    highlight = get_object_or_404(StoryHighlight, pk=pk, user=user)
    
    # Check if user is blocked
    is_blocked = BlockedUser.objects.filter(
        (Q(user=request.user) & Q(blocked_user=user)) |
        (Q(user=user) & Q(blocked_user=request.user))
    ).exists()
    
    if is_blocked:
        raise Http404("Highlight not found")
    
    # Check if user has a private account and current user is not following
    if user.is_private and user != request.user:
        is_following = Follow.objects.filter(follower=request.user, following=user).exists()
        if not is_following:
            raise PermissionDenied("This account is private")
    
    # Get stories in this highlight
    highlight_stories = HighlightStory.objects.filter(
        highlight=highlight
    ).select_related('story').order_by('order')
    
    # For AJAX requests, return JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        stories_data = []
        for hs in highlight_stories:
            story = hs.story
            stories_data.append({
                'id': str(story.id),
                'type': story.story_type,
                'file_url': story.file.url,
                'caption': story.caption,
                'location': story.location,
                'created_at': story.created_at.isoformat(),
                'music_track': story.music_track,
                'music_artist': story.music_artist,
            })
        
        return JsonResponse({
            'highlight': {
                'id': highlight.id,
                'title': highlight.title,
                'cover_image': highlight.cover_image.url if highlight.cover_image else None,
                'created_at': highlight.created_at.isoformat(),
                'updated_at': highlight.updated_at.isoformat(),
            },
            'user': {
                'id': user.id,
                'username': user.username,
                'profile_picture': user.profile_picture.url,
                'is_verified': user.is_verified,
            },
            'stories': stories_data,
        })
    
    context = {
        'profile_user': user,
        'highlight': highlight,
        'highlight_stories': highlight_stories,
    }
    
    return render(request, 'stories/view_highlight.html', context)

@login_required
def create_highlight(request):
    """
    Create a new highlight
    """
    if request.method == 'POST':
        form = StoryHighlightForm(request.POST, request.FILES)
        if form.is_valid():
            highlight = form.save(commit=False)
            highlight.user = request.user
            highlight.save()
            
            # Get selected stories
            story_ids = request.POST.getlist('stories')
            
            # Add stories to highlight
            for i, story_id in enumerate(story_ids):
                try:
                    story = Story.objects.get(pk=story_id, user=request.user)
                    HighlightStory.objects.create(
                        highlight=highlight,
                        story=story,
                        order=i
                    )
                except Story.DoesNotExist:
                    pass
            
            # For AJAX requests, return JSON
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'highlight_id': highlight.id,
                    'redirect_url': reverse('stories:highlights', kwargs={'username': request.user.username}),
                })
            
            return redirect('stories:highlights', username=request.user.username)
    else:
        form = StoryHighlightForm()
    
    # Get user's stories (including expired ones)
    stories = Story.objects.filter(
        user=request.user,
        is_hidden=False
    ).order_by('-created_at')
    
    context = {
        'form': form,
        'stories': stories,
    }
    
    return render(request, 'stories/create_highlight.html', context)

@login_required
def edit_highlight(request, pk):
    """
    Edit an existing highlight
    """
    highlight = get_object_or_404(StoryHighlight, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = StoryHighlightForm(request.POST, request.FILES, instance=highlight)
        if form.is_valid():
            highlight = form.save()
            
            # Get selected stories
            story_ids = request.POST.getlist('stories')
            
            # Remove existing stories
            HighlightStory.objects.filter(highlight=highlight).delete()
            
            # Add stories to highlight
            for i, story_id in enumerate(story_ids):
                try:
                    story = Story.objects.get(pk=story_id, user=request.user)
                    HighlightStory.objects.create(
                        highlight=highlight,
                        story=story,
                        order=i
                    )
                except Story.DoesNotExist:
                    pass
            
            # For AJAX requests, return JSON
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'highlight_id': highlight.id,
                    'redirect_url': reverse('stories:highlights', kwargs={'username': request.user.username}),
                })
            
            return redirect('stories:highlights', username=request.user.username)
    else:
        form = StoryHighlightForm(instance=highlight)
    
    # Get user's stories (including expired ones)
    stories = Story.objects.filter(
        user=request.user,
        is_hidden=False
    ).order_by('-created_at')
    
    # Get stories already in this highlight
    highlight_story_ids = HighlightStory.objects.filter(
        highlight=highlight
    ).values_list('story_id', flat=True)
    
    context = {
        'form': form,
        'highlight': highlight,
        'stories': stories,
        'highlight_story_ids': highlight_story_ids,
    }
    
    return render(request, 'stories/edit_highlight.html', context)

@login_required
def delete_highlight(request, pk):
    """
    Delete a highlight
    """
    highlight = get_object_or_404(StoryHighlight, pk=pk, user=request.user)
    
    if request.method == 'POST':
        highlight.delete()
        
        # For AJAX requests, return JSON
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
            })
        
        return redirect('stories:highlights', username=request.user.username)
    
    context = {
        'highlight': highlight,
    }
    
    return render(request, 'stories/delete_highlight.html', context)
