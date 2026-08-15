"""Lightweight in-process periodic task runner.

Single-user local deployment has no separate worker/scheduler process, so
the periodic cleanup tasks run on a daemon thread inside the web process
instead. Started once from config/wsgi.py when the app loads (not from
management commands like migrate/collectstatic, which never import wsgi.py).
"""
import logging
import threading
import time

logger = logging.getLogger(__name__)

_started = False
_started_lock = threading.Lock()

CHECK_INTERVAL_SECONDS = 30 * 60  # run the loop every 30 min


def _run_periodic_tasks():
    from jobs.tasks import cleanup_stale_pending_jobs_task, cleanup_temp_files_task

    while True:
        for task in (cleanup_temp_files_task, cleanup_stale_pending_jobs_task):
            try:
                task()
            except Exception:
                logger.exception("Scheduled task %s failed", task.__name__)
        time.sleep(CHECK_INTERVAL_SECONDS)


def start_scheduler():
    global _started
    with _started_lock:
        if _started:
            return
        _started = True
    threading.Thread(target=_run_periodic_tasks, daemon=True).start()
