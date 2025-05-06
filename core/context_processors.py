from django.conf import settings
from django.utils import timezone

def global_context(request):
    """
    Add global context data to be accessible in all templates.
    This includes app settings, user info, and Tailwind CSS classes.
    """
    # Try to get app settings from database if available
    app_settings = {}
    try:
        from analytics.models import AppSetting
        # Only include public settings
        for setting in AppSetting.objects.filter(is_public=True):
            app_settings[setting.key] = setting.value
    except:
        # If analytics app is not installed or there's an error
        pass
    
    # Tailwind CSS classes for common UI elements
    tailwind = {
        # Base styles
        'body': 'bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100',
        
        # Container styles
        'container': 'max-w-7xl mx-auto px-4 sm:px-6 lg:px-8',
        
        # Card styles
        'card': 'bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden',
        'card_header': 'px-4 py-5 border-b border-gray-200 dark:border-gray-700 sm:px-6',
        'card_body': 'px-4 py-5 sm:p-6',
        'card_footer': 'px-4 py-4 sm:px-6 bg-gray-50 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700',
        
        # Button styles
        'btn_primary': 'inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500',
        'btn_secondary': 'inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500',
        'btn_danger': 'inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500',
        
        # Form styles
        'input': 'shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md',
        'select': 'mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md',
        'checkbox': 'focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 dark:border-gray-600 dark:bg-gray-700 rounded',
        'textarea': 'shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md',
        
        # Navigation
        'nav': 'bg-white dark:bg-gray-800 shadow',
        'nav_link': 'text-gray-500 dark:text-gray-300 hover:text-gray-700 dark:hover:text-white px-3 py-2 rounded-md text-sm font-medium',
        'nav_link_active': 'text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 px-3 py-2 rounded-md text-sm font-medium',
        
        # Tables
        'table': 'min-w-full divide-y divide-gray-200 dark:divide-gray-700',
        'table_head': 'bg-gray-50 dark:bg-gray-700',
        'table_th': 'px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider',
        'table_body': 'bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700',
        'table_td': 'px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300',
        
        # Alerts
        'alert_success': 'bg-green-50 dark:bg-green-900 border-l-4 border-green-400 p-4',
        'alert_info': 'bg-blue-50 dark:bg-blue-900 border-l-4 border-blue-400 p-4',
        'alert_warning': 'bg-yellow-50 dark:bg-yellow-900 border-l-4 border-yellow-400 p-4',
        'alert_error': 'bg-red-50 dark:bg-red-900 border-l-4 border-red-400 p-4',
        
        # Badges
        'badge': 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
        'badge_gray': 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200',
        'badge_red': 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200',
        'badge_green': 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200',
        'badge_blue': 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200',
        
        # Utility classes
        'divider': 'border-t border-gray-200 dark:border-gray-700',
        'avatar': 'h-10 w-10 rounded-full',
        'avatar_sm': 'h-8 w-8 rounded-full',
        'avatar_lg': 'h-14 w-14 rounded-full',
    }
    
    # Application info
    app_info = {
        'name': getattr(settings, 'APP_NAME', 'NoChat'),
        'version': getattr(settings, 'APP_VERSION', '1.0.0'),
        'environment': getattr(settings, 'ENVIRONMENT', 'production'),
        'debug': settings.DEBUG,
        'current_year': timezone.now().year,
    }
    
    # User-specific context
    user_context = {}
    if request.user.is_authenticated:
        # Add user-specific data
        user_context = {
            'has_unread_notifications': False,  # Placeholder, replace with actual logic
            'has_unread_messages': False,       # Placeholder, replace with actual logic
        }
        
        # Try to get notification count if notifications app is available
        try:
            from notifications.models import Notification
            user_context['unread_notifications_count'] = Notification.objects.filter(
                recipient=request.user, 
                is_read=False
            ).count()
            user_context['has_unread_notifications'] = user_context['unread_notifications_count'] > 0
        except:
            pass
        
        # Try to get unread messages count if messaging app is available
        try:
            from messaging.models import Message, MessageRead, Conversation
            # Get all conversations the user is part of
            conversations = Conversation.objects.filter(participants=request.user)
            
            # Count unread messages
            unread_count = 0
            for conv in conversations:
                # Get all messages in this conversation
                messages = Message.objects.filter(conversation=conv)
                # Exclude messages sent by the user
                messages = messages.exclude(sender=request.user)
                # Get IDs of messages read by the user
                read_message_ids = MessageRead.objects.filter(
                    user=request.user,
                    message__in=messages
                ).values_list('message_id', flat=True)
                # Count unread messages
                unread_count += messages.exclude(id__in=read_message_ids).count()
            
            user_context['unread_messages_count'] = unread_count
            user_context['has_unread_messages'] = unread_count > 0
        except:
            pass
    
    return {
        'tailwind': tailwind,
        'app_info': app_info,
        'app_settings': app_settings,
        'user_context': user_context,
    }
