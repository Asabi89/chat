from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('explore/', views.ExploreView.as_view(), name='explore'),
    path('feedback/', views.FeedbackCreateView.as_view(), name='feedback'),
    path('feedback/success/', views.FeedbackSuccessView.as_view(), name='feedback_success'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('privacy/', views.PrivacyPolicyView.as_view(), name='privacy'),
    path('terms/', views.TermsOfServiceView.as_view(), name='terms'),
    path('log-activity/', views.activity_logger, name='log_activity'),
]
