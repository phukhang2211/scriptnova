"""Auto-login for the single-user local deployment.

There's no login screen — whoever has access to the machine has access to
the app, same as any other locally-installed software. A single local user
is created on first use and every request is transparently authenticated
as that user (including /admin/, handy for poking at the DB).
"""
import threading

from django.contrib.auth import get_user_model, login

_provision_lock = threading.Lock()
_local_user_id = None

LOCAL_USERNAME = "local"


def get_or_create_local_user():
    global _local_user_id
    User = get_user_model()
    if _local_user_id is not None:
        try:
            return User.objects.get(pk=_local_user_id)
        except User.DoesNotExist:
            _local_user_id = None

    with _provision_lock:
        user, _created = User.objects.get_or_create(
            username=LOCAL_USERNAME,
            defaults={"is_staff": True, "is_superuser": True},
        )
        _local_user_id = user.pk
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
