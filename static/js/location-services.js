
class LocationService {
    constructor() {
        this.locationInput = document.querySelector('.location-autocomplete');
        this.locationBtn = document.querySelector('.use-location-btn');
        this.searchRadius = 50; // Default 50km radius
        
        // Initialize Google Places Autocomplete
        if (this.locationInput) {
            this.initAutocomplete();
        }
        
        // Initialize geolocation button
        if (this.locationBtn) {
            this.initGeolocation();
        }
    }

    initAutocomplete() {
        // Initialize Google Places Autocomplete
        const autocomplete = new google.maps.places.Autocomplete(this.locationInput, {
            componentRestrictions: { country: 'KE' }, // Restrict to Kenya
            types: ['(cities)'], // Restrict to cities
            fields: ['address_components', 'geometry', 'name']
        });

        // Handle place selection
        autocomplete.addListener('place_changed', () => {
            const place = autocomplete.getPlace();
            if (place.geometry) {
                const lat = place.geometry.location.lat();
                const lng = place.geometry.location.lng();
                this.updateLocationData(lat, lng, place.name);
            }
        });
    }

    initGeolocation() {
        this.locationBtn.addEventListener('click', () => {
            if ('geolocation' in navigator) {
                // Show loading state
                this.locationBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
                this.locationBtn.disabled = true;

                navigator.geolocation.getCurrentPosition(
                    position => this.handleGeolocationSuccess(position),
                    error => this.handleGeolocationError(error),
                    { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }
                );
            } else {
                this.showError('Geolocation is not supported by your browser');
            }
        });
    }

    async handleGeolocationSuccess(position) {
        try {
            const { latitude, longitude } = position.coords;
            const response = await this.reverseGeocode(latitude, longitude);
            
            if (response.results[0]) {
                const address = response.results[0].formatted_address;
                this.locationInput.value = address;
                this.updateLocationData(latitude, longitude, address);
            }
        } catch (error) {
            this.showError('Could not determine your location');
        } finally {
            // Reset button state
            this.locationBtn.innerHTML = '<i class="fas fa-crosshairs"></i>';
            this.locationBtn.disabled = false;
        }
    }

    handleGeolocationError(error) {
        let errorMessage = 'Could not determine your location';
        
        switch(error.code) {
            case error.PERMISSION_DENIED:
                errorMessage = 'Please allow location access to use this feature';
                break;
            case error.POSITION_UNAVAILABLE:
                errorMessage = 'Location information is unavailable';
                break;
            case error.TIMEOUT:
                errorMessage = 'Location request timed out';
                break;
        }
        
        this.showError(errorMessage);
        this.locationBtn.innerHTML = '<i class="fas fa-crosshairs"></i>';
        this.locationBtn.disabled = false;
    }

    async reverseGeocode(lat, lng) {
        const response = await fetch(`/api/reverse-geocode/?lat=${lat}&lng=${lng}`);
        if (!response.ok) throw new Error('Geocoding failed');
        return response.json();
    }

    updateLocationData(lat, lng, address) {
        // Update hidden inputs with location data
        const locationData = {
            latitude: lat,
            longitude: lng,
            address: address,
            timestamp: Date.now()
        };
        
        // Store location data in localStorage
        localStorage.setItem('userLocation', JSON.stringify(locationData));
        
        // Dispatch custom event
        window.dispatchEvent(new CustomEvent('locationUpdated', { 
            detail: locationData 
        }));
    }

    showError(message) {
        // Create error toast
        const toast = document.createElement('div');
        toast.className = 'location-error-toast';
        toast.innerHTML = `
            <i class="fas fa-exclamation-circle"></i>
            <span>${message}</span>
        `;
        
        document.body.appendChild(toast);
        
        // Remove toast after 3 seconds
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
}

// Initialize location service when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new LocationService();
});
