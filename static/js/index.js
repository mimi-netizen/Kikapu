// Main document ready function
document.addEventListener('DOMContentLoaded', function() {
  initBackToTop();
  initCategoriesDropdown();
  initCarousels();
  initCategoryNavigation();
  initSuperDealsTimer();
  initDealCategories();
  initStickyElements();
  initGooglePlaces();
});

// Back to Top functionality
function initBackToTop() {
  const backToTopButton = document.getElementById('back-to-top');
  if (backToTopButton) {
    window.addEventListener('scroll', function() {
      if (window.pageYOffset > 300) {
        backToTopButton.classList.add('visible');
      } else {
        backToTopButton.classList.remove('visible');
      }
    });
    
    backToTopButton.addEventListener('click', function() {
      window.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    });
  }
}

// Categories Dropdown functionality
function initCategoriesDropdown() {
  const categoriesDropdown = document.getElementById('categoriesDropdown');
  const mainCategoryItems = document.querySelectorAll('.all-category-main');
  const backButtons = document.querySelectorAll('.all-categories-back');
  let isDropdownOpen = false;

  if (categoriesDropdown) {
    // Toggle dropdown
    window.toggleCategoriesDropdown = function() {
      isDropdownOpen = !isDropdownOpen;
      categoriesDropdown.classList.toggle('show');
      document.querySelectorAll('.all-subcategories-menu').forEach(menu => {
        menu.style.display = 'none';
      });
    }

    // Close dropdown when clicking outside
    document.addEventListener('click', function(event) {
      const isClickInside = event.target.closest('.all-categories-dropdown');
      if (!isClickInside && isDropdownOpen) {
        toggleCategoriesDropdown();
      }
    });

    initCategoryInteractions(mainCategoryItems);
    initBackButtons(backButtons);
    initWindowResize(mainCategoryItems);
  }
}

// Category Interactions
function initCategoryInteractions(mainCategoryItems) {
  mainCategoryItems.forEach(item => {
    const handleMainCategoryInteraction = (e) => {
      const subcategoriesMenu = item.nextElementSibling;
      if (subcategoriesMenu) {
        if (window.innerWidth <= 992) {
          e.preventDefault();
          subcategoriesMenu.classList.add('show');
        } else {
          subcategoriesMenu.style.display = 'block';
        }
      }
    };

    const handleMainCategoryLeave = () => {
      const subcategoriesMenu = item.nextElementSibling;
      if (subcategoriesMenu && window.innerWidth > 992) {
        subcategoriesMenu.style.display = 'none';
      }
    };

    if (window.innerWidth > 992) {
      item.addEventListener('mouseenter', handleMainCategoryInteraction);
      item.addEventListener('mouseleave', handleMainCategoryLeave);
    } else {
      item.addEventListener('click', handleMainCategoryInteraction);
    }

    item._handleInteraction = handleMainCategoryInteraction;
    item._handleLeave = handleMainCategoryLeave;
  });
}

// Back Buttons
function initBackButtons(backButtons) {
  backButtons.forEach(button => {
    button.addEventListener('click', function(e) {
      e.stopPropagation();
      const subcategoriesMenu = button.closest('.all-subcategories-menu');
      if (subcategoriesMenu) {
        if (window.innerWidth <= 992) {
          subcategoriesMenu.classList.remove('show');
        } else {
          subcategoriesMenu.style.display = 'none';
        }
      }
    });
  });
}

// Window Resize
function initWindowResize(mainCategoryItems) {
  let previousWidth = window.innerWidth;
  window.addEventListener('resize', function() {
    if ((previousWidth <= 992 && window.innerWidth > 992) ||
        (previousWidth > 992 && window.innerWidth <= 992)) {
      updateEventListeners(mainCategoryItems);
      resetSubcategoryMenus();
    }
    previousWidth = window.innerWidth;
  });
}

