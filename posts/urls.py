from django.urls import path
from . import views

app_name = 'posts'

urlpatterns = [
    # Feed and explore
    path('', views.feed_view, name='feed'),
    path('explore/', views.explore_view, name='explore'),
    
    # Post CRUD
    path('create/', views.create_post_view, name='create'),
    path('<uuid:pk>/', views.post_detail_view, name='detail'),
    path('<uuid:pk>/edit/', views.edit_post_view, name='edit'),
    path('<uuid:pk>/delete/', views.delete_post_view, name='delete'),
    
    # Post interactions
    path('<uuid:pk>/like/', views.like_post_view, name='like'),
    path('<uuid:pk>/save/', views.save_post_view, name='save'),
    path('<uuid:pk>/comment/', views.add_comment_view, name='comment'),
    
    # Comment interactions
    path('comment/<uuid:pk>/delete/', views.delete_comment_view, name='delete_comment'),
    path('comment/<uuid:pk>/like/', views.like_comment_view, name='like_comment'),
    
    # User posts
    path('user/<str:username>/', views.user_posts_view, name='user_posts'),
    path('saved/', views.saved_posts_view, name='saved_posts'),
]
