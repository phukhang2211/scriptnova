"""Auto-login for the single-user local deployment.

There's no login screen — whoever has access to the machine has access to
the app, same as any other locally-installed software. A single local user
is created on first use and every request is transparently authenticated
as that user (including /admin/, handy for poking at the DB).
"""
from django.contrib.auth import get_user_model, login

LOCAL_USERNAME = "local"


def get_or_create_local_user():
    User = get_user_model()
    user, _created = User.objects.get_or_create(
        username=LOCAL_USERNAME,
        defaults={"is_staff": True, "is_superuser": True},
    )
    return user


class AutoLoginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            user = get_or_create_local_user()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            request.user = user
        return self.get_response(request)