// Update Event Listeners
function updateEventListeners(mainCategoryItems) {
  mainCategoryItems.forEach(item => {
    if (item._handleInteraction) {
      item.removeEventListener('mouseenter', item._handleInteraction);
      item.removeEventListener('click', item._handleInteraction);
    }
    if (item._handleLeave) {
      item.removeEventListener('mouseleave', item._handleLeave);
    }

    if (window.innerWidth > 992) {
      item.addEventListener('mouseenter', item._handleInteraction);
      if (item._handleLeave) {
        item.addEventListener('mouseleave', item._handleLeave);
      }
    } else {
      item.addEventListener('click', item._handleInteraction);
    }
  });
}

// Reset Subcategory Menus
function resetSubcategoryMenus() {
  document.querySelectorAll('.all-subcategories-menu').forEach(menu => {
    if (window.innerWidth > 992) {
      menu.style.display = 'none';
      menu.classList.remove('show');
    } else {
      menu.style.display = '';
      menu.classList.remove('show');
    }
  });
}

// Carousels
function initCarousels() {
  let heroSlideIndex = 1;
  let bottomSlideIndex = 1;
  let heroAutoAdvanceTimer;
  let bottomAutoAdvanceTimer;

  // Show Hero Slides
  function showHeroSlides(n) {
    const slides = document.getElementsByClassName("hero-carousel-slide");
    if (slides.length === 0) return;
    
    if (n > slides.length) { heroSlideIndex = 1 }
    if (n < 1) { heroSlideIndex = slides.length }
    
    for (let i = 0; i < slides.length; i++) {
      slides[i].style.display = "none";
    }
    
    slides[heroSlideIndex - 1].style.display = "block";
  }

  // Move Hero Slide
  window.moveHeroSlide = function(n) {
    if (heroAutoAdvanceTimer) {
      clearTimeout(heroAutoAdvanceTimer);
    }
    showHeroSlides(heroSlideIndex += n);
    startHeroAutoAdvance();
  }

  // Start Hero Auto Advance
  function startHeroAutoAdvance() {
    if (heroAutoAdvanceTimer) {
      clearTimeout(heroAutoAdvanceTimer);
    }
    heroAutoAdvanceTimer = setTimeout(() => {
      moveHeroSlide(1);
    }, 5000);
  }

  // Initialize carousels
  showHeroSlides(heroSlideIndex);
  startHeroAutoAdvance();

  // Add hover handlers
  const heroCarousel = document.querySelector('.hero-carousel-container');
  if (heroCarousel) {
    heroCarousel.addEventListener('mouseenter', () => {
      if (heroAutoAdvanceTimer) {
        clearTimeout(heroAutoAdvanceTimer);
      }
    });
    
    heroCarousel.addEventListener('mouseleave', () => {
      startHeroAutoAdvance();
    });
  }
}

// Category Navigation
function initCategoryNavigation() {
  const categoryItems = document.querySelectorAll('.category-item');
  const itemsPerPage = 6;
  let currentPage = 0;

  function showCategories(page) {
    const startIndex = page * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    
    categoryItems.forEach((item, index) => {
      if (index >= startIndex && index < endIndex) {
        item.style.display = 'block';
        setTimeout(() => item.style.opacity = '1', 10);
      } else {
        item.style.display = 'none';
        item.style.opacity = '0';
      }
    });
    
    updateNavigationButtons(page);
    updatePaginationIndicator(page);
  }

  function updateNavigationButtons(page) {
    const prevBtn = document.querySelector('.category-nav-btn.prev');
    const nextBtn = document.querySelector('.category-nav-btn.next');
    
    if (prevBtn && nextBtn) {
      prevBtn.disabled = page === 0;
      nextBtn.disabled = (page + 1) * itemsPerPage >= categoryItems.length;
    }
  }

  function updatePaginationIndicator(page) {
    const indicator = document.querySelector('.pagination-indicator');
    if (indicator) {
      const totalPages = Math.ceil(categoryItems.length / itemsPerPage);
      indicator.textContent = `Page ${page + 1} of ${totalPages}`;
    }
  }

  // Initialize
  showCategories(currentPage);
}

