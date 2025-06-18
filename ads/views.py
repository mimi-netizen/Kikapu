from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse
from django.http import JsonResponse
from ads.forms import PostAdsForm, AdsEditForm
from ads.models import Ads, AdsImages, County, City, Category, AdsTopBanner, AdsRightBanner, AdsBottomBanner, Bookmark, AdPriceHistory, DraftAd
from profiles.models import Profile
from ads.models import FeaturedSlot
from datetime import datetime, timedelta
from .models import Conversation, Message
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
from django.db import models  # Add this line

# @cache_page(60 * 15)  # Remove or reduce cache time for testing
def ads_listing(request):
    excluded_categories = ['Adult Products', 'Intimacy & Relationships']
    
    # Get all filter parameters
    search_query = request.GET.get('search', '').strip()
    sort = request.GET.get('sort', '-date_created')
    category = request.GET.get('category')
    county = request.GET.get('county')
    city = request.GET.get('city')
    condition = request.GET.get('condition')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    
    # Start with base queryset
    ads_list = Ads.objects.select_related(
        'seller', 
        'category', 
        'city', 
        'county'
    ).prefetch_related(
        'images',
        'saved_by'
    ).exclude(
        category__category__in=excluded_categories
    ).filter(status='ACTIVE')

    # Apply text search if provided
    if search_query:
        ads_list = ads_list.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__category__icontains=search_query)
        )

    # Apply category filter
    if category:
        try:
            category_obj = Category.objects.get(slug=category)
            if category_obj.parent is None:
                # Include ads from subcategories if main category
                subcategories = Category.objects.filter(parent=category_obj)
                ads_list = ads_list.filter(
                    Q(category=category_obj) | Q(category__in=subcategories)
                )
            else:
                ads_list = ads_list.filter(category=category_obj)
        except Category.DoesNotExist:
            pass

    # Apply location filters
    if county:
        ads_list = ads_list.filter(county__slug=county)
        if city:
            ads_list = ads_list.filter(city__slug=city)

    # Apply condition filter
    if condition:
        ads_list = ads_list.filter(condition=condition)

    # Apply price range filter
    if min_price:
        try:
            ads_list = ads_list.filter(price__gte=float(min_price))
        except ValueError:
            pass

    if max_price:
        try:
            ads_list = ads_list.filter(price__lte=float(max_price))
        except ValueError:
            pass

    # Apply sorting
    if sort == 'price_low':
        ads_list = ads_list.order_by('price')
    elif sort == 'price_high':
        ads_list = ads_list.order_by('-price')
    elif sort == '-views_count':
        ads_list = ads_list.order_by('-views_count')
    else:
        ads_list = ads_list.order_by(sort)

    # Pagination
    paginator = Paginator(ads_list, 20)
    page = request.GET.get('page')
    ads_listing = paginator.get_page(page)

    # Get categories with subcategories and counts
    categories = []
    main_categories = Category.objects.filter(parent=None).order_by('category')
    
    for main_cat in main_categories:
        # Get count for main category and its subcategories
        main_cat_count = Ads.objects.filter(
            Q(category=main_cat) | Q(category__parent=main_cat),
            status='ACTIVE'
        ).count()
        
        categories.append({
            'id': main_cat.id,
            'category': main_cat.category,
            'slug': main_cat.slug,
            'ads_count': main_cat_count,
            'is_main': True
        })
        
        # Add subcategories
        for sub_cat in Category.objects.filter(parent=main_cat).order_by('category'):
            sub_cat_count = Ads.objects.filter(category=sub_cat, status='ACTIVE').count()
            categories.append({
                'id': sub_cat.id,
                'category': f"  - {sub_cat.category}",  # Indent subcategories
                'slug': sub_cat.slug,
                'ads_count': sub_cat_count,
                'is_main': False
            })

    # Get counties and cities with counts
    counties = County.objects.values('id', 'county_name', 'slug').annotate(
        ads_count=Count('ads', filter=Q(ads__status='ACTIVE'))
    ).order_by('county_name')
    
    cities = None
    if county:
        try:
            county_obj = County.objects.get(slug=county)
            cities = City.objects.filter(county=county_obj).order_by('city_name')
        except County.DoesNotExist:
            pass

    # Current filters for display
    current_filters = {
        'search': search_query,
        'category': category,
        'county': county,
        'city': city,
        'condition': condition,
        'min_price': min_price,
        'max_price': max_price,
        'sort': sort
    }

    # Get conditions from model choices
    conditions = [{'value': value, 'label': label} for value, label in Ads.CONDITION_CHOICES]
    
    context = {
        'ads_listing': ads_listing,
        'categories': categories,
        'counties': counties,
        'cities': cities,  # Pass cities to template for dropdown population
        'search_query': search_query,  # Add this to context
        'current_filters': {
            'sort': sort,
            'category': category,
            'county': county,
            'city': city,
            'search': search_query,  # Add this to current_filters
        }
    }
    
    return render(request, 'ads/ads-listing.html', context)

