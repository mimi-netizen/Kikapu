from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse
from django.http import JsonResponse
from ads.forms import PostAdsForm, AdsEditForm
from ads.models import (Ads, HeroBanner, AdsImages, County, City, Category, 
    AdsTopBanner, AdsRightBanner, AdsBottomBanner, Bookmark, AdPriceHistory, 
    DraftAd, TodayDeal, PopularCategory)
from profiles.models import Profile
from ads.models import FeaturedSlot
from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404
from django.db.models import Max, Count, Q
from django.utils.text import slugify
from django.views.decorators.http import require_POST
import unicodedata
import logging
logger = logging.getLogger(__name__)
from django.db import transaction
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
from django.template.loader import render_to_string
from django.utils import timezone
from ads.models import AdDraft  # Import AdDraft model
from django.views.decorators.cache import cache_page
from django.views.generic import DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView
from django.db.models import Avg, Max, Min
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
import json
from django.urls import reverse
from django.utils import timezone

def home(request):
    excluded_categories = ['Adult Products', 'Adult Toys', 'Intimacy & Relationships', 'Other Adult']
    
    # Get deals for the three grids
    bundle_deals = Ads.objects.filter(is_bundle=True).order_by('-date_created')[:2]
    featured_deals = Ads.objects.filter(is_featured=True).order_by('-date_created')[:2]
    negotiable_deals = Ads.objects.filter(negotiable='yes').order_by('-date_created')[:2]
    
    # Get popular categories
    popular_categories = PopularCategory.objects.all()[:14]
    
    # Get main categories with their subcategories and structure the data
    main_categories_data = []
    main_categories = Category.objects.filter(parent=None).prefetch_related('subcategories')
    
    for main_category in main_categories:
        # Get subcategories and their counts
        subcategories_data = [{
            'name': sub.category,
            'slug': sub.slug,
            'count': Ads.objects.filter(category=sub, is_active=True).count()
        } for sub in main_category.subcategories.all()]

        # Create main category data
        main_categories_data.append({
            'category': main_category.category,
            'icon': main_category.icon or 'fa-folder',  # Default icon if none set
            'subcategories': subcategories_data
        })
    
    featured_ads = Ads.objects.filter(
        is_featured=True
    ).exclude(
        category__category__in=excluded_categories
    ).select_related(
        'seller', 
        'category', 
        'city', 
        'county'
    ).prefetch_related('images')[:6]
    
    recent_ads = Ads.objects.exclude(
        category__category__in=excluded_categories
    ).select_related(
        'seller', 
        'category', 
        'city', 
        'county'
    ).prefetch_related('images').order_by('-date_created')[:6]
    
    # Get active hero banners
    hero_banners = HeroBanner.objects.filter(is_active=True).order_by('-created_at')

    # Get active bottom banners
    bottom_banners = AdsBottomBanner.objects.filter(is_active=True).order_by('-created_at')
    
    # Get listings from followed sellers for authenticated users
    followed_listings = []
    if request.user.is_authenticated:
        try:
            user_profile = request.user.profile
            followed_sellers = user_profile.following.all()
            if followed_sellers:
                followed_listings = Ads.objects.filter(
                    seller__in=followed_sellers,
                    is_active=True
                ).exclude(
                    category__category__in=excluded_categories
                ).select_related(
                    'seller', 
                    'category', 
                    'city', 
                    'county'
                ).prefetch_related('images').order_by('-date_created')[:6]
        except AttributeError:
            # In case user has no profile
            followed_listings = []
    
    # Get recommended ads (for all users, with personalization for authenticated users)
    recommended_ads = []
    if request.user.is_authenticated:
        # For authenticated users, try to personalize based on followed sellers
        try:
            user_profile = request.user.profile
            followed_sellers = user_profile.following.all()
            if followed_sellers:
                recommended_ads = Ads.objects.filter(
                    seller__in=followed_sellers,
                    is_active=True
                ).exclude(
                    category__category__in=excluded_categories
                ).select_related(
                    'seller', 
                    'category', 
                    'city', 
                    'county'
                ).prefetch_related('images').order_by('-date_created')[:6]
        except AttributeError:
            # In case user has no profile
            recommended_ads = []
    if not recommended_ads:  # Fallback if no personalized recommendations or user not authenticated
        recommended_ads = Ads.objects.filter(
            is_active=True
        ).exclude(
            category__category__in=excluded_categories
        ).select_related(
            'seller', 
            'category', 
            'city', 
            'county'
        ).prefetch_related('images').order_by('-views')[:6]  # Order by popularity
    
    # Get top rated sellers
    top_rated_sellers = Profile.objects.filter(
        is_seller=True  # First, ensure we only get sellers
    ).annotate(
        avg_rating=Avg('received_reviews__rating'),
        ads_count=Count('ads', filter=Q(ads__is_active=True))
    ).filter(
        ads_count__gt=0  # Only include sellers with active ads
    ).order_by('-avg_rating', '-ads_count')[:6]

    context = {
        'featured_ads': featured_ads,
        'recent_ads': recent_ads,
        'main_categories': main_categories_data,  # Use the structured data
        'hero_banners': hero_banners,
        'bottom_banners': bottom_banners,
        'top_rated_sellers': top_rated_sellers,
        'bundle_deals': bundle_deals,
        'featured_deals': featured_deals,
        'negotiable_deals': negotiable_deals,
        'popular_categories': popular_categories,
        'followed_listings': followed_listings,
        'recommended_ads': recommended_ads,
    }
    
    return render(request, 'pages/index.html', context)


# Search Ads View
def ads_search(request):
    query = request.GET.get('query', '').strip()  # Get the search query from the request
    ads = Ads.objects.all()  # Default to all ads if no query is provided

    if query:
        # Use Q objects to filter ads by title or description
        ads = Ads.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        ).distinct()

    # Context for the search results
    context = {
        'ads': ads,
        'query': query,
    }

    return render(request, 'ads/search_results.html', context)

# Faq view
def faq(request):
    return render(request, 'pages/faq.html')

# Terms of service view
def terms_of_service(request):
    return render(request, 'pages/terms-of-service.html')

# Contact view
def contact(request):
    return render(request, 'pages/contact.html')

def handler404(request, exception):
    # Get popular categories
    popular_categories = Category.objects.annotate(
        ads_count=Count('ads')
    ).order_by('-ads_count')[:6]
    
    # Get suggested items (featured or popular)
    suggested_items = Ads.objects.filter(
        is_active=True,
        is_featured=True
    ).select_related(
        'category', 'seller'
    ).prefetch_related('images')[:4]
    
    context = {
        'popular_categories': popular_categories,
        'suggested_items': suggested_items,
    }
    
    return render(request, '404.html', context, status=404)