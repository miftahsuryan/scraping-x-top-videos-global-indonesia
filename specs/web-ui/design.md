# Design: Local Scraper Dashboard

## Architecture and Rationale

The feature adds a small, local FastAPI application with HTML, vanilla JavaScript, and CSS assets. FastAPI and Uvicorn are explicit new Python dependencies; no Node.js, database, or remote service is introduced. This suits the current Python-only project and supports a one-command local launch.

The dashboard reuses the existing main.run_scraper coroutine rather than duplicating search, authentication, ranking, or export behavior. A process-local job service starts that coroutine in a background task and exposes a narrow, validated HTTP API. It permits exactly one active job because browser session state and output/index.json are shared by the existing scraper.

```text
Browser (localhost only)
  GET /                         static dashboard shell
  POST /api/jobs                validated JobService.start(...)
  GET /api/jobs/current         non-secret current job snapshot
  GET /api/reports              safe OutputRepository catalogue
  GET /api/reports/{report_id}  validated ScrapeReport
                                     |
FastAPI application --> JobService --> main.run_scraper(...)
       |                                  existing Playwright/X flow
       +--> OutputRepository ------------> output/index.json and report JSON
```

The server starts at 127.0.0.1:8000. Account management is not required for this local-only threat model. Binding to 0.0.0.0, reverse proxies, and remote access are deliberately outside scope. The UI never displays, stores, or transmits X credentials.

_Requirements: REQ-UI-1.1 to REQ-UI-1.3, REQ-UI-2.5, REQ-UI-3.1 to REQ-UI-3.6, REQ-UI-6.1 to REQ-UI-6.4_

## Components and File Boundaries

| File | Responsibility |
| --- | --- |
| web_ui.py | Dashboard entry point. Configures Uvicorn's explicit loopback host and port, without changing main.py CLI behavior. |
| src/web/app.py | FastAPI application factory, static-file/template configuration, root/health/API routes, response mapping, and request logging. |
| src/web/schemas.py | Pydantic request and response types plus validators. Imports config values; never duplicates category or period lists. |
| src/web/jobs.py | JobService and in-memory ScrapeJob state machine. Enforces exclusivity, calls the existing scraper coroutine, maps success/failure, and never persists secrets/error traces. |
| src/web/reports.py | OutputRepository. Reads and validates index.json and report files, constrains paths below OUTPUT_DIR, and issues opaque report IDs. |
| src/web/templates/index.html | Accessible dashboard structure: header, run form, status, report filters/list, and selected-report detail. |
| src/web/static/app.js | API client, client-side usability validation, active-only polling, safe DOM text rendering, and empty/error-state presentation. |
| src/web/static/styles.css | Responsive accessible visual system. CSS only, with no compilation step. |
| tests/test_web_schemas.py | Schema validation and serialization tests. |
| tests/test_web_jobs.py | Job lifecycle, exclusivity, completion, and failure-release tests with the scraper coroutine mocked. |
| tests/test_web_reports.py | Output containment, malformed JSON/schema, missing catalogue, and valid report tests using temporary directories. |
| tests/test_web_api.py | Root, health, validation, conflict, catalogue, and selected-report endpoint tests with isolated application state. |

src/web/__init__.py establishes the package. Existing scraper code remains authoritative for scraping behavior and report generation.

_Requirements: REQ-UI-1.2, REQ-UI-2.1 to REQ-UI-2.5, REQ-UI-3.1 to REQ-UI-3.6, REQ-UI-4.1 to REQ-UI-4.4, REQ-UI-7.1, REQ-UI-8.1_

## Interfaces and Data Model

### Dashboard command

```text
python web_ui.py
```

The documented default is 127.0.0.1:8000. The entry point explicitly passes that host to Uvicorn and must not infer a public host from environment configuration in this feature.

### API

| Method and path | Request | Success | Failure |
| --- | --- | --- | --- |
| GET / | none | dashboard HTML | safe startup error only |
| GET /api/health | none | status ok | 503 if application dependencies are unavailable |
| POST /api/jobs | ScrapeRequest | 202 plus JobSnapshot | 422 invalid input; 409 active job |
| GET /api/jobs/current | none | current or idle JobSnapshot | 200 without stack traces/secrets |
| GET /api/reports | optional known locale/category/period filters | catalogue metadata | 200 with empty list/safe warnings |
| GET /api/reports/{report_id} | opaque server-issued ID | validated ScrapeReport | 404 unknown; 422 corrupt selected report |

ScrapeRequest fields:

```text
periods: list[str]        non-empty subset of src.config.PERIODS
categories: list[str]     non-empty subset of src.config.CATEGORIES
keywords_id: str | null   bounded raw input, parsed through parse_keywords
keywords_gl: str | null   bounded raw input, parsed through parse_keywords
headless: bool            explicit form value
```

The UI's all selection expands to the current config lists before submitting. Server validation remains authoritative: duplicates, unknown identifiers, empty selections, non-boolean headless values, and keyword text above a documented bound are rejected. Keyword text exists only in active job input and is excluded from logs and status responses.

JobSnapshot fields:

```text
job_id: str | null
state: idle | queued | running | completed | failed
message: str
started_at: ISO-8601 string | null
finished_at: ISO-8601 string | null
completed_reports: int
total_tweets: int
```

