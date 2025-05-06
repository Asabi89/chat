from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.http import JsonResponse
from posts.models import Post
from stories.models import Story
from accounts.models import User, Follow
from .models import Feedback
from .forms import FeedbackForm
import datetime
class HomeView(LoginRequiredMixin, TemplateView):
    """Home page view showing feed of posts from followed users"""
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get IDs of users the current user follows
        following_ids = user.following.values_list('following_id', flat=True)
        
        # Get posts from followed users and the user's own posts
        posts = Post.objects.filter(
            Q(user_id__in=following_ids) | Q(user=user)
        ).select_related('user').prefetch_related('media_files', 'likes').order_by('-created_at')[:20]
        
        # Get active stories from followed users
        now = datetime.datetime.now()
        
        # Instead of using distinct('user'), use a different approach
        # First, get the latest story for each user
        latest_stories_by_user = {}
        for story in Story.objects.filter(
            user_id__in=following_ids,
            expires_at__gt=now
        ).select_related('user').order_by('-created_at'):
            if story.user_id not in latest_stories_by_user:
                latest_stories_by_user[story.user_id] = story
        
        # Convert the dictionary values to a list
        stories = list(latest_stories_by_user.values())
        
        # Get suggested users to follow
        suggested_users = User.objects.exclude(
            Q(id=user.id) | Q(id__in=following_ids)
        ).annotate(
            followers_count=Count('followers')
        ).order_by('-followers_count')[:5]
        
        context.update({
            'posts': posts,
            'stories': stories,
            'suggested_users': suggested_users,
        })
        
        return context


class ExploreView(LoginRequiredMixin, TemplateView):
    """
    Explore page showing popular and suggested content
    """
    template_name = 'core/explore.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get popular posts based on engagement score
        popular_posts = Post.objects.filter(
            is_archived=False,
            is_hidden=False
        ).order_by('-engagement_score')[:12]
        
        # Get trending reels
        trending_reels = Reel.objects.filter(
            is_archived=False,
            is_hidden=False
        ).order_by('-engagement_score')[:8]
        
        # Get trending hashtags
        trending_hashtags = TrendingHashtag.objects.filter(
            date=datetime.date.today()
        ).select_related('hashtag')[:10]
        
        context.update({
            'popular_posts': popular_posts,
            'trending_reels': trending_reels,
            'trending_hashtags': trending_hashtags,
        })
        return context


class FeedbackCreateView(LoginRequiredMixin, CreateView):
    """
    View for users to submit feedback or bug reports
    """
    model = Feedback
    form_class = FeedbackForm
    template_name = 'core/feedback.html'
    success_url = reverse_lazy('core:feedback_success')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class FeedbackSuccessView(LoginRequiredMixin, TemplateView):
    """
    Success page after submitting feedback
    """
    template_name = 'core/feedback_success.html'


class AboutView(TemplateView):
    """
    About page with information about the platform
    """
    template_name = 'core/about.html'


class PrivacyPolicyView(TemplateView):
    """
    Privacy policy page
    """
    template_name = 'core/privacy_policy.html'


class TermsOfServiceView(TemplateView):
    """
    Terms of service page
    """
    template_name = 'core/terms_of_service.html'


@login_required
def activity_logger(request):
    """
    AJAX endpoint to log user activity
    """
    if request.method == 'POST' and request.is_ajax():
        activity_type = request.POST.get('activity_type')
        content_id = request.POST.get('content_id', '')
        
        if activity_type:
            Activity.objects.create(
                user=request.user,
                activity_type=activity_type,
                content_id=content_id,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'}, status=400)
