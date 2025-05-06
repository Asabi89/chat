from django.urls import path
from . import views

app_name = 'reels'

urlpatterns = [
    # Reels feed
    path('', views.reels_feed_view, name='feed'),
    
    # Reel CRUD
    path('create/', views.create_reel_view, name='create'),
    path('<uuid:pk>/', views.reel_detail_view, name='detail'),
    path('<uuid:pk>/edit/', views.edit_reel_view, name='edit'),
    path('<uuid:pk>/delete/', views.delete_reel_view, name='delete'),
    
    # Reel interactions
    path('<uuid:pk>/like/', views.like_reel_view, name='like'),
    path('<uuid:pk>/save/', views.save_reel_view, name='save'),
    path('<uuid:pk>/comment/', views.add_comment_view, name='comment'),
    path('<uuid:pk>/share/', views.share_reel_view, name='share'),
    
    # Comment interactions
    path('comment/<int:pk>/delete/', views.delete_comment_view, name='delete_comment'),
    path('comment/<int:pk>/like/', views.like_comment_view, name='like_comment'),
    
    # User reels
    path('user/<str:username>/', views.user_reels_view, name='user_reels'),
    path('saved/', views.saved_reels_view, name='saved_reels'),
]
