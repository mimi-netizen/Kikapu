from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Banner
from payments.utils import initiate_stk_push

@login_required
def purchase_banner(request):
    if request.method == 'POST':
        image = request.FILES.get('banner_image')
        duration = int(request.POST.get('duration', 1))
        phone_number = request.POST.get('phone_number')
        
        # Calculate price based on duration
        prices = {1: 500, 2: 900, 4: 1600}
        amount = prices.get(duration, 500)
        
        # Create unpublished banner
        banner = Banner.objects.create(
            user=request.user,
            image=image,
            is_active=False
        )
        
        # Initiate payment
        response = initiate_stk_push(
            phone_number=phone_number,
            amount=amount,
            reference=f"BANNER{banner.id}",
            description=f"Banner Ad Payment for {duration} weeks"
        )
        
        if 'CheckoutRequestID' in response:
            return JsonResponse({'status': 'success', 'message': 'Payment initiated'})
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})
