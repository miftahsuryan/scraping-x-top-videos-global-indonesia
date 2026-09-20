# Design: Explore Tweet Screenshots (`explore-tweet-screenshots`)

## Architecture and Rationale

This feature enhances Explore mode scraping by automatically capturing high-resolution PNG element screenshots of top-ranked tweets directly during Playwright execution.

```text
Playwright Page (x.com/explore)
     |
     +--> Locate top candidate articles (`article[data-testid='tweet']`)
     |
     +--> `article.screenshot(path=...)` --> OUTPUT-X/screenshots/tweet_<id>.png
     |
     +--> Save relative path in VideoTweet.screenshot_path
     |
     +--> Save in output report JSON
     |
     v
FastAPI Server (/api/screenshots/<filename>) --> Rendered in Web UI Dashboard
```

- **Screenshot Engine**: Playwright's `article.screenshot()` method is called on top-ranked tweets in `scrape_explore_for_you`.
- **Directory Structure**: Images are stored in `OUTPUT-X/screenshots/`.
- **API Endpoint**: FastAPI serves images from `OUTPUT-X/screenshots/` under `/api/screenshots/{filename}` with strict path sanitization.
- **Web UI**: Dashboard UI renders the screenshot image in tweet cards when `screenshot_path` is present.

_Requirements: REQ-SHOT-1.1 to REQ-SHOT-1.3, REQ-SHOT-2.1, REQ-SHOT-2.2, REQ-SHOT-3.1, REQ-SHOT-3.2_

## Components and File Boundaries

| File | Responsibility |
| --- | --- |
| `src/models.py` | Add `screenshot_path: str | None` field to `VideoTweet`. |
| `src/scraper.py` | Implement `_capture_tweet_screenshot` helper and trigger it for top results in `scrape_explore_for_you`. |
| `src/web/app.py` | Add `/api/screenshots/{filename}` endpoint to safely serve PNG files from `OUTPUT-X/screenshots/`. |
| `src/web/templates/index.html` | Include image container in tweet detail modal/card. |
| `src/web/static/app.js` | Update tweet rendering JS to display screenshot thumbnail/preview if `screenshot_path` is present. |
| `tests/test_screenshots.py` | Automated tests for screenshot path generation, file serving, and security path containment. |

_Requirements: REQ-SHOT-1.1, REQ-SHOT-2.1, REQ-SHOT-3.1, REQ-SHOT-3.2, REQ-SHOT-4.2_

## Interfaces and Data Model

### Data Model Change (`src/models.py`)

```python
class VideoTweet(BaseModel):
    tweet_url: str
    video_url: str | None = None
    caption: str = ""
    username: str = ""
    handle: str = ""
    posted_at: str | None = None
    engagement: EngagementMetrics
    source: str = "search"
    screenshot_path: str | None = Field(
        default=None, description="Path file screenshot PNG tweet jika ada"
    )
```

### Static File API (`src/web/app.py`)

- `GET /api/screenshots/{filename}`:
  - Validates `filename` (must end with `.png`, contain no path separators `/` or `\\`, and exist within `OUTPUT-X/screenshots/`).
  - Returns `FileResponse` with media type `image/png`.
  - Returns `404 Not Found` if file does not exist or path traversal attempt is detected.

_Requirements: REQ-SHOT-2.1, REQ-SHOT-2.2, REQ-SHOT-3.1_

---

## Enterprise Technical Standards Coverage

### 1. Security
- **Addressed**: `GET /api/screenshots/{filename}` strictly validates filename against path traversal attacks (rejecting `/`, `..`, null bytes). Standard directory containment checks ensure files stay within `OUTPUT-X/screenshots/`. X auth cookies/secrets are never in image metadata or endpoint logs.

### 2. Reliability & Error Handling
- **Addressed**: `_capture_tweet_screenshot` uses explicit `try/except` with timeouts. If taking a screenshot fails (e.g. element detached or network lag), the error is logged as a warning, `screenshot_path` is set to `None`, and scraper execution continues without throwing an unhandled exception.

### 3. Observability
- **Addressed**: Structured logger messages emit screenshot generation events, file paths, and any failure warnings.

### 4. Testing
- **Addressed**: Automated tests in `tests/test_screenshots.py` test `VideoTweet` schema with `screenshot_path`, file path resolution, static route validation, and path traversal protection.

### 5. Performance & Scalability
- **Addressed**: Screenshots are taken only for the final top-N selected tweets (not every candidate scanned), minimizing I/O overhead.

### 6. Documentation
- **Addressed**: Function docstrings updated in `src/scraper.py` and API route docs updated in `src/web/app.py`.

### 7. Code Quality & Maintainability
- **Addressed**: Modular implementation across `models.py`, `scraper.py`, and `app.py`. Enforces `ruff check .` standards.

### 8. Compliance & Data Handling
- **Addressed**: Screenshots store public tweet DOM nodes as visible on screen. Credentials/tokens are not rendered in tweet DOM containers.

### 9. CI/CD & Versioning
- **Addressed**: Fully backwards compatible; existing report reading and API endpoints handle `screenshot_path=None` gracefully.
