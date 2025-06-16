from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ads.models import Ads, Bookmark
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.urls import reverse
from django.db.models import Q, Count, Avg, Sum, F, ExpressionWrapper, DurationField, FloatField
from django.contrib.auth.models import User
from .models import Profile, SavedSearch, Review
from ads.models import Ads, Category
from .forms import ProfileUpdateForm, StoreSettingsForm, SavedSearchForm
from django.utils import timezone
from datetime import timedelta

# importing messages
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout

from django.contrib.auth.forms import User

from authentication.forms import UserRegistrationForm, UserUpdateForm, ProfileUpdateForm


# Model Forms.

# Create your views here.

# Profile Dashboard view
@login_required
def profile_dashboard(request):
    profile = request.user.profile
    
    if profile.is_seller:
        return seller_dashboard(request)
    else:
        return buyer_dashboard(request)

@login_required
def seller_dashboard(request):
    profile = request.user.profile
    
    # Get seller statistics
    total_ads = profile.ads.count()
    active_ads = profile.ads.filter(is_sold=False).count()
    sold_ads = profile.ads.filter(is_sold=True).count()
    
    # Get recent reviews with related data
    recent_reviews = profile.received_reviews.all()[:5]
    
    # Get recent ads with all related data and avoid N+1 queries
    recent_ads = profile.ads.all()\
        .select_related('category', 'county', 'city')\
        .prefetch_related('images')\
        .order_by('-date_created')[:5]
    
    # Update to use views_count since we haven't done the migration yet
    # After migration, this will need to be changed to clicks_count
    for ad in recent_ads:
        ad.clicks_count = ad.views_count  # Temporary fix until migration
    
    context = {
        'total_ads': total_ads,
        'active_ads': active_ads,
        'sold_ads': sold_ads,
        'recent_reviews': recent_reviews,
        'recent_ads': recent_ads,
        'profile': profile,
    }
    
    return render(request, 'profiles/seller_dashboard.html', context)

@login_required
def buyer_dashboard(request):
    profile = request.user.profile
    
    # Get saved searches
    saved_searches = profile.saved_searches.all().order_by('-last_checked')
    
    # Get favorite sellers
    favorite_sellers = profile.favorite_sellers.all()
    
    # Get bookmarked ads
    bookmarks = profile.bookmarks.all().order_by('-date_created')
    
    context = {
        'saved_searches': saved_searches,
        'favorite_sellers': favorite_sellers,
        'bookmarks': bookmarks,
        'profile': profile,
        'saved_ads': bookmarks,  # Add this line to match the template
        'bookmarks_count': bookmarks.count()  # Optional: Add this for consistency
    }
    
    return render(request, 'profiles/buyer_dashboard.html', context)

@login_required
def store_settings(request):
    profile = request.user.profile
    if not profile.is_seller:
        messages.error(request, "Only sellers can access store settings.")
        return redirect('profile_dashboard')
    
    if request.method == 'POST':
        form = StoreSettingsForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Store settings updated successfully!")
            return redirect('profiles:sellers')  # Changed this line to redirect to dashboard
    else:
        form = StoreSettingsForm(instance=profile)
    
    return render(request, 'profiles/store_settings.html', {'form': form})


@login_required
def save_search(request):
    if request.method == 'POST':
        form = SavedSearchForm(request.POST)
        if form.is_valid():
            saved_search = form.save(commit=False)
            saved_search.save()
            request.user.profile.saved_searches.add(saved_search)
            messages.success(request, "Search saved successfully!")
            return redirect('profiles:dashboard')  # Changed from 'profiles:buyer_dashboard' to 'profiles:dashboard'
    return redirect('profiles:dashboard')  # Changed this line too

@login_required
def toggle_favorite_seller(request, seller_id):
    if request.method == 'POST':
        seller = get_object_or_404(Profile, id=seller_id, is_seller=True)
        profile = request.user.profile
        
        if seller in profile.favorite_sellers.all():
            profile.favorite_sellers.remove(seller)
            is_favorite = False
        else:
            profile.favorite_sellers.add(seller)
            is_favorite = True
            
        return JsonResponse({
            'status': 'success',
            'is_favorite': is_favorite
        })
    
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def delete_saved_search(request, search_id):
    saved_search = get_object_or_404(SavedSearch, id=search_id, saved_by=request.user.profile)
    saved_search.delete()
    messages.success(request, "Saved search deleted successfully!")
    return redirect('profiles:buyer_dashboard')

