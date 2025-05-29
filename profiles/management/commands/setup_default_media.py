import os
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Sets up default media files'

    def handle(self, *args, **kwargs):
        # Ensure media directories exist
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'default'), exist_ok=True)
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'profile_pictures'), exist_ok=True)

        # Copy default profile picture from static to media
        static_pic = os.path.join(settings.STATIC_ROOT, 'images', 'default-profile-pic.jpg')
        media_pic = os.path.join(settings.MEDIA_ROOT, 'default', 'default-profile-pic.jpg')

        if os.path.exists(static_pic):
            shutil.copy2(static_pic, media_pic)
            self.stdout.write(self.style.SUCCESS('Successfully copied default profile picture'))
        else:
            self.stdout.write(self.style.WARNING('Default profile picture not found in static files'))
