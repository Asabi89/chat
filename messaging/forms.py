from django import forms
from .models import Message, Conversation

class MessageForm(forms.ModelForm):
    """
    Form for creating a new message
    """
    class Meta:
        model = Message
        fields = ['message_type', 'text', 'file', 'shared_content_id', 'latitude', 'longitude']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Type your message...', 'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control-file'}),
            'shared_content_id': forms.HiddenInput(),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['message_type'].widget = forms.HiddenInput()
        self.fields['message_type'].initial = 'text'
        # Make all fields except text optional
        for field in self.fields:
            if field != 'text':
                self.fields[field].required = False


class ConversationForm(forms.ModelForm):
    """
    Form for creating a new conversation
    """
    participants = forms.ModelMultipleChoiceField(
        queryset=None,  # Will be set in __init__
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    
    class Meta:
        model = Conversation
        fields = ['participants', 'is_group_chat', 'group_name', 'group_avatar']
        widgets = {
            'is_group_chat': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'group_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Group name'}),
            'group_avatar': forms.FileInput(attrs={'class': 'form-control-file'}),
        }
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make group fields optional
        self.fields['group_name'].required = False
        self.fields['group_avatar'].required = False
        
        # Set queryset to exclude the current user
        if user:
            from accounts.models import User
            from django.db.models import Q
            
            # Exclude users who have blocked the current user or been blocked by the current user
            blocked_users = User.objects.filter(
                Q(user_blocks__blocked_user=user) | Q(blocked_by__user=user)
            ).distinct()
            
            self.fields['participants'].queryset = User.objects.exclude(
                Q(id=user.id) | Q(id__in=blocked_users)
            )
    
    def clean(self):
        cleaned_data = super().clean()
        is_group_chat = cleaned_data.get('is_group_chat')
        group_name = cleaned_data.get('group_name')
        participants = cleaned_data.get('participants')
        
        if is_group_chat and not group_name:
            self.add_error('group_name', 'Group name is required for group chats')
        
        if participants and len(participants) < 1:
            self.add_error('participants', 'You must select at least one participant')
        
        if is_group_chat and participants and len(participants) < 2:
            self.add_error('participants', 'Group chats require at least 2 other participants')
        
        return cleaned_data
