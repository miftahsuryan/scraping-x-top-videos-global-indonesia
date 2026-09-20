# Tasks — Video Downloader (TwitterSaver.net Proxy)

## Phase 1: Foundation

### Task 1: Add httpx dependency
- [x] Add `httpx` to `requirements.txt`. (Requirement: NFR-1)

### Task 2: Extend VideoTweet model
- [x] Add `download_path: str | None = Field(default=None, ...)` to `VideoTweet` in
`src/models.py`. Ensure backward compatibility (default=None means existing
JSON files load without error). (Requirement: FR-5)

## Phase 2: Core Downloader

### Task 3: Create src/downloader.py skeleton
- [x] Create the module with imports, constants (TWITTERSAVER_URL, DELAY_MIN/MAX,
MAX_RETRIES, DOWNLOAD_DIR), and type hints. (Requirement: FR-8, FR-9)

### Task 4: Implement resolve_video_url()
- [x] Playwright-based URL resolution:
  - Navigate to twittersaver.net/en
  - Fill input, click Download button
  - Wait for #data-result with timeout
  - Parse HTML for best MP4 link
  - Return URL string or None
  (Requirement: FR-3)

### Task 5: Implement download_video()
- [x] httpx async streaming download:
  - Stream to file via asyncio.to_thread
  - Return bool success/failure
  - Handle HTTP errors and exceptions
  (Requirement: FR-4)

### Task 6: Implement run_downloader()
- [x] Main orchestrator:
  - Read index.json or specific report
  - Filter tweets (skip if download_path set or file exists)
  - Loop: resolve -> download -> update report
  - Rate limiting between requests
  - Retry logic with exponential backoff
  - Summary logging
  (Requirement: FR-1, FR-2, FR-6, FR-9, FR-10)

## Phase 3: CLI Integration

### Task 7: Add CLI flags to main.py
- [x] Add --download and --report arguments. Wire to run_downloader().
(Requirement: FR-7)

## Phase 4: Testing

### Task 8: Write unit tests
- [x] Create tests/test_downloader.py:
  - Test quality selection logic (1080 > 720 > 480)
  - Test tweet ID extraction from URL
  - Test skip logic (existing download_path)
  - Test download path generation
  (Requirement: all acceptance criteria)

## Phase 5: Verification

### Task 9: Run lint and tests
- [x] `ruff check .` -- no errors
- [x] `pytest tests/` -- all 37 tests pass
(Requirement: NFR-3)
