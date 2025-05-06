from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    path('', views.search_view, name='search'),
    path('hashtag/<str:name>/', views.hashtag_view, name='hashtag'),
    path('history/', views.search_history_view, name='history'),
    path('history/clear/', views.clear_search_history, name='clear_history'),
    path('trending/', views.trending_view, name='trending'),
    path('explore/', views.explore_view, name='explore'),
]
