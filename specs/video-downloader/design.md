# Design — Video Downloader (TwitterSaver.net Proxy)

## Architecture Overview

```
main.py (--download)
    |
    v
run_downloader()
    |
    +-- Read OUTPUT-X/index.json
    +-- For each report file:
          +-- Read ScrapeReport JSON
          +-- Filter: skip tweets with download_path
          +-- For each tweet:
                +-- resolve_video_url(page, tweet_url)   [Playwright]
                +-- download_video(url, output_path)     [httpx]
                +-- update_report(report, tweet, path)
```

## Component Design

### 1. `src/downloader.py`

#### `resolve_video_url(page: Page, tweet_url: str) -> str | None`
- Navigates to `https://twittersaver.net/en`
- Fills `#s_input` with the tweet URL
- Clicks the Download button (`button.btn-red`)
- Waits for `#data-result` to contain content (timeout 30s, poll every 1s)
- Parses the HTML for download links:
  - Looks for `<a>` tags with href containing `.mp4` or `video.twimg.com`
  - If multiple qualities found, selects highest resolution (1080 > 720 > 480)
  - Returns the direct MP4 URL string, or `None` if not found

#### `download_video(url: str, output_path: Path) -> bool`
- Uses `httpx.AsyncClient` with streaming
- Streams to file with `async for chunk in response.aiter_bytes(chunk_size=8192)`
- Returns `True` on success, `False` on HTTP error or exception

#### `run_downloader(report_path: Path | None, headless: bool) -> None`
- Main orchestrator coroutine
- Reads index.json or single report
- Opens Playwright browser (reuses `init_browser_context`)
- Iterates tweets, calls resolve + download
- Logs summary: total, succeeded, skipped, failed

### 2. HTML Parsing Strategy

TwitterSaver's API returns HTML injected into `#data-result`. The parsed HTML
contains download buttons with quality labels. Strategy:

```python
result_html = await page.inner_html("#data-result")
# Find all <a> tags with download links
# Filter for .mp4 or video.twimg.com URLs
# Sort by quality indicator in surrounding text
# Return best URL
```

Quality detection priority: `1080` > `720` > `480` > any other.
If only one link found, use it regardless of quality label.

### 3. File Organization

```
OUTPUT-X/downloads/
  2026-09-20/                    # scraped_date from report
    tweet_2101516770255270041.mp4
    tweet_abc123def456.mp4
```

Tweet ID extracted from tweet_url: last path segment before query params.

### 4. Data Model Change

Add to `VideoTweet`:
```python
download_path: str | None = Field(
    default=None,
    description="Path to downloaded MP4 file relative to OUTPUT-X"
)
```

### 5. CLI Integration

New flags in `main.py`:
```python
parser.add_argument("--download", action="store_true",
    help="Download videos from twittersaver.net for scraped tweets")
parser.add_argument("--report", type=str, default=None,
    help="Specific report file to download from (used with --download)")
```

When `--download` is set, `run_downloader()` is called instead of the scraper.

### 6. Error Handling

| Scenario | Handling |
|---|---|
| twittersaver.net times out (30s) | Log warning, skip tweet, continue |
| No download link found in HTML | Log warning, skip tweet, continue |
| httpx download fails (HTTP error) | Retry up to 2x with backoff, then skip |
| Report file not found | Log error, exit with code 1 |
| Disk write error | Log error, skip tweet, continue |

### 7. Rate Limiting

```python
await asyncio.sleep(random.uniform(3.0, 5.0))
```

Applied after each twittersaver.net navigation + resolution cycle.

## Enterprise Standards Coverage

| Category | Status | Notes |
|---|---|---|
| Security | Addressed | Tweet URLs validated; no user input injection into downloads |
| Reliability | Addressed | Retry with backoff; graceful per-tweet failure isolation |
| Observability | Addressed | Structured logging with levels; progress summary |
| Testing | Addressed | Unit tests for HTML parsing, skip logic, quality selection |
| Performance | Addressed | Sequential processing; no unbounded loops |
| Documentation | Addressed | Docstrings on all public functions |
| Code Quality | Addressed | Single responsibility; follows existing style |
| Compliance | Addressed | No sensitive data logged; downloads are public content |
| CI/CD | Addressed | Covered by existing ruff + pytest pipeline |