# Profile Settings view
@login_required(login_url='login')
def profile_settings(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, f"Your profile has been updated successfully!")
            return redirect('profiles:profile-settings')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'user_form':user_form,
        'profile_form':profile_form
    }
    return render(request, 'profiles/account-setting.html', context)

# Profile Ads view
@login_required
def my_ads(request):
    # Ensure user has a profile
    if not hasattr(request.user, 'profile'):
        messages.error(request, "Please complete your profile first.")
        return redirect('login')

    # Get the seller's profile
    seller_profile = request.user.profile
    
    # Get all ads for the current seller with optimized queries
    ads = Ads.objects.filter(seller=seller_profile)\
                    .select_related('category', 'county', 'city')\
                    .prefetch_related('images')\
                    .order_by('-date_created')
    
    # Calculate status counts using the correct field names
    status_counts = {
        'all': ads.count(),
        'published': ads.filter(is_active=True).count(),
        'featured': ads.filter(is_featured=True).count(),
        'sold': ads.filter(is_sold=True).count(),
        'active': ads.filter(is_active=True, is_sold=False).count(),
        'expired': ads.filter(is_active=False).count(),
    }

    context = {
        'ads': ads,
        'status_counts': status_counts,
        
    }
    
    return render(request, 'profiles/all-ads.html', context)

# Profile Favorite Ads view
@login_required(login_url='login')
def profile_favorite_ads(request):
    # Get user's bookmarked ads with related data
    bookmarked_ads = request.user.profile.bookmarks.all()\
        .select_related('category', 'seller', 'seller__user')\
        .prefetch_related('images')\
        .order_by('-date_created')

    context = {
        'bookmarked_ads': bookmarked_ads,
        'bookmarks_count': bookmarked_ads.count()
    }
    return render(request, 'profiles/favourite-ads.html', context)

# Profile Delete view
@login_required(login_url='login')
def profile_close(request):
    if request.method == 'POST':
        confirm_close = request.POST.get('confirm_close')
        if confirm_close == 'yes':
            # Get the user and delete their account
            user = request.user
            logout(request)
            user.delete()
            messages.success(request, 'Your account has been successfully deleted.')
            return redirect('home')
        else:
            messages.info(request, 'Account deletion cancelled.')
            return redirect('profiles:profile-settings')
            
    return render(request, 'profiles/account-close.html')

# Profile view
@login_required
def profile(request):
    user_profile = request.user.profile
    user_ads = Ads.objects.filter(seller=user_profile)
    
    context = {
        'profile': user_profile,
        'ads': user_ads,
    }
    return render(request, 'profiles/profile.html', context)

# Sellers List view
# @login_required
def sellers_list(request):
    # Base queryset with annotations
    sellers = Profile.objects.filter(is_seller=True).annotate(
        avg_rating=Avg('received_reviews__rating'),
        reviews_count=Count('received_reviews'),
        ads_count=Count('ads'),
        num_followers=Count('followers'),  # Changed to num_followers
        activity_score=ExpressionWrapper(
            (Count('ads') * 0.4) + 
            (Avg('received_reviews__rating', default=0) * 0.3) + 
            (Count('followers') * 0.3),
            output_field=FloatField()
        )
    )

    context = {
        'sellers': sellers,
    }
    return render(request, 'profiles/sellers.html', context)

@login_required
def seller_profile(request, pk):
    seller = get_object_or_404(Profile, pk=pk)
    
    # Get seller's ads with prefetched relationships
    seller_ads = Ads.objects.filter(seller=seller)\
        .select_related('category', 'county', 'city')\
        .prefetch_related('images')\
        .order_by('-date_created')
    
    # Get seller's stats
    stats = {
        'total_ads': seller_ads.count(),
        'active_ads': seller_ads.filter(is_active=True, is_sold=False).count(),
        'followers_count': seller.followers.count(),
        'avg_response_time': seller.received_messages.aggregate(
            avg_time=Avg('response_time')
        )['avg_time']
    }
    
    context = {
        'seller': seller,
        'seller_ads': seller_ads,
        'stats': stats,
    }
    return render(request, 'profiles/seller-profile.html', context)

