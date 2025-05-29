from django.urls import path
from django.contrib.auth import views as auth_views
from authentication.forms import EmailValidationOnForgotPassword, EmailSetPassword

from . import views

urlpatterns = [
    path('register/', views.signup_view, name='register'),
    path('signup-success/', views.signup_success_view, name='signup-success'),
    path('activate/<str:uidb64>/<str:token>/', views.account_activate_view, name='activate'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Add this new path for resending activation email
    path('resend-activation/', views.resend_activation, name='resend_activation'),

    path('password-reset/', auth_views.PasswordResetView.as_view(
        form_class=EmailValidationOnForgotPassword, 
        template_name="authentication/password-reset.html"
    ), name="reset_password"),

    path('password-reset-message/', auth_views.PasswordResetDoneView.as_view(
        template_name="authentication/password-reset-message.html"
    ), name="password_reset_done"),

    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        form_class=EmailSetPassword,
        template_name="authentication/password-reset-confirm.html"
    ), name="password_reset_confirm"),

    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name="authentication/password-reset-complete.html"
    ), name="password_reset_complete"),  

    path('check-session/', views.check_session, name='check-session'),
]