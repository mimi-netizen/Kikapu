# Generated by Django 2.2.15 on 2025-02-23 09:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='store_location',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
