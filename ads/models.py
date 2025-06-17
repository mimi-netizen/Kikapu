from django.db import models
from django.contrib.auth.models import User
from ckeditor.fields import RichTextField
from django.utils.text import slugify
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Count, F
import uuid
import json

# Phone Number Validator
phone_validator = RegexValidator(
    regex=r'^\+?254?\d{9}$', 
    message="Phone number must be a valid Kenyan phone number (e.g., +254712345678)"
)

class TodayDeal(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='deals/')
    discount = models.CharField(max_length=20)
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    deal_price = models.DecimalField(max_digits=10, decimal_places=2)
    sold_count = models.IntegerField(default=0)
    is_hot = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class PopularCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, blank=True)
    icon = models.ImageField(upload_to='categories/')
    item_count = models.IntegerField(default=0)
    bg_color = models.CharField(max_length=7, default='#FFFFFF')  # Hex color

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while PopularCategory.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Popular Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

# Messages Model   
class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    ad = models.ForeignKey('Ads', on_delete=models.CASCADE, related_name='conversations', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_time = models.DateTimeField(null=True, blank=True)
    unread_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-updated_at']
        # constraints = [
        #     models.UniqueConstraint(
        #         fields=['ad'],
        #         condition=Q(participants__isnull=False),
        #         name='unique_conversation_per_ad'
        #     )
        # ]
        indexes = [
            models.Index(fields=['-updated_at']),
            models.Index(fields=['-last_message_time']),
            models.Index(fields=['unread_count']),
        ]

    def __str__(self):
        participants = self.participants.values_list('username', flat=True)
        return f"Conversation about {self.ad} between {', '.join(participants)}"

    def get_other_participant(self, user):
        return self.participants.exclude(id=user.id).first()

    @property
    def unread_messages(self):
        return self.messages.filter(read=False, receiver=self.user).count()

    def get_unread_messages_for_user(self, user):
        return self.messages.filter(read=False, receiver=user).count() 
    
    def latest_message(self):
        return self.messages.select_related('sender', 'receiver').first()

    def update_unread_count(self, user=None):
        query = self.messages.filter(is_read=False)
        if user:
            query = query.filter(receiver=user)
        self.unread_count = query.count()
        self.save(update_fields=['unread_count'])

    def mark_messages_read(self, user):
        messages_updated = self.messages.filter(
            receiver=user,
            is_read=False
        ).update(is_read=True)
        
        if messages_updated:
            self.update_unread_count(user)
            self.save(update_fields=['updated_at'])
        
        return messages_updated

    @classmethod
    def get_or_create_conversation(cls, user1, user2, ad=None):
        query = cls.objects.filter(participants=user1).filter(participants=user2)
        if ad is not None:
            query = query.filter(ad=ad)
        else:
            query = query.filter(ad__isnull=True)
        conversation = query.first()
        if not conversation:
            conversation = cls.objects.create(ad=ad)
            conversation.participants.add(user1, user2)
        return conversation

    def get_other_participant(self, user):
        return self.participants.exclude(id=user.id).first()
    
    
    @classmethod
    def get_user_conversations(cls, user):
        return cls.objects.filter(
            participants=user
        ).annotate(
            unread_messages=Count(
                'messages',
                filter=Q(messages__is_read=False, messages__receiver=user)
            )
        ).select_related('ad').prefetch_related('participants')

    @classmethod
    def get_conversation_with_messages(cls, conversation_id, user):
        return cls.objects.filter(
            id=conversation_id,
            participants=user
        ).prefetch_related(
            models.Prefetch(
                'messages',
                queryset=Message.objects.select_related('sender', 'receiver')
            )
        ).first()

    def update_last_message_time(self):
        latest = self.messages.first()
        if latest:
            self.last_message_time = latest.created_at
            self.save(update_fields=['last_message_time', 'updated_at'])

class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation, 
        related_name='messages', 
        on_delete=models.CASCADE, 
        null=True,  # Keep this temporarily
        default=None  
    )
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    ad = models.ForeignKey('Ads', on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    notification_sent = models.BooleanField(default=False)
    email_notification_sent = models.BooleanField(default=False)
    push_notification_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_read']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"Message from {self.sender} to {self.receiver} about {self.ad}"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        
        if not hasattr(self, 'conversation'):
            self.conversation = Conversation.get_or_create_conversation(
                self.sender,
                self.receiver,
                self.ad
            )

        super().save(*args, **kwargs)

        if is_new:
            self.conversation.last_message_time = self.created_at
            self.conversation.unread_count = F('unread_count') + 1
            self.conversation.save(
                update_fields=['last_message_time', 'updated_at', 'unread_count']
            )

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])
            self.conversation.update_unread_count(self.receiver)

        read = models.BooleanField(default=False)

# County Model
class County(models.Model):
    COUNTY_CHOICES = [
        ('Mombasa', 'Mombasa'),
        ('Kwale', 'Kwale'),
        ('Kilifi', 'Kilifi'),
        ('Tana River', 'Tana River'),
        ('Lamu', 'Lamu'),
        ('Taita-Taveta', 'Taita-Taveta'),
        ('Nairobi', 'Nairobi'),
        ('Kiambu', 'Kiambu'),
        ('Muranga', 'Muranga'),
        ('Kirinyaga', 'Kirinyaga'),
        ('Nyandarua', 'Nyandarua'),
        ('Nyeri', 'Nyeri'),
        ('Nakuru', 'Nakuru'),
        ('Laikipia', 'Laikipia'),
        ('Samburu', 'Samburu'),
        ('Trans-Nzoia', 'Trans-Nzoia'),
        ('Uasin Gishu', 'Uasin Gishu'),
        ('Elgeyo-Marakwet', 'Elgeyo-Marakwet'),
        ('Nandi', 'Nandi'),
        ('Baringo', 'Baringo'),
        ('Bomet', 'Bomet'),
        ('Bungoma', 'Bungoma'),
        ('Busia', 'Busia'),
        ('Embu', 'Embu'),
        ('Garissa', 'Garissa'),
        ('Homa Bay', 'Homa Bay'),
        ('Isiolo', 'Isiolo'),
        ('Kajiado', 'Kajiado'),
        ('Kakamega', 'Kakamega'),
        ('Kericho', 'Kericho'),
        ('Kisii', 'Kisii'),
        ('Kisumu', 'Kisumu'),
        ('Kitui', 'Kitui'),
        ('Machakos', 'Machakos'),
        ('Makueni', 'Makueni'),
        ('Mandera', 'Mandera'),
        ('Marsabit', 'Marsabit'),
        ('Meru', 'Meru'),
        ('Migori', 'Migori'),
        ('Narok', 'Narok'),
        ('Nyamira', 'Nyamira'),
        ('Siaya', 'Siaya'),
        ('Tharaka-Nithi', 'Tharaka-Nithi'),
        ('Turkana', 'Turkana'),
        ('Vihiga', 'Vihiga'),
        ('Wajir', 'Wajir'),
        ('West Pokot', 'West Pokot')
    ]

    county_name = models.CharField(
        max_length=100, 
        unique=True, 
        choices=COUNTY_CHOICES
    )
    slug = models.SlugField(unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.county_name)
            unique_slug = base_slug
            counter = 1
            while County.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)

    @property
    def ads_count(self):  # Changed from total_ads to ads_count
        return self.ads.count()  

    class Meta:
        verbose_name_plural = "Counties"

    def __str__(self):
        return self.county_name


