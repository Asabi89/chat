from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.urls import reverse
from posts.models import Post, Media, Like, SavedPost
from .models import User, Profile, Follow, BlockedUser
from .forms import (
    CustomUserCreationForm, 
    CustomAuthenticationForm, 
    ProfileEditForm, 
    AccountSettingsForm,
    CustomPasswordChangeForm
)
def register_view(request):
    """
    User registration view
    """
    if request.user.is_authenticated:
        return redirect('core:home')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Don't log the user in automatically
            messages.success(request, "Registration successful! Please log in to continue.")
            # Redirect to login page instead of home
            return redirect('accounts:login')  # Make sure 'accounts:login' is the correct URL name
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """
    User login view
    """
    if request.user.is_authenticated:
        return redirect('core:home')
        
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Update last_active in profile
                user.profile.save()  # This will update the last_active field via auto_now
                messages.success(request, f"Welcome back, {user.username}!")
                
                # Redirect to the page user was trying to access, or home
                next_page = request.GET.get('next')
                return redirect(next_page if next_page else 'core:home')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """
    User logout view
    """
    if request.method == 'POST':
        logout(request)
        messages.success(request, "You have been logged out successfully.")
    return redirect('accounts:login')


@login_required
def profile_view(request, username):
    """
    User profile view
    """
    user = get_object_or_404(User, username=username)
    
    # Check if the profile user has blocked the current user
    if BlockedUser.objects.filter(user=user, blocked_user=request.user).exists():
        return render(request, 'accounts/blocked.html', {'blocked_by': user})
    
    # Check if current user has blocked the profile user
    is_blocked = BlockedUser.objects.filter(user=request.user, blocked_user=user).exists()
    
    # Check if the profile is private and the current user is not following
    is_following = Follow.objects.filter(follower=request.user, following=user).exists()
    can_view = not user.is_private or user == request.user or is_following
    
    # Get posts if the user can view the profile
    posts = []
    if can_view:
        # Import here to avoid circular import
        from posts.models import Post
        posts = Post.objects.filter(user=user).order_by('-created_at')
        
        # Increment profile views if not the profile owner
        if user != request.user:
            user.profile.profile_views += 1
            user.profile.save()
    
    # Paginate posts
    paginator = Paginator(posts, 12)  # Show 12 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'profile_user': user,
        'posts': page_obj,
        'is_following': is_following,
        'is_blocked': is_blocked,
        'can_view': can_view,
    }
    
    return render(request, 'accounts/profile.html', context)

from posts.models import Post, Media
import uuid

@login_required
def edit_profile_view(request):
    """
    Edit user profile view
    """
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            # Check if profile picture is being updated
            if 'profile_picture' in request.FILES:
                # Create a new post for the profile picture update
                profile_pic = request.FILES['profile_picture']
                
                # Create the post
                post = Post.objects.create(
                    id=uuid.uuid4(),
                    user=request.user,
                    caption="Updated my profile picture",
                    post_type='image'
                )
                
                # Create the media for the post
                media = Media.objects.create(
                    post=post,
                    file=profile_pic,
                    media_type='image',
                    order=0
                )
                
                # Save the post reference to the user
                user = form.save(commit=False)
                user.profile_picture_post = post
                user.save()
                
                # Update user's post count
                request.user.profile.posts_count = request.user.profile.posts_count + 1
                request.user.profile.save()
                
                messages.success(request, "Your profile has been updated successfully and a post has been created.")
            else:
                form.save()
                messages.success(request, "Your profile has been updated successfully.")
                
            return redirect('accounts:profile', username=request.user.username)
    else:
        form = ProfileEditForm(instance=request.user)
    
    return render(request, 'accounts/edit_profile.html', {'form': form})


@login_required
def account_settings_view(request):
    """
    Account settings view
    """
    if request.method == 'POST':
        form = AccountSettingsForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your account settings have been updated successfully.")
            return redirect('accounts:settings')
    else:
        form = AccountSettingsForm(instance=request.user)
    
    return render(request, 'accounts/settings.html', {'form': form})



