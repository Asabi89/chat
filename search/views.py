from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Count, F
from django.utils import timezone
from django.core.paginator import Paginator

from .models import Hashtag, SearchHistory, TrendingHashtag
from accounts.models import User, Follow, BlockedUser
from posts.models import Post
from reels.models import Reel

import datetime

@login_required
def search_view(request):
    """
    Main search view
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'general')
    
    # Initialize results
    users = []
    hashtags = []
    posts = []
    reels = []
    
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
    
    if query:
        # Save search history
        SearchHistory.objects.create(
            user=request.user,
            query=query,
            search_type=search_type
        )
        
        # Search based on type
        if search_type == 'user' or search_type == 'general':
            users = User.objects.filter(
                Q(username__icontains=query) | 
                Q(first_name__icontains=query) | 
                Q(last_name__icontains=query)
            ).exclude(
                id__in=blocked_ids
            )[:20]
        
        if search_type == 'hashtag' or search_type == 'general':
            hashtags = Hashtag.objects.filter(
                name__icontains=query
            )[:20]
        
        if search_type == 'post' or search_type == 'general':
            posts = Post.objects.filter(
                Q(caption__icontains=query) |
                Q(location__icontains=query) |
                Q(hashtags__hashtag__name__icontains=query)
            ).exclude(
                Q(user__in=blocked_ids) |
                Q(is_archived=True) |
                Q(is_hidden=True)
            ).distinct()[:20]
        
        if search_type == 'reel' or search_type == 'general':
            reels = Reel.objects.filter(
                Q(caption__icontains=query) |
                Q(audio_track__icontains=query) |
                Q(audio_artist__icontains=query) |
                Q(hashtags__hashtag__name__icontains=query)
            ).exclude(
                Q(user__in=blocked_ids) |
                Q(is_archived=True) |
                Q(is_hidden=True)
            ).distinct()[:20]
    
    # Get trending hashtags
    trending_hashtags = TrendingHashtag.objects.filter(
        date=timezone.now().date()
    ).select_related('hashtag')[:10]
    
    # For AJAX requests, return JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'full_name': user.get_full_name(),
                'profile_picture': user.profile_picture.url,
                'is_verified': user.is_verified,
            })
        
        hashtags_data = []
        for hashtag in hashtags:
            hashtags_data.append({
                'id': hashtag.id,
                'name': hashtag.name,
                'post_count': hashtag.post_count,
            })
        
        posts_data = []
        for post in posts:
            posts_data.append({
                'id': post.id,
                'user': {
                    'username': post.user.username,
                    'profile_picture': post.user.profile_picture.url,
                },
                'caption': post.caption[:100] + '...' if len(post.caption) > 100 else post.caption,
                'likes_count': post.likes_count,
                'comments_count': post.comments_count,
            })
        
        reels_data = []
        for reel in reels:
            reels_data.append({
                'id': reel.id,
                'user': {
                    'username': reel.user.username,
                    'profile_picture': reel.user.profile_picture.url,
                },
                'caption': reel.caption[:100] + '...' if len(reel.caption) > 100 else reel.caption,
                'views_count': reel.views_count,
                'likes_count': reel.likes_count,
            })
        
        trending_data = []
        for trend in trending_hashtags:
            trending_data.append({
                'id': trend.hashtag.id,
                'name': trend.hashtag.name,
                'post_count_24h': trend.post_count_24h,
            })
        
        return JsonResponse({
            'users': users_data,
            'hashtags': hashtags_data,
            'posts': posts_data,
            'reels': reels_data,
            'trending': trending_data,
        })
    
    context = {
        'query': query,
        'search_type': search_type,
        'users': users,
        'hashtags': hashtags,
        'posts': posts,
        'reels': reels,
        'trending_hashtags': trending_hashtags,
    }
    
    return render(request, 'search/search.html', context)

@login_required
def hashtag_view(request, name):
    """
    View for hashtag detail page
    """
    hashtag = get_object_or_404(Hashtag, name=name)
    
    # Get posts with this hashtag
    posts = Post.objects.filter(
        hashtags__hashtag=hashtag,
        is_archived=False,
        is_hidden=False
    ).exclude(
        user__in=BlockedUser.objects.filter(
            Q(user=request.user) | Q(blocked_user=request.user)
        ).values_list('user', 'blocked_user')
    ).select_related('user').order_by('-created_at')
    
    # Get reels with this hashtag
    reels = Reel.objects.filter(
        hashtags__hashtag=hashtag,
        is_archived=False,
        is_hidden=False
    ).exclude(
        user__in=BlockedUser.objects.filter(
            Q(user=request.user) | Q(blocked_user=request.user)
        ).values_list('user', 'blocked_user')
    ).select_related('user').order_by('-created_at')
    
    # Increment view count for trending
    try:
        trending, created = TrendingHashtag.objects.get_or_create(
            hashtag=hashtag,
            date=timezone.now().date()
        )
        trending.view_count_24h = F('view_count_24h') + 1
        trending.save()
    except:
        pass
    
    # Paginate posts
    paginator = Paginator(posts, 12)  # Show 12 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'hashtag': hashtag,
        'posts': page_obj,
        'reels': reels[:12],  # Show first 12 reels
        'post_count': posts.count(),
        'reel_count': reels.count(),
    }
    
    return render(request, 'search/hashtag.html', context)

@login_required
def clear_search_history(request):
    """
    Clear user's search history
    """
    if request.method == 'POST':
        SearchHistory.objects.filter(user=request.user).delete()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
        
        return redirect('search:search')
    
    return redirect('search:search')

@login_required
def search_history_view(request):
    """
    View user's search history
    """
    history = SearchHistory.objects.filter(user=request.user)[:50]
    
    # For AJAX requests, return JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        history_data = []
        for item in history:
            history_data.append({
                'id': item.id,
                'query': item.query,
                'search_type': item.search_type,
                'created_at': item.created_at.isoformat(),
            })
        
        return JsonResponse({
            'history': history_data,
        })
    
    context = {
        'history': history,
    }
    
    return render(request, 'search/history.html', context)

@login_required
def trending_view(request):
    """
    View for trending hashtags and content
    """
    # Get trending hashtags
    trending_hashtags = TrendingHashtag.objects.filter(
        date=timezone.now().date()
    ).select_related('hashtag')[:20]
    
        # Get trending posts (last 24 hours)
    yesterday = timezone.now() - datetime.timedelta(days=1)
    trending_posts = Post.objects.filter(
        created_at__gte=yesterday,
        is_archived=False,
        is_hidden=False
    ).exclude(
        user__in=BlockedUser.objects.filter(
            Q(user=request.user) | Q(blocked_user=request.user)
        ).values_list('user', 'blocked_user')
    ).annotate(
        engagement=Count('likes') + Count('comments')*2 + Count('saved_by')*3
    ).order_by('-engagement')[:20]
    
    # Get trending reels (last 24 hours)
    trending_reels = Reel.objects.filter(
        created_at__gte=yesterday,
        is_archived=False,
        is_hidden=False
    ).exclude(
        user__in=BlockedUser.objects.filter(
            Q(user=request.user) | Q(blocked_user=request.user)
        ).values_list('user', 'blocked_user')
    ).order_by('-engagement_score')[:20]
    
    # For AJAX requests, return JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        hashtags_data = []
        for trend in trending_hashtags:
            hashtags_data.append({
                'id': trend.hashtag.id,
                'name': trend.hashtag.name,
                'post_count_24h': trend.post_count_24h,
                'view_count_24h': trend.view_count_24h,
                'engagement_score': trend.engagement_score,
            })
        
        posts_data = []
        for post in trending_posts:
            posts_data.append({
                'id': post.id,
                'user': {
                    'username': post.user.username,
                    'profile_picture': post.user.profile_picture.url,
                },
                'caption': post.caption[:100] + '...' if len(post.caption) > 100 else post.caption,
                'likes_count': post.likes_count,
                'comments_count': post.comments_count,
            })
        
        reels_data = []
        for reel in trending_reels:
            reels_data.append({
                'id': reel.id,
                'user': {
                    'username': reel.user.username,
                    'profile_picture': reel.user.profile_picture.url,
                },
                'caption': reel.caption[:100] + '...' if len(reel.caption) > 100 else reel.caption,
                'views_count': reel.views_count,
                'likes_count': reel.likes_count,
            })
        
        return JsonResponse({
            'hashtags': hashtags_data,
            'posts': posts_data,
            'reels': reels_data,
        })
    
    context = {
        'trending_hashtags': trending_hashtags,
        'trending_posts': trending_posts,
        'trending_reels': trending_reels,
    }
    
    return render(request, 'search/trending.html', context)

@login_required
def explore_view(request):
    """
    View for explore page (recommended content)
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
    
    # Get user interests (hashtags)
    user_interests = request.user.interests.all()
    
    # Get posts with hashtags that match user interests
    interest_posts = Post.objects.filter(
        hashtags__hashtag__in=user_interests,
        is_archived=False,
        is_hidden=False
    ).exclude(
        Q(user=request.user) |
        Q(user__in=blocked_ids)
    ).distinct()
    
    # Get posts from users that are followed by users the current user follows
    # (friends of friends)
    friends_of_friends = User.objects.filter(
        followers__follower__in=following
    ).exclude(
        Q(id__in=following) |
        Q(id=request.user.id) |
        Q(id__in=blocked_ids)
    ).values_list('id', flat=True)
    
    friend_posts = Post.objects.filter(
        user__in=friends_of_friends,
        is_archived=False,
        is_hidden=False
    )
    
    # Get popular posts (high engagement)
    popular_posts = Post.objects.filter(
        is_archived=False,
        is_hidden=False
    ).exclude(
        Q(user=request.user) |
        Q(user__in=blocked_ids) |
        Q(id__in=interest_posts.values_list('id', flat=True)) |
        Q(id__in=friend_posts.values_list('id', flat=True))
    ).annotate(
        engagement=Count('likes') + Count('comments')*2 + Count('saved_by')*3
    ).order_by('-engagement')[:50]
    
    # Combine and shuffle posts
    from itertools import chain
    import random
    
    all_posts = list(chain(interest_posts[:20], friend_posts[:20], popular_posts[:20]))
    random.shuffle(all_posts)
    
    # Get reels with similar logic
    interest_reels = Reel.objects.filter(
        hashtags__hashtag__in=user_interests,
        is_archived=False,
        is_hidden=False
    ).exclude(
        Q(user=request.user) |
        Q(user__in=blocked_ids)
    ).distinct()
    
    friend_reels = Reel.objects.filter(
        user__in=friends_of_friends,
        is_archived=False,
        is_hidden=False
    )
    
    popular_reels = Reel.objects.filter(
        is_archived=False,
        is_hidden=False
    ).exclude(
        Q(user=request.user) |
        Q(user__in=blocked_ids) |
        Q(id__in=interest_reels.values_list('id', flat=True)) |
        Q(id__in=friend_reels.values_list('id', flat=True))
    ).order_by('-engagement_score')[:50]
    
    all_reels = list(chain(interest_reels[:20], friend_reels[:20], popular_reels[:20]))
    random.shuffle(all_reels)
    
    # Paginate posts
    paginator = Paginator(all_posts, 12)  # Show 12 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'posts': page_obj,
        'reels': all_reels[:12],  # Show first 12 reels
    }
    
    # For AJAX requests, return JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        start = int(request.GET.get('start', 0))
        end = start + 12  # Load 12 posts at a time
        
        posts_data = []
        for post in all_posts[start:end]:
            posts_data.append({
                'id': post.id,
                'user': {
                    'username': post.user.username,
                    'profile_picture': post.user.profile_picture.url,
                },
                'caption': post.caption[:100] + '...' if len(post.caption) > 100 else post.caption,
                'likes_count': post.likes_count,
                'comments_count': post.comments_count,
            })
        
        return JsonResponse({
            'posts': posts_data,
            'has_more': end < len(all_posts),
        })
    
    return render(request, 'search/explore.html', context)