# City-County Mapping
CITY_COUNTY_MAPPING = {
    # Coast Region
    'Voi': 'Taita-Taveta', 'Mwatate': 'Taita-Taveta', 'Taveta': 'Taita-Taveta', 'Wundanyi': 'Taita-Taveta',
    'Mombasa': 'Mombasa', 'Nyali': 'Mombasa', 'Likoni': 'Mombasa', 'Changamwe': 'Mombasa', 'Kisauni': 'Mombasa', 'Mtwapa': 'Kilifi',
    'Kwale': 'Kwale', 'Ukunda': 'Kwale', 'Msambweni': 'Kwale', 'Lunga Lunga': 'Kwale', 'Kinango': 'Kwale',
    'Kilifi': 'Kilifi', 'Malindi': 'Kilifi', 'Watamu': 'Kilifi', 'Kaloleni': 'Kilifi', 'Rabai': 'Kilifi',
    'Tana River': 'Tana River', 'Hola': 'Tana River', 'Garsen': 'Tana River', 'Bura': 'Tana River',
    'Lamu': 'Lamu', 'Mokowe': 'Lamu', 'Shela': 'Lamu', 'Faza': 'Lamu', 'Mpeketoni': 'Lamu', 'Witu': 'Lamu',
    
    # Nairobi Region
    'Nairobi': 'Nairobi', 'Karen': 'Nairobi', "Lang'ata": 'Nairobi', 'Westlands': 'Nairobi',
    'Embakasi': 'Nairobi', 'Kasarani': 'Nairobi', 'Gikambura': 'Nairobi', 'Kilimani': 'Nairobi', 
    'Donholm': 'Nairobi', 'Jogoo Road': 'Nairobi', 'Eastleigh': 'Nairobi', 'Buru Buru': 'Nairobi',
    'Pangani': 'Nairobi', 'Hurlingham': 'Nairobi', 'Parklands': 'Nairobi', 'Ziwani': 'Nairobi',
    'Kawangware': 'Nairobi', 'Kabete': 'Nairobi', 'South B': 'Nairobi', 'South C': 'Nairobi',
    'Kariobangi': 'Nairobi', 'Starehe': 'Nairobi',

    
    # Nyanza Region
    'Kisumu': 'Kisumu', 'Ahero': 'Kisumu', 'Muhoroni': 'Kisumu',
    'Homa Bay': 'Homa Bay', 'Kendu Bay': 'Homa Bay', 'Mbita': 'Homa Bay', 'Oyugis': 'Homa Bay',
    'Migori': 'Migori', 'Rongo': 'Migori', 'Awendo': 'Migori', 'Uriri': 'Migori',
    'Siaya': 'Siaya', 'Bondo': 'Siaya', 'Ugunja': 'Siaya', 'Yala': 'Siaya',
    'Kisii': 'Kisii', 'Ogembo': 'Kisii', 'Nyamache': 'Kisii', 'Suneka': 'Kisii',
    'Nyamira': 'Nyamira', 'Keroka': 'Nyamira', 'Nyansiongo': 'Nyamira', 'Ekerenyo': 'Nyamira',

    # Rift Valley Region
    'Nakuru': 'Nakuru', 'Naivasha': 'Nakuru', 'Gilgil': 'Nakuru', 'Molo': 'Nakuru', 'Njoro': 'Nakuru',
    'Uasin Gishu': 'Uasin Gishu', 'Kesses': 'Uasin Gishu', 'Moiben': 'Uasin Gishu', 'Burnt Forest': 'Uasin Gishu', 'Ziwa': 'Uasin Gishu',
    'Turkana': 'Turkana', 'Kakuma': 'Turkana', 'Lokichogio': 'Turkana', 'Kalokol': 'Turkana', 'Lokichar': 'Turkana',
    'West Pokot': 'West Pokot', 'Kacheliba': 'West Pokot', 'Alale': 'West Pokot', 'Sigor': 'West Pokot', 'Lomut': 'West Pokot',
    'Baringo': 'Baringo', 'Marigat': 'Baringo', 'Kabarnet': 'Baringo', 'Mogotio': 'Baringo', 'Eldama Ravine': 'Baringo',
    'Bomet': 'Bomet', 'Longisa': 'Bomet', 'Sotik': 'Bomet', 'Chepalungu': 'Bomet',
    'Kericho': 'Kericho', 'Litein': 'Kericho', 'Bureti': 'Kericho', 'Sosiot': 'Kericho',
    'Samburu': 'Samburu', 'Baragoi': 'Samburu', "Archer's Post": 'Samburu', 'Wamba': 'Samburu',
    'Trans-Nzoia': 'Trans-Nzoia', 'Kitale': 'Trans-Nzoia', 'Endebess': 'Trans-Nzoia', 'Kwanza': 'Trans-Nzoia',
    'Elgeyo-Marakwet': 'Elgeyo-Marakwet', 'Iten': 'Elgeyo-Marakwet', 'Kapsowar': 'Elgeyo-Marakwet', 'Chepkorio': 'Elgeyo-Marakwet',
    'Nandi': 'Nandi', 'Kapsabet': 'Nandi', 'Nandi Hills': 'Nandi', 'Mosoriot': 'Nandi',
    'Narok': 'Narok', 'Kilgoris': 'Narok', 'Emurua Dikirr': 'Narok', 'Ololulung\'a': 'Narok',

    # Western Region
    'Kakamega': 'Kakamega', 'Mumias': 'Kakamega', 'Malava': 'Kakamega', 'Butere': 'Kakamega', 'Khayega': 'Kakamega',
    'Bungoma': 'Bungoma', 'Webuye': 'Bungoma', 'Malakisi': 'Bungoma', 'Chwele': 'Bungoma', 'Naitiri': 'Bungoma',
    'Busia': 'Busia', 'Malaba': 'Busia', 'Nambale': 'Busia', 'Funyula': 'Busia',
    'Vihiga': 'Vihiga', 'Mbale': 'Vihiga', 'Luanda': 'Vihiga', 'Majengo': 'Vihiga',

    # Eastern Region
    'Embu': 'Embu', 'Runyenjes': 'Embu', 'Siakago': 'Embu', 'Manyatta': 'Embu',
    'Kitui': 'Kitui', 'Mwingi': 'Kitui', 'Mutomo': 'Kitui', 'Kwa Vonza': 'Kitui',
    'Machakos': 'Machakos', 'Athi River': 'Machakos', 'Mwala': 'Machakos', 'Kathiani': 'Machakos',
    'Makueni': 'Makueni', 'Makindu': 'Makueni', 'Sultan Hamud': 'Makueni', 'Kibwezi': 'Makueni',
    'Meru': 'Meru', 'Maua': 'Meru', 'Nkubu': 'Meru', 'Timau': 'Meru',
    'Tharaka-Nithi': 'Tharaka-Nithi', 'Marimanti': 'Tharaka-Nithi', 'Gatunga': 'Tharaka-Nithi', 'Magutuni': 'Tharaka-Nithi',

    # North Eastern Region
    'Garissa': 'Garissa', 'Dadaab': 'Garissa', 'Fafi': 'Garissa', 'Liboi': 'Garissa',
    'Isiolo': 'Isiolo', 'Garba Tulla': 'Isiolo', 'Merti': 'Isiolo', 'Kinna': 'Isiolo',
    'Mandera': 'Mandera', 'El Wak': 'Mandera', 'Takaba': 'Mandera', 'Rhamu': 'Mandera',
    'Marsabit': 'Marsabit', 'Laisamis': 'Marsabit', 'Loiyangalani': 'Marsabit', 'Maikona': 'Marsabit',
    'Wajir': 'Wajir', 'Habaswein': 'Wajir', 'Tarbaj': 'Wajir', 'Griftu': 'Wajir',

    # Central Region
    'Kiambu': 'Kiambu', 'Thika': 'Kiambu', 'Ruiru': 'Kiambu', 'Kikuyu': 'Kiambu',
    'Muranga': 'Muranga', 'Kenol': 'Muranga', 'Maragua': 'Muranga', 'Kangema': 'Muranga',
    'Kirinyaga': 'Kirinyaga', 'Kerugoya': 'Kirinyaga', 'Sagana': 'Kirinyaga', 'Wanguru': 'Kirinyaga', 'Baricho': 'Kirinyaga',
    'Nyandarua': 'Nyandarua', 'Ol Kalou': 'Nyandarua', 'Ndaragwa': 'Nyandarua', 'Njabini': 'Nyandarua', 'Engineer': 'Nyandarua',
    'Nyeri': 'Nyeri', 'Karatina': 'Nyeri', 'Othaya': 'Nyeri', 'Mweiga': 'Nyeri',
    'Laikipia': 'Laikipia', 'Nanyuki': 'Laikipia', 'Rumuruti': 'Laikipia', 'Nyahururu': 'Laikipia', 'Dol Dol': 'Laikipia',

    # Kajiado County
    'Kajiado': 'Kajiado', 'Kitengela': 'Kajiado', 'Ngong': 'Kajiado', 'Kajiado Town': 'Kajiado', 'Isinya': 'Kajiado',
}

