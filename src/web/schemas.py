"""Validated request schemas for the local scraper dashboard.

Implements web-ui task 3 (REQ-UI-2.1 through REQ-UI-2.4, REQ-UI-6.1,
and REQ-UI-8.1).
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.config import CATEGORIES, PERIODS, parse_keywords

MAX_KEYWORD_INPUT_LENGTH = 500


class JobState(str, Enum):
    """Scraper job lifecycle states."""

    IDLE = "idle"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ScrapeRequest(BaseModel):
    """Validate the non-secret options for one dashboard scraper run."""

    model_config = ConfigDict(extra="forbid", strict=True)

    periods: list[str] = Field(min_length=1, max_length=len(PERIODS))
    categories: list[str] = Field(min_length=1, max_length=len(CATEGORIES))
    keywords_id: str | None = Field(default=None, max_length=MAX_KEYWORD_INPUT_LENGTH)
    keywords_gl: str | None = Field(default=None, max_length=MAX_KEYWORD_INPUT_LENGTH)
    headless: bool

    @field_validator("periods")
    @classmethod
    def validate_periods(cls, periods: list[str]) -> list[str]:
        """Reject duplicate or unsupported period identifiers."""
        return _validate_selection(
            values=periods,
            allowed=PERIODS,
            field_name="periods",
        )

    @field_validator("categories")
    @classmethod
    def validate_categories(cls, categories: list[str]) -> list[str]:
        """Reject duplicate or unsupported category identifiers."""
        return _validate_selection(
            values=categories,
            allowed=CATEGORIES,
            field_name="categories",
        )

    def parsed_keywords_id(self) -> list[str]:
        """Return Indonesian keywords using the scraper's established parser."""
        return parse_keywords(self.keywords_id)

    def parsed_keywords_gl(self) -> list[str]:
        """Return global keywords using the scraper's established parser."""
        return parse_keywords(self.keywords_gl)


class JobSnapshot(BaseModel):
    """Non-secret state snapshot of a scraper job."""

    model_config = ConfigDict(extra="forbid")

    job_id: str | None = None
    state: JobState = JobState.IDLE
    message: str = ""
    started_at: datetime | None = None
    finished_at: datetime | None = None
    completed_reports: int = 0
    total_tweets: int = 0


class ScrapeResponse(BaseModel):
    """Response after accepting a scrape run request."""

    model_config = ConfigDict(extra="forbid")

    job_id: str
    state: JobState
    message: str


def _validate_selection(
    *,
    values: list[str],
    allowed: list[str],
    field_name: str,
) -> list[str]:
    """Validate a non-empty, unique subset of configured values."""
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} must not contain duplicate values")

    unknown_values = sorted(set(values).difference(allowed))
    if unknown_values:
        raise ValueError(f"{field_name} contains unsupported values")

    return values
