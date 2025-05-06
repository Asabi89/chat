from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import CustomPasswordResetForm, CustomSetPasswordForm

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Password reset
    path('password-reset/', 
        auth_views.PasswordResetView.as_view(
            template_name='accounts/password_reset.html',
            form_class=CustomPasswordResetForm,
            email_template_name='accounts/password_reset_email.html',
            subject_template_name='accounts/password_reset_subject.txt',
        ), 
        name='password_reset'),
    path('password-reset/done/', 
        auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_done.html'
        ), 
        name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html',
            form_class=CustomSetPasswordForm,
        ), 
        name='password_reset_confirm'),
    path('password-reset-complete/', 
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html'
        ), 
        name='password_reset_complete'),
    
    # Profile
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
   
    path('settings/', views.account_settings_view, name='settings'),
    path('settings/password/', views.change_password_view, name='change_password'),
    path('profile/<str:username>/followers/', views.followers_view, name='followers'),
    path('profile/<str:username>/following/', views.following_view, name='following'),
    path('privacy-security/', views.privacy_security_view, name='privacy_security'),
    path('activity/', views.activity_view, name='activity'),
    path('data-storage/', views.data_storage_view, name='data_storage'),
    path('deactivate/', views.deactivate_view, name='deactivate'),
    path('delete/', views.delete_view, name='delete'),
    # Add these URL patterns to accounts/urls.py
    path('<str:username>/profile-picture/', views.profile_picture_view, name='profile_picture'),

    path('profile/delete-picture/', views.delete_profile_picture_view, name='delete_profile_picture'),

    # Follow/Block
    path('follow/<str:username>/', views.follow_toggle_view, name='follow_toggle'),
    path('block/<str:username>/', views.block_toggle_view, name='block_toggle'),
    path('blocked-users/', views.blocked_users_view, name='blocked_users'),
    path('notifications-settings/', views.notifications_settings, name='notification_settings'),
    # Search and suggestions
    path('search/', views.search_users_view, name='search_users'),
    path('suggested-users/', views.suggested_users_view, name='suggested_users'),
]
