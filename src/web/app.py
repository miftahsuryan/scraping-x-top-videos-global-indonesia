"""FastAPI application factory for the local scraper dashboard.

Implements web-ui task 2 (REQ-UI-1.1, REQ-UI-1.2, REQ-UI-1.3,
REQ-UI-6.1, REQ-UI-6.2, and REQ-UI-7.1).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.web.jobs import JobService
from src.web.reports import OutputRepository
from src.web.schemas import ScrapeRequest, ScrapeResponse

logger = logging.getLogger(__name__)

_WEB_DIRECTORY = Path(__file__).resolve().parent


@dataclass(frozen=True)
class DashboardAssets:
    """Resolved asset locations required by the dashboard application."""

    static_directory: Path
    template_directory: Path

    def validate(self) -> None:
        """Ensure all files needed to serve the dashboard shell are present."""
        index_template = self.template_directory / "index.html"
        if not self.static_directory.is_dir() or not index_template.is_file():
            raise RuntimeError(
                "Dashboard assets are unavailable. Reinstall the project files."
            )


def create_app(
    *,
    assets: DashboardAssets | None = None,
    job_service: JobService | None = None,
    output_repository: OutputRepository | None = None,
    run_scraper_fn=None,
) -> FastAPI:
    """Create the local dashboard application with no cross-origin policy."""
    configured_assets = assets or DashboardAssets(
        static_directory=_WEB_DIRECTORY / "static",
        template_directory=_WEB_DIRECTORY / "templates",
    )
    configured_assets.validate()

    svc = job_service or JobService()
    repo = output_repository or OutputRepository()

    app = FastAPI(
        title="X Video Scraper Dashboard",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.mount(
        "/static",
        StaticFiles(directory=configured_assets.static_directory),
        name="static",
    )

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """Return field-level validation feedback without echoing request input."""
        field_errors = [
            {
                "field": _format_validation_location(error["loc"]),
                "message": error["msg"],
            }
            for error in exc.errors()
        ]
        logger.warning(
            "event=dashboard_request_rejected method=%s path=%s error_count=%s",
            request.method,
            request.url.path,
            len(field_errors),
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Request validation failed.",
                "fields": field_errors,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(
        request: Request,
        _: Exception,
    ) -> JSONResponse:
        """Return a safe response for unexpected application errors."""
        logger.error(
            "event=dashboard_unhandled_error method=%s path=%s",
            request.method,
            request.url.path,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected dashboard error occurred."},
        )

    @app.get("/", include_in_schema=False)
    async def dashboard() -> FileResponse:
        """Serve the dashboard shell."""
        return FileResponse(configured_assets.template_directory / "index.html")

    @app.get("/api/health", include_in_schema=False)
    async def health() -> dict[str, str]:
        """Report that the local dashboard application is ready."""
        return {"status": "ok"}

    @app.post("/api/jobs", status_code=status.HTTP_202_ACCEPTED)
    async def start_job(request: ScrapeRequest) -> ScrapeResponse:
        """Start a new scraper job."""
        if svc.is_active:
            snapshot = svc.get_snapshot()
            return ScrapeResponse(
                job_id=snapshot.job_id or "",
                state=snapshot.state,
                message="A scraper job is already active.",
            )

        if run_scraper_fn is None:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"detail": "Scraper function not available."},
            )

        snapshot = await svc.start(request, run_scraper_fn)
        return ScrapeResponse(
            job_id=snapshot.job_id or "",
            state=snapshot.state,
            message=snapshot.message,
        )

    @app.get("/api/jobs/current")
    async def current_job() -> dict[str, Any]:
        """Get current job status."""
        snapshot = svc.get_snapshot()
        return snapshot.model_dump()

    @app.get("/api/reports")
    async def list_reports(
        locale: str | None = Query(default=None),
        category: str | None = Query(default=None),
        period: str | None = Query(default=None),
    ) -> list[dict]:
        """List available reports with optional filters."""
        entries = repo.list_reports(locale=locale, category=category, period=period)
        return [entry.to_dict() for entry in entries]

    @app.get("/api/reports/{report_id}", response_model=None)
    async def get_report(report_id: str):
        """Get a specific report by ID."""
        report = repo.get_report(report_id)
        if report is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "Report not found."},
            )
        return report.model_dump()

    logger.info("event=dashboard_application_created")
    return app


def _format_validation_location(location: tuple[object, ...]) -> str:
    """Format a validation location without including the submitted value."""
    parts = [str(part) for part in location if part != "body"]
    return ".".join(parts) or "request"
