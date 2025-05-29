
// Intersection Observer for scroll animations
const animateOnScroll = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('animate');
    }
  });
}, { threshold: 0.1 });

// Apply to elements
document.querySelectorAll('.animate-on-scroll').forEach((element) => {
  animateOnScroll.observe(element);
});

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    e.preventDefault();
    document.querySelector(this.getAttribute('href')).scrollIntoView({
      behavior: 'smooth'
    });
  });
});

// Image lazy loading with fade
const lazyLoad = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const img = entry.target;
      img.src = img.dataset.src;
      img.classList.add('fade-in');
      lazyLoad.unobserve(img);
    }
  });
});

document.querySelectorAll('img[data-src]').forEach(img => lazyLoad.observe(img));

// Parallax effect
document.addEventListener('scroll', () => {
  const parallaxElements = document.querySelectorAll('.parallax');
  parallaxElements.forEach(element => {
    const speed = element.dataset.speed || 0.5;
    const offset = window.pageYOffset * speed;
    element.style.transform = `translateY(${offset}px)`;
  });
});

// Smooth counter animation
function animateCounter(element, target) {
  let current = 0;
  const increment = target / 100;
  const animation = setInterval(() => {
    current += increment;
    element.textContent = Math.floor(current);
    if (current >= target) {
      element.textContent = target;
      clearInterval(animation);
    }
  }, 10);
}

// Initialize counters
document.querySelectorAll('.counter').forEach(counter => {
  animateCounter(counter, parseInt(counter.dataset.target));
});
