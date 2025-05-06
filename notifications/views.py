from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone

from .models import Notification, NotificationSetting
from .forms import NotificationSettingsForm

@login_required
def notification_list_view(request):
    """
    View to display user's notifications
    """
    # Get all notifications for the user
    notifications = Notification.objects.filter(recipient=request.user)
    
    # Paginate notifications
    paginator = Paginator(notifications, 20)  # 20 notifications per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Mark notifications as read if requested
    if request.GET.get('mark_read') == 'true':
        unread_notifications = notifications.filter(is_read=False)
        unread_notifications.update(is_read=True)
    
    # For AJAX requests, return JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        notification_data = []
        for notification in page_obj:
            notification_data.append({
                'id': str(notification.id),
                'type': notification.notification_type,
                'text': notification.text,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat(),
                'sender': {
                    'username': notification.sender.username if notification.sender else None,
                    'profile_picture': notification.sender.profile_picture.url if notification.sender else None,
                } if notification.sender else None,
                'content_id': notification.content_id,
            })
        
        return JsonResponse({
            'notifications': notification_data,
            'has_next': page_obj.has_next(),
            'unread_count': notifications.filter(is_read=False).count(),
        })
    
    context = {
        'notifications': page_obj,
        'unread_count': notifications.filter(is_read=False).count(),
    }
    
    return render(request, 'notifications/notification_list.html', context)

@login_required
def notification_settings_view(request):
    """
    View to edit notification settings
    """
    # Get or create notification settings for the user
    notification_settings, created = NotificationSetting.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = NotificationSettingsForm(request.POST, instance=notification_settings)
        if form.is_valid():
            form.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success', 'message': 'Notification settings updated'})
            return redirect('notifications:settings')
    else:
        form = NotificationSettingsForm(instance=notification_settings)
    
    context = {
        'form': form,
    }
    
    return render(request, 'notifications/notification_settings.html', context)

@login_required
@require_POST
def mark_notification_read_view(request, notification_id):
    """
    AJAX view to mark a single notification as read
    """
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    
    return JsonResponse({
        'status': 'success',
        'notification_id': str(notification.id),
        'unread_count': Notification.objects.filter(recipient=request.user, is_read=False).count(),
    })

@login_required
@require_POST
def mark_all_read_view(request):
    """
    AJAX view to mark all notifications as read
    """
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    
    return JsonResponse({
        'status': 'success',
        'unread_count': 0,
    })

@login_required
@require_POST
def delete_notification_view(request, notification_id):
    """
    AJAX view to delete a notification
    """
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.delete()
    
    return JsonResponse({
        'status': 'success',
        'notification_id': str(notification_id),
        'unread_count': Notification.objects.filter(recipient=request.user, is_read=False).count(),
    })

@login_required
def unread_count_view(request):
    """
    AJAX view to get the count of unread notifications
    """
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    
    return JsonResponse({
        'unread_count': unread_count
    })
