from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from profiles.models import Profile
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
import logging

logger = logging.getLogger(__name__)

class UserRegistrationForm(UserCreationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'type': 'text',
        'class': 'form-control',  
        'name': 'username', 
        'placeholder': 'Username',
        'autocomplete': 'username'
    }))

    password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',  
        'name': 'password1', 
        'placeholder': 'Password',
        'autocomplete': 'new-password'
    }))

    password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',  
        'name': 'password2', 
        'placeholder': 'Retype Password',
        'autocomplete': 'new-password'
    }))
    
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',  
        'placeholder': 'Email Address',
        'autocomplete': 'email'
    }))

    account_type = forms.ChoiceField(
        choices=[('buyer', 'Buyer'), ('seller', 'Seller')],
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        initial='buyer',
        help_text='Select your account type'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'account_type']

    def clean(self):
        cleaned_data = super().clean()
        logger.debug(f"Cleaning form data: {cleaned_data}")
        
        # Check if passwords match
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match")
            
        return cleaned_data

    def clean_username(self):
        username = self.cleaned_data.get('username')
        logger.debug(f"Cleaning username: {username}")
        if not username:
            raise forms.ValidationError("Username is required")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("A user with that username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        logger.debug(f"Cleaning email: {email}")
        if not email:
            raise forms.ValidationError("Email is required")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This Email address is already in use.")
        return email

class EmailValidationOnForgotPassword(PasswordResetForm):
    email = forms.EmailField(label="", widget=forms.EmailInput(attrs={
        'class': 'form-control',  
        'placeholder': 'Email Address',
        'autocomplete': 'email'
    }))

    def clean_email(self):
        email = self.cleaned_data['email']
        if not User.objects.filter(email__iexact=email, is_active=True).exists():
            raise forms.ValidationError("There is no user registered with the specified email address!")

        return email

class EmailSetPassword(SetPasswordForm):
    new_password1 = forms.CharField(label="", widget=forms.PasswordInput(attrs={
        'class': 'form-control',  
        'name': 'new_password1', 
        'placeholder': 'Password',
        'autocomplete': 'new-password'
    }))

    new_password2 = forms.CharField(label="", widget=forms.PasswordInput(attrs={
        'class': 'form-control',  
        'name': 'new_password2', 
        'placeholder': 'Retype Password',
        'autocomplete': 'new-password'
    }))

class UserUpdateForm(ModelForm):
    first_name = forms.CharField(label="First Name", widget=forms.TextInput(attrs={
        'type': 'text',
        'class': 'form-control',  
        'name': 'first_name', 
        'placeholder': 'First Name',
        'autocomplete': 'given-name'
    }))

    last_name = forms.CharField(label="Last Name", widget=forms.TextInput(attrs={
        'type': 'text',
        'class': 'form-control',  
        'name': 'last_name', 
        'placeholder': 'Last Name',
        'autocomplete': 'family-name'
    }))

    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={
        'type': 'email',
        'class': 'form-control',  
        'placeholder': 'Email Address',
        'autocomplete': 'email'
    }))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        # exclude = ['user']

class ProfileUpdateForm(ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_pic']