JobService holds one asyncio lock and active task. States follow idle -> queued -> running -> completed or failed. Completion derives counts from the safe catalogue. Failure stores a generic operator-safe message and logs a structured internal event. A finally path releases the run lock. Jobs do not survive restart.

OutputRepository treats every file reference as untrusted. It receives valid entries from index.json, joins each to the resolved output root, resolves it, and rejects it unless the output root remains its ancestor. It opens UTF-8 JSON, validates it using the existing ScrapeReport Pydantic model, and never returns raw file paths. It recomputes safe paths for opaque report IDs.

_Requirements: REQ-UI-2.1 to REQ-UI-2.5, REQ-UI-3.1 to REQ-UI-3.5, REQ-UI-4.1 to REQ-UI-4.4, REQ-UI-6.1 to REQ-UI-6.3_

## User Experience

The single dashboard has, from top to bottom:

1. A product header with a local-only indicator and engagement formula.
2. A run panel with period/category multi-select controls, Indonesian/global keyword fields, headless toggle, inline validation, and a Start scraping button.
3. A current-run panel with state, timestamps, safe progress text, counters, and an indeterminate progress indicator while active.
4. Report filters for locale, category, and period, with an available-report list.
5. A selected-report summary and ranked tweet cards. Metric labels accompany every value, and X/video links open only after an operator activates them.

The browser polls current-job state only while queued/running, stops in terminal/idle states, and refreshes the catalogue after completion. All fields originating from JSON use textContent or created DOM text nodes, never HTML injection. CSS collapses into one column at narrow widths, wraps long captions/URLs, exposes focus states, and has sufficient contrast.

_Requirements: REQ-UI-2.1 to REQ-UI-2.3, REQ-UI-3.2 to REQ-UI-3.5, REQ-UI-4.3, REQ-UI-5.1 to REQ-UI-5.5, REQ-UI-6.3_

## Error Handling and Observability

- Invalid input receives structured 422 feedback and never reaches scraper execution.
- A simultaneous start receives 409 and keeps the UI observing the active job.
- Scraper exceptions set failed state, log server-side with job ID, return a generic recovery message, and release the lock.
- No output is a normal empty state. Corrupt catalogue entries are skipped and logged; requesting a corrupt report yields 422 without breaking valid reports.
- Startup, state transitions, rejected jobs, report validation failures, and I/O faults emit structured logging using the current Python logging system. Logs may include job ID, state, counts, and safe failure type; they must not include cookie values, raw keywords, raw X queries, captions, or stack traces in HTTP responses.

_Requirements: REQ-UI-1.3, REQ-UI-2.3, REQ-UI-3.3 to REQ-UI-3.5, REQ-UI-4.4, REQ-UI-6.1, REQ-UI-7.1_

## Testing and Manual Verification

Tests mock Playwright-facing execution, so neither credentials, browser launch, nor network access are needed. Automated coverage includes known/unknown/duplicate/empty/overlong run input; active-job conflict; successful completion; failure lock release; absent/corrupt/traversal output; filters; endpoint responses; and absence of secret fields from serializations.

New src/web/ Python modules have an 85% line coverage target. Project-wide coverage is explicitly deferred because the project has no coverage tool. A manual Chromium check is required at desktop and narrow mobile widths: valid/invalid form behavior, active/completed state, no-output state, report filters, and external links.

_Requirements: REQ-UI-8.1 to REQ-UI-8.3_

## Enterprise Standard Coverage

1. **Security — Addressed:** loopback bind, same-origin API, strict validation, output containment, safe DOM text, no default CORS, and no secret fields. Requirements REQ-UI-1.1, REQ-UI-2.2 to REQ-UI-2.3, REQ-UI-4.2, REQ-UI-6.1 to REQ-UI-6.3.
2. **Reliability & Error Handling — Addressed:** single-job lock, finally release, I/O/schema isolation, and safe diagnostics. Requirements REQ-UI-1.3, REQ-UI-3.3 to REQ-UI-3.6, REQ-UI-4.4.
3. **Observability — Addressed:** structured credential-safe lifecycle/failure logs with job IDs. Requirement REQ-UI-7.1.
4. **Testing — Addressed:** unit/API tests, 85% new-module expectation, and Chromium manual check. Requirements REQ-UI-8.1 to REQ-UI-8.3.
5. **Performance & Scalability — Addressed:** one bounded scraper job, short report reads, active-only polling, no media proxy, and stated single-local-operator limitation. Requirements REQ-UI-3.3 and REQ-UI-5.3.
6. **Documentation — Addressed:** README and usage documentation cover setup, operation, and limitations. Requirement REQ-UI-7.2.
7. **Code Quality & Maintainability — Addressed:** typed single-responsibility modules use existing config/models as source of truth; Ruff/pytest required. Requirements REQ-UI-2.1 and REQ-UI-8.2.
8. **Compliance & Data Handling — Addressed:** cookies and submitted keywords are not exposed/persisted; tweet retention remains existing report behavior. Requirements REQ-UI-6.1 and REQ-UI-6.4.
9. **CI/CD & Versioning — Explicitly N/A:** no CI, release, or changelog system currently exists. The UI preserves CLI and JSON-output compatibility and runs established local checks.
