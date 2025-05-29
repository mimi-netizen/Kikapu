from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.shortcuts import render, redirect, HttpResponse, get_object_or_404, Http404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import UserRegistrationForm
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .tokens import account_activation_token
from django.http import JsonResponse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from profiles.models import Profile
from django.core.mail import EmailMessage
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

def resend_activation(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email, is_active=False)
            current_site = get_current_site(request)
            
            # Prepare email
            mail_subject = 'Activate your Kikapu account'
            context = {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
                'protocol': 'https' if request.is_secure() else 'http'
            }
            
            html_message = render_to_string('authentication/confirm-email.html', context)
            plain_message = strip_tags(html_message)
            
            email = EmailMultiAlternatives(
                mail_subject,
                plain_message,
                settings.EMAIL_HOST_USER,
                [user.email]
            )
            email.attach_alternative(html_message, "text/html")
            email.send()
            
            messages.success(request, 'Activation email has been resent. Please check your inbox.')
            return redirect('signup-success')
            
        except User.DoesNotExist:
            messages.error(request, 'No inactive account found with this email.')
            return redirect('signup')
    
    return redirect('login')

def signup_view(request):       
    if request.method == 'POST':
        reg_form = UserRegistrationForm(request.POST)
        logger.debug(f"Form data: {request.POST}")

        if reg_form.is_valid():
            logger.debug("Form is valid")
            try:
                with transaction.atomic():
                    # Create inactive user
                    user = reg_form.save(commit=False)
                    user.is_active = False
                    user.save()
                    logger.debug(f"Created user: {user.username}")

                    # Update the profile created by signal
                    user.profile.is_seller = reg_form.cleaned_data['account_type'] == 'seller'
                    user.profile.save()
                    logger.debug(f"Updated profile for user: {user.username}")

                    # Send activation email with updated context
                    current_site = get_current_site(request)
                    mail_subject = 'Activate your Kikapu account'
                    domain = settings.DOMAIN  # Use the domain from settings
                    context = {
                        'user': user,
                        'domain': domain,
                        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                        'token': account_activation_token.make_token(user),
                        'protocol': 'https' if request.is_secure() else 'http'
                    }
                    
                    html_message = render_to_string('authentication/confirm-email.html', context)
                    plain_message = strip_tags(html_message)
                    
                    email = EmailMultiAlternatives(
                        mail_subject,
                        plain_message,
                        settings.EMAIL_HOST_USER,
                        [user.email]
                    )
                    email.attach_alternative(html_message, "text/html")
                    email.send(fail_silently=False)
                    logger.debug(f"Sent activation email to: {user.email}")
                    
                    messages.success(request, 'Please check your email to complete registration.')
                    return redirect('signup-success')

            except Exception as e:
                logger.error(f"Registration failed with error: {str(e)}")
                messages.error(request, f'Registration failed: {str(e)}')
                return render(request, 'authentication/register.html', {'reg_form': reg_form})
        else:
            logger.debug(f"Form errors: {reg_form.errors}")
            messages.error(request, 'Please correct the errors below.')
                            
    else:
        reg_form = UserRegistrationForm()

    context = {
        'reg_form': reg_form,
    }
    return render(request, 'authentication/register.html', context)



def signup_success_view(request):
    return render(request, 'authentication/signup-success.html')

def account_activate_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        
        if account_activation_token.check_token(user, token):
            user.is_active = True
            user.save()
            messages.success(request, 'Your account has been activated successfully! You can now login.')
            return redirect('login')
        else:
            messages.error(request, 'Invalid activation link.')
            return redirect('login')
            
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        messages.error(request, 'Invalid activation link.')
        return redirect('login')
    

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(email=email)
            user = authenticate(username=user.username, password=password)
            
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return redirect('profiles:dashboard')
                else:
                    messages.error(request, 'Please activate your account first. Check your email for the activation link.')
            else:
                messages.error(request, 'Invalid email or password.')
        except User.DoesNotExist:
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'authentication/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def check_session(request):
    # Check if the user's session is still valid
    if request.user.is_authenticated:
        return JsonResponse({'authenticated': True})
    return JsonResponse({'authenticated': False})