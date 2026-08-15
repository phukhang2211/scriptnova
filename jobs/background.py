"""In-process background task runner.

Replaces Celery for single-user deployment: no broker, no separate worker
service. Tasks run in a daemon thread so the request can return immediately
while ffmpeg/AssemblyAI work happens off the request thread.

Celery @shared_task-wrapped callables can still be called directly (bypassing
.delay()) — calling the task object runs its underlying function synchronously
in whatever thread calls it.
"""
import logging
import threading

logger = logging.getLogger(__name__)


def run_in_background(task, *args, **kwargs):
    def _run():
        try:
            task(*args, **kwargs)
        except Exception:
            logger.exception("Background task %s failed", getattr(task, "__name__", task))

    threading.Thread(target=_run, daemon=True).start()
