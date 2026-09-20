# Requirements — Video Downloader (TwitterSaver.net Proxy)

## Context

The X/Twitter Video Engagement Scraper collects tweet URLs and metadata into
JSON reports under `OUTPUT-X/`. Currently, `video_url` fields are often `null`
because X serves videos as `blob:` URLs via JavaScript media players. This
feature adds a post-processing step that resolves downloadable MP4 links using
twittersaver.net as a proxy, then downloads the files locally.

## Actors

- **Primary user**: CLI operator running `python main.py --download`
- **External service**: twittersaver.net (third-party Twitter video resolver)

## Functional Requirements

### FR-1: Report Discovery
The system SHALL read `OUTPUT-X/index.json` to discover all report files from
the latest scraper run.

### FR-2: Tweet Filtering
The system SHALL skip tweets that already have a non-null `download_path` field,
enabling safe re-runs without re-downloading.

### FR-3: URL Resolution via TwitterSaver
For each tweet URL, the system SHALL:
1. Navigate Playwright to `https://twittersaver.net/en`
2. Input the tweet URL into the search form (`#s_input`)
3. Click the Download button
4. Wait for `#data-result` to populate (timeout: 30s)
5. Extract the highest-quality MP4 download link from the rendered HTML

### FR-4: Video Download
The system SHALL download the resolved MP4 URL using `httpx` async streaming
to `OUTPUT-X/downloads/{scraped_date}/{tweet_id}.mp4`.

### FR-5: Report Update
After successful download, the system SHALL update the source report JSON
with the `download_path` field set on the corresponding tweet.

### FR-6: Skip Already-Downloaded
If a tweet already has `download_path` set and the file exists on disk,
the system SHALL skip both resolution and download.

### FR-7: CLI Interface
The system SHALL accept these CLI flags:
- `--download` — enable download mode (reads reports, resolves, downloads)
- `--report PATH` — target a specific report file instead of all from index

### FR-8: Rate Limiting
The system SHALL wait 3-5 seconds between twittersaver.net requests to avoid
triggering rate limits or account restrictions.

### FR-9: Retry Logic
The system SHALL retry failed resolutions/downloads up to 2 times with
exponential backoff (2s, 4s). After exhausting retries, log the failure
and continue to the next tweet.

### FR-10: Output Structure
Downloaded files SHALL be organized as:
```
OUTPUT-X/downloads/{scraped_date}/tweet_{tweet_id}.mp4
```

## Non-Functional Requirements

### NFR-1: Dependency
Add `httpx` to `requirements.txt`. No other new dependencies.

### NFR-2: Observability
All operations SHALL use structured logging via the `logging` module.
Log levels: INFO for progress, WARNING for retries/skips, ERROR for failures.

### NFR-3: Resilience
A failure in one tweet's download SHALL NOT prevent processing of subsequent
tweets. The system processes tweets sequentially with independent error handling.

## Acceptance Criteria

- [ ] `python main.py --download` reads all reports and downloads videos
- [ ] `python main.py --download --report path/to/report.json` processes one file
- [ ] Tweets with existing `download_path` are skipped
- [ ] Downloaded MP4 files exist at `OUTPUT-X/downloads/{date}/tweet_{id}.mp4`
- [ ] Source report JSONs are updated with `download_path` values
- [ ] Rate limiting: >=3s delay between twittersaver.net requests
- [ ] Failed downloads are logged and retried (max 2x), then skipped
- [ ] All code passes `ruff check .` and `pytest tests/`
