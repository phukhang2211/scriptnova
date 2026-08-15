# ScriptNova — Claude Code Context

## Project overview

A self-hosted, single-machine Django transcription tool. There is no
login, no billing, and no multi-tenancy — one local `User` (username
`local`) is auto-provisioned and auto-authenticated on every request by
`jobs.middleware.AutoLoginMiddleware`. Upload audio/video, a background
thread transcribes it via AssemblyAI, and the transcript shows on a job
detail page with live polling.

This started life as a hosted SaaS ("tryscriptnova.com") with Stripe/
Paddle/VietQR billing, email verification, Google OAuth, Cloudflare R2,
and Sentry. All of that was stripped out to turn it into an open-source,
Windows-friendly local tool — see git history before this point for the
old SaaS version if that context is ever needed.

## Stack

- **Backend**: Django 6, SQLite, in-process background threads (no Celery/Redis)
- **Storage**: local filesystem (`media/`)
- **Speech**: AssemblyAI (`best` model, language auto-detection, speaker labels, summarization)
- **Frontend**: server-rendered templates, vanilla JS polling + XHR upload, no build step
- **i18n**: English + Vietnamese (`locale/vi/`)

## How to run locally (Windows)

```
setup.bat   REM create venv, install deps, migrate
run.bat     REM start the server and open the browser
```

Or manually:
```bash
python -m venv .venv && source .venv/bin/activate  # (or .venv\Scripts\activate on Windows)
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

## Key files

| Path | Purpose |
|------|---------|
| `jobs/models.py` | `Job`, `AppSettings` (singleton API-key store), `ProcessedWebhookEvent` |
| `jobs/views.py` | Dashboard, upload, job detail/status, exports, Settings page |
| `jobs/tasks.py` | Background task: ffmpeg → AssemblyAI transcribe → save |
| `jobs/services.py` | AssemblyAI wrapper (sync + async) |
| `jobs/appsettings.py` | Reads the AssemblyAI key from DB (Settings page) with env-var fallback |
| `jobs/middleware.py` | `AutoLoginMiddleware` — provisions and logs in the single local user |
| `jobs/background.py` | Thread-based background task runner (replaces Celery) |
| `jobs/scheduler.py` | Thread-based periodic cleanup (replaces Celery beat) |
| `jobs/exports.py` | DOCX + SRT export generators |
| `templates/jobs/settings.html` | In-app API key entry — no `.env` editing required |
| `config/urls.py` | URL config incl. `/health/` endpoint |

## Architecture notes

- `job.current_step` + `job.progress` updated inside the background task at each stage
- Polling endpoint (`/jobs/<pk>/status/`) returns `steps`, `progress`, `current_step`
- JS on job_detail updates stepper + progress bar without page reload
- Speaker labels stored in `utterances` JSON (each sentence has a `speaker` field)
- AI summary stored in `job.summary`
- Files stored locally under `media/uploads/`; deleted only when the user clicks
  "Delete job" (no automatic expiry — this isn't a hosted service anymore)
- AssemblyAI async path: when `ASSEMBLYAI_WEBHOOK_URL` is set, the task submits and
  returns; webhook view completes the job. Default (sync) path blocks until done —
  the right choice for local use since there's no public URL for a webhook to hit.
- No login: `AutoLoginMiddleware` authenticates every request as the single local
  user. `@login_required` decorators are kept on views for clarity but never redirect.

## Translations

```bash
python manage.py makemessages -l vi --ignore=.venv --ignore=staticfiles
# edit locale/vi/LC_MESSAGES/django.po
python scripts/compile_locales.py   # compiles .po -> .mo via Babel, no gettext needed
```

## Running tests

```bash
python manage.py test jobs
```
