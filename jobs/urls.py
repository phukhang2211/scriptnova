from django.urls import path

from . import views

app_name = "jobs"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("upload/", views.upload_job, name="upload"),
    path("jobs/<int:pk>/", views.job_detail, name="job_detail"),
    path("jobs/<int:pk>/status/", views.job_status, name="job_status"),
    path("jobs/<int:pk>/retry/", views.retry_job, name="retry_job"),
    path("jobs/<int:pk>/delete/", views.delete_job, name="delete_job"),
    path("jobs/<int:pk>/export/docx/", views.export_docx, name="export_docx"),
    path("jobs/<int:pk>/export/srt/", views.export_srt, name="export_srt"),
    path("webhooks/assemblyai/", views.assemblyai_webhook, name="assemblyai_webhook"),
    path("settings/", views.settings_view, name="settings"),
]
