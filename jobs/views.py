import json
from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.translation import gettext as _

from .appsettings import get_app_settings
from .background import run_in_background
from .forms import AppSettingsForm, JobUploadForm
from .models import Job, ProcessedWebhookEvent
from .services import assemblyai_configured
from .tasks import complete_job_from_webhook, transcribe_job_task


@login_required
def dashboard(request):
    if not assemblyai_configured():
        messages.info(request, _("Add your AssemblyAI API key to start transcribing."))
        return redirect("jobs:settings")

    q = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()
    jobs = Job.objects.filter(user=request.user)
    if q:
        jobs = jobs.filter(file__icontains=q)
    if status_filter in ("pending", "processing", "done", "failed"):
        jobs = jobs.filter(status=status_filter)
    form = JobUploadForm()
    return render(
        request,
        "jobs/dashboard.html",
        {
            "jobs": jobs,
            "form": form,
            "q": q,
            "status_filter": status_filter,
        },
    )


@login_required
def upload_job(request):
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    if request.method != "POST":
        if is_ajax:
            return JsonResponse({"error": "POST required"}, status=405)
        return redirect("jobs:dashboard")

    if not assemblyai_configured():
        msg = _("Add your AssemblyAI API key on the Settings page first.")
        if is_ajax:
            return JsonResponse({"error": str(msg)}, status=400)
        messages.error(request, msg)
        return redirect("jobs:settings")

    recent_uploads = Job.objects.filter(
        user=request.user,
        created_at__gte=datetime.now(timezone.utc) - timedelta(minutes=1),
    ).count()
    files = request.FILES.getlist("file")
    if not files:
        files = [request.FILES.get("file")] if request.FILES.get("file") else []
    if recent_uploads + len(files) > settings.UPLOADS_PER_MINUTE_LIMIT:
        msg = _("Too many uploads in a short time. Please wait one minute.")
        if is_ajax:
            return JsonResponse({"error": str(msg)}, status=429)
        messages.error(request, msg)
        return redirect("jobs:dashboard")

    if not files:
        msg = _("Please choose at least one file.")
        if is_ajax:
            return JsonResponse({"error": str(msg)}, status=400)
        messages.error(request, msg)
        return redirect("jobs:dashboard")

    max_mb = settings.MAX_UPLOAD_FILE_SIZE_MB
    max_bytes = max_mb * 1024 * 1024
    created_jobs = []
    for uploaded_file in files:
        filename = uploaded_file.name.lower()
        if uploaded_file.size > max_bytes:
            msg = _("File %(name)s is too large (max %(max_mb)s MB).") % {
                "name": uploaded_file.name, "max_mb": max_mb
            }
            if is_ajax:
                return JsonResponse({"error": str(msg)}, status=400)
            messages.error(request, msg)
            return redirect("jobs:dashboard")
        if not any(filename.endswith(ext) for ext in settings.ALLOWED_UPLOAD_EXTENSIONS):
            allowed_exts = ", ".join(settings.ALLOWED_UPLOAD_EXTENSIONS)
            msg = _("Unsupported file type: %(name)s. Allowed: %(exts)s") % {
                "name": uploaded_file.name, "exts": allowed_exts
            }
            if is_ajax:
                return JsonResponse({"error": str(msg)}, status=400)
            messages.error(request, msg)
            return redirect("jobs:dashboard")

        language_code = request.POST.get("language_code", "").strip()
        job = Job(user=request.user, file=uploaded_file, status=Job.Status.PENDING,
                  language_code=language_code)
        job.save()
        run_in_background(transcribe_job_task, job.id)
        created_jobs.append(job)

    if not created_jobs:
        msg = _("No valid files were uploaded.")
        if is_ajax:
            return JsonResponse({"error": str(msg)}, status=400)
        messages.error(request, msg)
        return redirect("jobs:dashboard")

    if is_ajax:
        return JsonResponse({
            "jobs": [
                {"pk": j.pk, "redirect": reverse("jobs:job_detail", kwargs={"pk": j.pk})}
                for j in created_jobs
            ],
            "count": len(created_jobs),
            "dashboard_redirect": reverse("jobs:dashboard"),
        })

    if len(created_jobs) == 1:
        messages.info(request, _("Upload received. Transcription has started."))
        return redirect("jobs:job_detail", pk=created_jobs[0].pk)
    messages.info(
        request,
        _("%(count)s files uploaded. Transcription has started.") % {"count": len(created_jobs)},
    )
    return redirect("jobs:dashboard")


