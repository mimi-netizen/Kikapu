from django.db import migrations


def copy_views_to_clicks(apps, schema_editor):
    Ads = apps.get_model('ads', 'Ads')
    for ad in Ads.objects.all():
        ad.clicks_count = ad.views_count
        ad.last_clicked = ad.last_viewed
        ad.save()


class Migration(migrations.Migration):

    dependencies = [
        ('ads', '0003_rename_views_to_clicks'),
    ]

    operations = [
        migrations.RunPython(copy_views_to_clicks),
    ]