@login_required(login_url='login')
def post_ads(request):
    if request.method == 'POST':
        form = PostAdsForm(request.POST, request.FILES, user=request.user)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    ads = form.save(commit=False)
                    ads.seller = request.user.profile
                    
                    # Ensure category is properly set (main or sub)
                    category_id = request.POST.get('category')
                    if category_id:
                        category = Category.objects.get(id=category_id)
                        ads.category = category
                        
                    ads.save()
                    form.save_m2m()

                    images = request.FILES.getlist('images')
                    for image in images:
                        AdsImages.objects.create(
                            ad=ads,
                            image=image
                        )

                    messages.success(request, 'Your ad has been posted successfully!')
                    return redirect('ads:ads-listing')

            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
                return render(request, 'ads/post-ads.html', {'form': form})
    else:
        form = PostAdsForm(user=request.user)

    context = {
        'form': form,
        'main_categories': Category.objects.filter(parent=None).prefetch_related('subcategories'),
        'categories': Category.objects.all().select_related('parent'),  # Add select_related
        'counties': County.objects.all(),
        'cities': City.objects.all(),
        'top_banners': AdsTopBanner.objects.order_by('-created_at')[:5],
        'right_banners': AdsRightBanner.objects.order_by('-created_at')[:5],
        'bottom_banners': AdsBottomBanner.objects.order_by('-created_at')[:5],
    }

    return render(request, 'ads/post-ads.html', context)
    

# message views
@login_required
def send_message(request, ad_id):
    if request.method != 'POST':
        return redirect('ads:ads-detail', ad_id)

    ad = get_object_or_404(Ads, id=ad_id)
    content = request.POST.get('message')
    receiver = ad.seller.user

    conversation = Conversation.get_or_create_conversation(request.user, receiver, ad)

    message = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        receiver=receiver,
        ad=ad,
        content=content,
        is_read=False  # Changed from read to is_read
    )

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'message': {
                'id': message.id,
                'content': message.content,
                'created_at': message.created_at.isoformat(),
                'sender_username': message.sender.username
            }
        })

    messages.success(request, 'Message sent successfully!')
    return redirect('ads:ads-detail', ad_id)


@login_required
def inbox(request):
    if not request.user.is_authenticated:
        messages.warning(request, 'Please log in to access your inbox.')
        return redirect('login')

    conversations = Conversation.objects.filter(
        participants=request.user
    ).prefetch_related(
        models.Prefetch(
            'messages',
            queryset=Message.objects.select_related('sender', 'receiver')
        ),
        'participants__profile'
    ).order_by('-last_message_time')

    for conv in conversations:
        conv.other_user = conv.get_other_participant(request.user)
        conv.unread_count = Message.objects.filter(conversation=conv, receiver=request.user, is_read=False).count()

    return render(request, 'ads/inbox.html', {
        'conversations': conversations,
        'current_user_id': request.user.id
    })

