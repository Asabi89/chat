from django import forms
from .models import Reel, ReelComment

class ReelForm(forms.ModelForm):
    """
    Form for creating and editing reels
    """
    caption = forms.CharField(max_length=2200, required=False, 
    widget=forms.Textarea(attrs={'placeholder': 'Write a caption...', 'rows': 3}))
    audio_track = forms.CharField(max_length=255, required=False,
    widget=forms.TextInput(attrs={'placeholder': 'Add audio track name'}))
    audio_artist = forms.CharField(max_length=255, required=False,
    widget=forms.TextInput(attrs={'placeholder': 'Add artist name'}))
    
    class Meta:
        model = Reel
        fields = ['video', 'caption', 'audio_track', 'audio_artist']
    
    def clean_video(self):
        video = self.cleaned_data.get('video')
        if video:
            # Validate video file type
            if not video.name.lower().endswith(('.mp4', '.mov', '.avi')):
                raise forms.ValidationError("Unsupported video format. Please use MP4, MOV, or AVI.")
            
            # Validate file size (max 100MB)
            if video.size > 100 * 1024 * 1024:
                raise forms.ValidationError("Video file is too large. Maximum size is 100MB.")
        
        return video


class ReelCommentForm(forms.ModelForm):
    """
    Form for creating comments on reels
    """
    text = forms.CharField(max_length=1000, 
    widget=forms.Textarea(attrs={'placeholder': 'Add a comment...', 'rows': 1}))
    
    class Meta:
        model = ReelComment
        fields = ['text']
