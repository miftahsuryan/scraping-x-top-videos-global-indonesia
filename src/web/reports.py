"""Safe output-report repository for the dashboard.

Implements web-ui task 5 (REQ-UI-4.1 through REQ-UI-4.4, REQ-UI-5.1,
REQ-UI-5.2, REQ-UI-5.4, REQ-UI-6.3, and REQ-UI-8.1).
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

from src.config import OUTPUT_DIR
from src.models import ScrapeReport

logger = logging.getLogger(__name__)


class ReportCatalogueEntry:
    """Metadata for a single report in the catalogue."""

    def __init__(
        self,
        report_id: str,
        locale: str,
        category: str,
        period: str,
        filename: str,
        scraped_at: str,
        total_items: int,
    ) -> None:
        self.report_id = report_id
        self.locale = locale
        self.category = category
        self.period = period
        self.filename = filename
        self.scraped_at = scraped_at
        self.total_items = total_items

    def to_dict(self) -> dict:
        """Convert to serializable dict."""
        return {
            "report_id": self.report_id,
            "locale": self.locale,
            "category": self.category,
            "period": self.period,
            "filename": self.filename,
            "scraped_at": self.scraped_at,
            "total_items": self.total_items,
        }


class OutputRepository:
    """Read and validate reports from the output directory."""

    def __init__(self, output_dir: str = OUTPUT_DIR) -> None:
        self._output_root = Path(output_dir).resolve()

    def _make_report_id(self, filename: str) -> str:
        """Create an opaque report ID from filename."""
        return hashlib.sha256(filename.encode()).hexdigest()[:16]

    def _safe_path(self, relative_path: str) -> Path | None:
        """Resolve a path and ensure it stays within OUTPUT_DIR."""
        candidate = (self._output_root / relative_path).resolve()
        if not str(candidate).startswith(str(self._output_root)):
            logger.warning("event=path_traversal_attempt path=%s", relative_path)
            return None
        return candidate

    def list_reports(
        self,
        locale: str | None = None,
        category: str | None = None,
        period: str | None = None,
    ) -> list[ReportCatalogueEntry]:
        """List available reports, optionally filtered."""
        index_path = self._output_root / "index.json"
        if not index_path.is_file():
            logger.info("event=catalogue_not_found")
            return []

        try:
            with open(index_path, encoding="utf-8") as f:
                index_data = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("event=catalogue_load_error error=%s", exc)
            return []

        results = index_data.get("results", [])
        entries: list[ReportCatalogueEntry] = []

        for result in results:
            r_locale = result.get("locale", "")
            r_category = result.get("category", "")
            r_period = result.get("period", "")

            if locale and r_locale != locale:
                continue
            if category and r_category != category:
                continue
            if period and r_period != period:
                continue

            filename = result.get("filename", "")
            report_id = self._make_report_id(filename)

            entries.append(ReportCatalogueEntry(
                report_id=report_id,
                locale=r_locale,
                category=r_category,
                period=r_period,
                filename=filename,
                scraped_at=result.get("scraped_at", ""),
                total_items=result.get("total_items", 0),
            ))

        return entries

    def get_report(self, report_id: str) -> ScrapeReport | None:
        """Load and validate a report by its opaque ID."""
        entries = self.list_reports()
        target = None
        for entry in entries:
            if entry.report_id == report_id:
                target = entry
                break

        if target is None:
            logger.info("event=report_not_found report_id=%s", report_id)
            return None

        safe_path = self._safe_path(target.filename)
        if safe_path is None:
            return None

        if not safe_path.is_file():
            logger.warning("event=report_file_missing report_id=%s", report_id)
            return None

        try:
            with open(safe_path, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("event=report_load_error report_id=%s error=%s", report_id, exc)
            return None

        try:
            return ScrapeReport.model_validate(data)
        except Exception as exc:  # noqa: BLE001
            logger.warning("event=report_validation_error report_id=%s error=%s", report_id, exc)
            return None