# Mapping of subcategories to their main categories
# This is a dictionary where the key is the subcategory and the value is the main category
SUBCATEGORY_PARENT_MAPPING = {
    # Cars & Vehicles
    'Cars': 'Cars & Vehicles',
    'Trucks': 'Cars & Vehicles',
    'Buses & Microbuses': 'Cars & Vehicles',
    'Motorcycles': 'Cars & Vehicles',
    'Bicycles': 'Cars & Vehicles',
    'Tricycles': 'Cars & Vehicles',
    'Boats & Marine': 'Cars & Vehicles',
    'RVs & Campers': 'Cars & Vehicles',
    'ATVs & Quads': 'Cars & Vehicles',
    'Scooters': 'Cars & Vehicles',
    'Vans & Minivans': 'Cars & Vehicles',
    'SUVs & Crossovers': 'Cars & Vehicles',
    'Pickups & Trucks': 'Cars & Vehicles',
    'Commercial Vehicles': 'Cars & Vehicles',
    'Heavy Machinery': 'Cars & Vehicles',
    'Construction Equipment': 'Cars & Vehicles',
    'Agricultural Equipment': 'Cars & Vehicles',
    'Motorhomes & Campers': 'Cars & Vehicles',
    'Vehicle Parts & Accessories': 'Cars & Vehicles',
    'Heavy Equipment': 'Cars & Vehicles',
    'Other Vehicles': 'Cars & Vehicles',

    # Real Estate
    'Houses for Sale': 'Real Estate',
    'Apartments for Sale': 'Real Estate',
    'Houses for Rent': 'Real Estate',
    'Apartments for Rent': 'Real Estate',
    'Land for Rent': 'Real Estate',
    'Land for Sale': 'Real Estate',
    'Commercial Properties for Sale': 'Real Estate',
    'Commercial Properties for Rent': 'Real Estate',
    'Vacation Rentals': 'Real Estate',
    'Short-term Rentals': 'Real Estate',
    'Long-term Rentals': 'Real Estate',
    'Real Estate Services': 'Real Estate',
    'Real Estate Investment': 'Real Estate',
    'Real Estate Development': 'Real Estate',
    'Real Estate Management': 'Real Estate',
    'Real Estate Consulting': 'Real Estate',
    'Real Estate Financing': 'Real Estate',
    'Real Estate Auctions': 'Real Estate',
    'Parking & Storage': 'Real Estate',
    'Room Rentals': 'Real Estate',
    'Other Real Estate': 'Real Estate',

    # Electronics
    'Smartphones': 'Electronics',
    'Feature Phones': 'Electronics',
    'Tablets': 'Electronics',
    'Laptops': 'Electronics',
    'Desktop Computers': 'Electronics',
    'Computer Parts & Accessories': 'Electronics',
    'TVs': 'Electronics',
    'Audio & Video Equipment': 'Electronics',
    'Cameras': 'Electronics',
    'Wearable Technology': 'Electronics',
    'Audio Equipment': 'Electronics',
    'Cameras & Photography': 'Electronics',
    'Gaming Consoles': 'Electronics',
    'Smart Home Devices': 'Electronics',
    'Other Electronics': 'Electronics',

    # Furniture
    'Living Room Furniture': 'Furniture',
    'Bedroom Furniture': 'Furniture',
    'Dining Room Furniture': 'Furniture',
    'Office Furniture': 'Furniture',
    'Outdoor Furniture': 'Furniture',
    'Storage & Organization': 'Furniture',
    'Home Decor': 'Furniture',
    'Lighting': 'Furniture',
    'Rugs & Carpets': 'Furniture',
    'Curtains & Blinds': 'Furniture',
    'Wall Art & Mirrors': 'Furniture',
    'Shelving & Bookcases': 'Furniture',
    'Desks & Workstations': 'Furniture',
    'Chairs & Seating': 'Furniture',
    'Tables & Desks': 'Furniture',
    'Sofas & Couches': 'Furniture',
    'Beds & Mattresses': 'Furniture',
    'Dressers & Wardrobes': 'Furniture',
    'Nightstands & Bedside Tables': 'Furniture',
    'Bedding & Linens': 'Furniture',
    'Kitchen & Dining': 'Furniture',
    'Other Furniture': 'Furniture',

    # Home Appliances
    'Refrigerators': 'Home Appliances',
    'Washing Machines': 'Home Appliances',
    'Dryers': 'Home Appliances',
    'Dishwashers': 'Home Appliances',
    'Ovens & Stoves': 'Home Appliances',
    'Microwaves': 'Home Appliances',
    'Air Conditioners': 'Home Appliances',
    'Heaters': 'Home Appliances',
    'Fans': 'Home Appliances',
    'Vacuum Cleaners': 'Home Appliances',
    'Coffee Makers': 'Home Appliances',
    'Blenders & Mixers': 'Home Appliances',
    'Toasters & Grills': 'Home Appliances',
    'Other Appliances': 'Home Appliances',

    # Fashion
    "Men's Clothing": 'Fashion',
    "Women's Clothing": 'Fashion',
    "Children's Clothing": 'Fashion',
    'Shoes & Footwear': 'Fashion',
    'Bags & Luggage': 'Fashion',
    'Jewelry & Watches': 'Fashion',
    'Fashion Accessories': 'Fashion',
    'Traditional Wear': 'Fashion',
    'Other Fashion': 'Fashion',

    # Home & Garden
    'Home Decor': 'Home & Garden',
    'Garden & Outdoor': 'Home & Garden',
    'Tools & Home Improvement': 'Home & Garden',
    'Cleaning Supplies': 'Home & Garden',
    'Other Home Items': 'Home & Garden'
}

