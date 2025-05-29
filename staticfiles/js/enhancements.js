// Enhanced Header and UI Functionality

document.addEventListener('DOMContentLoaded', function() {
  // Sticky Header
  const stickyHeader = document.getElementById('sticky-header');
  const headerHeight = stickyHeader ? stickyHeader.offsetHeight : 0;
  
  // Create scroll progress bar
  const progressBar = document.createElement('div');
  progressBar.className = 'scroll-progress-bar';
  document.body.appendChild(progressBar);
  
  // Handle scroll events
  window.addEventListener('scroll', function() {
    // Update sticky header
    if (stickyHeader) {
      if (window.pageYOffset > headerHeight) {
        stickyHeader.classList.add('sticky');
      } else {
        stickyHeader.classList.remove('sticky');
      }
    }
    
    // Update scroll progress bar
    const scrollTop = document.documentElement.scrollTop || document.body.scrollTop;
    const scrollHeight = document.documentElement.scrollHeight || document.body.scrollHeight;
    const clientHeight = document.documentElement.clientHeight;
    const scrolled = (scrollTop / (scrollHeight - clientHeight)) * 100;
    progressBar.style.width = scrolled + '%';
  });
  
  // Add active class to current nav item
  const currentLocation = window.location.pathname;
  const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
  
  navLinks.forEach(link => {
    const linkPath = link.getAttribute('href');
    if (linkPath === currentLocation || 
        (currentLocation.includes(linkPath) && linkPath !== '/')) {
      link.classList.add('active');
    }
  });
  
  // Enhance dropdown menus with animation
  const dropdownToggles = document.querySelectorAll('.dropdown-toggle');
  
  dropdownToggles.forEach(toggle => {
    const dropdown = toggle.nextElementSibling;
    if (dropdown && dropdown.classList.contains('dropdown-menu')) {
      // Add animation classes
      dropdown.classList.add('animate__animated', 'animate__fadeIn', 'animate__faster');
    }
  });
});
