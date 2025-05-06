from django import forms
from .models import NotificationSetting

class NotificationSettingsForm(forms.ModelForm):
    """
    Form for editing notification settings
    """
    class Meta:
        model = NotificationSetting
        exclude = ['user']
        
        widgets = {
            # Push notification widgets
            'likes': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'comments': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'comment_likes': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'follows': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'follow_requests': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'messages': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'mentions': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tags': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'story_views': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'story_reactions': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'post_shares': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            
            # Email notification widgets
            'email_likes': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_comments': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_follows': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_messages': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_system': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Group fields for better organization in the template
        self.push_notification_fields = [
            'likes', 'comments', 'comment_likes', 'follows', 'follow_requests',
            'messages', 'mentions', 'tags', 'story_views', 'story_reactions', 'post_shares'
        ]
        
        self.email_notification_fields = [
            'email_likes', 'email_comments', 'email_follows', 'email_messages', 'email_system'
        ]
