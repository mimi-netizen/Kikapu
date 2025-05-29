from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ads', '0002_auto_20250214_0956'),  # Make sure this matches your last migration
    ]

    operations = [
        # First create new fields
        migrations.AddField(
            model_name='ads',
            name='clicks_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='ads',
            name='last_clicked',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
