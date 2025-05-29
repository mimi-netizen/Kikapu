from profiles.models import Profile
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if not instance.is_superuser and created:
        try:
            # Only create profile if it doesn't exist
            Profile.objects.get_or_create(user=instance)
        except Exception as e:
            print(f"Error creating profile for {instance.username}: {e}")

# Remove the save_profile signal as it's redundant