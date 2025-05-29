from django.utils import timezone

class LastSeenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                if not hasattr(request.user, 'profile'):
                    from profiles.models import Profile
                    Profile.objects.create(user=request.user)
                request.user.profile.update_last_seen()
            except Exception:
                pass  # Fail silently if there are any issues
        return self.get_response(request)
