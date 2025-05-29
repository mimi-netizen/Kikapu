from django.core.management.base import BaseCommand
from django.utils.html import strip_tags
from ads.models import Ads

class Command(BaseCommand):
    help = 'Cleans HTML tags from all product descriptions'

    def handle(self, *args, **options):
        products = Ads.objects.all()
        cleaned_count = 0
        
        for product in products:
            cleaned_description = strip_tags(product.description)
            if cleaned_description != product.description:
                product.description = cleaned_description
                product.save()
                cleaned_count += 1
                self.stdout.write(f'Cleaned product {product.id}')
        
        self.stdout.write(self.style.SUCCESS(f'Successfully cleaned {cleaned_count} product descriptions'))