// SuperDeals Timer
function initSuperDealsTimer() {
  function updateTimer() {
    const countdownElement = document.getElementById('superdeals-countdown');
    if (!countdownElement) return;

    const now = new Date();
    const endTime = new Date();
    endTime.setHours(23, 59, 59);

    const timeDiff = endTime - now;
    if (timeDiff <= 0) {
      countdownElement.innerHTML = 'Ended';
      return;
    }

    const hours = Math.floor(timeDiff / (1000 * 60 * 60));
    const minutes = Math.floor((timeDiff % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((timeDiff % (1000 * 60)) / 1000);

    const timeElement = countdownElement.querySelector('.time');
    if (timeElement) {
      timeElement.textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
  }

  // Update timer every second
  const timer = document.getElementById('superdeals-countdown');
  if (timer) {
    setInterval(updateTimer, 1000);
    updateTimer();
  }
}

// Deal Categories
function initDealCategories() {
  const categoryCards = document.querySelectorAll('.deal-category-card');
  categoryCards.forEach(card => {
    card.addEventListener('click', function(e) {
      e.preventDefault();
      const targetId = this.getAttribute('href').substring(1);

      categoryCards.forEach(c => c.classList.remove('active'));
      this.classList.add('active');

      document.querySelectorAll('.deals-products').forEach(content => {
        content.classList.remove('active');
      });
      document.getElementById(targetId).classList.add('active');
    });
  });
}

// Sticky Elements
function initStickyElements() {
  const sidebar = document.querySelector('.sticky-sidebar');
  const header = document.querySelector('header');
  
  function updateSidebarPosition() {
    if (header && sidebar && window.innerWidth > 991) {
      const headerHeight = header.offsetHeight;
      sidebar.style.top = `${headerHeight + 15}px`;
      sidebar.style.maxHeight = `calc(100vh - ${headerHeight + 30}px)`;
    } else if (sidebar) {
      sidebar.style.top = '';
      sidebar.style.maxHeight = '';
    }
  }

  if (sidebar) {
    updateSidebarPosition();
    window.addEventListener('resize', updateSidebarPosition);
    window.addEventListener('scroll', updateSidebarPosition);
  }
}

// Google Places Integration
function initGooglePlaces() {
  const locationInput = document.getElementById('id_location');
  if (locationInput && typeof google !== 'undefined' && google.maps && google.maps.places) {
    try {
      new google.maps.places.Autocomplete(locationInput);
    } catch (error) {
      console.warn('Google Maps Places Autocomplete initialization failed:', error);
    }
  }
}

// Age Verification
let categoryTarget = null;

function showAgeVerification(event, categorySlug) {
  event.preventDefault();
  categoryTarget = categorySlug;
  document.getElementById('ageVerifyModal').style.display = 'block';
  document.body.style.overflow = 'hidden';
}

function verifyAge(isAdult) {
  const modal = document.getElementById('ageVerifyModal');
  document.body.style.overflow = 'auto';
  
  if (isAdult) {
    modal.style.display = 'none';
    if (categoryTarget) {
      window.location.href = `/category/${categoryTarget}/`;
    }
  } else {
    modal.style.display = 'none';
    if (typeof toastr !== 'undefined') {
      toastr.warning("Sorry! You must be 18 or older to view this category. Try checking out our other awesome categories!");
    } else {
      alert("Sorry! You must be 18 or older to view this category. Try checking out our other awesome categories!");
    }
  }
  categoryTarget = null;
}

// Login Modal
function showLoginPrompt() {
  const modal = document.getElementById('loginPromptModal');
  if (modal && typeof bootstrap !== 'undefined') {
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
  }
}

// Category Slider
function slideCategories(direction) {
  const wrapper = document.querySelector('.category-wrapper');
  if (wrapper) {
    const scrollAmount = wrapper.offsetWidth / 2;
    wrapper.scrollBy({
      left: direction === 'next' ? scrollAmount : -scrollAmount,
      behavior: 'smooth'
    });
  }
}