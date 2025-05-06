from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.db.models import Q, F, Count
from django.core.paginator import Paginator
from django.utils import timezone
from django.urls import reverse
from django.contrib import messages

from .models import Post, Media, Like, Comment, CommentLike, SavedPost, PostTag
from .forms import PostForm, CommentForm, MediaForm
from accounts.models import User, Follow, BlockedUser
from notifications.utils import create_notification
from accounts.models import User
import re
import json
import uuid
@login_required
def feed_view(request):
    """
    View for user's feed (posts from followed users)
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
    
    # Get posts from followed users and the user's own posts
    posts = Post.objects.filter(
        (Q(user__in=following) | Q(user=request.user)) &
        (Q(is_archived=False) & Q(is_hidden=False)) |
        Q(profile_picture_of__in=following)  # Include profile picture posts
    ).exclude(
        user__in=blocked_ids
    ).select_related('user').prefetch_related('media_files').distinct()
    
    # Paginate posts
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Check which posts are liked by the current user
    liked_posts = Like.objects.filter(
        user=request.user, 
        post__in=page_obj.object_list
    ).values_list('post_id', flat=True)
    
    # Check which posts are saved by the current user
    saved_posts = SavedPost.objects.filter(
        user=request.user, 
        post__in=page_obj.object_list
    ).values_list('post_id', flat=True)
    
    context = {
        'posts': page_obj,
        'liked_posts': liked_posts,
        'saved_posts': saved_posts,
    }
    
    # For AJAX requests, return JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        post_data = []
        for post in page_obj:
            post_data.append({
                'id': str(post.id),
                'user': {
                    'username': post.user.username,
                    'profile_picture': post.user.profile_picture.url,
                },
                'caption': post.caption,
                'location': post.location,
                'post_type': post.post_type,
                'created_at': post.created_at.isoformat(),
                'likes_count': post.likes_count,
                'comments_count': post.comments_count,
                'media_files': [
                    {
                        'id': str(media.id),
                        'file': media.file.url,
                        'media_type': media.media_type,
                        'order': media.order,
                    } for media in post.media_files.all()
                ],
                'is_liked': str(post.id) in liked_posts,
                'is_saved': str(post.id) in saved_posts,
            })
        
        return JsonResponse({
            'posts': post_data,
            'has_next': page_obj.has_next(),
        })
    
    return render(request, 'posts/feed.html', context)

@login_required
def explore_view(request):
    """
    View for explore page (popular and recommended posts)
    """
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
    
    # Get popular posts (high engagement score)
    posts = Post.objects.filter(
        is_archived=False,
        is_hidden=False
    ).exclude(
        user__in=blocked_ids
    ).order_by('-engagement_score', '-created_at')
    
    # Paginate posts
    paginator = Paginator(posts, 12)  # Show more posts in explore grid
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'posts': page_obj,
    }
    
    # For AJAX requests, return JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        post_data = []
        for post in page_obj:
            # Get first media for thumbnail
            first_media = post.media_files.first()
            post_data.append({
                'id': str(post.id),
                'user': {
                    'username': post.user.username,
                },
                'thumbnail': first_media.file.url if first_media else None,
                'media_type': first_media.media_type if first_media else None,
                'likes_count': post.likes_count,
                'comments_count': post.comments_count,
            })
        
        return JsonResponse({
            'posts': post_data,
            'has_next': page_obj.has_next(),
        })
    
    return render(request, 'posts/explore.html', context)

@login_required
def create_post_view(request):
    """
    View for creating a new post
    """
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            # Create post
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            
            # Process media files
            media_files = request.FILES.getlist('media_files')
            media_types = request.POST.getlist('media_types')
            
            if not media_files:
                # Delete post if no media files
                post.delete()
                return HttpResponseBadRequest("No media files provided")
            
            # Determine post type based on number of media files
            if len(media_files) > 1:
                post.post_type = 'carousel'
            else:
                post.post_type = media_types[0]  # 'image' or 'video'
            
            post.save()
            
            # Save media files
            for i, (file, media_type) in enumerate(zip(media_files, media_types)):
                Media.objects.create(
                    post=post,
                    file=file,
                    media_type=media_type,
                    order=i
                )
            
            # Process user tags
            if 'user_tags' in request.POST:
                user_tags = json.loads(request.POST.get('user_tags'))
                for username in user_tags:
                    try:
                        tagged_user = User.objects.get(username=username)
                        PostTag.objects.create(post=post, user=tagged_user)
                        
                        # Create notification for tagged user
                        create_notification(
                            recipient=tagged_user,
                            sender=request.user,
                            notification_type='tag',
                            text=f"{request.user.username} tagged you in a post",
                            content_id=str(post.id)
                        )
                    except User.DoesNotExist:
                        pass
            
            # Update user's post count
            profile = request.user.profile
            profile.posts_count = F('posts_count') + 1
            profile.save()
            
            # Redirect to post detail
            return redirect('posts:detail', pk=post.pk)
    else:
        form = PostForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'posts/create_post.html', context)

@login_required
def post_detail_view(request, pk):
    """
    View for post detail
    """
    post = get_object_or_404(Post, pk=pk)
    
    # Check if post is archived or hidden
    if post.is_archived and post.user != request.user:
        return HttpResponseForbidden("This post is no longer available")
    
    if post.is_hidden:
        return HttpResponseForbidden("This post has been removed")
    
    # Check if user is blocked
    is_blocked = BlockedUser.objects.filter(
        (Q(user=request.user) & Q(blocked_user=post.user)) | 
        (Q(user=post.user) & Q(blocked_user=request.user))
    ).exists()
    
    if is_blocked:
        return HttpResponseForbidden("You cannot view this post")
    
    # Increment view count
    if request.user != post.user:
        post.views_count = F('views_count') + 1
        post.save()
        post.refresh_from_db()
    
    # Get comments
    comments = Comment.objects.filter(post=post, parent=None).select_related('user')
    
    # Check if post is liked by current user
    is_liked = Like.objects.filter(user=request.user, post=post).exists()
    
    # Check if post is saved by current user
    is_saved = SavedPost.objects.filter(user=request.user, post=post).exists()
    
    # Get user tags
    user_tags = PostTag.objects.filter(post=post).select_related('user')
    
    context = {
        'post': post,
        'comments': comments,
        'is_liked': is_liked,
        'is_saved': is_saved,
        'user_tags': user_tags,
        'comment_form': CommentForm(),
    }
    
    return render(request, 'posts/post_detail.html', context)

@login_required
def edit_post_view(request, pk):
    """
    View for editing a post
    """
    post = get_object_or_404(Post, pk=pk)
    
    # Check if user is the post owner
    if post.user != request.user:
        return HttpResponseForbidden("You cannot edit this post")
    
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, "Post updated successfully")
            return redirect('posts:detail', pk=post.pk)
    else:
        form = PostForm(instance=post)
    
    context = {
        'form': form,
        'post': post,
    }
    
    return render(request, 'posts/edit_post.html', context)

@login_required
def delete_post_view(request, pk):
    """
    View for deleting a post
    """
    post = get_object_or_404(Post, pk=pk)
    
    # Check if user is the post owner
    if post.user != request.user:
        return HttpResponseForbidden("You cannot delete this post")
    
    if request.method == 'POST':
        # Archive post instead of deleting
        post.is_archived = True
        post.save()
        
        # Update user's post count
        profile = request.user.profile
        profile.posts_count = F('posts_count') - 1
        profile.save()
        
        messages.success(request, "Post deleted successfully")
        return redirect('accounts:profile', username=request.user.username)
    
    context = {
        'post': post,
    }
    
    return render(request, 'posts/delete_post.html', context)

@login_required
@require_POST
def like_post_view(request, pk):
    """
    AJAX view for liking/unliking a post
    """
    post = get_object_or_404(Post, pk=pk)
    
    # Check if user is blocked
    is_blocked = BlockedUser.objects.filter(
        (Q(user=request.user) & Q(blocked_user=post.user)) | 
        (Q(user=post.user) & Q(blocked_user=request.user))
    ).exists()
    
    if is_blocked:
        return JsonResponse({'status': 'error', 'message': 'You cannot interact with this post'})
    
    # Check if post is already liked
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    
    if created:
        # Increment like count
        post.likes_count = F('likes_count') + 1
        post.save()
        post.refresh_from_db()
        
        # Create notification for post owner
        if post.user != request.user:
            create_notification(
                recipient=post.user,
                sender=request.user,
                notification_type='like',
                text=f"{request.user.username} liked your post",
                content_id=str(post.id)
            )
        
        # Update engagement score
        post.calculate_engagement_score()
        
        return JsonResponse({
            'status': 'success', 
            'action': 'liked',
            'likes_count': post.likes_count
        })
    else:
        # Unlike post
        like.delete()
        
        # Decrement like count
        post.likes_count = F('likes_count') - 1
        post.save()
        post.refresh_from_db()
        
        # Update engagement score
        post.calculate_engagement_score()
        
        return JsonResponse({
            'status': 'success', 
            'action': 'unliked',
            'likes_count': post.likes_count
        })

@login_required
@require_POST
def save_post_view(request, pk):
    """
    AJAX view for saving/unsaving a post
    """
    post = get_object_or_404(Post, pk=pk)
    
    # Check if post is already saved
    saved, created = SavedPost.objects.get_or_create(user=request.user, post=post)
    
    if created:
        # Increment save count
        post.saves_count = F('saves_count') + 1
        post.save()
        post.refresh_from_db()
        
        # Update engagement score
        post.calculate_engagement_score()
        
        return JsonResponse({
            'status': 'success', 
            'action': 'saved',
            'saves_count': post.saves_count
        })
    else:
        # Unsave post
        saved.delete()
        
        # Decrement save count
        post.saves_count = F('saves_count') - 1
        post.save()
        post.refresh_from_db()
        
        # Update engagement score
        post.calculate_engagement_score()
        
        return JsonResponse({
            'status': 'success', 
            'action': 'unsaved',
            'saves_count': post.saves_count
        })

@login_required
@require_POST
def add_comment_view(request, pk):
    """
    View for adding a comment to a post
    """
    post = get_object_or_404(Post, pk=pk)
    
    # Check if user is blocked
    is_blocked = BlockedUser.objects.filter(
        (Q(user=request.user) & Q(blocked_user=post.user)) | 
        (Q(user=post.user) & Q(blocked_user=request.user))
    ).exists()
    
    if is_blocked:
        return JsonResponse({'status': 'error', 'message': 'You cannot comment on this post'})
    
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.user = request.user
        comment.post = post
        
        # Check for parent comment (reply)
        parent_id = request.POST.get('parent_id')
        if parent_id:
            try:
                parent_comment = Comment.objects.get(id=parent_id, post=post)
                comment.parent = parent_comment
            except Comment.DoesNotExist:
                pass
        
        comment.save()
        
        # Increment comment count
        post.comments_count = F('comments_count') + 1
        post.save()
        post.refresh_from_db()
        
        # Update engagement score
        post.calculate_engagement_score()
        
        # Create notification for post owner
        if post.user != request.user:
            create_notification(
                recipient=post.user,
                sender=request.user,
                notification_type='comment',
                text=f"{request.user.username} commented on your post",
                content_id=str(post.id)
            )
        
        # Create notification for parent comment owner (if reply)
        if comment.parent and comment.parent.user != request.user and comment.parent.user != post.user:
            create_notification(
                recipient=comment.parent.user,
                sender=request.user,
                notification_type='comment',
                text=f"{request.user.username} replied to your comment",
                content_id=str(post.id)
            )
        
        # Process mentions in comment
        mentions = re.findall(r'@(\w+)', comment.text)
        for username in mentions:
            try:
                mentioned_user = User.objects.get(username=username)
                # Don't notify yourself or users already notified
                if mentioned_user != request.user and mentioned_user != post.user and (not comment.parent or mentioned_user != comment.parent.user):
                    create_notification(
                        recipient=mentioned_user,
                        sender=request.user,
                        notification_type='mention',
                        text=f"{request.user.username} mentioned you in a comment",
                        content_id=str(post.id)
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
                'comments_count': post.comments_count
            })
        
        return redirect('posts:detail', pk=post.pk)
    
    # If form is invalid
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'error',
            'errors': form.errors
        }, status=400)
    
    messages.error(request, "Error adding comment")
    return redirect('posts:detail', pk=post.pk)

@login_required
@require_POST
def delete_comment_view(request, pk):
    """
    View for deleting a comment
    """
    comment = get_object_or_404(Comment, pk=pk)
    
    # Check if user is the comment owner or post owner
    if comment.user != request.user and comment.post.user != request.user:
        return HttpResponseForbidden("You cannot delete this comment")
    
    post = comment.post
    
    # Delete comment
    comment.delete()
    
    # Decrement comment count
    post.comments_count = F('comments_count') - 1
    post.save()
    post.refresh_from_db()
    
    # Update engagement score
    post.calculate_engagement_score()
    
    # For AJAX requests
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'comments_count': post.comments_count
        })
    
    messages.success(request, "Comment deleted successfully")
    return redirect('posts:detail', pk=post.pk)

@login_required
@require_POST
def like_comment_view(request, pk):
    """
    AJAX view for liking/unliking a comment
    """
    comment = get_object_or_404(Comment, pk=pk)
    
    # Check if user is blocked
    is_blocked = BlockedUser.objects.filter(
        (Q(user=request.user) & Q(blocked_user=comment.user)) | 
        (Q(user=comment.user) & Q(blocked_user=request.user))
    ).exists()
    
    if is_blocked:
        return JsonResponse({'status': 'error', 'message': 'You cannot interact with this comment'})
    
    # Check if comment is already liked
    like, created = CommentLike.objects.get_or_create(user=request.user, comment=comment)
    
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
                notification_type='comment_like',
                text=f"{request.user.username} liked your comment",
                content_id=str(comment.post.id)
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
def user_posts_view(request, username):
    """
    View for displaying a user's posts
    """
    user = get_object_or_404(User, username=username)
    
    # Check if user is blocked
    is_blocked = BlockedUser.objects.filter(
        (Q(user=request.user) & Q(blocked_user=user)) | 
        (Q(user=user) & Q(blocked_user=request.user))
    ).exists()
    
    if is_blocked:
        return HttpResponseForbidden("You cannot view this user's posts")
    
    # Check if profile is private and user is not following
    if user.is_private and user != request.user:
        is_following = Follow.objects.filter(follower=request.user, following=user).exists()
        if not is_following:
            return HttpResponseForbidden("This account is private")
    
    # Get user's posts
    posts = Post.objects.filter(
        user=user,
        is_archived=False,
        is_hidden=False
    ).order_by('-created_at')
    
    # Paginate posts
    paginator = Paginator(posts, 12)  # Show in grid layout
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'profile_user': user,
        'posts': page_obj,
    }
    
    # For AJAX requests, return JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        post_data = []
        for post in page_obj:
            # Get first media for thumbnail
            first_media = post.media_files.first()
            post_data.append({
                'id': str(post.id),
                'thumbnail': first_media.file.url if first_media else None,
                'media_type': first_media.media_type if first_media else None,
                'likes_count': post.likes_count,
                'comments_count': post.comments_count,
                'post_type': post.post_type,
            })
        
        return JsonResponse({
            'posts': post_data,
            'has_next': page_obj.has_next(),
        })
    
    return render(request, 'posts/user_posts.html', context)

@login_required
def saved_posts_view(request):
    """
    View for displaying a user's saved posts
    """
    # Get saved posts
    saved = SavedPost.objects.filter(user=request.user).order_by('-created_at')
    
    # Get the actual posts
    posts = Post.objects.filter(
        id__in=saved.values_list('post_id', flat=True),
        is_archived=False,
        is_hidden=False
    ).select_related('user').prefetch_related('media_files')
    
    # Paginate posts
    paginator = Paginator(posts, 12)  # Show in grid layout
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'posts': page_obj,
    }
    
    # For AJAX requests, return JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        post_data = []
        for post in page_obj:
            # Get first media for thumbnail
            first_media = post.media_files.first()
            post_data.append({
                'id': str(post.id),
                'user': {
                    'username': post.user.username,
                },
                'thumbnail': first_media.file.url if first_media else None,
                'media_type': first_media.media_type if first_media else None,
                'likes_count': post.likes_count,
                'comments_count': post.comments_count,
                'post_type': post.post_type,
            })
        
        return JsonResponse({
            'posts': post_data,
            'has_next': page_obj.has_next(),
        })
    
    return render(request, 'posts/saved_posts.html', context)
