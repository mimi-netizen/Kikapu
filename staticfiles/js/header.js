document.addEventListener('DOMContentLoaded', function() {
  console.log('header.js loaded');
  // Toggle mobile search bar using event delegation
  document.addEventListener('click', function(e) {
    if (e.target.closest('.mobile-search-toggle')) {
      console.log('Search toggle clicked');
      e.preventDefault();
      e.stopPropagation();
      const searchBar = document.querySelector('.mobile-search-bar');
      if (searchBar) {
        searchBar.classList.toggle('d-none');
        if (!searchBar.classList.contains('d-none')) {
          searchBar.querySelector('input').focus();
        }
      } else {
        console.log('Search bar not found');
      }
    } else {
      // Close search bar when clicking outside
      const searchBar = document.querySelector('.mobile-search-bar');
      const searchToggle = document.querySelector('.mobile-search-toggle');
      if (searchBar && searchToggle && !searchToggle.contains(e.target) && !searchBar.contains(e.target)) {
        searchBar.classList.add('d-none');
      }
    }
  });
});
