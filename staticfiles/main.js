"use strict";
(function($) {
  $(window).on('load', function() {
    $('#preloader').fadeOut();
  });

  /* Sticky Nav */
  $(window).on('scroll', function() {
    if ($(window).scrollTop() > 100) {
      $('.scrolling-navbar').addClass('top-nav-collapse');
    } else {
      $('.scrolling-navbar').removeClass('top-nav-collapse');
    }
  });

  /* slicknav mobile menu active */
  $('.mobile-menu').slicknav({
    prependTo: '.navbar-header',
    parentTag: 'liner',
    allowParentLinks: true,
    duplicate: true,
    label: '',
    closedSymbol: '<i class="lni-chevron-right"></i>',
    openedSymbol: '<i class="lni-chevron-down"></i>',
  });

  /* WOW Scroll Spy */
  var wow = new WOW({
    mobile: false
  });
  wow.init();

  /* Nivo Lightbox */
  $('.lightbox').nivoLightbox({
    effect: 'fadeScale',
    keyboardNav: true,
  });

  /* Counter */
  $('.counterUp').counterUp({
    delay: 10,
    time: 1000
  });

  /* Search */
  $('.search-query .form-control').on('click', function(e){
    e.stopPropagation();
    $(this).parent().toggleClass('query-focus');
  });
  $('body').on('click', function() {
    if ($('.search-query').hasClass('query-focus')) {
      $('.search-query').removeClass('query-focus');
    }
  });
  $('.search-suggestion').on('click', function(e) {
    e.stopPropagation();
  });

  /* Testimonials Carousel */
  var owl = $("#testimonials");
  owl.owlCarousel({
    navigation: false,
    pagination: true,
    slideSpeed: 1000,
    stopOnHover: true,
    autoPlay: true,
    items: 2,
    itemsDesktop : [1199,2],
    itemsDesktopSmall : [980,2],
    itemsTablet: [768,1],
    itemsTablet: [767,1],
    itemsTabletSmall: [480,1],
    itemsMobile : [479,1],
  });

  /* New Products Owl Carousel */
  $("#new-products").owlCarousel({
    navigation: true,
    pagination: false,
    slideSpeed: 1000,
    stopOnHover: true,
    autoPlay: false,
    items: 3,
    itemsDesktop : [1199,3],
    itemsDesktopSmall : [980,2],
    itemsTablet: [768,1],
    itemsTablet: [767,1],
    itemsTabletSmall: [480,1],
    itemsMobile : [479,1],
  });

  /* New Products Owl Carousel */
  $("#categories-icon-slider").owlCarousel({
    navigation: false,
    pagination: false,
    slideSpeed: 1000,
    stopOnHover: true,
    autoPlay: true,
    items: 5,
    itemsDesktop : [1199,3],
    itemsDesktopSmall : [980,4],
    itemsTablet: [768,3],
    itemsTablet: [767,3],
    itemsTabletSmall: [480,2],
    itemsMobile : [479,2],
  });

  /* owl Carousel active */
  var owl;
  $(document).ready(function () {
    owl = $("#owl-demo");
    owl.owlCarousel({
      navigation: false, // Show next and prev buttons
      slideSpeed: 300,
      paginationSpeed: 400,
      singleItem: true,
      afterInit: afterOWLinit, // do some work after OWL init
      afterUpdate : afterOWLinit
    });

    function afterOWLinit() {
      // adding A to div.owl-page
      $('.owl-controls .owl-page').append('<a class="item-link" />');
      var pafinatorsLink = $('.owl-controls .item-link');
      $.each(this.owl.userItems, function (i) {
        /** 
         * this.owl.userItems - it's your HTML <div class="item"><img src="http://www.ow...t of us"></div>
         */
        $(pafinatorsLink[i])
          // Give some styles and set background image for pagination item
          .css({
            'background': 'url(' + $(this).find('img').attr('src') + ') center center no-repeat',
            '-webkit-background-size': 'cover',
            '-moz-background-size': 'cover',
            '-o-background-size': 'cover',
            'background-size': 'cover'
          })
          // set Custom Event for pagination item
          .click(function () {
            owl.trigger('owl.goTo', i);
          });
      });
      // add Custom PREV NEXT controls
      $('.owl-pagination').prepend('<a href="#prev" class="prev-owl"/>');
      $('.owl-pagination').append('<a href="#next" class="next-owl"/>');
      // set Custom event for NEXT custom control
      $(".next-owl").click(function () {
        owl.trigger('owl.next');
      });
      // set Custom event for PREV custom control
      $(".prev-owl").click(function () {
        owl.trigger('owl.prev');
      });
    }
  });

  /* Editor Note Js */
  $('#summernote').summernote({
    height: 250,                 // set editor height
    minHeight: null,             // set minimum height of editor
    maxHeight: null,             // set maximum height of editor
    focus: false                  // set focus to editable area after initializing summernote
  });

  /* Back Top Link active */
  var offset = 200;
  var duration = 500;
  $(window).scroll(function() {
    if ($(this).scrollTop() > offset) {
      $('.back-to-top').fadeIn(400);
    } else {
      $('.back-to-top').fadeOut(400);
    }
  });
  $('.back-to-top').on('click',function(event) {
    event.preventDefault();
    $('html, body').animate({
      scrollTop: 0
    }, 600);
    return false;
  });

  /* Product Grids active */
  var itemList = $('.item-list');
  var gridStyle = $('.grid');
  var listStyle = $('.list');
  $('.list,switchToGrid').on('click',function(e) {
    e.preventDefault();
    itemList.removeClass("make-grid");
    itemList.removeClass("make-compact");
    itemList.addClass("make-list");
    gridStyle.removeClass("active");
    listStyle.addClass("active");
  });
  gridStyle.on('click',function(e) {
    e.preventDefault();
    itemList.removeClass("make-list");
    itemList.removeClass("make-compact");
    itemList.addClass("make-grid");
    listStyle.removeClass("active");
    $(this).addClass("active");
  });

  /* Handle County-City Selection */
  $(document).ready(function() {
    const countySelect = document.getElementById('id_county');
    const citySelect = document.getElementById('id_city');

    if (countySelect && citySelect) {
      function updateCities(countyId) {
        const citySelect = document.getElementById('id_city');
        citySelect.innerHTML = '<option value="">Select City</option>';
        if (countyId) {
          // Ensure the new endpoint is used
          fetch(`/api/cities/${countyId}/`)
            .then(response => {
              if (!response.ok) throw new Error('Network response was not ok');
              return response.json();
            })
            .then(data => {
              data.forEach(city => {
                citySelect.add(new Option(city.name, city.id));
              });
            })
            .catch(error => console.error('Error:', error));
        }
      }

      if (countySelect.value) {
        // If county is already selected (e.g., in edit form), load its cities
        updateCities(countySelect.value);
      }

      // Add event listener to county select
      countySelect.addEventListener('change', (e) => {
        updateCities(e.target.value);
      });
    }
  });
}(jQuery));