@login_required
def change_password_view(request):
    """
    Change password view
    """
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            # Update session to prevent logout
            login(request, request.user)
            messages.success(request, "Your password has been changed successfully.")
            return redirect('accounts:settings')
    else:
        form = CustomPasswordChangeForm(request.user)
    
    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
def followers_view(request, username):
    """View to show user's followers"""
    user = get_object_or_404(User, username=username)
    
    # Check if the profile is private and the current user is not following
    is_following = Follow.objects.filter(follower=request.user, following=user).exists()
    can_view = not user.is_private or user == request.user or is_following
    
    if not can_view:
        return HttpResponseForbidden("This account is private")
    
    followers = Follow.objects.filter(following=user).select_related('follower')
    
    # Add is_followed property to each follower object
    for follow in followers:
        follow.is_followed = Follow.objects.filter(
            follower=request.user, 
            following=follow.follower
        ).exists()
    
    context = {
        'profile_user': user,
        'followers': followers,
    }
    return render(request, 'accounts/followers.html', context)

@login_required
def following_view(request, username):
    """View to show users that a user is following"""
    user = get_object_or_404(User, username=username)
    
    # Check if the profile is private and the current user is not following
    is_following = Follow.objects.filter(follower=request.user, following=user).exists()
    can_view = not user.is_private or user == request.user or is_following
    
    if not can_view:
        return HttpResponseForbidden("This account is private")
    
    following = Follow.objects.filter(follower=user).select_related('following')
    
    # Add is_followed property to each following object
    for follow in following:
        follow.is_followed = Follow.objects.filter(
            follower=request.user, 
            following=follow.following
        ).exists()
    
    context = {
        'profile_user': user,
        'following': following,
    }
    return render(request, 'accounts/following.html', context)


@login_required
@require_POST
def follow_toggle_view(request, username):
    """
    AJAX view to follow/unfollow a user
    """
    user_to_follow = get_object_or_404(User, username=username)
    
    # Can't follow yourself
    if request.user == user_to_follow:
        return JsonResponse({'status': 'error', 'message': 'You cannot follow yourself'}, status=400)
    
    # Check if blocked
    if BlockedUser.objects.filter(
        Q(user=request.user, blocked_user=user_to_follow) | 
        Q(user=user_to_follow, blocked_user=request.user)
    ).exists():
        return JsonResponse({'status': 'error', 'message': 'Unable to follow this user'}, status=400)
    
    # Check if already following
    follow, created = Follow.objects.get_or_create(follower=request.user, following=user_to_follow)
    
    if created:
        # Increment followers count
        user_to_follow.profile.followers_count += 1
        user_to_follow.profile.save()
        
        # Increment following count
        request.user.profile.following_count += 1
        request.user.profile.save()
        
        # Create notification (will be implemented in notifications app)
        from notifications.models import Notification
        Notification.objects.create(
            recipient=user_to_follow,
        sender=request.user,
        notification_type='follow',
        )
        
        return JsonResponse({'status': 'following'})
    else:
                # Unfollow
        follow.delete()
        
        # Decrement followers count
        user_to_follow.profile.followers_count = max(0, user_to_follow.profile.followers_count - 1)
        user_to_follow.profile.save()
        
        # Decrement following count
        request.user.profile.following_count = max(0, request.user.profile.following_count - 1)
        request.user.profile.save()
        
        return JsonResponse({'status': 'not_following'})


@login_required
@require_POST
def block_toggle_view(request, username):
    """
    AJAX view to block/unblock a user
    """
    user_to_block = get_object_or_404(User, username=username)
    
    # Can't block yourself
    if request.user == user_to_block:
        return JsonResponse({'status': 'error', 'message': 'You cannot block yourself'}, status=400)
    
    # Check if already blocked
    block, created = BlockedUser.objects.get_or_create(user=request.user, blocked_user=user_to_block)
    
    if created:
        # If the user was following the blocked user, remove the follow
        follow = Follow.objects.filter(follower=request.user, following=user_to_block).first()
        if follow:
            follow.delete()
            # Update counts
            request.user.profile.following_count = max(0, request.user.profile.following_count - 1)
            request.user.profile.save()
            user_to_block.profile.followers_count = max(0, user_to_block.profile.followers_count - 1)
            user_to_block.profile.save()
        
        # If the blocked user was following the user, remove the follow
        follow = Follow.objects.filter(follower=user_to_block, following=request.user).first()
        if follow:
            follow.delete()
            # Update counts
            user_to_block.profile.following_count = max(0, user_to_block.profile.following_count - 1)
            user_to_block.profile.save()
            request.user.profile.followers_count = max(0, request.user.profile.followers_count - 1)
            request.user.profile.save()
        
        return JsonResponse({'status': 'blocked'})
    else:
        # Unblock
        block.delete()
        return JsonResponse({'status': 'unblocked'})


