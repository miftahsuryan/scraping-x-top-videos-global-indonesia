# Enterprise-Grade Technical Standards

This is the quality bar every feature's `design.md`, `tasks.md`, and
implementation must meet. It is not optional decoration — `/spec-design`,
`/spec-tasks`, and `/spec-check` all check against it explicitly.

**Rule:** every category below must end up marked one of:
- **Addressed** — state where (which requirement / design section / task)
- **Explicitly N/A** — state why it doesn't apply to this feature
- **Not addressed** — this is a gap, it must be fixed before moving on

Silently skipping a category is not allowed — only "Addressed" or
"Explicitly N/A" with a reason are acceptable outcomes.

## 1. Security
- Every input (API param, form field, file, message) is validated and
  sanitized before use.
- Every endpoint/action has an explicit authentication and authorization
  check — never "assumed handled elsewhere."
- No secrets, keys, or credentials hardcoded — env vars or a secrets
  manager only.
- Sensitive data is encrypted in transit and at rest.
- Actions that matter (auth failures, permission changes, deletions) are
  audit-logged.

## 2. Reliability & Error Handling
- Every call to an external system (DB, network, file, queue) has explicit
  error handling — no bare/silent `except`, no ignored rejected promises.
- Transient failures (timeouts, 5xx, connection drops) retry with backoff
  where it makes sense; permanent failures fail fast with a clear error.
- Failure of one component degrades gracefully rather than cascading.
- Error messages are useful for debugging but never leak internals
  (stack traces, secrets, raw queries) to end users.

## 3. Observability
- Structured logs, not raw print statements — with correlation/request IDs
  where the system spans multiple calls.
- Log levels used correctly (debug/info/warn/error), no error-level noise
  for expected conditions.
- Key operations emit metrics (latency, success/failure counts) where the
  project already has metrics infrastructure.
- Services expose a health/readiness check.

## 4. Testing
- Business logic has unit tests, not just the happy path — edge cases and
  failure paths are covered too.
- External dependencies are covered by integration tests or clearly
  documented as manually verified.
- A minimum coverage expectation is stated (or explicitly deferred) rather
  than left unstated.

## 5. Performance & Scalability
- No unbounded loops or N+1 query patterns over data that can grow.
- List/collection endpoints are paginated.
- Resources (connections, file handles, locks) are always released, even
  on the error path.
- Any known scaling limit or assumption is written down, not implied.

## 6. Documentation
- Public functions, classes, and API endpoints have docstrings/comments
  explaining intent, not just restating the code.
- README / setup instructions are updated when setup steps change.
- Non-obvious design decisions get a short rationale in `design.md`.

## 7. Code Quality & Maintainability
- Follows the lint/format/style rules in `AGENTS.md` — no exceptions
  without a stated reason.
- No dead code or commented-out blocks left behind.
- Functions/modules have a single, clear responsibility.

## 8. Compliance & Data Handling
- Personal or sensitive data is identified explicitly; handling follows
  the project's stated policy (see `AGENTS.md`).
- No sensitive data ends up in logs, error messages, or URLs.
- Data retention/deletion behavior is defined for anything persisted.

## 9. CI/CD & Versioning
- The change is covered by the project's existing test/lint pipeline.
- Breaking changes include a migration note or backward-compatibility plan.
- User-facing changes are reflected in a changelog where the project keeps
  one.
