from django import forms
from .models import Post, Comment, Media

class PostForm(forms.ModelForm):
    """
    Form for creating and editing posts
    """
    location = forms.CharField(max_length=100, required=False, 
                              widget=forms.TextInput(attrs={'placeholder': 'Add location'}))
    caption = forms.CharField(max_length=2200, required=False, 
                             widget=forms.Textarea(attrs={'placeholder': 'Write a caption...', 'rows': 3}))
    
    class Meta:
        model = Post
        fields = ['caption', 'location', 'post_type']
        widgets = {
            'post_type': forms.HiddenInput(),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        # Additional validation can be added here
        return cleaned_data


class MediaForm(forms.ModelForm):
    """
    Form for uploading media files
    """
    class Meta:
        model = Media
        fields = ['file', 'media_type', 'order']
        widgets = {
            'media_type': forms.HiddenInput(),
            'order': forms.HiddenInput(),
        }


class CommentForm(forms.ModelForm):
    """
    Form for creating comments
    """
    text = forms.CharField(max_length=1000, 
    widget=forms.Textarea(attrs={'placeholder': 'Add a comment...', 'rows': 1}))
    
    class Meta:
        model = Comment
        fields = ['text']