@login_required
def conversation_detail(request, conversation_id):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        conversation = get_object_or_404(
            Conversation.objects.prefetch_related('messages'),
            id=conversation_id,
            participants=request.user
        )
        
        # Manually mark messages as read instead of using non-existent method
        Message.objects.filter(conversation=conversation, receiver=request.user, is_read=False).update(is_read=True)
        
        # No need to update unread count separately as it's handled in the inbox view
        
        ad_data = None
        if conversation.ad:
            ad_data = {
                'id': conversation.ad.id,
                'title': conversation.ad.title
            }
        else:
            ad_data = {
                'id': None,
                'title': 'General Inquiry'
            }
        
        messages = conversation.messages.all().order_by('created_at')
        
        other_user = conversation.get_other_participant(request.user)
        other_user_data = {
            'id': other_user.id if other_user else request.user.id,
            'username': other_user.username if other_user else request.user.username,
            'profile_picture': other_user.profile.profile_picture_url.url if other_user and hasattr(other_user.profile, 'profile_picture_url') and other_user.profile.profile_picture_url else None
        }

        return JsonResponse({
            'id': conversation.id,
            'ad': ad_data,
            'other_user': other_user_data,
            'participants': [
                {
                    'id': p.id,
                    'username': p.username,
                    'profile_picture': p.profile.profile_picture_url.url if hasattr(p.profile, 'profile_picture_url') and p.profile.profile_picture_url else None
                } for p in conversation.participants.all()
            ],
            'messages': [
                {
                    'id': message.id,
                    'sender': {
                        'id': message.sender.id,
                        'username': message.sender.username,
                        'profile_picture': message.sender.profile.profile_picture_url.url if hasattr(message.sender.profile, 'profile_picture_url') and message.sender.profile.profile_picture_url else None
                    },
                    'content': message.content,
                    'timestamp': message.created_at.isoformat() if message.created_at else '',
                    'is_read': message.is_read,
                    'created_at': message.created_at.isoformat()
                } for message in messages
            ],
            'unread_count': sum(1 for m in messages if not m.is_read and m.receiver == request.user)
        })
    
    conversation = get_object_or_404(
        Conversation.objects.prefetch_related('messages'),
        id=conversation_id,
        participants=request.user
    )
    
    # Manually mark messages as read instead of using non-existent method
    Message.objects.filter(conversation=conversation, receiver=request.user, is_read=False).update(is_read=True)
    
    # No need to update unread count separately as it's handled in the inbox view
    
    return render(request, 'ads/conversation_detail.html', {
        'conversation': conversation,
        'other_user': conversation.get_other_participant(request.user),
    })

@login_required
@require_POST
def delete_conversation(request, conversation_id):
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user
    )
    conversation.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    messages.success(request, 'Conversation deleted successfully.')
    return redirect('ads:inbox')


def ads_search(request):
    # Get search parameters
    query = request.GET.get('query', '').strip()
    location = request.GET.get('location', '').strip()

    # Start with all ads
    ads_search_result = Ads.objects.select_related(
        'seller', 
        'category', 
        'city', 
        'county'
    ).prefetch_related('images')

    # Apply search filters
    if query:
        ads_search_result = ads_search_result.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(category__category__icontains=query)
        )

    # Apply location filter if provided
    if location:
        ads_search_result = ads_search_result.filter(
            Q(city__city_name__icontains=location) |
            Q(county__county_name__icontains=location)
        )

    # Order results
    ads_search_result = ads_search_result.order_by('-date_created')

    # Get banner ads
    active_time = datetime.now() - timedelta(days=30)
    top_banners = AdsTopBanner.objects.filter(created_at__gte=active_time)
    right_banners = AdsRightBanner.objects.filter(created_at__gte=active_time)
    bottom_banners = AdsBottomBanner.objects.filter(created_at__gte=active_time)

    context = {
        'ads_search_result': ads_search_result,
        'query': query,
        'location': location,
        'top_banners': top_banners,
        'right_banners': right_banners,
        'bottom_banners': bottom_banners,
        'result_count': ads_search_result.count(),
    }

    return render(request, 'ads/ads-search.html', context)

