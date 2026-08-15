import os

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()

STEP_ORDER = ["queued", "converting", "uploading", "transcribing", "done"]
STEP_LABELS = {
    "queued": _("Queued"),
    "converting": _("Converting"),
    "uploading": _("Uploading"),
    "transcribing": _("Transcribing"),
    "done": _("Done"),
}
STEP_PROGRESS = {
    "queued": 0,
    "converting": 20,
    "uploading": 40,
    "transcribing": 60,
    "done": 100,
}


class Job(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        PROCESSING = "processing", _("Processing")
        DONE = "done", _("Done")
        FAILED = "failed", _("Failed")

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="jobs")
    file = models.FileField(upload_to="uploads/", max_length=500)
    transcript = models.TextField(blank=True)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING
    )
    error_message = models.TextField(blank=True)
    current_step = models.CharField(max_length=32, default="queued")
    progress = models.IntegerField(default=0)
    audio_duration_seconds = models.FloatField(null=True, blank=True)
    utterances = models.JSONField(null=True, blank=True)
    summary = models.TextField(blank=True)
    assemblyai_transcript_id = models.CharField(max_length=64, blank=True)
    language_code = models.CharField(max_length=16, blank=True)  # e.g. "vi", "en" — empty = auto-detect
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def original_filename(self):
        return os.path.basename(self.file.name) if self.file else ""

    def get_steps(self) -> list[dict]:
        current = self.current_step if self.current_step in STEP_ORDER else "queued"
        current_idx = STEP_ORDER.index(current)
        last_idx = len(STEP_ORDER) - 1
        return [
            {
                "key": key,
                "label": str(STEP_LABELS[key]),
                "state": (
                    "done" if i < current_idx or (i == current_idx == last_idx)
                    else "active" if i == current_idx
                    else "pending"
                ),
            }
            for i, key in enumerate(STEP_ORDER)
        ]

    def __str__(self):
        return f"Job#{self.pk} ({self.status})"


class AppSettings(models.Model):
    """Singleton row holding the AssemblyAI API key and app preferences.

    Edited through the /settings/ page instead of hand-editing .env — that's
    the whole point of this being in the DB rather than in Django settings.
    """
    assemblyai_api_key = models.CharField(max_length=255, blank=True)
    notify_on_complete = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "App settings"


class ProcessedWebhookEvent(models.Model):
    """Dedup table for the optional AssemblyAI async-completion webhook."""
    provider = models.CharField(max_length=32, default="assemblyai")
    event_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=128)
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-processed_at"]

    def __str__(self):
        return f"{self.provider}:{self.event_id}"
