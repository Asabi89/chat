from django import forms
from .models import SearchHistory

class SearchForm(forms.Form):
    """
    Form for search functionality
    """
    query = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'search-input',
            'placeholder': 'Search...',
            'autocomplete': 'off'
        })
    )
    
    type = forms.ChoiceField(
        choices=[
            ('general', 'All'),
            ('user', 'Users'),
            ('hashtag', 'Hashtags'),
            ('post', 'Posts'),
            ('reel', 'Reels'),
        ],
        required=False,
        initial='general',
        widget=forms.Select(attrs={
            'class': 'search-type-select'
        })
    )

class ClearSearchHistoryForm(forms.Form):
    """
    Form for clearing search history
    """
    confirm = forms.BooleanField(
        required=True,
        initial=True,
        widget=forms.HiddenInput()
    )
