# Generated by Django 2.2.15 on 2025-02-14 09:56

import ckeditor.fields
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Ads',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ad_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('title', models.CharField(max_length=200)),
                ('description', ckeditor.fields.RichTextField()),
                ('price', models.DecimalField(decimal_places=2, help_text='Maximum price: 9,999,999.99', max_digits=10)),
                ('condition', models.CharField(choices=[('Excellent', 'Excellent'), ('Good', 'Good'), ('Fair', 'Fair')], default='Good', max_length=20)),
                ('brand', models.CharField(blank=True, max_length=200, null=True)),
                ('phone', models.CharField(max_length=15, validators=[django.core.validators.RegexValidator(message='Phone number must be a valid Kenyan phone number (e.g., +254712345678)', regex='^\\+?254?\\d{9}$')])),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('is_featured', models.BooleanField(default=False)),
                ('featured_until', models.DateTimeField(blank=True, null=True)),
                ('is_sold', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('status', models.CharField(choices=[('ACTIVE', 'Active'), ('PENDING', 'Pending'), ('SOLD', 'Sold'), ('EXPIRED', 'Expired'), ('BLOCKED', 'Blocked')], default='ACTIVE', max_length=20)),
                ('views_count', models.PositiveIntegerField(default=0)),
                ('last_viewed', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'Ads',
                'ordering': ['-date_created'],
            },
        ),
        migrations.CreateModel(
            name='AdsBottomBanner',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Banner Title')),
                ('image', models.ImageField(upload_to='banners/bottom/', verbose_name='Banner Image')),
                ('link', models.URLField(blank=True, null=True, verbose_name='Banner Link')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Bottom Banner',
                'verbose_name_plural': 'Bottom Banners',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='AdsImages',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='uploads/listing_images')),
                ('is_primary', models.BooleanField(default=False)),
                ('uploaded_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'verbose_name_plural': 'Item Images',
            },
        ),
        migrations.CreateModel(
            name='AdsRightBanner',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Banner Title')),
                ('image', models.ImageField(upload_to='banners/right/', verbose_name='Banner Image')),
                ('link', models.URLField(blank=True, null=True, verbose_name='Banner Link')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Right Banner',
                'verbose_name_plural': 'Right Banners',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='AdsTopBanner',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Banner Title')),
                ('image', models.ImageField(upload_to='banners/top/', verbose_name='Banner Image')),
                ('link', models.URLField(blank=True, null=True, verbose_name='Banner Link')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Top Banner',
                'verbose_name_plural': 'Top Banners',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(choices=[('Cars', 'Cars'), ('Buses & Microbuses', 'Buses & Microbuses'), ('Heavy Equipment', 'Heavy Equipment'), ('Motorcycles', 'Motorcycles'), ('Trucks', 'Trucks'), ('Other Vehicles', 'Other Vehicles'), ('New Builds', 'New Builds'), ('Houses & Apartments for Rent', 'Houses & Apartments for Rent'), ('Houses & Apartments for Sale', 'Houses & Apartments for Sale'), ('Land for Sale', 'Land for Sale'), ('Commercial Property', 'Commercial Property'), ('Other Property', 'Other Property'), ('Phones', 'Phones'), ('Laptops', 'Laptops'), ('Desktops', 'Desktops'), ('Tablets', 'Tablets'), ('Televisions', 'Televisions'), ('Other Electronics', 'Other Electronics'), ("Men's Fashion", "Men's Fashion"), ("Women's Fashion", "Women's Fashion"), ("Kids' Fashion", "Kids' Fashion"), ('Other Fashion', 'Other Fashion'), ('Furniture', 'Furniture'), ('Appliances', 'Appliances'), ('Electronics', 'Electronics'), ('Home Decor', 'Home Decor'), ('Office Equipment', 'Office Equipment'), ('Other Home & Office', 'Other Home & Office'), ('Jobs', 'Jobs'), ('Services', 'Services'), ('Livestock', 'Livestock'), ('Farming Equipment', 'Farming Equipment'), ('Other Agriculture', 'Other Agriculture'), ('Fitness', 'Fitness'), ('Sports Equipment', 'Sports Equipment'), ('Other Sports & Outdoors', 'Other Sports & Outdoors'), ('Food', 'Food'), ('Beverages', 'Beverages'), ('Health', 'Health'), ('Beauty', 'Beauty'), ('Other', 'Other'), ('Adult Products', 'Adult Products'), ('Intimacy & Relationships', 'Intimacy & Relationships')], default='Other', max_length=50)),
                ('slug', models.SlugField(blank=True, null=True, unique=True)),
            ],
            options={
                'verbose_name_plural': 'Categories',
            },
        ),
        migrations.CreateModel(
            name='City',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('city_name', models.CharField(choices=[('Mombasa', 'Mombasa'), ('Likoni', 'Likoni'), ('Kisauni', 'Kisauni'), ('Nyali', 'Nyali'), ('Mtwapa', 'Mtwapa'), ('Lamu', 'Lamu'), ('Mpeketoni', 'Mpeketoni'), ('Faza', 'Faza'), ('Witu', 'Witu'), ('Taita-Taveta', 'Taita-Taveta'), ('Voi', 'Voi'), ('Mwatate', 'Mwatate'), ('Taveta', 'Taveta'), ('Wundanyi', 'Wundanyi'), ('Nairobi', 'Nairobi'), ('Karen', 'Karen'), ("Lang'ata", "Lang'ata"), ('Westlands', 'Westlands'), ('Embakasi', 'Embakasi'), ('Kasarani', 'Kasarani'), ('Kisumu', 'Kisumu'), ('Ahero', 'Ahero'), ('Muhoroni', 'Muhoroni'), ('Homa Bay', 'Homa Bay'), ('Kendu Bay', 'Kendu Bay'), ('Mbita', 'Mbita'), ('Oyugis', 'Oyugis'), ('Migori', 'Migori'), ('Rongo', 'Rongo'), ('Awendo', 'Awendo'), ('Uriri', 'Uriri'), ('Siaya', 'Siaya'), ('Bondo', 'Bondo'), ('Ugunja', 'Ugunja'), ('Yala', 'Yala'), ('Nakuru', 'Nakuru'), ('Naivasha', 'Naivasha'), ('Gilgil', 'Gilgil'), ('Molo', 'Molo'), ('Njoro', 'Njoro'), ('Uasin Gishu', 'Uasin Gishu'), ('Kesses', 'Kesses'), ('Moiben', 'Moiben'), ('Burnt Forest', 'Burnt Forest'), ('Ziwa', 'Ziwa'), ('Turkana', 'Turkana'), ('Kakuma', 'Kakuma'), ('Lokichogio', 'Lokichogio'), ('Kalokol', 'Kalokol'), ('Lokichar', 'Lokichar'), ('West Pokot', 'West Pokot'), ('Kacheliba', 'Kacheliba'), ('Alale', 'Alale'), ('Sigor', 'Sigor'), ('Lomut', 'Lomut'), ('Baringo', 'Baringo'), ('Marigat', 'Marigat'), ('Kabarnet', 'Kabarnet'), ('Mogotio', 'Mogotio'), ('Eldama Ravine', 'Eldama Ravine'), ('Bomet', 'Bomet'), ('Longisa', 'Longisa'), ('Sotik', 'Sotik'), ('Chepalungu', 'Chepalungu'), ('Kericho', 'Kericho'), ('Litein', 'Litein'), ('Bureti', 'Bureti'), ('Sosiot', 'Sosiot'), ('Samburu', 'Samburu'), ('Baragoi', 'Baragoi'), ("Archer's Post", "Archer's Post"), ('Wamba', 'Wamba'), ('Kakamega', 'Kakamega'), ('Mumias', 'Mumias'), ('Malava', 'Malava'), ('Butere', 'Butere'), ('Khayega', 'Khayega'), ('Bungoma', 'Bungoma'), ('Webuye', 'Webuye'), ('Malakisi', 'Malakisi'), ('Chwele', 'Chwele'), ('Naitiri', 'Naitiri'), ('Busia', 'Busia'), ('Malaba', 'Malaba'), ('Nambale', 'Nambale'), ('Funyula', 'Funyula'), ('Vihiga', 'Vihiga'), ('Mbale', 'Mbale'), ('Luanda', 'Luanda'), ('Majengo', 'Majengo'), ('Embu', 'Embu'), ('Runyenjes', 'Runyenjes'), ('Siakago', 'Siakago'), ('Manyatta', 'Manyatta'), ('Kitui', 'Kitui'), ('Mwingi', 'Mwingi'), ('Mutomo', 'Mutomo'), ('Kwa Vonza', 'Kwa Vonza'), ('Machakos', 'Machakos'), ('Athi River', 'Athi River'), ('Mwala', 'Mwala'), ('Kathiani', 'Kathiani'), ('Makueni', 'Makueni'), ('Makindu', 'Makindu'), ('Sultan Hamud', 'Sultan Hamud'), ('Kibwezi', 'Kibwezi'), ('Meru', 'Meru'), ('Maua', 'Maua'), ('Nkubu', 'Nkubu'), ('Timau', 'Timau'), ('Tharaka-Nithi', 'Tharaka-Nithi'), ('Marimanti', 'Marimanti'), ('Gatunga', 'Gatunga'), ('Magutuni', 'Magutuni'), ('Garissa', 'Garissa'), ('Dadaab', 'Dadaab'), ('Fafi', 'Fafi'), ('Liboi', 'Liboi'), ('Isiolo', 'Isiolo'), ('Garba Tulla', 'Garba Tulla'), ('Merti', 'Merti'), ('Kinna', 'Kinna'), ('Mandera', 'Mandera'), ('El Wak', 'El Wak'), ('Takaba', 'Takaba'), ('Rhamu', 'Rhamu'), ('Marsabit', 'Marsabit'), ('Laisamis', 'Laisamis'), ('Loiyangalani', 'Loiyangalani'), ('Maikona', 'Maikona'), ('Wajir', 'Wajir'), ('Habaswein', 'Habaswein'), ('Tarbaj', 'Tarbaj'), ('Griftu', 'Griftu'), ('Kiambu', 'Kiambu'), ('Thika', 'Thika'), ('Ruiru', 'Ruiru'), ('Kikuyu', 'Kikuyu'), ("Murang'a", "Murang'a"), ('Kenol', 'Kenol'), ('Maragua', 'Maragua'), ('Kangema', 'Kangema'), ('Kirinyaga', 'Kirinyaga'), ('Kerugoya', 'Kerugoya'), ('Sagana', 'Sagana'), ('Wanguru', 'Wanguru'), ('Baricho', 'Baricho'), ('Nyandarua', 'Nyandarua'), ('Ol Kalou', 'Ol Kalou'), ('Ndaragwa', 'Ndaragwa'), ('Njabini', 'Njabini'), ('Engineer', 'Engineer'), ('Nyeri', 'Nyeri'), ('Karatina', 'Karatina'), ('Othaya', 'Othaya'), ('Mweiga', 'Mweiga'), ('Laikipia', 'Laikipia'), ('Nanyuki', 'Nanyuki'), ('Rumuruti', 'Rumuruti'), ('Nyahururu', 'Nyahururu'), ('Dol Dol', 'Dol Dol')], max_length=100)),
                ('slug', models.SlugField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'Cities',
                'ordering': ['city_name'],
            },
        ),
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('last_message_time', models.DateTimeField(blank=True, null=True)),
                ('unread_count', models.PositiveIntegerField(default=0)),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='County',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('county_name', models.CharField(choices=[('Mombasa', 'Mombasa'), ('Kwale', 'Kwale'), ('Kilifi', 'Kilifi'), ('Tana River', 'Tana River'), ('Lamu', 'Lamu'), ('Taita-Taveta', 'Taita-Taveta'), ('Nairobi', 'Nairobi'), ('Kiambu', 'Kiambu'), ('Muranga', 'Muranga'), ('Kirinyaga', 'Kirinyaga'), ('Nyandarua', 'Nyandarua'), ('Nyeri', 'Nyeri'), ('Nakuru', 'Nakuru'), ('Laikipia', 'Laikipia'), ('Samburu', 'Samburu'), ('Trans-Nzoia', 'Trans-Nzoia'), ('Uasin Gishu', 'Uasin Gishu'), ('Elgeyo-Marakwet', 'Elgeyo-Marakwet'), ('Nandi', 'Nandi'), ('Baringo', 'Baringo'), ('Bomet', 'Bomet'), ('Bungoma', 'Bungoma'), ('Busia', 'Busia'), ('Embu', 'Embu'), ('Garissa', 'Garissa'), ('Homa Bay', 'Homa Bay'), ('Isiolo', 'Isiolo'), ('Kajiado', 'Kajiado'), ('Kakamega', 'Kakamega'), ('Kericho', 'Kericho'), ('Kisii', 'Kisii'), ('Kisumu', 'Kisumu'), ('Kitui', 'Kitui'), ('Machakos', 'Machakos'), ('Makueni', 'Makueni'), ('Mandera', 'Mandera'), ('Marsabit', 'Marsabit'), ('Meru', 'Meru'), ('Migori', 'Migori'), ('Narok', 'Narok'), ('Nyamira', 'Nyamira'), ('Siaya', 'Siaya'), ('Tharaka-Nithi', 'Tharaka-Nithi'), ('Turkana', 'Turkana'), ('Vihiga', 'Vihiga'), ('Wajir', 'Wajir'), ('West Pokot', 'West Pokot')], max_length=100, unique=True)),
                ('slug', models.SlugField(blank=True, null=True, unique=True)),
            ],
            options={
                'verbose_name_plural': 'Counties',
            },
        ),
        migrations.CreateModel(
            name='FeaturedSlot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slot_number', models.PositiveIntegerField()),
                ('status', models.CharField(choices=[('AVAILABLE', 'Available'), ('RESERVED', 'Reserved'), ('OCCUPIED', 'Occupied')], default='AVAILABLE', max_length=20)),
                ('valid_until', models.DateTimeField(blank=True, null=True)),
                ('price', models.DecimalField(decimal_places=2, default=150.0, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['slot_number'],
            },
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_read', models.BooleanField(default=False)),
                ('notification_sent', models.BooleanField(default=False)),
                ('email_notification_sent', models.BooleanField(default=False)),
                ('push_notification_sent', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='SavedAd',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('saved_at', models.DateTimeField(auto_now_add=True)),
                ('ad', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saved_by', to='ads.Ads')),
            ],
            options={
                'ordering': ['-saved_at'],
            },
        ),
    ]
