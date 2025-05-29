import requests
import base64
import json
from datetime import datetime
from django.conf import settings
from requests.auth import HTTPBasicAuth

def generate_access_token():
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    api_URL = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    r = requests.get(api_URL, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    return r.json()['access_token']

def generate_password(shortcode, passkey, timestamp):
    data = shortcode + passkey + timestamp
    encoded = base64.b64encode(data.encode())
    return encoded.decode('utf-8')

def initiate_stk_push(phone_number, amount, reference, description):
    access_token = generate_access_token()
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password = generate_password(
        settings.MPESA_EXPRESS_SHORTCODE,
        settings.MPESA_PASSKEY,
        timestamp
    )
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    
    payload = {
        'BusinessShortCode': settings.MPESA_EXPRESS_SHORTCODE,
        'Password': password,
        'Timestamp': timestamp,
        'TransactionType': 'CustomerPayBillOnline',
        'Amount': int(amount),
        'PartyA': phone_number,
        'PartyB': settings.MPESA_EXPRESS_SHORTCODE,
        'PhoneNumber': phone_number,
        'CallBackURL': 'https://e7dd-197-237-53-119.ngrok-free.app/payments/mpesa-callback/',
        'AccountReference': reference,
        'TransactionDesc': description
    }

    response = requests.post(
        'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest',
        json=payload,
        headers=headers
    )
    
    return response.json()