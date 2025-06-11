from django.urls import path
from . import views

app_name = 'ads'

urlpatterns = [
    path('post-ads/', views.post_ads, name='post-ads'),
    path('ads-listing/', views.ads_listing, name='ads-listing'),
    path('ads/<int:pk>/', views.ads_detail, name='ads-detail'),
    # path('ads/<int:pk>/delete/', views.delete_ad, name='ads-delete'),
    path('ads/<int:pk>/edit/', views.edit_ad, name='ads-edit'),
    path('category/', views.Category, name='category'), 
    path('category/<slug:category_slug>/', views.ads_by_category, name='category-archive'),
    path('county/<slug:county_slug>/', views.ads_by_county, name='county-archive'),
    path('city/<slug:city_slug>/', views.ads_by_city, name='city-archive'),
    path('seller/<int:pk>/', views.seller_profile, name='seller-profile'),
    path('seller/<int:pk>/ads/', views.ads_author_archive, name='seller-archive'),
    path('ads-search/', views.ads_search, name='ads-search'),
    path('inbox/', views.inbox, name='inbox'),
    path('conversation/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('conversation/<int:conversation_id>/delete/', views.delete_conversation, name='delete_conversation'),
    path('send-message/<int:ad_id>/', views.send_message, name='send-message'),
    path('toggle-bookmark/<int:ad_id>/', views.toggle_bookmark, name='toggle-bookmark'),
    path('bookmarks/', views.bookmarks, name='bookmarks'),
    path('ads/get-more-ads/<int:ad_id>/', views.get_more_ads, name='get-more-ads'),
    path('post-featured-ad/', views.post_featured_ad, name='post-featured-ad'),
    path('api/cities/<int:county_id>/', views.get_cities, name='get_cities'),
    path('featured-slots/', views.check_featured_slots, name='check-featured-slots'),
    path('delete/<int:pk>/', views.delete_ad, name='ads-delete'),
    path('my-ads/', views.my_ads, name='my-ads'),
    path('api/price-suggestions/<int:category_id>/', views.get_price_suggestions, name='price-suggestions'),
    path('api/auto-save-draft/', views.auto_save_draft, name='auto-save-draft'),
    path('featured-ad/check/<int:ad_id>/', views.check_featured_status, name='check-featured-status'),
    path('get-subcategories/', views.get_subcategories, name='get-subcategories'),
]