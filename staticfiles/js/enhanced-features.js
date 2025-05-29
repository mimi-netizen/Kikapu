
// Search Autocomplete
const initSearchAutocomplete = () => {
  const searchInput = document.querySelector('.search-autocomplete');
  const suggestions = document.querySelector('.search-suggestions');
  
  searchInput?.addEventListener('input', debounce(async (e) => {
    const query = e.target.value;
    if (query.length < 2) {
      suggestions.style.display = 'none';
      return;
    }
    
    try {
      const response = await fetch(`/api/search-suggestions/?q=${query}`);
      const data = await response.json();
      
      if (data.suggestions?.length) {
        suggestions.innerHTML = data.suggestions
          .map(s => `<div class="suggestion-item">${s}</div>`)
          .join('');
        suggestions.style.display = 'block';
      }
    } catch (err) {
      console.error('Search suggestion error:', err);
    }
  }, 300));
};

// Location Services
const initLocationServices = () => {
  const locationBtn = document.querySelector('.use-location-btn');
  const locationInput = document.querySelector('.location-autocomplete');
  
  locationBtn?.addEventListener('click', () => {
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(async (position) => {
        const { latitude, longitude } = position.coords;
        try {
          const response = await fetch(
            `/api/reverse-geocode/?lat=${latitude}&lng=${longitude}`
          );
          const data = await response.json();
          locationInput.value = data.formatted_address;
        } catch (err) {
          console.error('Geocoding error:', err);
        }
      });
    }
  });
};

// Initialize all enhancements
document.addEventListener('DOMContentLoaded', () => {
  initSearchAutocomplete();
  initLocationServices();
  
  // Initialize animations
  AOS.init();
  
  // Initialize lazy loading
  const lazyImages = document.querySelectorAll('img[data-src]');
  const imageObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target;
        img.src = img.dataset.src;
        img.classList.add('fade-in');
        observer.unobserve(img);
      }
    });
  });
  
  lazyImages.forEach(img => imageObserver.observe(img));
});
