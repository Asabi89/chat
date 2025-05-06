from django import forms
from .models import Feedback

class FeedbackForm(forms.ModelForm):
    """
    Form for user feedback and bug reports
    """
    class Meta:
        model = Feedback
        fields = ['feedback_type', 'subject', 'message', 'screenshot']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 5, 'class': 'w-full px-3 py-2 border rounded-lg'}),
            'subject': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
        }
