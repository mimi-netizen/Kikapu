from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Ads, AdsImages, Category, City, County, Conversation, Message, HeroBanner, AdsBottomBanner, AdsRightBanner, AdsTopBanner, HeroBanner
)
from django import forms
from .models import SUBCATEGORY_PARENT_MAPPING

class AdsImagesInline(admin.StackedInline):
    model = AdsImages
    extra = 1  # Adds one empty upload slot by default
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="100" style="object-fit:cover;" />'.format(obj.image.url))
        return 'No image'

class AdsAdmin(admin.ModelAdmin):
    list_display = (
        'ad_id',
        'title', 
        'price', 
        'seller', 
        'category', 
        'county', 
        'city', 
        'date_created', 
        'is_featured',
        'is_sold'
    )
    
    list_display_links = ('ad_id', 'title')
    list_editable = ['is_featured', 'is_sold']
    search_fields = ('title', 'price', 'county__county_name', 'city__city_name', 'category', 'seller__user__username')
    search_help_text = 'Search by title, price, county, city, category or seller'
    list_filter = ('price', 'date_created', 'county', 'city', 'is_featured', 'is_sold', 'category')
    list_per_page = 20

    inlines = [AdsImagesInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('seller', 'category', 'county', 'city')

class AdsImagesAdmin(admin.ModelAdmin):
    list_display = ('id', 'ad', 'image_preview', 'is_primary')
    search_help_text = 'Search by associated ad'
    search_fields = ('ad__title',)
    list_per_page = 20
    list_editable = ['is_primary']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="100" style="object-fit:cover;" />'.format(obj.image.url))
        return 'No image'

class CountyAdmin(admin.ModelAdmin):
    list_display = ('county_name', 'slug')
    prepopulated_fields = {'slug': ('county_name',)}
    search_fields = ('county_name', 'slug')
    search_help_text = 'Search by county name or slug'
    list_per_page = 20

class CityAdmin(admin.ModelAdmin):
    list_display = ('city_name', 'county', 'slug')
    list_filter = ('county',)
    prepopulated_fields = {'slug': ('city_name',)}
    search_fields = ('city_name', 'slug', 'county__county_name')
    search_help_text = 'Search by city name, slug, or county'
    list_per_page = 20

class CategoryAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Extract main categories and their subcategories from CATEGORY_CHOICES
        main_categories = []
        subcategories = []
        
        for main_cat, subs in Category.CATEGORY_CHOICES:
            if isinstance(subs, (tuple, list)):
                main_categories.append((main_cat, main_cat))
                for sub in subs:
                    if isinstance(sub, (tuple, list)) and len(sub) == 2:
                        subcategories.append((sub[0], f"{main_cat} → {sub[0]}"))

        # Set choices based on whether editing main category or subcategory
        if self.instance.pk:
            if self.instance.parent is None:
                self.fields['category'].choices = main_categories
            else:
                parent_category = self.instance.parent.category
                self.fields['category'].choices = [
                    (sub[0], sub[1]) for sub in subcategories 
                    if sub[1].startswith(parent_category)
                ]
        else:
            # For new categories
            self.fields['category'].choices = [
                ('Main Categories', main_categories),
                ('Subcategories', subcategories)
            ]

        # Clear and set parent choices to only main categories
        self.fields['parent'].queryset = Category.objects.filter(parent__isnull=True)
        self.fields['parent'].empty_label = "(No parent - Main Category)"

    class Meta:
        model = Category
        fields = '__all__'

class CategoryAdmin(admin.ModelAdmin):
    form = CategoryAdminForm
    list_display = ('category', 'get_parent_display', 'total_ads', 'slug')
    list_filter = ('parent',)
    search_fields = ('category',)
    readonly_fields = ('slug',)

    class Media:
        css = {
            'all': ['admin/css/forms.css']
        }
        js = [
            'admin/js/vendor/jquery/jquery.min.js',
            'admin/js/jquery.init.js',
            'admin/js/category_admin.js',
        ]

    def get_parent_display(self, obj):
        return obj.parent.category if obj.parent else '[Main Category]'
    get_parent_display.short_description = 'Parent Category'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parent')

    def save_model(self, request, obj, form, change):
        if obj.category in SUBCATEGORY_PARENT_MAPPING:
            # This is a subcategory
            parent_category_name = SUBCATEGORY_PARENT_MAPPING[obj.category]
            parent_obj, _ = Category.objects.get_or_create(
                category=parent_category_name,
                defaults={'parent': None}
            )
            obj.parent = parent_obj
        else:
            # This is a main category
            obj.parent = None
        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj is None:
            # For new categories, ensure parent field shows main categories
            qs = Category.objects.filter(parent__isnull=True)
            form.base_fields['parent'].queryset = qs
        return form
    
class BannerBaseAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'updated_at')
    search_fields = ('title',)
    search_help_text = 'Search banners by title'
    list_per_page = 20
    readonly_fields = ('created_at', 'updated_at')

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="200" height="100" style="object-fit:cover;" />'.format(obj.image.url))
        return 'No image'
    
    readonly_fields = ['image_preview']

class AdsTopBannerAdmin(BannerBaseAdmin):
    pass

class AdsRightBannerAdmin(BannerBaseAdmin):
    pass

class HeroBannerAdmin(BannerBaseAdmin):
    list_display = ('title', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active',)
    fields = ('title', 'image', 'url', 'is_active', 'image_preview')

class AdsBottomBannerAdmin(BannerBaseAdmin):
    pass

# Register models
admin.site.register(Ads, AdsAdmin)
admin.site.register(County, CountyAdmin)
admin.site.register(City, CityAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(AdsImages, AdsImagesAdmin)
admin.site.register(AdsTopBanner, AdsTopBannerAdmin)
admin.site.register(AdsRightBanner, AdsRightBannerAdmin)
admin.site.register(AdsBottomBanner, AdsBottomBannerAdmin)
admin.site.register(HeroBanner, HeroBannerAdmin)


