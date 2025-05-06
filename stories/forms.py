from django import forms
from .models import Story, StoryHighlight, HighlightStory
from django.forms import inlineformset_factory

class StoryForm(forms.ModelForm):
    """
    Form for creating and editing stories
    """
    class Meta:
        model = Story
        fields = ['file', 'story_type', 'caption', 'location', 'music_track', 'music_artist']
        widgets = {
            'caption': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add a caption...'}),
            'location': forms.TextInput(attrs={'placeholder': 'Add location...'}),
            'music_track': forms.TextInput(attrs={'placeholder': 'Song title...'}),
            'music_artist': forms.TextInput(attrs={'placeholder': 'Artist name...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['story_type'].widget = forms.RadioSelect(choices=Story.STORY_TYPES)
        self.fields['story_type'].initial = 'image'
        
        # Add file type validation based on story_type
        self.fields['file'].widget.attrs.update({
            'accept': '.jpg,.jpeg,.png,.mp4,.mov',
            'data-image-formats': '.jpg,.jpeg,.png',
            'data-video-formats': '.mp4,.mov',
        })
    
    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get('file')
        story_type = cleaned_data.get('story_type')
        
        if file and story_type:
            # Check file extension
            file_name = file.name.lower()
            if story_type == 'image' and not (file_name.endswith('.jpg') or file_name.endswith('.jpeg') or file_name.endswith('.png')):
                self.add_error('file', 'Please upload a valid image file (jpg, jpeg, png)')
            
            elif story_type == 'video' and not (file_name.endswith('.mp4') or file_name.endswith('.mov')):
                self.add_error('file', 'Please upload a valid video file (mp4, mov)')
            
            # Check file size
            if story_type == 'image' and file.size > 5 * 1024 * 1024:  # 5MB
                self.add_error('file', 'Image file size should not exceed 5MB')
            
            elif story_type == 'video' and file.size > 100 * 1024 * 1024:  # 100MB
                self.add_error('file', 'Video file size should not exceed 100MB')
        
        return cleaned_data

class StoryHighlightForm(forms.ModelForm):
    """
    Form for creating and editing story highlights
    """
    class Meta:
        model = StoryHighlight
        fields = ['title', 'cover_image']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Highlight title...'}),
        }
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title) < 1:
            raise forms.ValidationError("Title cannot be empty")
        return title

# Create a formset for managing stories in a highlight
HighlightStoryFormSet = inlineformset_factory(
    StoryHighlight,
    HighlightStory,
    fields=('story', 'order'),
    extra=1,
    can_delete=True
)
