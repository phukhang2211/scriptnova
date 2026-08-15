import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .appsettings import get_app_settings
from .exports import generate_docx, generate_srt
from .models import Job, ProcessedWebhookEvent
from .tasks import transcribe_job_task

User = get_user_model()


def _set_assemblyai_key(key="test-key"):
    app_settings = get_app_settings()
    app_settings.assemblyai_api_key = key
    app_settings.save(update_fields=["assemblyai_api_key"])


class DashboardTests(TestCase):
    """The client is auto-authenticated as the single local user by
    AutoLoginMiddleware — there's no login step in these tests."""

    def test_dashboard_redirects_to_settings_without_api_key(self):
        response = self.client.get(reverse("jobs:dashboard"))
        self.assertRedirects(response, reverse("jobs:settings"))

    def test_dashboard_loads_with_api_key_configured(self):
        _set_assemblyai_key()
        response = self.client.get(reverse("jobs:dashboard"))
        self.assertEqual(response.status_code, 200)


class UploadAndJobFlowTests(TestCase):
    def setUp(self):
        _set_assemblyai_key()

    @patch("jobs.views.run_in_background")
    def test_upload_creates_pending_job_and_queues_task(self, run_mock):
        f = SimpleUploadedFile("audio.mp3", b"fake audio bytes", content_type="audio/mpeg")
        response = self.client.post(reverse("jobs:upload"), {"file": f})
        self.assertEqual(Job.objects.count(), 1)
        job = Job.objects.first()
        self.assertEqual(job.status, Job.Status.PENDING)
        run_mock.assert_called_once_with(transcribe_job_task, job.id)
        self.assertRedirects(response, reverse("jobs:job_detail", kwargs={"pk": job.pk}))

    @patch("jobs.views.run_in_background")
    def test_single_xhr_upload_returns_json_with_job(self, run_mock):
        f = SimpleUploadedFile("audio.mp3", b"fake audio bytes", content_type="audio/mpeg")
        response = self.client.post(
            reverse("jobs:upload"), {"file": f},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        data = json.loads(response.content)
        self.assertEqual(data["count"], 1)
        self.assertEqual(len(data["jobs"]), 1)

    def test_unsupported_extension_returns_400_json(self):
        f = SimpleUploadedFile("notes.exe", b"nope", content_type="application/octet-stream")
        response = self.client.post(
            reverse("jobs:upload"), {"file": f},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 400)

    def test_upload_without_api_key_redirects_to_settings(self):
        app_settings = get_app_settings()
        app_settings.assemblyai_api_key = ""
        app_settings.save(update_fields=["assemblyai_api_key"])
        f = SimpleUploadedFile("audio.mp3", b"data", content_type="audio/mpeg")
        response = self.client.post(reverse("jobs:upload"), {"file": f})
        self.assertRedirects(response, reverse("jobs:settings"))
        self.assertEqual(Job.objects.count(), 0)

    def test_job_detail_is_user_scoped(self):
        other_user = User.objects.create_user(username="other", password="x")
        job = Job.objects.create(user=other_user, status=Job.Status.DONE, transcript="hi")
        response = self.client.get(reverse("jobs:job_detail", kwargs={"pk": job.pk}))
        self.assertEqual(response.status_code, 404)

    def test_job_status_json_fields(self):
        local_user = self.client.get(reverse("jobs:settings")).wsgi_request.user
        job = Job.objects.create(
            user=local_user, status=Job.Status.DONE, transcript="hello",
            current_step="done", progress=100,
        )
        response = self.client.get(reverse("jobs:job_status", kwargs={"pk": job.pk}))
        data = json.loads(response.content)
        self.assertEqual(data["status"], "done")
        self.assertTrue(data["terminal"])
        self.assertEqual(data["transcript"], "hello")

    def test_delete_job_removes_record(self):
        local_user = self.client.get(reverse("jobs:settings")).wsgi_request.user
        job = Job.objects.create(user=local_user, status=Job.Status.DONE, transcript="hi")
        response = self.client.post(reverse("jobs:delete_job", kwargs={"pk": job.pk}))
        self.assertRedirects(response, reverse("jobs:dashboard"))
        self.assertFalse(Job.objects.filter(pk=job.pk).exists())


class SettingsPageTests(TestCase):
    def test_save_assemblyai_key(self):
        response = self.client.post(reverse("jobs:settings"), {
            "assemblyai_api_key": "abc123",
            "notify_on_complete": "on",
        })
        self.assertRedirects(response, reverse("jobs:settings"))
        self.assertEqual(get_app_settings().assemblyai_api_key, "abc123")


class TaskExecutionTests(TestCase):
    def test_transcribe_task_marks_job_failed_on_exception(self):
        user = User.objects.create_user(username="u1", password="x")
        job = Job.objects.create(
            user=user,
            file=SimpleUploadedFile("audio.mp3", b"data"),
            status=Job.Status.PENDING,
        )
        with patch("jobs.tasks.transcribe_file", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                transcribe_job_task(job.id)
        job.refresh_from_db()
        self.assertEqual(job.status, Job.Status.FAILED)
        self.assertIn("boom", job.error_message)

    @patch("jobs.tasks.transcribe_file")
    def test_sync_path_marks_job_done(self, mock_transcribe):
        mock_transcribe.return_value = ("hello world", 12.5, [], "")
        user = User.objects.create_user(username="u2", password="x")
        job = Job.objects.create(
            user=user,
            file=SimpleUploadedFile("audio.mp3", b"data"),
            status=Job.Status.PENDING,
        )
        transcribe_job_task(job.id)
        job.refresh_from_db()
        self.assertEqual(job.status, Job.Status.DONE)
        self.assertEqual(job.transcript, "hello world")
        self.assertEqual(job.audio_duration_seconds, 12.5)

    @override_settings(ASSEMBLYAI_WEBHOOK_URL="https://example.com/hook")
    @patch("jobs.tasks.submit_file_async")
    def test_webhook_url_configured_uses_async_submit(self, mock_submit):
        mock_submit.return_value = "transcript-123"
        user = User.objects.create_user(username="u3", password="x")
        job = Job.objects.create(
            user=user,
            file=SimpleUploadedFile("audio.mp3", b"data"),
            status=Job.Status.PENDING,
        )
        transcribe_job_task(job.id)
        job.refresh_from_db()
        self.assertEqual(job.assemblyai_transcript_id, "transcript-123")
        self.assertEqual(job.current_step, "transcribing")


class AssemblyAIWebhookTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="webhookuser", password="x")
        self.job = Job.objects.create(
            user=self.user, status=Job.Status.PROCESSING,
            assemblyai_transcript_id="t-1",
        )

    @patch("jobs.views.complete_job_from_webhook")
    def test_completed_status_calls_complete_handler(self, mock_complete):
        response = self.client.post(
            reverse("jobs:assemblyai_webhook"),
            data=json.dumps({"transcript_id": "t-1", "status": "completed"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        mock_complete.assert_called_once_with(self.job.pk, "t-1")

    def test_error_status_marks_job_failed(self):
        response = self.client.post(
            reverse("jobs:assemblyai_webhook"),
            data=json.dumps({"transcript_id": "t-1", "status": "error"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, Job.Status.FAILED)

    @patch("jobs.views.complete_job_from_webhook")
    def test_duplicate_transcript_id_not_processed_again(self, mock_complete):
        payload = json.dumps({"transcript_id": "t-1", "status": "completed"})
        self.client.post(reverse("jobs:assemblyai_webhook"), data=payload, content_type="application/json")
        self.client.post(reverse("jobs:assemblyai_webhook"), data=payload, content_type="application/json")
        mock_complete.assert_called_once()
        self.assertEqual(ProcessedWebhookEvent.objects.count(), 1)

    def test_non_post_returns_405(self):
        response = self.client.get(reverse("jobs:assemblyai_webhook"))
        self.assertEqual(response.status_code, 405)


class ExportTests(TestCase):
    def test_generate_srt_from_utterances(self):
        user = User.objects.create_user(username="exportuser", password="x")
        job = Job.objects.create(
            user=user, status=Job.Status.DONE, transcript="hello world",
            utterances=[{"text": "hello", "start": 0, "end": 1000, "speaker": "A"}],
        )
        srt = generate_srt(job)
        self.assertIn("hello", srt)
        self.assertIn("00:00:00,000", srt)

    def test_generate_docx_returns_bytes(self):
        user = User.objects.create_user(username="exportuser2", password="x")
        job = Job.objects.create(user=user, status=Job.Status.DONE, transcript="hello world.")
        content = generate_docx(job)
        self.assertIsInstance(content, bytes)
        self.assertGreater(len(content), 0)


class DashboardSearchFilterTests(TestCase):
    def setUp(self):
        _set_assemblyai_key()
        local_user = self.client.get(reverse("jobs:settings")).wsgi_request.user
        self.done_job = Job.objects.create(
            user=local_user, status=Job.Status.DONE,
            file=SimpleUploadedFile("meeting-notes.mp3", b"x"),
        )
        self.failed_job = Job.objects.create(
            user=local_user, status=Job.Status.FAILED,
            file=SimpleUploadedFile("interview.mp3", b"x"),
        )

    def test_no_params_returns_all_jobs(self):
        response = self.client.get(reverse("jobs:dashboard"))
        self.assertEqual(len(response.context["jobs"]), 2)

    def test_search_by_filename_filters_correctly(self):
        response = self.client.get(reverse("jobs:dashboard"), {"q": "meeting"})
        jobs = list(response.context["jobs"])
        self.assertEqual(jobs, [self.done_job])

    def test_status_filter_failed(self):
        response = self.client.get(reverse("jobs:dashboard"), {"status": "failed"})
        jobs = list(response.context["jobs"])
        self.assertEqual(jobs, [self.failed_job])