def ads_detail(request, pk):
    ads_detail = get_object_or_404(Ads, pk=pk)
    
    # Increment views count if this is not the ad owner
    if request.user != ads_detail.seller.user:
        ads_detail.increment_views()
    
    # Get ad images and verify their existence
    ads_images = ads_detail.images.all()
    
    # Get banners
    active_time = datetime.now() - timedelta(days=30)
    top_banners = AdsTopBanner.objects.order_by('-created_at').filter(created_at__gte=active_time)
    right_banners = AdsRightBanner.objects.order_by('-created_at').filter(created_at__gte=active_time)
    bottom_banners = AdsBottomBanner.objects.order_by('-created_at').filter(created_at__gte=active_time)

    # Verify image existence
    for image in ads_images:
        if image.image:
            try:
                image.image.file  # This will check if file exists
            except:
                image.image = None  # Clear invalid image reference

    # Get or initialize viewed ads list from session
    viewed_ads = request.session.get('viewed_ads', [])
    
    # Convert ads_detail.id to string since session serializes to JSON
    ad_id_str = str(ads_detail.id)
    
    # Remove the ad if it's already in the list
    if ad_id_str in viewed_ads:
        viewed_ads.remove(ad_id_str)
    
    # Add the ad to the beginning of the list
    viewed_ads.insert(0, ad_id_str)
    
    # Keep only the last 6 viewed ads
    viewed_ads = viewed_ads[:6]
    
    # Update session
    request.session['viewed_ads'] = viewed_ads
    request.session.modified = True

    # Get all related ads (same category, excluding current ad)
    # We'll get all of them and paginate on the frontend
    related_ads = (Ads.objects
                  .filter(category=ads_detail.category)
                  .exclude(id=ads_detail.id)
                  .select_related('category', 'county', 'city', 'seller')
                  .prefetch_related('images')
                  .order_by('-date_created'))

    context = {
        'ads_detail': ads_detail,
        'ads_images': ads_images,
        'top_banners': top_banners,
        'right_banners': right_banners,
        'bottom_banners': bottom_banners,
        'related_ads': related_ads,
        'ads_per_page': 24,  # 6 ads per row * 4 rows
    }

    return render(request, 'ads/ads-detail.html', context)


def get_more_ads(request, ad_id):
    """AJAX view to get more related ads."""
    try:
        ad = get_object_or_404(Ads, id=ad_id)
        start = int(request.GET.get('start', 0))
        end = int(request.GET.get('end', 6))

        # Get related ads for the specified range
        related_ads = (Ads.objects
                       .filter(category=ad.category)
                       .exclude(id=ad_id)
                       .select_related('category', 'county', 'city', 'seller')
                       .prefetch_related('images')
                       .order_by('-date_created')[start:end])

        # Render only the ads HTML
        html = render_to_string('ads/partials/related-ad-card.html', 
                                 {'related_ads': related_ads},
                                 request=request)

        return JsonResponse({'html': html})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def seller_profile(request, pk):
    if not request.user.is_authenticated:
        # Return a JSON response if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'requires_auth': True})
    
    seller = get_object_or_404(Profile, pk=pk)
    
    # Get all categories for the filter
    categories = Category.objects.all()
    
    # Base queryset
    seller_ads = Ads.objects.filter(seller=seller)
    
    # Handle search
    search_query = request.GET.get('search')
    if search_query:
        seller_ads = seller_ads.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Handle category filter
    category_slug = request.GET.get('category')
    if category_slug:
        seller_ads = seller_ads.filter(category__slug=category_slug)
    
    context = {
        'seller': seller,
        'seller_ads': seller_ads,
        'categories': categories,  # Add categories to context
    }
    return render(request, 'ads/seller-profile.html', context)

