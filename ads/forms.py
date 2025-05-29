from django import forms
from ckeditor.widgets import CKEditorWidget
from .models import Ads, County, City, Category
from django.core.validators import RegexValidator, MinValueValidator
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
import bleach

class BaseAdsForm(forms.ModelForm):
    """Base form for both creating and editing ads"""
    # Phone number validator for Kenyan format
    phone_validator = RegexValidator(
        regex=r'^\+?254?\d{9,10}$',  # Allow both 9 and 10 digit formats
        message="Enter a valid Kenyan phone number (e.g., +254712345678 or 0712345678)"
    )

    # Bundle deal fields
    is_bundle_deal = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'data-toggle': 'collapse',
            'data-target': '#bundleDealOptions'
        })
    )
    bundle_price = forms.DecimalField(
        required=False,
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter bundle price in KES',
            'min': '0',
            'step': '0.01'
        })
    )
    min_bundle_quantity = forms.IntegerField(
        required=False,
        validators=[MinValueValidator(2)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Minimum quantity for bundle deal',
            'min': '2'
        })
    )

    # Form fields with better validation and styling
    title = forms.CharField(
        min_length=10,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter a descriptive title'
        })
    )

    description = forms.CharField(
        widget=CKEditorWidget(
            config_name='restricted',
            attrs={
                'class': 'form-control',
                'rows': '6'
            }
        )
    )

    price = forms.DecimalField(
        max_digits=14,  # Allows prices up to 9,999,999,999.99 KES
        decimal_places=2,
        validators=[MinValueValidator(0)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter price in KES',
            'min': '0',  # HTML5 validation for minimum value
            'step': '0.01'  # Allows for decimal values
        })
    )
    phone_number = forms.CharField(
        validators=[phone_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., +254712345678'
        })
    )

    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        empty_label="Select Category",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    county = forms.ModelChoiceField(
        queryset=County.objects.all(),
        empty_label="Select County",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    city = forms.ModelChoiceField(
        queryset=City.objects.none(),
        empty_label="Select City",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    condition = forms.ChoiceField(
        choices=Ads.CONDITION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    images = forms.FileField(
        required=True,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'multiple': True,
            'accept': 'image/*'
        })
    )

    brand = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter brand name'
        })
    )

    colour = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter color'
        })
    )

    weight = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Weight in kg',
            'step': '0.01'
        })
    )

    length = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Length in cm',
            'step': '0.1'
        })
    )

    width = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Width in cm',
            'step': '0.1'
        })
    )

    height = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Height in cm',
            'step': '0.1'
        })
    )

    negotiable = forms.ChoiceField(
        choices=Ads.NEGOTIATION_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )

    clothing_size = forms.ChoiceField(
        choices=Ads.SIZE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'data-type': 'size'
        })
    )

    shoe_size = forms.ChoiceField(
        choices=Ads.SHOE_SIZE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'data-type': 'size'
        })
    )

    custom_size = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter custom size',
            'style': 'display: none;'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        
        # Validate images
        images = self.files.getlist('images')
        if len(images) > 5:
            raise ValidationError("Maximum 5 images allowed")
        
        for image in images:
            if image.size > 3 * 1024 * 1024:  # 3MB
                raise ValidationError(f"Image {image.name} is too large. Maximum size is 3MB")

        # Validate price
        price = cleaned_data.get('price')
        if price and price > 9999999.99:
            raise ValidationError("Price cannot exceed 9,999,999.99")

        # Validate phone number format
        phone = cleaned_data.get('phone_number')
        if phone:
            if phone.startswith('0'):
                cleaned_data['phone_number'] = '+254' + phone[1:]
            elif not phone.startswith('+254'):
                raise ValidationError("Phone number must start with 0 or +254")

        return cleaned_data

    def clean_description(self):
        """Clean and sanitize the description field"""
        description = self.cleaned_data.get('description')
        
        # Define allowed tags and attributes
        allowed_tags = [
            'p', 'br', 'strong', 'em', 'u', 'ul', 'ol', 'li',
            'h2', 'h3', 'h4'
        ]
        allowed_attributes = {
            '*': ['class', 'style']
        }
        
        # Remove the `styles` parameter to avoid the TypeError
        cleaned_description = bleach.clean(
            description,
            tags=allowed_tags,
            attributes=allowed_attributes,
            strip=True
        )
        return cleaned_description

    class Meta:
        model = Ads
        fields = [
            'title', 'description', 'category', 'price', 'condition',
            'county', 'city', 'phone_number', 'images',
            'brand', 'colour', 'weight', 'length', 'width', 'height', 'negotiable',
            'clothing_size', 'shoe_size', 'custom_size',
        ]
        error_messages = {
            'title': {
                'required': "Please enter a title for your ad",
                'min_length': "Title must be at least 10 characters long"
            },
            'description': {
                'required': "Please describe your item",
                'min_length': "Description must be at least 30 characters long"
            },
            'price': {
                'required': "Please enter a price",
                'invalid': "Please enter a valid price"
            },
            'images': {
                'required': "Please upload at least one image"
            }
        }

class PostAdsForm(BaseAdsForm):
    """Form for creating new ads"""
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # If we have an instance and county is selected, populate cities
        if self.instance.pk and self.instance.county:
            self.fields['city'].queryset = City.objects.filter(county=self.instance.county)
        
        # If form is bound and county is selected
        if self.is_bound and 'county' in self.data:
            try:
                county_id = int(self.data.get('county'))
                self.fields['city'].queryset = City.objects.filter(county_id=county_id)
            except (ValueError, TypeError):
                pass

class AdsEditForm(BaseAdsForm):
    """Form for editing existing ads"""
    images = forms.FileField(
        required=False,  # Make images optional for editing
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'multiple': True,
            'accept': 'image/*'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['city'].queryset = City.objects.none()

        if 'county' in self.data:
            try:
                county_id = int(self.data.get('county'))
                self.fields['city'].queryset = City.objects.filter(county_id=county_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.county:
            self.fields['city'].queryset = City.objects.filter(county=self.instance.county)