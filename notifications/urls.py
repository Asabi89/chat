from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list_view, name='list'),
    path('settings/', views.notification_settings_view, name='settings'),
    path('mark-read/<uuid:notification_id>/', views.mark_notification_read_view, name='mark_read'),
    path('mark-all-read/', views.mark_all_read_view, name='mark_all_read'),
    path('delete/<uuid:notification_id>/', views.delete_notification_view, name='delete'),
    path('unread-count/', views.unread_count_view, name='unread_count'),
]
