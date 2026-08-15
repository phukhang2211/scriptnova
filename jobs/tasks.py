import os
import subprocess
import tempfile

from django.conf import settings
from django.core.mail import send_mail
from django.utils.translation import gettext as _

from .appsettings import get_app_settings
from .models import Job
from .services import fetch_transcript_by_id, submit_file_async, transcribe_file

VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


def _is_video(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in VIDEO_EXTENSIONS


def _convert_to_mp3(input_path: str) -> str:
    """Convert video to mono 16kHz MP3. Returns path to temp MP3 file."""
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.close()
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", input_path,
            "-vn", "-ac", "1", "-ar", "16000",
            "-q:a", "4",
            tmp.name,
        ],
        check=True,
        capture_output=True,
    )
    return tmp.name


def transcribe_job_task(job_id: int):
    job = Job.objects.get(pk=job_id)

    job.status = Job.Status.PROCESSING
    job.current_step = "uploading"
    job.progress = 40
    job.error_message = ""
    job.save(update_fields=["status", "current_step", "progress", "error_message"])

    file_name = job.file.name
    converted_path = None
    tmp_video_path = None
    try:
        if _is_video(file_name):
            job.current_step = "converting"
            job.progress = 20
            job.save(update_fields=["current_step", "progress"])
            suffix = os.path.splitext(file_name)[1] or ".bin"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp_video_path = tmp.name
                with job.file.open("rb") as src:
                    tmp.write(src.read())
            converted_path = _convert_to_mp3(tmp_video_path)
            transcribe_path = converted_path
        else:
            transcribe_path = job.file.path
    except Exception as exc:
        job.status = Job.Status.FAILED
        job.error_message = f"File preparation failed: {exc}"
        job.save(update_fields=["status", "error_message"])
        raise
    finally:
        if tmp_video_path and os.path.exists(tmp_video_path):
            os.unlink(tmp_video_path)

    webhook_url = getattr(settings, "ASSEMBLYAI_WEBHOOK_URL", "")
    webhook_token = getattr(settings, "ASSEMBLYAI_WEBHOOK_TOKEN", "")
    language_code = job.language_code or ""

    try:
        if webhook_url:
            # Async path: submit to AssemblyAI and return. Webhook handles completion.
            transcript_id = submit_file_async(
                transcribe_path,
                speaker_labels=True,
                webhook_url=webhook_url,
                webhook_auth_token=webhook_token,
                language_code=language_code,
            )
            job.assemblyai_transcript_id = transcript_id
            job.current_step = "transcribing"
            job.progress = 60
            job.save(update_fields=["assemblyai_transcript_id", "current_step", "progress"])
            # The webhook view will complete the job when AssemblyAI finishes.
        else:
            # Sync path: block until transcription completes.
            job.current_step = "transcribing"
            job.progress = 60
            job.save(update_fields=["current_step", "progress"])

            text, duration_seconds, sentences, summary = transcribe_file(
                transcribe_path,
                speaker_labels=True,
                language_code=language_code,
            )
            _save_completed_job(job, text, duration_seconds, sentences, summary)
            _notify_user(job)
    except Exception as exc:
        job.status = Job.Status.FAILED
        job.error_message = str(exc)
        job.save(update_fields=["status", "error_message"])
        raise
    finally:
        if converted_path and os.path.exists(converted_path):
            os.unlink(converted_path)


def _save_completed_job(
    job: Job,
    text: str,
    duration_seconds: float,
    sentences: list[dict],
    summary: str,
) -> None:
    job.transcript = text
    job.audio_duration_seconds = duration_seconds
    job.utterances = sentences or None
    job.summary = summary
    job.status = Job.Status.DONE
    job.current_step = "done"
    job.progress = 100
    job.save(update_fields=[
        "transcript", "audio_duration_seconds", "utterances", "summary",
        "status", "current_step", "progress",
    ])


def complete_job_from_webhook(job_id: int, transcript_id: str) -> None:
    """Called by the AssemblyAI webhook view when transcription completes."""
    job = Job.objects.get(pk=job_id)

    try:
        text, duration_seconds, sentences, summary = fetch_transcript_by_id(
            transcript_id, speaker_labels=True
        )
        _save_completed_job(job, text, duration_seconds, sentences, summary)
        _notify_user(job)
    except Exception as exc:
        job.status = Job.Status.FAILED
        job.error_message = str(exc)
        job.save(update_fields=["status", "error_message"])


def _notify_user(job: Job) -> None:
    try:
        app_settings = get_app_settings()
        if not app_settings.notify_on_complete:
            return
        email = job.user.email
        if not email:
            return
        site_url = getattr(settings, "SITE_URL", "http://127.0.0.1:8000")
        detail_url = f"{site_url}/jobs/{job.pk}/"
        send_mail(
            subject=_("Your transcript is ready"),
            message=_(
                "Hi %(username)s,\n\n"
                "Your transcript for %(filename)s is ready.\n\n"
                "View it here: %(url)s"
            ) % {
                "username": job.user.username,
                "filename": job.original_filename or f"Job #{job.pk}",
                "url": detail_url,
            },
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=True,
        )
    except Exception:
        pass


def cleanup_stale_pending_jobs_task():
    """Delete Job records stuck in PENDING for >2 hours (browser closed before upload completed)."""
    from datetime import timedelta

    from django.utils import timezone

    cutoff = timezone.now() - timedelta(hours=2)
    stale = Job.objects.filter(status=Job.Status.PENDING, created_at__lte=cutoff)
    count = stale.count()
    stale.delete()
    return f"Deleted {count} stale PENDING job(s)."


def cleanup_temp_files_task():
    """Delete orphaned temp audio/video files older than 2 hours.

    Catches files left behind by a background thread killed before its
    finally block could run.
    """
    import glob
    import time

    max_age = 2 * 60 * 60  # 2 hours in seconds
    now = time.time()
    tmp_dir = tempfile.gettempdir()
    patterns = [
        os.path.join(tmp_dir, ext)
        for ext in ("tmp*.mp3", "tmp*.mp4", "tmp*.mov", "tmp*.mkv",
                    "tmp*.webm", "tmp*.m4a", "tmp*.wav", "tmp*.aac", "tmp*.bin")
    ]
    removed = 0
    for pattern in patterns:
        for path in glob.glob(pattern):
            try:
                if now - os.path.getmtime(path) > max_age:
                    os.unlink(path)
                    removed += 1
            except OSError:
                pass
    return f"Removed {removed} orphaned temp file(s)."
