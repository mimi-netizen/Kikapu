from django.http import JsonResponse
from django.conf import settings
import requests

def reverse_geocode(request):
    lat = request.GET.get('lat')
    lng = request.GET.get('lng')
    
    if not lat or not lng:
        return JsonResponse({'error': 'Missing coordinates'}, status=400)
    
    try:
        # Using Google Maps Geocoding API
        url = f"https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'latlng': f"{lat},{lng}",
            'key': settings.GOOGLE_MAPS_API_KEY,
            'result_type': 'locality|administrative_area_level_1',  # Get city and county
            'language': 'en'
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if data['status'] == 'OK':
            return JsonResponse(data)
        else:
            return JsonResponse({'error': 'Geocoding failed'}, status=400)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