# Generate programmatically from CATEGORY_CHOICES
def populate_subcategory_mapping():
    for category_group in Category.CATEGORY_CHOICES:
        main_category = category_group[0]
        if isinstance(category_group[1], (list, tuple)):
            for sub in category_group[1]:
                if isinstance(sub, (list, tuple)) and len(sub) > 0:
                    SUBCATEGORY_PARENT_MAPPING[sub[0]] = main_category

# City Model
class City(models.Model):
    CITY_CHOICES = [
        # Coast Region
        ('Mombasa', 'Mombasa'), ('Likoni', 'Likoni'), ('Kisauni', 'Kisauni'), ('Nyali', 'Nyali'), ('Mtwapa', 'Mtwapa'),
        ('Lamu', 'Lamu'), ('Mpeketoni', 'Mpeketoni'), ('Faza', 'Faza'), ('Witu', 'Witu'),
        ('Taita-Taveta', 'Taita-Taveta'), ('Voi', 'Voi'), ('Mwatate', 'Mwatate'), ('Taveta', 'Taveta'), ('Wundanyi', 'Wundanyi'),
        
        # Nairobi Region
        ('Nairobi', 'Nairobi'), ('Karen', 'Karen'), ("Lang'ata", "Lang'ata"), ('Westlands', 'Westlands'), 
        ('Embakasi', 'Embakasi'), ('Kasarani', 'Kasarani'),
        
        # Nyanza Region
        ('Kisumu', 'Kisumu'), ('Ahero', 'Ahero'), ('Muhoroni', 'Muhoroni'),
        ('Homa Bay', 'Homa Bay'), ('Kendu Bay', 'Kendu Bay'), ('Mbita', 'Mbita'), ('Oyugis', 'Oyugis'),
        ('Migori', 'Migori'), ('Rongo', 'Rongo'), ('Awendo', 'Awendo'), ('Uriri', 'Uriri'),
        ('Siaya', 'Siaya'), ('Bondo', 'Bondo'), ('Ugunja', 'Ugunja'), ('Yala', 'Yala'),
        
        # Rift Valley Region
        ('Nakuru', 'Nakuru'), ('Naivasha', 'Naivasha'), ('Gilgil', 'Gilgil'), ('Molo', 'Molo'), ('Njoro', 'Njoro'),
        ('Uasin Gishu', 'Uasin Gishu'), ('Kesses', 'Kesses'), ('Moiben', 'Moiben'), ('Burnt Forest', 'Burnt Forest'), 
        ('Ziwa', 'Ziwa'),
        ('Turkana', 'Turkana'), ('Kakuma', 'Kakuma'), ('Lokichogio', 'Lokichogio'), ('Kalokol', 'Kalokol'), 
        ('Lokichar', 'Lokichar'),
        ('West Pokot', 'West Pokot'), ('Kacheliba', 'West Pokot'), ('Alale', 'Alale'), ('Sigor', 'Sigor'), 
        ('Lomut', 'Lomut'),
        ('Baringo', 'Baringo'), ('Marigat', 'Baringo'), ('Kabarnet', 'Baringo'), ('Mogotio', 'Baringo'), 
        ('Eldama Ravine', 'Eldama Ravine'),
        ('Bomet', 'Bomet'), ('Longisa', 'Longisa'), ('Sotik', 'Sotik'), ('Chepalungu', 'Chepalungu'),
        ('Kericho', 'Kericho'), ('Litein', 'Kericho'), ('Bureti', 'Kericho'), ('Sosiot', 'Sosiot'),
        ('Samburu', 'Samburu'), ('Baragoi', 'Samburu'), ("Archer's Post", "Archer's Post"), ('Wamba', 'Wamba'),
        
        # Western Region
        ('Kakamega', 'Kakamega'), ('Mumias', 'Mumias'), ('Malava', 'Malava'), ('Butere', 'Butere'), ('Khayega', 'Khayega'),
        ('Bungoma', 'Bungoma'), ('Webuye', 'Webuye'), ('Malakisi', 'Malakisi'), ('Chwele', 'Chwele'), ('Naitiri', 'Naitiri'),
        ('Busia', 'Busia'), ('Malaba', 'Malaba'), ('Nambale', 'Nambale'), ('Funyula', 'Funyula'),
        ('Vihiga', 'Vihiga'), ('Mbale', 'Mbale'), ('Luanda', 'Luanda'), ('Majengo', 'Majengo'),
        
        # Eastern Region
        ('Embu', 'Embu'), ('Runyenjes', 'Embu'), ('Siakago', 'Embu'), ('Manyatta', 'Manyatta'),
        ('Kitui', 'Kitui'), ('Mwingi', 'Kitui'), ('Mutomo', 'Kitui'), ('Kwa Vonza', 'Kwa Vonza'),
        ('Machakos', 'Machakos'), ('Athi River', 'Athi River'), ('Mwala', 'Mwala'), ('Kathiani', 'Kathiani'),
        ('Makueni', 'Makueni'), ('Makindu', 'Makueni'), ('Sultan Hamud', 'Makueni'), ('Kibwezi', 'Makueni'),
        ('Meru', 'Meru'), ('Maua', 'Meru'), ('Nkubu', 'Meru'), ('Timau', 'Meru'),
        ('Tharaka-Nithi', 'Tharaka-Nithi'), ('Marimanti', 'Tharaka-Nithi'), ('Gatunga', 'Gatunga'), ('Magutuni', 'Magutuni'),
        
        # North Eastern Region
        ('Garissa', 'Garissa'), ('Dadaab', 'Dadaab'), ('Fafi', 'Fafi'), ('Liboi', 'Liboi'),
        ('Isiolo', 'Isiolo'), ('Garba Tulla', 'Garba Tulla'), ('Merti', 'Merti'), ('Kinna', 'Kinna'),
        ('Mandera', 'Mandera'), ('El Wak', 'El Wak'), ('Takaba', 'Takaba'), ('Rhamu', 'Rhamu'),
        ('Marsabit', 'Marsabit'), ('Laisamis', 'Marsabit'), ('Loiyangalani', 'Marsabit'), ('Maikona', 'Maikona'),
        ('Wajir', 'Wajir'), ('Habaswein', 'Habaswein'), ('Tarbaj', 'Tarbaj'), ('Griftu', 'Griftu'),
        
        # Central Region
        ('Kiambu', 'Kiambu'), ('Thika', 'Thika'), ('Ruiru', 'Ruiru'), ('Kikuyu', 'Kikuyu'),
        ("Muranga", "Muranga"), ('Kenol', 'Kenol'), ('Maragua', 'Maragua'), ('Kangema', 'Kangema'),
        ('Kirinyaga', 'Kirinyaga'), ('Kerugoya', 'Kirinyaga'), ('Sagana', 'Sagana'), ('Wanguru', 'Wanguru'), 
        ('Baricho', 'Baricho'),
        ('Nyandarua', 'Nyandarua'), ('Ol Kalou', 'Ol Kalou'), ('Ndaragwa', 'Ndaragwa'), ('Njabini', 'Njabini'), 
        ('Engineer', 'Engineer'),
        ('Nyeri', 'Nyeri'), ('Karatina', 'Karatina'), ('Othaya', 'Othaya'), ('Mweiga', 'Mweiga'),
        ('Laikipia', 'Laikipia'), ('Nanyuki', 'Laikipia'), ('Rumuruti', 'Laikipia'), ('Nyahururu', 'Laikipia'), 
        ('Dol Dol', 'Dol Dol'),
    ]

    city_name = models.CharField(max_length=100, choices=CITY_CHOICES)
    slug = models.SlugField(blank=True, null=True)
    county = models.ForeignKey(County, on_delete=models.CASCADE)

    def clean(self):
        if self.city_name and self.county:
            expected_county = CITY_COUNTY_MAPPING.get(self.city_name)
            if (expected_county and expected_county != self.county.county_name):
                raise ValidationError({
                    'county': f'This city belongs to {expected_county} county, not {self.county.county_name}'
                })

    def save(self, *args, **kwargs):
        # First validate
        self.clean()
        
        # Auto-assign county if not set
        if not self.county:
            county_name = CITY_COUNTY_MAPPING.get(self.city_name)
            if county_name:
                county, _ = County.objects.get_or_create(county_name=county_name)
                self.county = county
        
        # Generate slug
        if not self.slug:
            base_slug = slugify(self.city_name)
            unique_slug = base_slug
            counter = 1
            while City.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = unique_slug
            
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Cities"
        unique_together = ('city_name', 'county')
        ordering = ['city_name']

    def __str__(self):
        return self.city_name
    

