from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    # Conversation views
    path('inbox/', views.inbox_view, name='inbox'),
    path('conversation/<uuid:conversation_id>/', views.conversation_view, name='conversation'),
    path('conversation/create/', views.create_conversation_view, name='create_conversation'),
    path('direct-message/<str:username>/', views.direct_message_view, name='direct_message'),
    
    # Message actions
    path('message/<uuid:message_id>/reaction/', views.message_reaction_view, name='message_reaction'),
    path('message/<uuid:message_id>/delete/', views.delete_message_view, name='delete_message'),
    path('message/<uuid:message_id>/edit/', views.edit_message_view, name='edit_message'),
    
    # Group conversation actions
    path('conversation/<uuid:conversation_id>/leave/', views.leave_group_view, name='leave_group'),
    path('conversation/<uuid:conversation_id>/add-participants/', views.add_participants_view, name='add_participants'),
    path('conversation/<uuid:conversation_id>/edit-group/', views.edit_group_view, name='edit_group'),
    
    # Utility endpoints
    path('conversation/<uuid:conversation_id>/mark-read/', views.mark_conversation_read_view, name='mark_conversation_read'),
    path('unread-count/', views.unread_count_view, name='unread_count'),
]
