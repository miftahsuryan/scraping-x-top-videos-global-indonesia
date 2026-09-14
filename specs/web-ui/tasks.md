# Tasks: Local Scraper Dashboard

## Preconditions

- [x] The user has reviewed and approved requirements.md and design.md.
- [x] /spec-check web-ui has passed with no enterprise-standard gaps.

## Implementation Plan

- [x] 1. Add the approved web dependencies and dashboard entry point without changing CLI behavior.
  - Add FastAPI/Uvicorn to requirements.txt and create web_ui.py with explicit loopback host/port launch.
  - _Requirements: REQ-UI-1.1, REQ-UI-1.2, REQ-UI-1.3, REQ-UI-7.2_

- [x] 2. Create the typed web package foundation and application factory.
  - Add src/web package files, dependency/configuration, credential-safe structured logging, health route, static/template registration, and route error mapping.
  - _Requirements: REQ-UI-1.1, REQ-UI-1.2, REQ-UI-1.3, REQ-UI-6.1, REQ-UI-6.2, REQ-UI-7.1_

- [x] 3. Implement and unit-test run request schemas and validation.
  - Build Pydantic request/response schemas from current config values; validate selections and input bounds; preserve existing keyword parser behavior.
  - _Requirements: REQ-UI-2.1, REQ-UI-2.2, REQ-UI-2.3, REQ-UI-2.4, REQ-UI-6.1, REQ-UI-8.1_

- [x] 4. Implement and unit-test the process-local scraper job service.
  - Reuse main.run_scraper in a background task; implement lifecycle snapshots, one-run exclusivity, safe success/failure handling, and finally lock release with a mocked scraper.
  - _Requirements: REQ-UI-2.5, REQ-UI-3.1, REQ-UI-3.2, REQ-UI-3.3, REQ-UI-3.4, REQ-UI-3.5, REQ-UI-3.6, REQ-UI-6.1, REQ-UI-7.1, REQ-UI-8.1_

- [x] 5. Implement and unit-test the safe output-report repository.
  - Read/filter catalogue data, issue opaque report IDs, constrain paths under OUTPUT_DIR, validate JSON as ScrapeReport, and cover absent/malformed/traversal cases.
  - _Requirements: REQ-UI-4.1, REQ-UI-4.2, REQ-UI-4.3, REQ-UI-4.4, REQ-UI-5.1, REQ-UI-5.2, REQ-UI-5.4, REQ-UI-6.3, REQ-UI-8.1_

- [x] 6. Add and integration-test dashboard API routes.
  - Connect job/report services to endpoints and test successful, validation, conflict, missing, and corrupt-report responses without Playwright or network use.
  - _Requirements: REQ-UI-2.2, REQ-UI-2.3, REQ-UI-3.1, REQ-UI-3.3, REQ-UI-4.1, REQ-UI-4.2, REQ-UI-4.4, REQ-UI-8.1_

- [x] 7. Build the responsive dashboard shell, styling, and browser behavior.
  - Implement controls, feedback, status polling, report filters, selected-report detail, ranked cards, empty/error states, safe external links, accessible labels/focus, and narrow-screen layout with static HTML/CSS/vanilla JavaScript.
  - _Requirements: REQ-UI-1.2, REQ-UI-2.1, REQ-UI-2.2, REQ-UI-2.3, REQ-UI-3.2, REQ-UI-3.4, REQ-UI-3.5, REQ-UI-4.3, REQ-UI-5.1, REQ-UI-5.2, REQ-UI-5.3, REQ-UI-5.4, REQ-UI-5.5, REQ-UI-6.3_

- [ ] 8. Document dashboard setup, behavior, security boundaries, and troubleshooting.
  - Update README.md and docs/USAGE.md with dependencies, start command, UI/CLI relationship, local-only constraint, no-output behavior, and credential guidance.
  - _Requirements: REQ-UI-1.1, REQ-UI-6.1, REQ-UI-6.4, REQ-UI-7.2_

- [ ] 9. Verify the completed feature.
  - Run ruff check . and pytest tests/; confirm 85% coverage for new src/web modules if coverage tooling is installed; manually check desktop/narrow Chromium scenarios from design.md.
  - _Requirements: REQ-UI-8.1, REQ-UI-8.2, REQ-UI-8.3_

## Execution Rule

/spec-execute web-ui performs exactly one unchecked implementation task per invocation, marks that task only after verification, then stops for the user's direction. No implementation task may begin until both preconditions are checked.
