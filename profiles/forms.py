from django import forms
from .models import Profile, SavedSearch

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'location', 'phone_number', 'profile_pic']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }

class StoreSettingsForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'store_name',
            'store_location',
            'store_description',
            'business_hours',
            'whatsapp_number',
            'preferred_contact_method',
            'store_banner',
            'store_logo'
        ]
        widgets = {
            'store_description': forms.Textarea(attrs={'rows': 4}),
            'business_hours': forms.TextInput(attrs={
                'placeholder': 'e.g., Mon-Fri: 9AM-5PM, Sat: 10AM-2PM'
            }),
            'store_banner': forms.FileInput(attrs={'accept': 'image/*'}),
            'store_logo': forms.FileInput(attrs={'accept': 'image/*'}),
            'store_location': forms.TextInput(attrs={'placeholder': 'e.g., Nairobi, Kenya'}),
        }

class SavedSearchForm(forms.ModelForm):
    class Meta:
        model = SavedSearch
        fields = ['name', 'category', 'min_price', 'max_price', 'location', 'notify_new_matches']
        widgets = {
            'min_price': forms.NumberInput(attrs={'placeholder': 'Minimum Price'}),
            'max_price': forms.NumberInput(attrs={'placeholder': 'Maximum Price'}),
            'location': forms.TextInput(attrs={'placeholder': 'e.g., Nairobi, Mombasa'}),
        }