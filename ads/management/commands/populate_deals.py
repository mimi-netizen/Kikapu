from django.core.management.base import BaseCommand
from ads.models import TodayDeal, PopularCategory
from django.core.files.base import ContentFile
from django.core.files import File
from django.conf import settings
import os
from urllib.request import urlopen
from tempfile import NamedTemporaryFile

class Command(BaseCommand):
    help = 'Populate Today\'s Deals and Popular Categories'

    def handle(self, *args, **kwargs):
        # Sample image URLs for deals
        deals_data = [
            {
                'title': 'Wireless Earbuds Pro',
                'discount': '50% OFF',
                'original_price': 5999.99,
                'deal_price': 2999.99,
                'sold_count': 1250,
                'is_hot': True,
                'image_url': 'https://picsum.photos/400/400?random=1'
            },
            {
                'title': 'Smart Watch Series 5',
                'discount': '40% OFF',
                'original_price': 12999.99,
                'deal_price': 7799.99,
                'sold_count': 856,
                'is_hot': True,
                'image_url': 'https://picsum.photos/400/400?random=2'
            },
            {
                'title': 'HD Security Camera',
                'discount': '30% OFF',
                'original_price': 3999.99,
                'deal_price': 2799.99,
                'sold_count': 432,
                'is_hot': False,
                'image_url': 'https://picsum.photos/400/400?random=3'
            },
            {
                'title': 'Gaming Mechanical Keyboard',
                'discount': '45% OFF',
                'original_price': 8999.99,
                'deal_price': 4949.99,
                'sold_count': 678,
                'is_hot': True,
                'image_url': 'https://picsum.photos/400/400?random=4'
            }
        ]

        # Create Popular Categories
        categories_data = [
            {
                'name': 'Electronics',
                'item_count': 15420,
                'bg_color': '#FF4747',
                'icon_url': 'https://picsum.photos/200/200?random=5'
            },
            {
                'name': 'Fashion',
                'item_count': 12350,
                'bg_color': '#47B0FF',
                'icon_url': 'https://picsum.photos/200/200?random=6'
            },
            {
                'name': 'Home & Garden',
                'item_count': 8765,
                'bg_color': '#47FF9C',
                'icon_url': 'https://picsum.photos/200/200?random=7'
            },
            {
                'name': 'Sports & Outdoors',
                'item_count': 6543,
                'bg_color': '#FFB347',
                'icon_url': 'https://picsum.photos/200/200?random=8'
            },
            {
                'name': 'Beauty & Health',
                'item_count': 5432,
                'bg_color': '#FF47E1',
                'icon_url': 'https://picsum.photos/200/200?random=9'
            },
            {
                'name': 'Automotive',
                'item_count': 4321,
                'bg_color': '#8347FF',
                'icon_url': 'https://picsum.photos/200/200?random=10'
            },
            {
                'name': 'Toys & Games',
                'item_count': 3456,
                'bg_color': '#47FFE1',
                'icon_url': 'https://picsum.photos/200/200?random=11'
            },
            {
                'name': 'Books & Media',
                'item_count': 2345,
                'bg_color': '#FFE147',
                'icon_url': 'https://picsum.photos/200/200?random=12'
            }
        ]

        # Create Today's Deals
        for deal_data in deals_data:
            image_url = deal_data.pop('image_url')
            deal = TodayDeal.objects.create(**deal_data)
            
            # Download and save the image
            img_temp = NamedTemporaryFile(delete=True)
            img_temp.write(urlopen(image_url).read())
            img_temp.flush()
            
            # Save the image to the model
            deal.image.save(f"{deal.title.lower().replace(' ', '_')}.jpg", File(img_temp))
            self.stdout.write(f'Created deal: {deal.title}')

        # Create Popular Categories
        for cat_data in categories_data:
            icon_url = cat_data.pop('icon_url')
            category = PopularCategory.objects.create(**cat_data)
            
            # Download and save the icon
            img_temp = NamedTemporaryFile(delete=True)
            img_temp.write(urlopen(icon_url).read())
            img_temp.flush()
            
            # Save the icon to the model
            category.icon.save(f"{category.name.lower().replace(' ', '_')}.jpg", File(img_temp))
            self.stdout.write(f'Created category: {category.name}')

        self.stdout.write(self.style.SUCCESS('Successfully populated deals and categories'))