@login_required
def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk, user=request.user)
    return render(request, "jobs/job_detail.html", {
        "job": job,
        "show_speakers": bool(job.utterances) and
                         any(u.get("speaker") for u in (job.utterances or [])),
    })


@login_required
def job_status(request, pk):
    """JSON for live job progress on the detail page (polling)."""
    job = get_object_or_404(Job, pk=pk, user=request.user)
    terminal = job.status in (Job.Status.DONE, Job.Status.FAILED)
    return JsonResponse(
        {
            "status": job.status,
            "terminal": terminal,
            "status_display": job.get_status_display(),
            "transcript": job.transcript or "",
            "summary": job.summary or "",
            "utterances": job.utterances or [],
            "error_message": job.error_message or "",
            "progress": job.progress,
            "current_step": job.current_step,
            "steps": job.get_steps(),
        }
    )


@login_required
def export_docx(request, pk):
    job = get_object_or_404(Job, pk=pk, user=request.user)
    if not job.transcript:
        messages.error(request, _("No transcript available yet."))
        return redirect("jobs:job_detail", pk=pk)

    from .exports import generate_docx
    content = generate_docx(job)
    base = job.original_filename.rsplit(".", 1)[0] if job.original_filename else f"job-{job.pk}"
    filename = f"{base}-transcript.docx"
    response = HttpResponse(
        content,
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required
def export_srt(request, pk):
    job = get_object_or_404(Job, pk=pk, user=request.user)
    if not job.transcript:
        messages.error(request, _("No transcript available yet."))
        return redirect("jobs:job_detail", pk=pk)
    from .exports import generate_srt
    content = generate_srt(job)
    base = job.original_filename.rsplit(".", 1)[0] if job.original_filename else f"job-{job.pk}"
    filename = f"{base}-transcript.srt"
    response = HttpResponse(content, content_type="text/plain; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required
@require_POST
def delete_job(request, pk):
    job = get_object_or_404(Job, pk=pk, user=request.user)
    if job.file:
        job.file.delete(save=False)
    job.delete()
    messages.success(request, _("Job deleted."))
    return redirect("jobs:dashboard")


@csrf_exempt
def assemblyai_webhook(request):
    """AssemblyAI calls this when async transcription completes."""
    if request.method != "POST":
        return HttpResponse(status=405)

    webhook_token = getattr(settings, "ASSEMBLYAI_WEBHOOK_TOKEN", "")
    if webhook_token:
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if auth_header != f"Bearer {webhook_token}":
            return HttpResponse(status=401)

    try:
        body = json.loads(request.body)
    except (ValueError, KeyError):
        return HttpResponse(status=400)

    transcript_id = body.get("transcript_id", "")
    status = body.get("status", "")
    if not transcript_id:
        return HttpResponse(status=400)

    # Deduplicate
    event_id = f"assemblyai:{transcript_id}"
    if ProcessedWebhookEvent.objects.filter(event_id=event_id).exists():
        return HttpResponse(status=200)
    ProcessedWebhookEvent.objects.create(
        provider="assemblyai",
        event_id=event_id,
        event_type=status,
    )

    job = Job.objects.filter(assemblyai_transcript_id=transcript_id).first()
    if not job:
        return HttpResponse(status=200)

    if status == "error":
        job.status = Job.Status.FAILED
        job.error_message = "AssemblyAI returned an error for this transcript."
        job.save(update_fields=["status", "error_message"])
        return HttpResponse(status=200)

    if status == "completed":
        complete_job_from_webhook(job.pk, transcript_id)

    return HttpResponse(status=200)


@login_required
def retry_job(request, pk):
    job = get_object_or_404(Job, pk=pk, user=request.user)
    if job.status == Job.Status.FAILED:
        job.status = Job.Status.PENDING
        job.error_message = ""
        job.save(update_fields=["status", "error_message"])
        run_in_background(transcribe_job_task, job.id)
        messages.info(request, _("Job #%(id)s queued for retry.") % {"id": job.id})
    return redirect("jobs:job_detail", pk=job.pk)


@login_required
def settings_view(request):
    app_settings = get_app_settings()
    if request.method == "POST":
        form = AppSettingsForm(request.POST, instance=app_settings)
        if form.is_valid():
            form.save()
            messages.success(request, _("Settings saved."))
            return redirect("jobs:settings")
    else:
        form = AppSettingsForm(instance=app_settings)
    return render(request, "jobs/settings.html", {
        "form": form,
        "assemblyai_configured": assemblyai_configured(),
    })
