# Project Agent Instructions — X/Twitter Video Engagement Scraper

This project uses a **spec-first workflow**: no code gets written until a
feature has an approved `requirements.md`, `design.md`, and `tasks.md`, and
both the spec and the implementation meet the bar in
`standards/enterprise-standards.md`. This file is loaded automatically into
every OpenCode session — treat it as ground truth, not something to
re-derive from memory.

## The workflow

Each feature lives in its own folder:

```
specs/<feature-slug>/requirements.md   # what & why (EARS acceptance criteria)
specs/<feature-slug>/design.md         # how (architecture, data, interfaces)
specs/<feature-slug>/tasks.md          # ordered, checkbox implementation plan
```

Move through it with these commands, in order:

1. `/spec-requirements <feature idea>` — drafts requirements.md
2. `/spec-design <feature-slug>` — drafts design.md from approved requirements
3. `/spec-tasks <feature-slug>` — drafts tasks.md from approved design
4. `/spec-check <feature-slug>` — audits the spec files for completeness and
   enterprise-standard coverage (read-only)
5. `/spec-execute <feature-slug> [task-number]` — implements **one** task,
   then stops
6. `/spec-status <feature-slug>` — quick read-only progress check

## Hard rules — do not skip these

1. **Never write implementation code before `tasks.md` exists, has been
   reviewed, and has passed `/spec-check`.**
2. **Never invent APIs, file paths, functions, or libraries.** If you're not
   certain something exists in this codebase, use the read/grep/glob tools to
   check first. Say "I'm not sure, let me check" instead of guessing.
3. **Work one task at a time.** After finishing a task, stop and wait for the
   user before starting the next one.
4. **Don't silently rewrite the spec files.** Stop, explain the conflict,
   propose the specific change, and wait for approval before editing any of
   requirements.md, design.md, or tasks.md.
5. **Trace everything.** Every task cites the requirement number(s) it
   satisfies; every code change maps back to a task.
6. **Meet the enterprise-grade bar.** Every category in
   `standards/enterprise-standards.md` must be marked Addressed or N/A in
   `design.md` — never silently skipped.
7. **Re-read before you act.** Read the actual current files at the start of
   `/spec-design`, `/spec-tasks`, `/spec-check`, and `/spec-execute`.

## Project context — X/Twitter Video Engagement Scraper

- **Language(s):** Python 3.10+ (PEP 8 compliance, explicit type hints across all modules)
- **Framework(s) & Tooling:** Playwright for headless browser automation & network interception, Pydantic for data validation, python-dotenv for configuration, httpx for async HTTP downloads
- **Package manager / install command:** `pip install -r requirements.txt && playwright install chromium`
- **Execution command:** `python main.py` (scrape), `python main.py --download` (download videos)
- **Test command:** `pytest tests/`
- **Lint/format command:** `ruff check .`
- **Folder structure notes:**
  - `src/` — Main application logic
    - `src/config.py` — Environment configuration and constants
    - `src/models.py` — Pydantic models for tweet data, metrics, and export schema
    - `src/browser.py` — Playwright browser lifecycle, stealth headers, cookie session management
    - `src/extractor.py` — Video URL extraction, tweet text extraction, and metric parsing (K/M to integer)
    - `src/scraper.py` — Scraper engine orchestrating Explore Indonesia and Global searches, candidate filtering, and ranking
    - `src/downloader.py` — Video download module using twittersaver.net proxy, httpx streaming, and report updates
  - `output/` — Saved JSON files in format `top15_videos_YYYY-MM.json`
  - `tests/` — Unit and integration tests
- **Data sensitivity / compliance notes:**
  - X authentication cookies (`auth_token`, `ct0`) are sensitive credentials. They must never be committed to Git or printed in logs.
  - Rate limiting and exponential backoff must be respected to avoid account restrictions or IP blocks.
- **Things to never touch / be careful with:**
  - Never hardcode user session tokens or credentials in code; use `.env` exclusively.
