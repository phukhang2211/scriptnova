from django.contrib import admin
from .models import Job, ProcessedWebhookEvent


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__username", "transcript")


@admin.register(ProcessedWebhookEvent)
class ProcessedWebhookEventAdmin(admin.ModelAdmin):
    list_display = ("provider", "event_id", "event_type", "processed_at")
    list_filter = ("provider", "event_type")
    search_fields = ("event_id", "event_type")
