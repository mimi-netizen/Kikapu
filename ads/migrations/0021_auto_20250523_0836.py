# Generated by Django 2.2.15 on 2025-05-23 08:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ads', '0020_auto_20250523_0736'),
    ]

    operations = [
        migrations.AddField(
            model_name='adsbottombanner',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='adsrightbanner',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='adstopbanner',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