@login_required
def blocked_users_view(request):
    """
    View to show users that the current user has blocked
    """
    blocked_users = BlockedUser.objects.filter(user=request.user).select_related('blocked_user')
    
    context = {
        'blocked_users': blocked_users,
    }
    
    return render(request, 'accounts/blocked_users.html', context)


@login_required
def search_users_view(request):
    """
    View to search for users
    """
    query = request.GET.get('q', '')
    users = []
    
    if query:
        # Get users that match the query and are not blocked
        blocked_users = BlockedUser.objects.filter(user=request.user).values_list('blocked_user_id', flat=True)
        blocked_by = BlockedUser.objects.filter(blocked_user=request.user).values_list('user_id', flat=True)
        
        users = User.objects.filter(
            Q(username__icontains=query) | 
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query)
        ).exclude(
            Q(id__in=blocked_users) | 
            Q(id__in=blocked_by) | 
            Q(id=request.user.id)
        )[:20]  # Limit to 20 results
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Return JSON for AJAX requests
        user_list = []
        for user in users:
            user_list.append({
                'id': user.id,
                'username': user.username,
                'full_name': user.get_full_name(),
                'profile_picture': user.profile_picture.url,
                'profile_url': reverse('accounts:profile', kwargs={'username': user.username}),
            })
        return JsonResponse({'users': user_list})
    
    context = {
        'query': query,
        'users': users,
    }
    
    return render(request, 'accounts/search_users.html', context)


@login_required
def suggested_users_view(request):
    """
    View to get suggested users to follow
    """
    # Get users that the current user is following
    following = Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
    
    # Get users that are blocked or have blocked the current user
    blocked_users = BlockedUser.objects.filter(user=request.user).values_list('blocked_user_id', flat=True)
    blocked_by = BlockedUser.objects.filter(blocked_user=request.user).values_list('user_id', flat=True)
    
    # Get users with similar interests
    user_interests = request.user.interests.all()
    
    # Find users with similar interests who the current user is not following
    suggested_users = User.objects.filter(
        interests__in=user_interests
    ).exclude(
        Q(id=request.user.id) | 
        Q(id__in=following) | 
        Q(id__in=blocked_users) | 
        Q(id__in=blocked_by)
    ).annotate(
        common_interests=Count('interests', filter=Q(interests__in=user_interests))
    ).order_by('-common_interests', '-profile__followers_count')[:10]
    
    # If not enough users found, add some popular users
    if suggested_users.count() < 10:
        more_users = User.objects.exclude(
            Q(id=request.user.id) | 
            Q(id__in=following) | 
            Q(id__in=blocked_users) | 
            Q(id__in=blocked_by) | 
            Q(id__in=suggested_users.values_list('id', flat=True))
        ).order_by('-profile__followers_count')[:10-suggested_users.count()]
        
        suggested_users = list(suggested_users) + list(more_users)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Return JSON for AJAX requests
        user_list = []
        for user in suggested_users:
            user_list.append({
                'id': user.id,
                'username': user.username,
                'full_name': user.get_full_name(),
                'profile_picture': user.profile_picture.url,
                'profile_url': reverse('accounts:profile', kwargs={'username': user.username}),
                'is_verified': user.is_verified,
            })
        return JsonResponse({'users': user_list})
    
    context = {
        'suggested_users': suggested_users,
    }
    
    return render(request, 'accounts/suggested_users.html', context)