# category model
class Category(models.Model):
    CATEGORY_CHOICES = [
    # Vehicles
    ('Cars & Vehicles', (
        ('Cars', 'Cars'),
        ('Trucks', 'Trucks'),
        ('Buses & Microbuses', 'Buses & Microbuses'),
        ('Motorcycles', 'Motorcycles'),
        ('Bicycles', 'Bicycles'),
        ('Tricycles', 'Tricycles'),
        ('Boats & Marine', 'Boats & Marine'),
        ('RVs & Campers', 'RVs & Campers'),
        ('ATVs & Quads', 'ATVs & Quads'),
        ('Scooters', 'Scooters'),
        ('Vans & Minivans', 'Vans & Minivans'),
        ('SUVs & Crossovers', 'SUVs & Crossovers'),
        ('Pickups & Trucks', 'Pickups & Trucks'),
        ('Commercial Vehicles', 'Commercial Vehicles'),
        ('Heavy Machinery', 'Heavy Machinery'),
        ('Construction Equipment', 'Construction Equipment'),
        ('Agricultural Equipment', 'Agricultural Equipment'),
        ('Motorhomes & Campers', 'Motorhomes & Campers'),
        ('Vehicle Parts & Accessories', 'Vehicle Parts & Accessories'),
        ('Heavy Equipment', 'Heavy Equipment'),
        ('Other Vehicles', 'Other Vehicles'),
    )),

    # Real Estate
    ('Real Estate', (
        ('Houses for Sale', 'Houses for Sale'),
        ('Apartments for Sale', 'Apartments for Sale'),
        ('Houses for Rent', 'Houses for Rent'),
        ('Apartments for Rent', 'Apartments for Rent'),
        ('Land for Rent', 'Land for Rent'),
        ('Land for Sale', 'Land for Sale'),
        ('Commercial Properties for Sale', 'Commercial Properties for Sale'),
        ('Commercial Properties for Rent', 'Commercial Properties for Rent'),
        ('Vacation Rentals', 'Vacation Rentals'),
        ('Short-term Rentals', 'Short-term Rentals'),
        ('Long-term Rentals', 'Long-term Rentals'),
        ('Real Estate Services', 'Real Estate Services'),
        ('Real Estate Investment', 'Real Estate Investment'),
        ('Real Estate Development', 'Real Estate Development'),
        ('Real Estate Management', 'Real Estate Management'),
        ('Real Estate Consulting', 'Real Estate Consulting'),
        ('Real Estate Financing', 'Real Estate Financing'),
        ('Real Estate Auctions', 'Real Estate Auctions'),
        ('Parking & Storage', 'Parking & Storage'),
        ('Room Rentals', 'Room Rentals'),
        ('Other Real Estate', 'Other Real Estate'),
    )),

    # Electronics
    ('Electronics', (
        ('Smartphones', 'Smartphones'),
        ('Feature Phones', 'Feature Phones'),
        ('Tablets', 'Tablets'),
        ('Laptops', 'Laptops'),
        ('Desktop Computers', 'Desktop Computers'),
        ('Computer Parts & Accessories', 'Computer Parts & Accessories'),
        ('TVs', 'TVs'),
        ('Audio & Video Equipment', 'Audio & Video Equipment'),
        ('Cameras', 'Cameras'),
        ('Wearable Technology', 'Wearable Technology'),
        ('Audio Equipment', 'Audio Equipment'),
        ('Cameras & Photography', 'Cameras & Photography'),
        ('Gaming Consoles', 'Gaming Consoles'),
        ('Smart Home Devices', 'Smart Home Devices'),
        ('Other Electronics', 'Other Electronics'),
    )),

    # Furniture
    ('Furniture', (
        ('Living Room Furniture', 'Living Room Furniture'),
        ('Bedroom Furniture', 'Bedroom Furniture'),
        ('Dining Room Furniture', 'Dining Room Furniture'),
        ('Office Furniture', 'Office Furniture'),
        ('Outdoor Furniture', 'Outdoor Furniture'),
        ('Storage & Organization', 'Storage & Organization'),
        ('Home Decor', 'Home Decor'),
        ('Lighting', 'Lighting'),
        ('Rugs & Carpets', 'Rugs & Carpets'),
        ('Curtains & Blinds', 'Curtains & Blinds'),
        ('Wall Art & Mirrors', 'Wall Art & Mirrors'),
        ('Shelving & Bookcases', 'Shelving & Bookcases'),
        ('Desks & Workstations', 'Desks & Workstations'),
        ('Chairs & Seating', 'Chairs & Seating'),
        ('Tables & Desks', 'Tables & Desks'),
        ('Sofas & Couches', 'Sofas & Couches'),
        ('Beds & Mattresses', 'Beds & Mattresses'),
        ('Dressers & Wardrobes', 'Dressers & Wardrobes'),
        ('Nightstands & Bedside Tables', 'Nightstands & Bedside Tables'),
        ('Bedding & Linens', 'Bedding & Linens'),
        ('Kitchen & Dining', 'Kitchen & Dining'),
        ('Other Furniture', 'Other Furniture'),
    )),
    

    # Home Appliances
    ('Home Appliances', (
        ('Refrigerators', 'Refrigerators'),
        ('Washing Machines', 'Washing Machines'),
        ('Dryers', 'Dryers'),
        ('Dishwashers', 'Dishwashers'),
        ('Ovens & Stoves', 'Ovens & Stoves'),
        ('Microwaves', 'Microwaves'),
        ('Air Conditioners', 'Air Conditioners'),
        ('Heaters', 'Heaters'),
        ('Fans', 'Fans'),
        ('Vacuum Cleaners', 'Vacuum Cleaners'),
        ('Coffee Makers', 'Coffee Makers'),
        ('Blenders & Mixers', 'Blenders & Mixers'),
        ('Toasters & Grills', 'Toasters & Grills'),
        ('Other Appliances', 'Other Appliances'),
    )),

    # Fashion & Accessories
    ('Fashion', (
        ('Men\'s Clothing', 'Men\'s Clothing'),
        ('Women\'s Clothing', 'Women\'s Clothing'),
        ('Children\'s Clothing', 'Children\'s Clothing'),
        ('Shoes & Footwear', 'Shoes & Footwear'),
        ('Bags & Luggage', 'Bags & Luggage'),
        ('Jewelry & Watches', 'Jewelry & Watches'),
        ('Fashion Accessories', 'Fashion Accessories'),
        ('Traditional Wear', 'Traditional Wear'),
        ('Other Fashion', 'Other Fashion'),
    )),

    # Home & Garden
    ('Home & Garden', (
        ('Home Decor', 'Home Decor'),
        ('Garden & Outdoor', 'Garden & Outdoor'),
        ('Tools & Home Improvement', 'Tools & Home Improvement'),
        ('Cleaning Supplies', 'Cleaning Supplies'),
        ('Other Home Items', 'Other Home Items'),
    )),

    # Jobs & Services
    ('Jobs & Services', (
        ('Full-time Jobs', 'Full-time Jobs'),
        ('Part-time Jobs', 'Part-time Jobs'),
        ('Internships', 'Internships'),
        ('Temporary Jobs', 'Temporary Jobs'),
        ('Volunteer Opportunities', 'Volunteer Opportunities'),
        ('Freelance Work', 'Freelance Work'),
        ('Professional Services', 'Professional Services'),
        ('Home Services', 'Home Services'),
        ('Educational Services', 'Educational Services'),
        ('Health Services', 'Health Services'),
        ('Beauty & Wellness', 'Beauty & Wellness'),
        ('Transportation Services', 'Transportation Services'),
        ('Event Planning', 'Event Planning'),
        ('Photography & Videography', 'Photography & Videography'),
        ('Cleaning Services', 'Cleaning Services'),
        ('Pet Services', 'Pet Services'),
        ('Childcare Services', 'Childcare Services'),
        ('Event Services', 'Event Services'),
        ('Other Services', 'Other Services'),
    )),

    # Agriculture & Pets
    ('Agriculture & Pets', (
        ('Livestock', 'Livestock'),
        ('Farm Produce', 'Farm Produce'),
        ('Agricultural Supplies', 'Agricultural Supplies'),
        ('Farming Equipment', 'Farming Equipment'),
        ('Seeds & Plants', 'Seeds & Plants'),
        ('Dogs', 'Dogs'),
        ('Cats', 'Cats'),
        ('Birds', 'Birds'),
        ('Fish & Aquariums', 'Fish & Aquariums'),
        ('Pet Supplies', 'Pet Supplies'),
        ('Other Agriculture & Pets', 'Other Agriculture & Pets'),
    )),

    # Sports & Leisure
    ('Sports & Leisure', (
        ('Exercise Equipment', 'Exercise Equipment'),
        ('Sports Gear', 'Sports Gear'),
        ('Outdoor Recreation', 'Outdoor Recreation'),
        ('Camping & Hiking', 'Camping & Hiking'),
        ('Musical Instruments', 'Musical Instruments'),
        ('Books & Magazines', 'Books & Magazines'),
        ('Art & Crafts', 'Art & Crafts'),
        ('Collectibles', 'Collectibles'),
        ('Other Sports & Leisure', 'Other Sports & Leisure'),
    )),

    # Kids & Babies
    ('Kids & Babies', (
        ('Baby Clothing', 'Baby Clothing'),
        ('Baby Gear', 'Baby Gear'),
        ('Toys', 'Toys'),
        ('Scooters', 'Scooters'),
        ('Bicycles', 'Bicycles'),
        ('Baby Furniture', 'Baby Furniture'),
        ('Baby Accessories', 'Baby Accessories'),
        ('Skates', 'Skates'),
        ('Educational Toys', 'Educational Toys'),
        ('Children\'s Furniture', 'Children\'s Furniture'),
        ('School Supplies', 'School Supplies'),
        ('Baby Care', 'Baby Care'),
        ('Other Kids Items', 'Other Kids Items'),
    )),

    # Health & Beauty
    ('Health & Beauty', (
        ('Skincare', 'Skincare'),
        ('Makeup', 'Makeup'),
        ('Hair Care', 'Hair Care'),
        ('Nail Care', 'Nail Care'),
        ('Personal Care', 'Personal Care'),
        ('Cosmetics', 'Cosmetics'),
        ('Perfumes', 'Perfumes'),
        ('Beauty Tools', 'Beauty Tools'),
        ('Wellness Products', 'Wellness Products'),
        ('Fitness Products', 'Fitness Products'),
        ('Fragrances', 'Fragrances'),
        ('Health Care Products', 'Health Care Products'),
        ('Vitamins & Supplements', 'Vitamins & Supplements'),
        ('Medical Equipment', 'Medical Equipment'),
        ('Other Health & Beauty', 'Other Health & Beauty'),
    )),

    # Business & Industrial
    ('Business & Industrial', (
        ('Office Furniture', 'Office Furniture'),
        ('Office Electronics', 'Office Electronics'),
        ('Office Supplies', 'Office Supplies'),
        ('Industrial Equipment', 'Industrial Equipment'),
        ('Manufacturing Equipment', 'Manufacturing Equipment'),
        ('Construction Equipment', 'Construction Equipment'),
        ('Warehouse Equipment', 'Warehouse Equipment'),
        ('Retail Equipment', 'Retail Equipment'),
        ('Restaurant Equipment', 'Restaurant Equipment'),
        ('Medical Equipment', 'Medical Equipment'),
        ('Laboratory Equipment', 'Laboratory Equipment'),
        ('Cleaning Equipment', 'Cleaning Equipment'),
        ('Safety Equipment', 'Safety Equipment'),
        ('Commercial Equipment', 'Commercial Equipment'),
        ('Packaging Equipment', 'Packaging Equipment'),
        ('Printing Equipment', 'Printing Equipment'),
        ('Agricultural Equipment', 'Agricultural Equipment'),
        ('Food Processing Equipment', 'Food Processing Equipment'),
        ('Construction Supplies', 'Construction Supplies'),
        ('Office Machinery', 'Office Machinery'),
        ('Retail Supplies', 'Retail Supplies'),
        ('Manufacturing Supplies', 'Manufacturing Supplies'),
        ('Shipping & Logistics', 'Shipping & Logistics'),
        ('Storage Solutions', 'Storage Solutions'),
        ('Restaurant Equipment', 'Restaurant Equipment'),
        ('Other Business Items', 'Other Business Items'),
    )),

    # Adult
    ('Adult', (
        ('Adult Products', 'Adult Products'),
        ('Adult Toys', 'Adult Toys'),
        ('Intimacy & Relationships', 'Intimacy & Relationships'),
        ('Other Adult', 'Other Adult'),
    )),

    # Other
    ('Other', (
        ('Miscellaneous', 'Miscellaneous'),
        ('General Items', 'General Items'),
        ('Collectibles', 'Collectibles'),
        ('Antiques', 'Antiques'),
        ('Crafts', 'Crafts'),
        ('Hobbies', 'Hobbies'),
        ('DIY & Tools', 'DIY & Tools'),
        ('Preloved Items', 'Preloved Items'),
        ('Vintage Items', 'Vintage Items'),
        ('Secondhand Items', 'Secondhand Items'),
        ('Mtumba Items', 'Mtumba Items'),
        ('Unwanted Items', 'Unwanted Items'),
        ('Wanted Items', 'Wanted Items'),
    )),
]


    category = models.CharField(
        max_length=100, 
        choices=CATEGORY_CHOICES,  # Use CATEGORY_CHOICES directly instead of empty list
        default='Other'
    )
    icon = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text='Font Awesome icon class (e.g. fa-car, fa-home)'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories'
    )
    slug = models.SlugField(unique=True, blank=True, null=True)

    def clean(self):
        if not hasattr(self, '_skip_clean'):
            parent_name = SUBCATEGORY_PARENT_MAPPING.get(self.category)
            if parent_name:
                # This is a subcategory
                if not self.parent:
                    try:
                        parent = Category.objects.get(category=parent_name)
                        self.parent = parent
                    except Category.DoesNotExist:
                        if not getattr(self, '_initializing', False):
                            raise ValidationError({
                                'category': f'Please select a parent category first'
                            })
            else:
                # This is a main category
                self.parent = None

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.category)
            unique_slug = base_slug
            counter = 1
            while Category.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = unique_slug

        # Prevent a category from being its own parent
        if self.pk and self.parent and self.parent.pk == self.pk:
            raise ValidationError("A category cannot be its own parent.")
        
        self.clean()
        super().save(*args, **kwargs)

    @property
    def total_ads(self):
        count = self.ads.count()
        for subcategory in self.subcategories.all():
            count += subcategory.total_ads
        return count

    @property
    def is_main_category(self):
        return self.parent is None

    @property
    def is_subcategory(self):
        return self.parent is not None

    @classmethod
    def get_main_categories(cls):
        return cls.objects.filter(parent=None)

    @classmethod
    def get_subcategories(cls, main_category):
        return cls.objects.filter(parent=main_category)

    @classmethod
    def initialize_categories(cls):
        """Initialize all categories and their subcategories"""
        # Set flag to skip validation during initialization
        setattr(cls, '_skip_clean', True)
        try:
            # Define icons for main categories
            CATEGORY_ICONS = {
                'Cars & Vehicles': 'fa-car',
                'Real Estate': 'fa-home',
                'Electronics': 'fa-laptop',
                'Furniture': 'fa-couch',
                'Home Appliances': 'fa-blender',
                'Fashion': 'fa-tshirt',
                'Home & Garden': 'fa-leaf',
                'Jobs & Services': 'fa-briefcase',
                'Agriculture & Pets': 'fa-paw',
                'Sports & Leisure': 'fa-futbol',
                'Kids & Babies': 'fa-baby',
                'Health & Beauty': 'fa-heart',
                'Business & Industrial': 'fa-industry',
                'Adult': 'fa-user-secret',
                'Other': 'fa-box'
            }
            
            # Create main categories first
            for main_cat, subcats in cls.CATEGORY_CHOICES:
                main_category, _ = cls.objects.get_or_create(
                    category=main_cat,
                    defaults={
                        'parent': None,
                        'slug': slugify(main_cat),
                        'icon': CATEGORY_ICONS.get(main_cat, 'fa-folder')
                    }
                )
                
                # Create subcategories
                if isinstance(subcats, (tuple, list)):
                    for subcat in subcats:
                        if isinstance(subcat, (tuple, list)) and len(subcat) >= 1:
                            cls.objects.get_or_create(
                                category=subcat[0],
                                defaults={
                                    'parent': main_category,
                                    'slug': slugify(subcat[0])
                                }
                            )
        finally:
            # Remove skip validation flag
            delattr(cls, '_skip_clean')

    def __str__(self):
        if self.is_subcategory:
            return f"{self.parent.category} > {self.category}"
        return self.category

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['category']
        constraints = [
            models.CheckConstraint(
                check=models.Q(category__isnull=False),
                name='category_not_null'
            )
        ]



