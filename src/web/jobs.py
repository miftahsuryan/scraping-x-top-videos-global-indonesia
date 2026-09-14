"""Process-local scraper job service.

Implements web-ui task 4 (REQ-UI-2.5, REQ-UI-3.1 through REQ-UI-3.6,
REQ-UI-6.1, REQ-UI-7.1, and REQ-UI-8.1).
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from src.web.schemas import JobSnapshot, JobState, ScrapeRequest

logger = logging.getLogger(__name__)


class JobService:
    """Manages a single active scraper job with exclusive access."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._active_task: asyncio.Task | None = None
        self._snapshot = JobSnapshot(state=JobState.IDLE, message="No active job.")

    async def start(
        self,
        request: ScrapeRequest,
        run_scraper_fn,
    ) -> JobSnapshot:
        """Start a new scraper job if none is active."""
        if self._lock.locked():
            return JobSnapshot(
                job_id=self._snapshot.job_id,
                state=JobState.RUNNING,
                message="A scraper job is already active.",
            )

        async with self._lock:
            job_id = uuid.uuid4().hex[:12]
            self._snapshot = JobSnapshot(
                job_id=job_id,
                state=JobState.QUEUED,
                message="Job queued.",
                started_at=datetime.now(timezone.utc),
            )
            logger.info("event=job_started job_id=%s", job_id)

            self._active_task = asyncio.create_task(
                self._run_job(job_id, request, run_scraper_fn)
            )

            return JobSnapshot(
                job_id=job_id,
                state=JobState.QUEUED,
                message="Scraper job started.",
            )

    async def _run_job(
        self,
        job_id: str,
        request: ScrapeRequest,
        run_scraper_fn,
    ) -> None:
        """Execute the scraper job in background."""
        self._snapshot = JobSnapshot(
            job_id=job_id,
            state=JobState.RUNNING,
            message="Scraper is running...",
            started_at=self._snapshot.started_at,
        )
        logger.info("event=job_running job_id=%s", job_id)

        try:
            await run_scraper_fn(
                periods=request.periods,
                categories=request.categories,
                custom_keywords_id=request.parsed_keywords_id(),
                custom_keywords_gl=request.parsed_keywords_gl(),
                headless=request.headless,
            )

            self._snapshot = JobSnapshot(
                job_id=job_id,
                state=JobState.COMPLETED,
                message="Scraper job completed successfully.",
                started_at=self._snapshot.started_at,
                finished_at=datetime.now(timezone.utc),
            )
            logger.info("event=job_completed job_id=%s", job_id)

        except Exception as exc:  # noqa: BLE001
            self._snapshot = JobSnapshot(
                job_id=job_id,
                state=JobState.FAILED,
                message="Scraper job failed. Check server logs for details.",
                started_at=self._snapshot.started_at,
                finished_at=datetime.now(timezone.utc),
            )
            logger.error("event=job_failed job_id=%s error=%s", job_id, exc)

        finally:
            self._active_task = None

    def get_snapshot(self) -> JobSnapshot:
        """Return current job state."""
        return self._snapshot

    @property
    def is_active(self) -> bool:
        """Check if a job is currently running."""
        return self._lock.locked()
