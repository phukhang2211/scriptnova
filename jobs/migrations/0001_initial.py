import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AppSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assemblyai_api_key', models.CharField(blank=True, max_length=255)),
                ('notify_on_complete', models.BooleanField(default=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(max_length=500, upload_to='uploads/')),
                ('transcript', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('done', 'Done'), ('failed', 'Failed')], default='pending', max_length=16)),
                ('error_message', models.TextField(blank=True)),
                ('current_step', models.CharField(default='queued', max_length=32)),
                ('progress', models.IntegerField(default=0)),
                ('audio_duration_seconds', models.FloatField(blank=True, null=True)),
                ('utterances', models.JSONField(blank=True, null=True)),
                ('summary', models.TextField(blank=True)),
                ('assemblyai_transcript_id', models.CharField(blank=True, max_length=64)),
                ('language_code', models.CharField(blank=True, max_length=16)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='jobs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ProcessedWebhookEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.CharField(default='assemblyai', max_length=32)),
                ('event_id', models.CharField(max_length=255, unique=True)),
                ('event_type', models.CharField(max_length=128)),
                ('processed_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-processed_at'],
            },
        ),
    ]
