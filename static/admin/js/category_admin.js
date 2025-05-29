(function() {
    'use strict';
    
    function initCategoryAdmin() {
        if (typeof django === 'undefined' || !django.jQuery) {
            setTimeout(initCategoryAdmin, 100);
            return;
        }

        const $ = django.jQuery;
        const categorySelect = $('#id_category');
        const parentSelect = $('#id_parent');
        
        if (categorySelect.length && parentSelect.length) {
            categorySelect.on('change', function() {
                const selected = $(this).find(':selected');
                if (!selected.length) return;
                
                const optgroup = selected.parent('optgroup');
                
                // Reset parent selection
                parentSelect.val('');
                
                if (optgroup.length && optgroup.attr('label') === 'Subcategories') {
                    const mainCategory = selected.text().split(' → ')[0];
                    
                    parentSelect.find('option').each(function() {
                        if ($(this).text() === mainCategory) {
                            parentSelect.val($(this).val());
                        }
                    });
                }
                
                parentSelect.prop('disabled', optgroup.length && optgroup.attr('label') === 'Main Categories');
            });
            
            // Trigger initial state
            categorySelect.trigger('change');
        }
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCategoryAdmin);
    } else {
        initCategoryAdmin();
    }
})();
