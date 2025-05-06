from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.core.exceptions import ValidationError
from .models import User, Profile
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import User

class CustomUserCreationForm(UserCreationForm):
    """
    Form for user registration with custom fields
    """
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget = forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget = forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'})
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Case-insensitive username check
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("A user with that username already exists.")
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Case-insensitive email check
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("A user with that email already exists.")
        return email

class CustomAuthenticationForm(AuthenticationForm):
    """
    Custom login form with styled widgets
    """
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username or Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Allow login with email
        if '@' in username:
            try:
                user = User.objects.get(email=username)
                return user.username
            except User.DoesNotExist:
                pass
        return username

class ProfileEditForm(forms.ModelForm):
    """
    Form for editing user profile
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'bio', 'website', 'phone_number', 'profile_picture', 'is_private']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-3 py-2 border rounded-lg'}),
            'website': forms.URLInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'phone_number': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['profile_picture'].help_text = "Updating your profile picture will create a post in your feed."
        self.fields['is_private'].help_text = "When your account is private, only people you approve can see your photos and videos."


class AccountSettingsForm(forms.ModelForm):
    """
    Form for editing account settings
    """
    class Meta:
        model = User
        fields = ('email', 'is_private', 'show_activity_status', 'allow_sharing', 'allow_mentions')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_private': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_activity_status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_sharing': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_mentions': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise ValidationError("A user with that email already exists.")
        return email


class CustomPasswordChangeForm(PasswordChangeForm):
    """
    Custom password change form with styled widgets
    """
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Current Password'}))
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New Password'}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm New Password'}))


class CustomPasswordResetForm(PasswordResetForm):
    """
    Custom password reset form with styled widgets
    """
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))


class CustomSetPasswordForm(SetPasswordForm):
    """
    Custom set password form with styled widgets
    """
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New Password'}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm New Password'}))
