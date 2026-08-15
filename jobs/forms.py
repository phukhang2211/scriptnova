from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from .models import AppSettings, Job


class JobUploadForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ["file"]
        labels = {"file": _("Audio or video file")}

    def clean_file(self):
        uploaded = self.cleaned_data["file"]
        max_mb = settings.MAX_UPLOAD_FILE_SIZE_MB
        max_bytes = max_mb * 1024 * 1024
        if uploaded.size > max_bytes:
            raise forms.ValidationError(
                _("File too large. Max size is %(max_mb)s MB.")
                % {"max_mb": max_mb}
            )

        filename = uploaded.name.lower()
        if not any(filename.endswith(ext) for ext in settings.ALLOWED_UPLOAD_EXTENSIONS):
            allowed = ", ".join(settings.ALLOWED_UPLOAD_EXTENSIONS)
            raise forms.ValidationError(
                _("Unsupported file type. Allowed: %(extensions)s") % {"extensions": allowed}
            )
        return uploaded


class AppSettingsForm(forms.ModelForm):
    class Meta:
        model = AppSettings
        fields = ["assemblyai_api_key", "notify_on_complete"]
        labels = {
            "assemblyai_api_key": _("AssemblyAI API key"),
            "notify_on_complete": _("Email me when a transcript finishes"),
        }
        widgets = {
            "assemblyai_api_key": forms.TextInput(attrs={"placeholder": "•••••••••••••••••••••"}),
        }
