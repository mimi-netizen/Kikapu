from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import MpesaPayment
from ads.models import Ads
from .utils import initiate_stk_push
import json
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@login_required
def initiate_payment(request, ad_id):
    ad = get_object_or_404(Ads, id=ad_id)
    
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        amount = 150  # Featured ad cost
        reference = f"AD{ad.id}"
        description = f"Featured Ad Payment for {ad.title}"
        
        # Create payment record
        payment = MpesaPayment.objects.create(
            ad=ad,
            phone_number=phone_number,
            amount=amount,
            reference=reference,
            description=description
        )
        
        # Initiate STK Push
        response = initiate_stk_push(
            phone_number=phone_number,
            amount=amount,
            reference=reference,
            description=description
        )
        
        if 'CheckoutRequestID' in response:
            payment.checkout_request_id = response['CheckoutRequestID']
            payment.merchant_request_id = response.get('MerchantRequestID')
            payment.save()
            return JsonResponse({'status': 'success', 'message': 'Payment initiated'})
        
        return JsonResponse({'status': 'error', 'message': 'Failed to initiate payment'})
    
    return render(request, 'payments/initiate_payment.html', {'ad': ad})

@csrf_exempt
def mpesa_callback(request):
    try:
        if request.method == 'POST':
            # Log the raw request body for debugging
            logger.info(f"M-Pesa Callback Raw Data: {request.body.decode()}")
            
            # Parse the JSON data
            data = json.loads(request.body)
            
            # Extract the necessary information
            body = data.get('Body', {})
            result = body.get('stkCallback', {})
            merchant_request_id = result.get('MerchantRequestID')
            checkout_request_id = result.get('CheckoutRequestID')
            result_code = result.get('ResultCode')
            
            # Log the parsed data
            logger.info(f"M-Pesa Callback Parsed Data: {data}")
            
            # Find the payment
            payment = MpesaPayment.objects.filter(
                checkout_request_id=checkout_request_id
            ).first()
            
            if payment:
                if result_code == 0:  # Successful payment
                    # Extract transaction details
                    callback_metadata = result.get('CallbackMetadata', {}).get('Item', [])
                    transaction_id = next((item.get('Value') for item in callback_metadata if item.get('Name') == 'MpesaReceiptNumber'), None)
                    
                    # Update payment
                    payment.status = 'COMPLETED'
                    payment.transaction_id = transaction_id
                    payment.save()
                    
                    # Update ad as featured
                    ad = payment.ad
                    ad.is_featured = True
                    ad.featured_until = datetime.now() + timedelta(days=7)
                    ad.save()
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Payment processed successfully'
                    })
                else:
                    # Payment failed
                    payment.status = 'FAILED'
                    payment.save()
                    
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Payment failed',
                        'result_code': result_code
                    })
            
            return JsonResponse({
                'status': 'error',
                'message': 'Payment record not found'
            })
            
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid request method'
        })
        
    except Exception as e:
        logger.error(f"M-Pesa Callback Error: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })
