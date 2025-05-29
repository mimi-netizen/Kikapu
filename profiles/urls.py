from django.urls import path
from . import views

app_name = 'profiles'

urlpatterns = [
    path('dashboard/', views.profile_dashboard, name='dashboard'),
    path('profile-settings/', views.profile_settings, name='profile-settings'),
    path('my-ads/', views.my_ads, name='profile-my-ads'),  # Make sure this matches the template
    path('favorite-ads/', views.profile_favorite_ads, name='profile-favorite-ads'),
    path('profile-close/', views.profile_close, name='profile-close'),
    path('sellers/', views.sellers_list, name='sellers'),
    path('store-settings/', views.store_settings, name='store-settings'),
    path('save-search/', views.save_search, name='save-search'),
    path('delete-saved-search/<int:search_id>/', views.delete_saved_search, name='delete-saved-search'),
    path('toggle-favorite-seller/<int:seller_id>/', views.toggle_favorite_seller, name='toggle-favorite-seller'),
    path('seller/<int:pk>/', views.seller_profile, name='seller-profile'),
    path('rate/<int:seller_id>/', views.rate_seller, name='rate_seller'),
    path('seller-store/<int:pk>/', views.seller_store, name='seller-store'),
    path('toggle-follow/<int:seller_id>/', views.toggle_follow, name='toggle-follow'),
    path('following/', views.following_list, name='following-list'),  # Changed from following_list to following-list
]