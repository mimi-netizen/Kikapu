from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from ads.models import Ads, Bookmark

# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    profile_pic = models.ImageField(
        default='images/default-profile-pic.jpg',  # Updated to match static directory structure
        upload_to='profile_pictures/',
        null=True,
        blank=True
    )
    # Seller specific fields
    is_seller = models.BooleanField(default=False)
    seller_since = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    store_name = models.CharField(max_length=255, blank=True, null=True)
    store_description = models.TextField(blank=True, null=True)
    store_banner = models.ImageField(upload_to='store_banners/', blank=True, null=True)
    store_logo = models.ImageField(upload_to='store_logos/', blank=True, null=True)
    store_name = models.CharField(max_length=100, blank=True)
    store_description = models.TextField(blank=True)
    business_hours = models.CharField(max_length=200, blank=True)
    whatsapp_number = models.CharField(max_length=15, blank=True)
    preferred_contact_method = models.CharField(
        max_length=20,
        choices=[
            ('phone', 'Phone Call'),
            ('whatsapp', 'WhatsApp'),
            ('email', 'Email'),
            ('in_app', 'In-App Message')
        ],
        default='phone'
    )
    followers = models.ManyToManyField('self', symmetrical=False, related_name='following', blank=True)
    store_location = models.CharField(max_length=100, blank=True, null=True)
    
    # Buyer specific fields
    saved_searches = models.ManyToManyField('SavedSearch', related_name='saved_by', blank=True)
    favorite_sellers = models.ManyToManyField('self', symmetrical=False, related_name='favorited_by', blank=True)
    bookmarks = models.ManyToManyField(Ads, through='ads.Bookmark', related_name='saved_by_profiles', through_fields=('profile', 'ad'))

    # Add these new fields
    last_seen = models.DateTimeField(default=timezone.now)
    is_premium = models.BooleanField(default=False)
    main_category = models.CharField(
        max_length=50, 
        choices=[
            ('electronics', 'Electronics'),
            ('fashion', 'Fashion'),
            ('home', 'Home & Living'),
            ('vehicles', 'Vehicles'),
        ],
        default='electronics'
    )
    is_verified = models.BooleanField(default=False)
    total_sales = models.PositiveIntegerField(default=0)
    # Remove total_ads field since we'll use annotation
    response_rate = models.FloatField(default=0)
    response_time = models.DurationField(null=True, blank=True)
    last_active = models.DateTimeField(auto_now=True)
    account_status = models.CharField(
        max_length=20,
        choices=[
            ('ACTIVE', 'Active'),
            ('SUSPENDED', 'Suspended'),
            ('BLOCKED', 'Blocked'),
            ('VERIFIED', 'Verified')
        ],
        default='ACTIVE'
    )

    def __str__(self):
        return self.user.username

    @property
    def average_rating(self):
        return self.received_reviews.aggregate(Avg('rating'))['rating__avg'] or 0.0

    @property
    def total_reviews(self):
        return self.received_reviews.count()

    @property
    def total_active_ads(self):
        return self.ads.filter(is_sold=False).count()

    @property
    def followers_count(self):  # Changed from get_followers_count to followers_count
        return self.followers.count()

    def update_last_seen(self):
        """Update the last seen timestamp"""
        self.last_seen = timezone.now()
        self.save(update_fields=['last_seen'])

    @property
    def is_online(self):
        """Check if user is currently online"""
        if not self.last_seen:
            return False
        return (timezone.now() - self.last_seen) < timezone.timedelta(minutes=15)

    def update_response_metrics(self):
        # Calculate response rate and time
        messages = self.profile_received_messages.all()
        if messages:
            responded = messages.filter(conversation__messages__sender=self).count()
            self.response_rate = (responded / messages.count()) * 100
            
            # Average response time
            response_times = messages.exclude(response_time=None).values_list('response_time', flat=True)
            if response_times:
                self.response_time = sum(response_times, timedelta()) / len(response_times)
            
            self.save(update_fields=['response_rate', 'response_time'])

    @property
    def get_total_ads(self):  # Add this property method
        return self.ads.count()

class SavedSearch(models.Model):
    name = models.CharField(max_length=100)
    query = models.CharField(max_length=200)
    category = models.ForeignKey('ads.Category', on_delete=models.SET_NULL, null=True, blank=True)
    min_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    location = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_checked = models.DateTimeField(auto_now=True)
    notify_new_matches = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} by {self.saved_by.first().user.username}"

class Review(models.Model):
    seller = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='received_reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_reviews')
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ad = models.ForeignKey('ads.Ads', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['reviewer', 'seller', 'ad']
        indexes = [
            models.Index(fields=['seller', '-created_at']),
            models.Index(fields=['rating']),
        ]

    def __str__(self):
        return f"{self.reviewer.username}'s review of {self.seller.user.username}"

    def clean(self):
        # Prevent users from reviewing themselves
        if self.reviewer == self.seller.user:
            raise ValidationError("You cannot review yourself.")
