// Bottom Banner Carousel Functionality
let currentBottomIndex = 0;
const bottomSlides = document.getElementsByClassName('bottom-carousel-slide');

// Show the slide at the given index
function showBottomSlide(index) {
  for (let i = 0; i < bottomSlides.length; i++) {
    bottomSlides[i].style.display = 'none';
  }
  bottomSlides[index].style.display = 'block';
}

// Move to the next or previous slide
function moveBottomSlide(direction) {
  currentBottomIndex += direction;
  if (currentBottomIndex < 0) {
    currentBottomIndex = bottomSlides.length - 1;
  } else if (currentBottomIndex >= bottomSlides.length) {
    currentBottomIndex = 0;
  }
  showBottomSlide(currentBottomIndex);
}

// Initialize the carousel when the page loads
document.addEventListener('DOMContentLoaded', function() {
  if (bottomSlides.length > 0) {
    showBottomSlide(currentBottomIndex);
    // Auto-advance slides every 4 seconds
    setInterval(function() {
      moveBottomSlide(1);
    }, 4000);
  }
});
