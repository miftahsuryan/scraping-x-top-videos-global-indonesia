# Tasks: Explore Tweet Screenshots (`explore-tweet-screenshots`)

## Preconditions

- [x] The user has reviewed and approved requirements.md and design.md.
- [x] /spec-check explore-tweet-screenshots has passed with no enterprise-standard gaps.

## Implementation Plan

- [x] 1. Update `VideoTweet` model schema.
  - Add optional `screenshot_path: str | None = Field(default=None)` in `src/models.py`.
  - _Requirements: REQ-SHOT-2.2_

- [x] 2. Implement Playwright screenshot capture in Explore scraper.
  - Add `_capture_tweet_screenshot` helper and trigger it in `scrape_explore_for_you` in `src/scraper.py` for top results, saving PNG images in `OUTPUT-X/screenshots/`.
  - _Requirements: REQ-SHOT-1.1, REQ-SHOT-1.2, REQ-SHOT-1.3, REQ-SHOT-2.1_

- [x] 3. Add safe static screenshot endpoint in Web UI server.
  - Implement `GET /api/screenshots/{filename}` route in `src/web/app.py` with filename sanitization and path traversal prevention.
  - _Requirements: REQ-SHOT-3.1, REQ-SHOT-4.1_

- [x] 4. Update Web UI dashboard templates and JavaScript to display tweet screenshots.
  - Update `src/web/templates/index.html` and `src/web/static/app.js` to render the screenshot image thumbnail/card in report modals.
  - _Requirements: REQ-SHOT-3.2_

- [x] 5. Implement automated unit and API integration tests for screenshot functionality.
  - Create `tests/test_screenshots.py` covering path sanitization, static serving route, model serialization, and path traversal protection.
  - _Requirements: REQ-SHOT-4.2_

- [x] 6. Verify feature implementation and code quality.
  - Run `pytest tests/` and `ruff check .` to ensure all tests pass and code complies with formatting standards.
  - _Requirements: REQ-SHOT-4.2_

## Execution Rule

Execute exactly one unchecked implementation task per step, mark that task complete after verification, then stop for user confirmation.
