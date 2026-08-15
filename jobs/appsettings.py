"""Helper around the AppSettings singleton row.

The AssemblyAI key can be set via the Settings page (stored in the DB) or,
as a fallback for advanced/Docker users, via the ASSEMBLYAI_API_KEY env var.
"""
from django.conf import settings


def get_app_settings():
    from .models import AppSettings

    obj, _created = AppSettings.objects.get_or_create(pk=1)
    return obj


def get_assemblyai_api_key() -> str:
    key = get_app_settings().assemblyai_api_key.strip()
    if key:
        return key
    return getattr(settings, "ASSEMBLYAI_API_KEY", "").strip()
