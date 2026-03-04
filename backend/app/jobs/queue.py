"""
Lightweight in-process job queue using asyncio.
Each PDF processing request becomes a Job with a UUID.
The client can poll GET /api/jobs/{job_id} for status + download URL.

For scaling beyond 1 instance → swap this for Redis + Celery (same interface).
"""
import asyncio
import time
import uuid
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from app.config import get_settings

settings = get_settings()


class JobStatus(str, Enum):
    PENDING  = "pending"
    RUNNING  = "running"
    DONE     = "done"
    ERROR    = "error"


class Job:
    def __init__(self, job_id: str, fn: Callable, kwargs: Dict[str, Any]):
        self.job_id    = job_id
        self.fn        = fn
        self.kwargs    = kwargs
        self.status    = JobStatus.PENDING
        self.result    : Optional[Path] = None
        self.filename  : str = "output.pdf"
        self.mime      : str = "application/pdf"
        self.error     : Optional[str] = None
        self.created_at: float = time.time()
        self.done_at   : Optional[float] = None


class JobQueue:
    def __init__(self):
        self._jobs: Dict[str, Job] = {}
        self._semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_JOBS)
        self._started = False

    async def _worker(self, job: Job):
        async with self._semaphore:
            job.status = JobStatus.RUNNING
            try:
                result_path, filename, mime = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: job.fn(**job.kwargs)
                )
                job.result   = result_path
                job.filename = filename
                job.mime     = mime
                job.status   = JobStatus.DONE
            except Exception as e:
                job.error  = str(e)
                job.status = JobStatus.ERROR
            finally:
                job.done_at = time.time()

    async def submit(self, fn: Callable, **kwargs) -> str:
        job_id = uuid.uuid4().hex
        job = Job(job_id, fn, kwargs)
        self._jobs[job_id] = job
        asyncio.create_task(self._worker(job))
        return job_id

    def get(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    def cleanup_old_jobs(self):
        """Remove completed jobs older than TTL."""
        cutoff = time.time() - settings.FILE_TTL_SECONDS
        to_delete = [
            jid for jid, j in self._jobs.items()
            if j.done_at and j.done_at < cutoff
        ]
        for jid in to_delete:
            job = self._jobs.pop(jid)
            if job.result and Path(job.result).exists():
                try:
                    Path(job.result).unlink()
                except Exception:
                    pass


# Singleton
queue = JobQueue()