class Bookmark(models.Model):
    profile = models.ForeignKey('profiles.Profile', on_delete=models.CASCADE, related_name='saved_ad_items')
    ad = models.ForeignKey('Ads', on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('profile', 'ad')
        ordering = ['-saved_at']

    def __str__(self):
        return f"{self.profile.user.username} saved {self.ad.title}"

# Ads Model
class Ads(models.Model):
    CONDITION_CHOICES = [
        ('Excellent', 'Excellent'),
        ('Good', 'Good'),
        ('Fair', 'Fair'),
    ]

    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('PENDING', 'Pending'),
        ('SOLD', 'Sold'),
        ('EXPIRED', 'Expired'),
        ('BLOCKED', 'Blocked')
    ]

    NEGOTIATION_CHOICES = (
        ('yes', 'Yes'),
        ('no', 'No'),
        ('not_sure', 'Not sure')
    )

    SIZE_CHOICES = (
        ('', 'Select Size'),
        ('XS', 'Extra Small'),
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),
        ('XXL', '2XL'),
        ('XXXL', '3XL'),
        ('CUSTOM', 'Custom Size'),
        ('NA', 'Not Applicable'),
    )

    SHOE_SIZE_CHOICES = (
        ('', 'Select Size'),
        ('35', 'EU 35 / UK 2.5'),
        ('36', 'EU 36 / UK 3.5'),
        ('37', 'EU 37 / UK 4'),
        ('38', 'EU 38 / UK 5'),
        ('39', 'EU 39 / UK 6'),
        ('40', 'EU 40 / UK 6.5'),
        ('41', 'EU 41 / UK 7.5'),
        ('42', 'EU 42 / UK 8'),
        ('43', 'EU 43 / UK 9'),
        ('44', 'EU 44 / UK 9.5'),
        ('45', 'EU 45 / UK 10.5'),
        ('46', 'EU 46 / UK 11'),
        ('CUSTOM', 'Custom Size'),
    )

    ad_id = models.UUIDField(
        default=uuid.uuid4, 
        editable=False, 
        unique=True
    )
    seller = models.ForeignKey(
        'profiles.Profile', 
        on_delete=models.CASCADE, 
        related_name='ads',
        null=True  # Temporary for migration
    )
    county = models.ForeignKey(County, on_delete=models.SET_NULL, null=True, related_name='ads')
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True)
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='ads'
    )
    title = models.CharField(max_length=200)
    description = RichTextField()
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        help_text="Maximum price: 9,999,999.99"
    )
    condition = models.CharField(
        max_length=20, 
        choices=CONDITION_CHOICES, 
        default='Good'
    )
    brand = models.CharField(max_length=100, blank=True, null=True)
    colour = models.CharField(max_length=50, blank=True, null=True)
    weight = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, help_text="Weight in kg")
    length = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    width = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    height = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    negotiable = models.CharField(max_length=10, choices=NEGOTIATION_CHOICES, default='not_sure')
    phone = models.CharField(
        max_length=15, 
        validators=[phone_validator]
    )
    clothing_size = models.CharField(max_length=10, choices=SIZE_CHOICES, blank=True, null=True)
    shoe_size = models.CharField(max_length=10, choices=SHOE_SIZE_CHOICES, blank=True, null=True)
    custom_size = models.CharField(max_length=50, blank=True, null=True, help_text="Specify custom size if selected above")
    date_created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    is_featured = models.BooleanField(default=False)
    is_bundle = models.BooleanField(default=False, help_text='Whether this is a bundle deal (multiple items sold together)')
    featured_until = models.DateTimeField(null=True, blank=True)
    is_sold = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE'
    )
    views_count = models.PositiveIntegerField(default=0)
    last_viewed = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Ads"
        ordering = ['-date_created']
        indexes = [
            models.Index(fields=['date_created']),
            models.Index(fields=['category']),
            models.Index(fields=['city']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['status']),
            models.Index(fields=['views_count']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # If this is a new ad
        if not self.pk:
            if self.seller:
                self.seller.is_seller = True
                self.seller.save()
        super().save(*args, **kwargs)

    def increment_views(self):
        """
        Increment the views counter using F() expression to avoid race conditions
        """
        self.views_count = F('views_count') + 1
        self.last_viewed = timezone.now()
        self.save(update_fields=['views_count', 'last_viewed'])
        self.refresh_from_db()  # Refresh to get the new views_count value

    @property
    def seller_rating(self):
        return self.seller.average_rating if self.seller else 0.0

    @property
    def seller_total_reviews(self):
        return self.seller.total_reviews if self.seller else 0

# Images Model for Ads
class AdsImages(models.Model):
    ad = models.ForeignKey(Ads, related_name='images', on_delete=models.CASCADE, default=None, null=True)
    image = models.ImageField(upload_to='uploads/listing_images')
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = "Item Images"

    def __str__(self):
        return f"Image for {self.ad.title}"

# Banner Models
class AdsTopBanner(models.Model):
    title = models.CharField(max_length=255, verbose_name=_('Banner Title'))
    image = models.ImageField(upload_to='banners/top/', verbose_name=_('Banner Image'))
    link = models.URLField(blank=True, null=True, verbose_name=_('Banner Link'))
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _('Top Banner')
        verbose_name_plural = _('Top Banners')
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class AdsRightBanner(models.Model):
    title = models.CharField(max_length=255, verbose_name=_('Banner Title'))
    image = models.ImageField(upload_to='banners/right/', verbose_name=_('Banner Image'))
    link = models.URLField(blank=True, null=True, verbose_name=_('Banner Link'))
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _('Right Banner')
        verbose_name_plural = _('Right Banners')
        ordering = ['-created_at']

    def __str__(self):
        return self.title

# Hero Banner Model
class HeroBanner(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='banners/hero/')
    url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Hero Banner'
        verbose_name_plural = 'Hero Banners'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class AdsBottomBanner(models.Model):
    title = models.CharField(max_length=255, verbose_name=_('Banner Title'))
    image = models.ImageField(upload_to='banners/bottom/', verbose_name=_('Banner Image'))
    link = models.URLField(blank=True, null=True, verbose_name=_('Banner Link'))
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _('Bottom Banner')
        verbose_name_plural = _('Bottom Banners')
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class FeaturedSlot(models.Model):
    SLOT_STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('RESERVED', 'Reserved'),
        ('OCCUPIED', 'Occupied')
    ]

    slot_number = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20,
        choices=SLOT_STATUS_CHOICES,
        default='AVAILABLE'
    )
    current_ad = models.ForeignKey(
        'Ads',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='featured_slot'
    )
    valid_until = models.DateTimeField(null=True, blank=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=150.00
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['slot_number']

    def __str__(self):
        return f"Featured Slot {self.slot_number} - {self.status}"

    def check_availability(self):
        if self.valid_until and self.valid_until < timezone.now():
            self.status = 'AVAILABLE'
            self.current_ad = None
            self.save()
        return self.status == 'AVAILABLE'

class DraftAd(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()  # Changed from JSONField to TextField
    last_modified = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-last_modified']

    def set_content(self, data):
        """Serialize the data to JSON string"""
        self.content = json.dumps(data)

    def get_content(self):
        """Deserialize the JSON string to Python dict"""
        try:
            return json.loads(self.content)
        except (json.JSONDecodeError, TypeError):
            return {}

class AdPriceHistory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['category', 'created_at'])
        ]

    def __str__(self):
        return f"Price history for {self.category} at {self.created_at}"

class AdDraft(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()  # Will store JSON as text
    last_modified = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-last_modified']
        get_latest_by = 'last_modified'

    def set_content(self, data):
        """Serialize data to JSON string"""
        self.content = json.dumps(data)

    def get_content(self):
        """Deserialize JSON string to data"""
        try:
            return json.loads(self.content)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def save(self, *args, **kwargs):
        # Ensure content is JSON serializable
        if isinstance(self.content, dict):
            self.content = json.dumps(self.content)
        super().save(*args, **kwargs)

class AdInteraction(models.Model):
    INTERACTION_TYPES = (
        ('view', 'View'),
        ('like', 'Like'),
        ('contact', 'Contact'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ad_interactions')
    ad = models.ForeignKey(Ads, on_delete=models.CASCADE, related_name='interactions')
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'ad', 'interaction_type')
        indexes = [
            models.Index(fields=['user', 'interaction_type']),
            models.Index(fields=['ad', 'interaction_type']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} {self.interaction_type}d {self.ad.title} on {self.created_at.strftime('%Y-%m-%d')}"