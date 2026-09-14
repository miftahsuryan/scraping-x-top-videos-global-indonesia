"""Tests for dashboard run-request validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.config import CATEGORIES, PERIODS, parse_keywords
from src.web.schemas import MAX_KEYWORD_INPUT_LENGTH, ScrapeRequest


def test_scrape_request_accepts_current_config_values() -> None:
    """Configured period/category values and boolean settings are accepted."""
    request = ScrapeRequest(
        periods=PERIODS,
        categories=CATEGORIES,
        keywords_id='"breaking news",update',
        keywords_gl="market,ai",
        headless=True,
    )

    assert request.periods == PERIODS
    assert request.categories == CATEGORIES
    assert request.parsed_keywords_id() == parse_keywords(request.keywords_id)
    assert request.parsed_keywords_gl() == parse_keywords(request.keywords_gl)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("periods", []),
        ("categories", []),
        ("periods", ["3days", "3days"]),
        ("categories", [CATEGORIES[0], CATEGORIES[0]]),
        ("periods", ["invalid"]),
        ("categories", ["invalid"]),
    ],
)
def test_scrape_request_rejects_invalid_selection(
    field_name: str,
    value: list[str],
) -> None:
    """Selections must be non-empty, unique, and defined in configuration."""
    payload: dict[str, object] = {
        "periods": [PERIODS[0]],
        "categories": [CATEGORIES[0]],
        "headless": True,
    }
    payload[field_name] = value

    with pytest.raises(ValidationError):
        ScrapeRequest.model_validate(payload)


@pytest.mark.parametrize("field_name", ["keywords_id", "keywords_gl"])
def test_scrape_request_rejects_overlong_keywords(field_name: str) -> None:
    """Keyword fields are bounded before they can reach scraper execution."""
    payload: dict[str, object] = {
        "periods": [PERIODS[0]],
        "categories": [CATEGORIES[0]],
        "headless": False,
        field_name: "a" * (MAX_KEYWORD_INPUT_LENGTH + 1),
    }

    with pytest.raises(ValidationError):
        ScrapeRequest.model_validate(payload)


@pytest.mark.parametrize(
    "payload_update",
    [
        {"headless": "true"},
        {"periods": PERIODS[0]},
        {"unexpected": "value"},
    ],
)
def test_scrape_request_rejects_wrong_types_and_extra_fields(
    payload_update: dict[str, object],
) -> None:
    """Strict request validation disallows coercion and unknown fields."""
    payload: dict[str, object] = {
        "periods": [PERIODS[0]],
        "categories": [CATEGORIES[0]],
        "headless": True,
    }
    payload.update(payload_update)

    with pytest.raises(ValidationError):
        ScrapeRequest.model_validate(payload)
