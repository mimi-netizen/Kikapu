from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from ads.models import Ads, Category
from profiles.models import Profile

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return ['home', 'faq', 'terms-of-service', 'contact']

    def location(self, item):
        return reverse(item)

class AdsSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.7

    def items(self):
        return Ads.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at

class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return Category.objects.all()

class SellerSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5

    def items(self):
        return Profile.objects.filter(is_seller=True, is_active=True)