@login_required
def profile_picture_view(request, username):
    """
    View for displaying a user's profile picture in gallery mode
    """
    user = get_object_or_404(User, username=username)
    
    # Check if the profile user has blocked the current user
    if BlockedUser.objects.filter(user=user, blocked_user=request.user).exists():
        return render(request, 'accounts/blocked.html', {'blocked_by': user})
    
    # Check if current user has blocked the profile user
    is_blocked = BlockedUser.objects.filter(user=request.user, blocked_user=user).exists()
    
    # Check if the profile is private and the current user is not following
    is_following = Follow.objects.filter(follower=request.user, following=user).exists()
    can_view = not user.is_private or user == request.user or is_following
    
    if not can_view:
        return HttpResponseForbidden("This account is private")
    
    # Get profile pictures history from posts
    from posts.models import Post, Media, Like, SavedPost
    
    # Get all user's posts with images to use as profile picture history
    profile_pictures = Post.objects.filter(
        user=user,
        is_archived=False,
        is_hidden=False,
    ).exclude(media_files__isnull=True).order_by('-created_at')[:10]  # Limit to recent 10
    
    # Create a list of media items for the gallery
    gallery_items = []
    for post in profile_pictures:
        # Get the first media file for each post
        media = post.media_files.first()
        if media:
            gallery_items.append({
                'id': str(post.id),
                'file': media.file,
                'created_at': post.created_at,
                'likes_count': post.likes_count,
                'comments_count': post.comments_count,
                'caption': post.caption
            })
    
    # Add current profile picture if not already in the list
    current_picture_in_list = False
    for item in gallery_items:
        if str(user.profile_picture.url).endswith(str(item['file'])):
            current_picture_in_list = True
            break
    
    if not current_picture_in_list and user.profile_picture_post:
        # Use the profile picture post if available
        media = user.profile_picture_post.media_files.first()
        if media:
            gallery_items.insert(0, {
                'id': str(user.profile_picture_post.id),
                'file': media.file,
                'created_at': user.profile_picture_post.created_at,
                'likes_count': user.profile_picture_post.likes_count,
                'comments_count': user.profile_picture_post.comments_count,
                'caption': user.profile_picture_post.caption
            })
    elif not current_picture_in_list:
        # Create a dummy post object for the current profile picture
        from django.utils import timezone
        current_picture = {
            'id': 'profile-pic',
            'file': user.profile_picture,
            'created_at': timezone.now(),
            'likes_count': 0,
            'comments_count': 0,
            'caption': ''
        }
        gallery_items.insert(0, current_picture)
    
    # Check if current picture is liked/saved
    is_liked = False
    is_saved = False
    if user.profile_picture_post:
        is_liked = Like.objects.filter(user=request.user, post=user.profile_picture_post).exists()
        is_saved = SavedPost.objects.filter(user=request.user, post=user.profile_picture_post).exists()
    
    context = {
        'profile_user': user,
        'gallery_items': gallery_items,
        'is_liked': is_liked,
        'is_saved': is_saved,
        'is_following': is_following,
        'is_blocked': is_blocked,
    }
    
    return render(request, 'accounts/profile_picture.html', context)

@login_required
@require_POST
def delete_profile_picture_view(request):
    """
    View to delete profile picture
    """
    user = request.user
    
    # Check if user has a profile picture post
    if user.profile_picture_post:
        # Archive the post instead of deleting it
        post = user.profile_picture_post
        post.is_archived = True
        post.save()
        
        # Update user's post count
        user.profile.posts_count = max(0, user.profile.posts_count - 1)
        user.profile.save()
        
        # Remove reference to the post
        user.profile_picture_post = None
    
    # Set default profile picture
    user.profile_picture = 'default_profile.png'
    user.save()
    
    messages.success(request, "Profile picture has been removed.")
    return redirect('accounts:profile', username=user.username)


def privacy_security_view(request):
    return render(request, 'accounts/privacy_security.html') 

def notifications_settings(request):
    return render(request, 'accounts/notification_settings.html')       

def activity_view(request):
    return render(request, 'accounts/activity.html')

def data_storage_view(request):
    return render(request, 'accounts/data_storage.html')

def deactivate_view(request):
    return render(request, 'accounts/deactivate.html')

def delete_view(request):
    return render(request, 'accounts/delete.html')