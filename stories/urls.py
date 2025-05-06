from django.urls import path
from . import views

app_name = 'stories'

urlpatterns = [
    # Story feed
    path('', views.story_feed, name='feed'),
    
    # Create, view, and delete stories
    path('create/', views.create_story, name='create'),
    path('view/<uuid:pk>/', views.view_story, name='view'),
    path('delete/<uuid:pk>/', views.delete_story, name='delete'),
    
    # Story reactions
    path('view/<uuid:pk>/react/', views.react_to_story, name='react'),
    path('view/<uuid:pk>/unreact/', views.delete_reaction, name='unreact'),
    
    # Story viewers
    path('view/<uuid:pk>/viewers/', views.story_viewers, name='viewers'),
    
    # User stories
    path('user/<str:username>/', views.user_stories, name='user_stories'),
    
    # Highlights
    path('user/<str:username>/highlights/', views.highlights, name='highlights'),
    path('user/<str:username>/highlights/<int:pk>/', views.view_highlight, name='view_highlight'),
    path('highlights/create/', views.create_highlight, name='create_highlight'),
    path('highlights/<int:pk>/edit/', views.edit_highlight, name='edit_highlight'),
    path('highlights/<int:pk>/delete/', views.delete_highlight, name='delete_highlight'),
]
