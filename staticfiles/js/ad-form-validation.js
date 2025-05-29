$(document).ready(function() {
    // Phone number validation
    function validatePhone(phone) {
        const regex = /^\+?254?\d{9,10}$/;
        return regex.test(phone);
    }

    // Image validation
    function validateImages(files) {
        if (files.length > 5) {
            return "Maximum 5 images allowed";
        }
        for (let file of files) {
            if (file.size > 3 * 1024 * 1024) {
                return `Image ${file.name} is too large. Maximum size is 3MB`;
            }
        }
        return null;
    }

    // Form validation
    $('#adForm').on('submit', function(e) {
        let isValid = true;
        const errors = [];

        // Title validation
        const title = $('#id_title').val();
        if (title.length < 10) {
            errors.push("Title must be at least 10 characters long");
            isValid = false;
        }

        // Description validation
        const description = $('#id_description').val();
        if (description.length < 30) {
            errors.push("Description must be at least 30 characters long");
            isValid = false;
        }

        // Phone validation
        const phone = $('#id_phone_number').val();
        if (!validatePhone(phone)) {
            errors.push("Please enter a valid phone number");
            isValid = false;
        }

        // Image validation
        const images = $('#id_images')[0].files;
        const imageError = validateImages(images);
        if (imageError) {
            errors.push(imageError);
            isValid = false;
        }

        // Price validation
        const price = parseFloat($('#id_price').val());
        if (price > 9999999.99) {
            errors.push("Price cannot exceed 9,999,999.99");
            isValid = false;
        }

        if (!isValid) {
            e.preventDefault();
            // Show errors in alert
            const errorList = errors.join('\n• ');
            alert('Please fix the following errors:\n• ' + errorList);
        }
    });

    // Dynamic city loading
    $('#id_county').change(function() {
        const countyId = $(this).val();
        updateCities(countyId);
    });

    function updateCities(countyId) {
        const citySelect = document.getElementById('id_city');
        citySelect.innerHTML = '<option value="">Select City</option>';
        if (countyId) {
            fetch(`/api/cities/${countyId}/`)
                .then(response => {
                    if (!response.ok) throw new Error('Network response was not ok');
                    return response.json();
                })
                .then(data => {
                    if (Array.isArray(data)) {
                        data.forEach(city => {
                            citySelect.add(new Option(city.name, city.id));
                        });
                    } else {
                        console.error("Expected an array for cities, got:", data);
                    }
                })
                .catch(error => console.error('Error:', error));
        }
    }
});
