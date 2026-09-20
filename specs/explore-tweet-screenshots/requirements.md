# Requirements: Explore Tweet Screenshots (`explore-tweet-screenshots`)

## Introduction
When running Explore scraping mode, the scraper collects top tweets. To provide visual preview capabilities similar to TweetPik (TweetHunter's screenshot tool), the scraper will capture clean, high-resolution element screenshots of top tweets from the Explore tab and store them locally under `OUTPUT-X/screenshots/`. These screenshots will be linked in the JSON report output and displayed in the local Web UI dashboard.

## Scope

### In Scope
- Element screenshot capture of `article[data-testid='tweet']` using Playwright during Explore mode scraping.
- Local storage of PNG screenshots in `OUTPUT-X/screenshots/` using tweet ID based filenames.
- Extension of `VideoTweet` model to include `screenshot_path: str | None`.
- Web UI static endpoint `/api/screenshots/<filename>` with directory traversal protection.
- Rendering tweet screenshots inside the Web UI dashboard report modal.

### Out of Scope
- External 3rd-party TweetPik API network requests (all screenshots rendered locally via Playwright).
- Modifying search-mode query scraping logic.

---

## Acceptance Criteria (EARS Format)

### Requirement 1: Local Screenshot Capture Engine
- **REQ-SHOT-1.1**: WHEN Explore scraper selects top ranked tweets, THEN THE SYSTEM SHALL capture an element screenshot of each selected tweet's `article[data-testid='tweet']` container.
- **REQ-SHOT-1.2**: WHEN taking a screenshot, THEN THE SYSTEM SHALL wait for media elements inside the tweet container to render or timeout gracefully.
- **REQ-SHOT-1.3**: IF capturing a screenshot fails for a specific tweet, THEN THE SYSTEM SHALL log a warning, record `screenshot_path` as null, and SHALL NOT abort the scraping process.

### Requirement 2: Image Storage & Data Schema
- **REQ-SHOT-2.1**: WHEN saving a screenshot, THEN THE SYSTEM SHALL ensure `OUTPUT-X/screenshots/` exists and store the image using a sanitized name format `tweet_<tweet_id>.png`.
- **REQ-SHOT-2.2**: WHEN writing `ScrapeReport` JSON files, THEN THE SYSTEM SHALL store the relative path in `VideoTweet.screenshot_path`.

### Requirement 3: Web UI Dashboard Integration
- **REQ-SHOT-3.1**: WHEN requested, THEN THE SYSTEM SHALL serve saved screenshots via `/api/screenshots/<filename>` while strictly preventing directory traversal outside `OUTPUT-X/screenshots/`.
- **REQ-SHOT-3.2**: WHEN viewing a tweet in the Web UI report modal, THEN THE SYSTEM SHALL display its screenshot image when available.

### Requirement 4: Quality & Compliance
- **REQ-SHOT-4.1**: THE SYSTEM SHALL NOT expose credentials or session cookies in screenshot image files or metadata.
- **REQ-SHOT-4.2**: Implementation SHALL include automated tests and pass `pytest tests/` and `ruff check .`.
