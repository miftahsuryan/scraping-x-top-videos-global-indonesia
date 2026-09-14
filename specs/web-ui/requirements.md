# Requirements: Local Scraper Dashboard

## Introduction

The X/Twitter Video Scraper is currently operated only through CLI arguments and writes JSON reports to output/. This feature adds a responsive, local-only browser dashboard that lets an operator start an existing scrape configuration, observe its status, and browse reports already written by the scraper. It is an alternative entry point, not a replacement for the CLI.

The dashboard operates only on the local machine. X credentials remain server-side in .env and are never exposed to the browser, API payloads, logs, status text, or output.

## Scope

In scope:

- Start a scraper run with existing period, category, custom keyword, and headless-browser options.
- Show concise polling status for the active or most recent run.
- Browse and filter valid JSON reports under output/.
- Display ranked tweets, metrics, and external X/video links.

Out of scope:

- Accounts, remote or multi-user deployment, scheduling, or job history beyond current-process state and output files.
- Editing credentials, default keywords, existing reports, or source configuration in the browser.
- Downloading, proxying, embedding, or re-hosting video media.

## Acceptance Criteria (EARS Format)

### Requirement 1: Local Dashboard Access

- **REQ-UI-1.1**: WHEN the operator starts the dashboard command, THEN THE SYSTEM SHALL serve it only on loopback (127.0.0.1) on its documented port and SHALL not bind to an externally reachable interface by default.
- **REQ-UI-1.2**: WHEN the root dashboard URL is opened, THEN THE SYSTEM SHALL render a responsive interface without requiring a Node.js build step.
- **REQ-UI-1.3**: WHEN startup fails because the port is occupied or a runtime dependency is missing, THEN THE SYSTEM SHALL exit with an actionable error that does not disclose credentials.

### Requirement 2: Scrape Configuration and Validation

- **REQ-UI-2.1**: WHEN the operator opens the run form, THEN THE SYSTEM SHALL offer all values currently defined by src.config.CATEGORIES and src.config.PERIODS, with an all-values option for each.
- **REQ-UI-2.2**: WHEN the operator submits a run, THEN THE SYSTEM SHALL accept only a non-empty selection of known periods and categories, optional comma-separated Indonesian and global keywords, and an explicit headless setting.
- **REQ-UI-2.3**: IF submitted periods, categories, keywords, or option types are invalid, THEN THE SYSTEM SHALL reject the request with field-level, credential-safe validation feedback and SHALL NOT start a scraper process.
- **REQ-UI-2.4**: WHEN valid custom keywords are submitted, THEN THE SYSTEM SHALL pass them through existing parse_keywords behavior and preserve existing merge-with-default-keywords behavior.
- **REQ-UI-2.5**: WHEN a run is started from the dashboard, THEN THE SYSTEM SHALL use the existing scraper orchestration and SHALL write reports in the same output/{locale}/{category}/ structure and output/index.json format as an equivalent CLI run.

### Requirement 3: Run Lifecycle and Status

- **REQ-UI-3.1**: WHEN a valid run request is accepted, THEN THE SYSTEM SHALL start it without blocking the browser request and SHALL assign it a non-secret, process-local job identifier.
- **REQ-UI-3.2**: WHILE a scraper job is queued or running, THEN THE SYSTEM SHALL expose its state and a human-readable progress summary to the dashboard.
- **REQ-UI-3.3**: WHILE a scraper job is queued or running, THEN THE SYSTEM SHALL prevent a second run from starting and SHALL return a clear conflict response containing the active job identifier.
- **REQ-UI-3.4**: WHEN a scraper job completes, THEN THE SYSTEM SHALL show its completed state, total reports, total tweets, and completion time; it SHALL refresh the report catalogue.
- **REQ-UI-3.5**: IF a scraper job fails, THEN THE SYSTEM SHALL mark it failed, retain a concise safe error summary for the current process, release the run lock, and allow a later run.
- **REQ-UI-3.6**: WHEN the dashboard process stops, THEN THE SYSTEM SHALL not claim that a previously in-process scraper job can be resumed.

