# Project guidance

## Scope

Read `ProjectBrief.md` before making changes. Work is phased: Phase 1 must capture and review representative public StoryGraph HTML before the Discord bot or event engine is implemented.

## Safety and privacy

- Use only consenting, public StoryGraph profiles.
- Never add StoryGraph passwords, session cookies, login automation, or private journal notes.
- Keep polling low-impact: one or two concurrent requests, conservative timeouts, jitter, and bounded retries.
- Do not commit unredacted HTML, review text, usernames, or other personal information.
- Escape all user-controlled text before Discord presentation is implemented.

## Architecture

Keep StoryGraph URL handling, HTTP, and parsing isolated from Discord, persistence, and event detection. Use typed dataclasses/models and deterministic event keys. A failed parse must not replace a known-good snapshot.

## Validation

Run `pytest` before committing. Prefer fixture-based tests; normal tests must not make live StoryGraph requests. When selectors change, update `DISCOVERY.md`, redact new fixtures, and add regression tests.