@login_required
@login_required
def rate_seller(request, seller_id):
    seller = get_object_or_404(Profile, id=seller_id)

    if request.method == 'POST':
        try:
            rating = int(request.POST.get('rating', 0))
            comment = request.POST.get('comment', '').strip()

            # Validate rating
            if rating < 1 or rating > 5:
                messages.error(request, "Invalid rating. Please select 1-5 stars.")
                return redirect('profiles:rate-seller', seller_id=seller_id)

            # Prevent self-rating
            if seller.user == request.user:
                messages.error(request, "You cannot rate yourself.")
                return redirect('profiles:seller-profile', pk=seller_id)

            # Create the review
            Review.objects.create(
                seller=seller,
                reviewer=request.user,
                rating=rating,
                comment=comment
            )

            messages.success(request, "Thank you for your review!")

        except ValueError:
            messages.error(request, "Invalid rating value.")
        except Exception as e:
            messages.error(request, str(e))

        return redirect('profiles:seller-profile', pk=seller_id)

    # Handle GET: show the form
    return render(request, 'profiles/rate-seller.html', {'seller': seller})


@login_required
def seller_store(request, pk):
    seller = get_object_or_404(Profile, pk=pk)
    
    # Get seller's ads with prefetched relationships
    seller_ads = Ads.objects.filter(seller=seller)\
        .select_related('category', 'county', 'city')\
        .prefetch_related('images')\
        .order_by('-date_created')
    
    # Get store statistics
    stats = {
        'total_ads': seller_ads.count(),
        'active_ads': seller_ads.filter(is_active=True, is_sold=False).count(),
        'rating': seller.received_reviews.aggregate(Avg('rating'))['rating__avg'] or 0,
        'reviews_count': seller.received_reviews.count(),
        'followers_count': seller.followers.count()  # Make sure this is correctly calculated
    }
    
    # Filter by category if provided
    category = request.GET.get('category')
    if category:
        seller_ads = seller_ads.filter(category__slug=category)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        seller_ads = seller_ads.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    context = {
        'seller': seller,
        'seller_ads': seller_ads,
        'stats': stats,
        'current_category': category,
        'search_query': search_query,
        'all_categories': Category.objects.all(),
    }
    
    return render(request, 'profiles/seller-store.html', context)

@login_required
def toggle_follow(request, seller_id):
    """Toggle following a seller"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        seller = get_object_or_404(Profile, id=seller_id, is_seller=True)
        user_profile = request.user.profile
        
        # Prevent self-following
        if (seller == user_profile):
            return JsonResponse({'error': 'You cannot follow yourself'}, status=400)
        
        is_following = seller.followers.filter(id=user_profile.id).exists()
        
        if (is_following):
            seller.followers.remove(user_profile)
        else:
            seller.followers.add(user_profile)
        
        return JsonResponse({
            'status': 'success',
            'is_following': not is_following,
            'followers_count': seller.followers.count()
        })
        
    except Profile.DoesNotExist:
        return JsonResponse({'error': 'Seller not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def following_list(request):
    """Display list of sellers that the user is following"""
    user_profile = request.user.profile
    
    # Get all sellers the user is following with their stats
    following_sellers = Profile.objects.filter(
        followers=user_profile
    ).annotate(
        avg_rating=Avg('received_reviews__rating'),
        reviews_count=Count('received_reviews'),
        total_ads=Count('ads'),
        active_ads_count=Count('ads', filter=Q(ads__is_active=True, ads__is_sold=False))
    ).select_related('user')
    
    context = {
        'following_sellers': following_sellers,
        'following_count': following_sellers.count()
    }
    
    return render(request, 'profiles/following_list.html', context)


@login_required
def delete_favorite_ad(request, ad_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method.'}, status=405)
    try:
        ad = get_object_or_404(Ads, id=ad_id)
        bookmark = Bookmark.objects.filter(profile=request.user.profile, ad=ad)
        if bookmark.exists():
            bookmark.delete()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success'})
            else:
                from django.contrib import messages
                messages.success(request, 'Ad removed from favorites.')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'not_found'}, status=404)
            else:
                from django.contrib import messages
                messages.error(request, 'Ad not found in your favorites.')
        return redirect('profiles:profile-favorite-ads')
    except Exception as e:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': str(e)}, status=400)
        else:
            from django.contrib import messages
            messages.error(request, 'An error occurred while removing the ad.')
            return redirect('profiles:profile-favorite-ads')