def ads_by_category(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    
    # Get all ads from this category and its subcategories
    if category.is_main_category:
        ads_list = Ads.objects.filter(
            Q(category=category) | Q(category__in=category.subcategories.all())
        )
    else:
        ads_list = Ads.objects.filter(category=category)
    
    # Add sorting options
    sort = request.GET.get('sort', '-date_created')
    if sort == 'price_low':
        ads_list = ads_list.order_by('price')
    elif sort == 'price_high':
        ads_list = ads_list.order_by('-price')
    else:
        ads_list = ads_list.order_by(sort)
    
    # Pagination
    paginator = Paginator(ads_list, 20)
    page = request.GET.get('page')
    ads_by_category = paginator.get_page(page)
    
    context = {
        'category': category,
        'ads_by_category': ads_by_category,
        'main_categories': Category.objects.filter(parent=None).prefetch_related('subcategories'),
        'is_main_category': category.is_main_category,
        'subcategories': category.subcategories.all() if category.is_main_category else None,
        'parent_category': category.parent if category.is_subcategory else None,
        'current_sort': sort,
    }

    return render(request, 'ads/category-archive.html', context)

def ads_by_county(request, county_slug):
    county = get_object_or_404(County, slug=county_slug)
    ads_by_county = Ads.objects.filter(county=county)
    categories = Category.objects.all()  # Add this line
    active_time = datetime.now() - timedelta(days=30)
    top_banners = AdsTopBanner.objects.order_by('-created_at').filter(created_at__gte=active_time)
    right_banners = AdsRightBanner.objects.order_by('-created_at').filter(created_at__gte=active_time)
    bottom_banners = AdsBottomBanner.objects.order_by('-created_at').filter(created_at__gte=active_time)

    context = {
        'ads_by_county': ads_by_county,
        'county': county,
        'categories': categories,  # Add this line
        'top_banners': top_banners,
        'right_banners': right_banners,
        'bottom_banners': bottom_banners,
    }

    return render(request, 'ads/county-archive.html', context)

def ads_by_city(request, city_slug):
    city = get_object_or_404(City, slug=city_slug)
    ads_by_city = Ads.objects.filter(city=city)
    categories = Category.objects.all()  # Add this line
    active_time = datetime.now() - timedelta(days=30)
    top_banners = AdsTopBanner.objects.order_by('-created_at').filter(created_at__gte=active_time)
    right_banners = AdsRightBanner.objects.order_by('-created_at').filter(created_at__gte=active_time)
    bottom_banners = AdsBottomBanner.objects.order_by('-created_at').filter(created_at__gte=active_time)

    context = {
        'ads_by_city': ads_by_city,
        'city': city,
        'categories': categories,  # Add this line
        'top_banners': top_banners,
        'right_banners': right_banners,
        'bottom_banners': bottom_banners,
    }

    return render(request, 'ads/city-archive.html', context)

def get_cities(request, county_id):
    try:
        cities = City.objects.filter(county_id=county_id).values('id', 'city_name', 'slug')
        cities_list = list(cities)
        # Transform the data to match expected format
        for city in cities_list:
            city['name'] = city.pop('city_name')
        print(f"County ID: {county_id}, Cities found: {len(cities_list)}")  # Debug log to server console
        return JsonResponse(cities_list, safe=False)
    except Exception as e:
        print(f"Error in get_cities for county_id {county_id}: {str(e)}")  # Debug log to server console
        return JsonResponse({'error': str(e)}, status=400)

def get_cities_by_slug(request, county_slug):
    try:
        county = County.objects.get(slug=county_slug)
        cities = City.objects.filter(county=county).values('id', 'city_name', 'slug')
        cities_list = list(cities)
        for city in cities_list:
            city['name'] = city.pop('city_name')
        return JsonResponse(cities_list, safe=False)
    except County.DoesNotExist:
        return JsonResponse({'error': 'County not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def ads_author_archive(request, pk):
    seller = get_object_or_404(Profile, pk=pk)
    ads_by_author = Ads.objects.filter(seller=seller)
    categories = Category.objects.all()  # Add this line
    
    active_time = datetime.now() - timedelta(days=30)
    top_banners = AdsTopBanner.objects.order_by('-created_at').filter(created_at__gte=active_time)
    right_banners = AdsRightBanner.objects.order_by('-created_at').filter(created_at__gte=active_time)
    bottom_banners = AdsBottomBanner.objects.order_by('-created_at').filter(created_at__gte=active_time)

    context = {
        'seller': seller,
        'ads_by_author': ads_by_author,
        'categories': categories,  # Add this line
        'top_banners': top_banners,
        'right_banners': right_banners,
        'bottom_banners': bottom_banners,
    }

    return render(request, 'ads/author-archive.html', context)


@login_required(login_url='login')
def edit_ad(request, pk):
    ad = get_object_or_404(Ads, pk=pk, seller=request.user.profile)
    
    if request.method == 'POST':
        form = AdsEditForm(request.POST, request.FILES, instance=ad)
        if form.is_valid():
            try:
                with transaction.atomic():
                    ad = form.save()
                    
                    # Handle new images if uploaded
                    new_images = request.FILES.getlist('images')
                    for image in new_images:
                        AdsImages.objects.create(ad=ad, image=image)

                    messages.success(request, 'Ad updated successfully.')
                    return redirect('ads:ads-detail', pk=ad.pk)
            except Exception as e:
                messages.error(request, f'Error updating ad: {str(e)}')
    else:
        form = AdsEditForm(instance=ad)

    return render(request, 'ads/ads-edit.html', {
        'form': form,
        'ad': ad
    })

@login_required(login_url='login')
def delete_ad(request, pk):
    try:
        ad = get_object_or_404(Ads, pk=pk)
        if request.method == 'POST':
            ad.delete()
            messages.success(request, 'The ad has been deleted successfully.')
            return redirect('ads:ads_listing')
    except Exception as e:
        messages.error(request, 'An error occurred while deleting the ad. Please try again.')
        return redirect('ads:ads-delete', pk=pk)

    return render(request, 'ads/ads-delete.html', {'ad': ad})

@login_required
def toggle_bookmark(request, ad_id):
    """Toggle save/unsave an ad"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
        
    try:
        ad = get_object_or_404(Ads, id=ad_id)
        profile = getattr(request.user, 'profile', None)
        if not profile:
            return JsonResponse({'error': 'User profile not found.'}, status=400)
        bookmark = Bookmark.objects.filter(profile=profile, ad=ad).first()

        if bookmark:
            bookmark.delete()
            return JsonResponse({'status': 'success', 'action': 'unsaved', 'is_bookmarked': False})
        else:
            Bookmark.objects.create(profile=profile, ad=ad)
            return JsonResponse({'status': 'success', 'action': 'saved', 'is_bookmarked': True})

    except Ads.DoesNotExist:
        return JsonResponse({'error': 'Ad not found'}, status=404)
    except Exception as e:
        print(f"Error in toggle_bookmark: {str(e)}")
        return JsonResponse({'error': 'An error occurred while saving the listing'}, status=500)

@login_required
def bookmarks(request):
    """View saved ads"""
    bookmarks = Bookmark.objects.filter(user=request.user).select_related('ad')
    context = {
        'bookmarks': bookmarks,
    }
    return render(request, 'ads/bookmarks.html', context)

@login_required
def post_featured_ad(request):
    """Handle featured ad posting with enhanced validation and processing"""
    # Get the price for featured slots
    featured_slot_price = FeaturedSlot.objects.first().price if FeaturedSlot.objects.exists() else 150.00
    
    if request.method == 'POST':
        form = PostAdsForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create the ad but don't save yet
                    ad = form.save(commit=False)
                    ad.seller = request.user.profile
                    ad.is_featured = True  # Mark as featured
                    ad.featured_until = timezone.now() + timedelta(days=30)  # Set featured expiration
                    ad.save()
                    form.save_m2m()

                    # Handle images
                    images = request.FILES.getlist('images')
                    if not images:
                        raise ValidationError("Featured ads require at least one image")
                    
                    for image in images:
                        AdsImages.objects.create(ad=ad, image=image)

                    # Find an available featured slot
                    available_slot = FeaturedSlot.objects.filter(status='AVAILABLE').first()
                    if not available_slot:
                        messages.warning(request, 'No featured slots available. Your ad will be queued.')
                    else:
                        available_slot.status = 'OCCUPIED'
                        available_slot.current_ad = ad
                        available_slot.valid_until = timezone.now() + timedelta(days=30)
                        available_slot.save()

                    # Redirect to payment
                    return redirect('payments:initiate_payment', ad_id=ad.id)

            except ValidationError as e:
                messages.error(request, str(e))
                return render(request, 'ads/post_featured_ad.html', {'form': form})
            except Exception as e:
                messages.error(request, f"Error creating featured ad: {str(e)}")
                return render(request, 'ads/post_featured_ad.html', {'form': form})
    else:
        form = PostAdsForm(user=request.user)

    context = {
        'form': form,
        'featured_slot_price': featured_slot_price,
        'categories': Category.objects.all(),
        'counties': County.objects.all(),
        'cities': City.objects.all(),
    }
    return render(request, 'ads/post_featured_ad.html', context)

@login_required
def check_featured_status(request, ad_id):
    """Check the featured status of an ad"""
    ad = get_object_or_404(Ads, id=ad_id, seller=request.user.profile)
    
    data = {
        'is_featured': ad.is_featured,
        'featured_until': ad.featured_until.isoformat() if ad.featured_until else None,
        'days_remaining': (ad.featured_until - timezone.now()).days if ad.featured_until else 0
    }
    
    return JsonResponse(data)

def manage_featured_slots():
    """Utility function to manage featured slots"""
    # Clean up expired slots
    expired_slots = FeaturedSlot.objects.filter(
        status='OCCUPIED',
        valid_until__lt=timezone.now()
    )
    
    for slot in expired_slots:
        if slot.current_ad:
            # Update the ad's featured status
            slot.current_ad.is_featured = False
            slot.current_ad.featured_until = None
            slot.current_ad.save()
            
        # Reset the slot
        slot.status = 'AVAILABLE'
        slot.current_ad = None
        slot.save()

    # Process queued ads if slots are available
    available_slots = FeaturedSlot.objects.filter(status='AVAILABLE')
    if available_slots.exists():
        queued_ads = Ads.objects.filter(
            is_featured=True,
            featured_until__isnull=True
        ).order_by('date_created')
        
        for ad in queued_ads:
            slot = available_slots.first()
            if slot:
                slot.status = 'OCCUPIED'
                slot.current_ad = ad
                slot.valid_until = timezone.now() + timedelta(days=30)
                slot.save()
                
                ad.featured_until = slot.valid_until
                ad.save()
                
                available_slots = available_slots.exclude(id=slot.id)
            else:
                break

@login_required
def check_featured_slots(request):
    # Clean up expired slots first
    FeaturedSlot.objects.filter(
        status='OCCUPIED',
        valid_until__lt=timezone.now()
    ).update(
        status='AVAILABLE',
        current_ad=None
    )

    # Get available slots
    available_slots = FeaturedSlot.objects.filter(status='AVAILABLE').count()
    total_slots = FeaturedSlot.objects.count()
    
    data = {
        'available_slots': available_slots,
        'total_slots': total_slots,
        'price_per_slot': FeaturedSlot.objects.first().price if total_slots > 0 else 150.00
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(data)
    
    return render(request, 'ads/featured_slots.html', data)

"""
def index(request):
    # Removed this function as it's now handled by pages.views.home
    pass
"""

@login_required
def my_ads(request):
    """Display user's ads with filtering"""
    queryset = Ads.objects.filter(seller=request.user.profile)
    
    # Apply filters
    search = request.GET.get('search')
    status = request.GET.get('status')
    category = request.GET.get('category')
    
    if search:
        queryset = queryset.filter(title__icontains=search)
    if status:
        queryset = queryset.filter(status=status)
    if category:
        queryset = queryset.filter(category_id=category)
        
    # Order by date created
    queryset = queryset.order_by('-date_created')
    
    # Pagination
    paginator = Paginator(queryset, 16)
    page = request.GET.get('page')
    ads = paginator.get_page(page)
    
    # Get summary stats
    total_ads = queryset.count()
    active_ads = queryset.filter(status='active').count()
    pending_ads = queryset.filter(status='pending').count()
    expired_ads = queryset.filter(status='expired').count()
    
    context = {
        'ads': ads,
        'total_ads': total_ads,
        'active_ads': active_ads,
        'pending_ads': pending_ads,
        'expired_ads': expired_ads,
        'categories': Category.objects.all(),
    }
    
    return render(request, 'ads/my-ads.html', context)

def get_price_suggestions(request, category_id):
    """Get price suggestions for a category based on historical data"""
    try:
        # Get the category
        category = get_object_or_404(Category, id=category_id)
        
        # Get active ads in this category
        active_ads = Ads.objects.filter(
            category=category,
            status='ACTIVE'
        )

        # Calculate price statistics
        stats = active_ads.aggregate(
            avg_price=Avg('price'),
            min_price=Min('price'),
            max_price=Max('price')
        )

        # Return price suggestions
        return JsonResponse({
            'average': round(float(stats['avg_price'] or 0), 2),
            'min': round(float(stats['min_price'] or 0), 2),
            'max': round(float(stats['max_price'] or 0), 2),
            'currency': 'KES'
        })
    except Category.DoesNotExist:
        return JsonResponse({'error': 'Category not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@require_POST
@login_required
def auto_save_draft(request):
    """Auto-save draft ad content"""
    try:
        form_data = {
            'title': request.POST.get('title', ''),
            'description': request.POST.get('description', ''),
            'price': request.POST.get('price', ''),
            'category': request.POST.get('category', ''),
            'county': request.POST.get('county', ''),
            'city': request.POST.get('city', ''),
            'condition': request.POST.get('condition', ''),
            'phone_number': request.POST.get('phone_number', ''),
            'brand': request.POST.get('brand', ''),
            'colour': request.POST.get('colour', ''),
            'weight': request.POST.get('weight', ''),
            'length': request.POST.get('length', ''),
            'width': request.POST.get('width', ''),
            'height': request.POST.get('height', ''),
            'negotiable': request.POST.get('negotiable', ''),
        }

        draft, _ = AdDraft.objects.get_or_create(user=request.user)
        draft.set_content(form_data)
        draft.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Draft saved',
            'timestamp': draft.last_modified.isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@require_POST
def get_subcategories(request):
    """Return subcategories for a given main category"""
    try:
        category_id = request.POST.get('category_id')
        if category_id:
            category = Category.objects.get(id=category_id)
            if category.is_main_category:
                subcategories = category.subcategories.all()
                data = [{'id': sub.id, 'name': sub.category} for sub in subcategories]
                return JsonResponse({'subcategories': data})
        return JsonResponse({'subcategories': []})
    except Category.DoesNotExist:
        return JsonResponse({'error': 'Category not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def send_message_to_seller(request, seller_id):
    if request.method != 'POST':
        return redirect('profiles:seller-profile', seller_id)

    seller_profile = get_object_or_404(Profile, user__id=seller_id)
    receiver = seller_profile.user
    content = request.POST.get('message')

    conversation = Conversation.get_or_create_conversation(request.user, receiver, ad=None)
    message = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        receiver=receiver,
        content=content,
        is_read=False
    )

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'message': {
                'id': message.id,
                'content': message.content,
                'created_at': message.created_at.isoformat(),
                'sender_username': message.sender.username
            }
        })

    messages.success(request, 'Message sent successfully!')
    return redirect('ads:seller-profile', seller_id)