### Requirement 4: Report Catalogue and Filtering

- **REQ-UI-4.1**: WHEN the dashboard loads or a run completes, THEN THE SYSTEM SHALL list report metadata from output/index.json when available and SHALL present an empty-state message when no catalogue exists.
- **REQ-UI-4.2**: WHEN a report's JSON file is requested, THEN THE SYSTEM SHALL resolve it only below the configured output/ directory, reject traversal or absolute paths, and validate its content as a ScrapeReport before returning it.
- **REQ-UI-4.3**: WHEN the operator filters by locale, category, or period, THEN THE SYSTEM SHALL display only matching available reports and preserve a clear no-results state.
- **REQ-UI-4.4**: IF index.json or a selected report is absent, malformed, or inconsistent with expected schema, THEN THE SYSTEM SHALL provide a safe diagnostic, leave other valid reports usable, and SHALL NOT crash.

### Requirement 5: Ranked Report Presentation

- **REQ-UI-5.1**: WHEN the operator selects a valid report, THEN THE SYSTEM SHALL show locale, category, period, scrape timestamp, item count, and engagement-score formula.
- **REQ-UI-5.2**: WHEN a report has tweets, THEN THE SYSTEM SHALL display each tweet's rank, author display name and handle, caption, likes, reposts, views, replies, total score, and posted time when present.
- **REQ-UI-5.3**: WHEN a tweet or video URL is displayed, THEN THE SYSTEM SHALL render it as a user-initiated external link with safe link attributes and SHALL NOT proxy or fetch media through the dashboard server.
- **REQ-UI-5.4**: WHEN a report contains no tweets, THEN THE SYSTEM SHALL show a clear empty-result message rather than an empty card area.
- **REQ-UI-5.5**: WHEN the dashboard is viewed on a narrow screen, THEN THE SYSTEM SHALL keep controls, filters, metrics, and links usable without horizontal page overflow.

### Requirement 6: Security, Privacy, and Data Handling

- **REQ-UI-6.1**: THE SYSTEM SHALL never include X_AUTH_TOKEN, X_CT0, CF_CLEARANCE, browser cookies, or environment-variable values in HTML, JavaScript, API responses, logs, status text, or error messages.
- **REQ-UI-6.2**: THE SYSTEM SHALL accept state-changing run requests only from the same local origin and SHALL not enable cross-origin requests by default.
- **REQ-UI-6.3**: WHEN rendering tweet-derived fields, THEN THE SYSTEM SHALL treat them as untrusted text and render them without executable HTML.
- **REQ-UI-6.4**: THE SYSTEM SHALL not persist submitted custom keywords or job error details beyond process memory, except where normal existing report JSON retains tweet content.

### Requirement 7: Observability and Documentation

- **REQ-UI-7.1**: WHEN a dashboard server starts, a job transitions state, a report fails validation, or a request is rejected, THEN THE SYSTEM SHALL emit structured, credential-safe logs at an appropriate level with the job identifier where applicable.
- **REQ-UI-7.2**: WHEN implementation is complete, THEN THE SYSTEM SHALL document installation, local start command, capabilities, limitations, and troubleshooting in README.md and docs/USAGE.md.

### Requirement 8: Quality Verification

- **REQ-UI-8.1**: WHEN the UI is implemented, THEN THE SYSTEM SHALL include automated tests for request validation, job exclusivity and failure release, report-path containment, malformed report handling, and key successful API flows.
- **REQ-UI-8.2**: WHEN implementation is complete, THEN THE SYSTEM SHALL pass `pytest tests/` and `ruff check .`.
- **REQ-UI-8.3**: WHEN the dashboard is manually verified, THEN THE SYSTEM SHALL be checked in current Chromium at desktop and narrow mobile viewport widths; this is required because browser layout is not fully covered by Python tests.
