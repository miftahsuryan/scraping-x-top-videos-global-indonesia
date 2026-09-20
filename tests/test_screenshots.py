"""Tests for screenshot static route and schema fields."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from src.models import EngagementMetrics, VideoTweet
from src.web.app import create_app


def test_video_tweet_schema_with_screenshot_path() -> None:
    """VideoTweet correctly handles screenshot_path with date subfolder."""
    tweet = VideoTweet(
        tweet_url="https://x.com/user/status/123",
        engagement=EngagementMetrics(likes=10, views=100, reposts=2, replies=1, total_score=112),
        screenshot_path="OUTPUT-X/screenshots/2026-09-20/tweet_123.png"
    )
    assert tweet.screenshot_path == "OUTPUT-X/screenshots/2026-09-20/tweet_123.png"


def test_screenshot_api_serving_and_traversal_defense(tmp_path: Path) -> None:
    """Test serving valid screenshot and rejecting path traversal attempts."""
    app = create_app()
    client = TestClient(app)

    screenshots_dir = Path("OUTPUT-X/screenshots/2026-09-20")
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    test_file = screenshots_dir / "test_dummy.png"
    test_file.write_bytes(b"dummy image content")

    try:
        # Valid fetch with date subfolder
        response = client.get("/api/screenshots/2026-09-20/test_dummy.png")
        assert response.status_code == 200
        assert response.content == b"dummy image content"

        # Invalid date format
        response_bad_date = client.get("/api/screenshots/not-a-date/test_dummy.png")
        assert response_bad_date.status_code == 404

        # Traversal in date
        response_traversal_date = client.get("/api/screenshots/../app.py/test.png")
        assert response_traversal_date.status_code == 404

        # Traversal in filename
        response_traversal_file = client.get("/api/screenshots/2026-09-20/../app.py")
        assert response_traversal_file.status_code == 404

        # Non-existent file
        response_non_existent = client.get("/api/screenshots/2026-09-20/non_existent.png")
        assert response_non_existent.status_code == 404
    finally:
        if test_file.exists():
            test_file.unlink()
