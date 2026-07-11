# StoryGraph discovery report

Status: **blocked by upstream anti-bot challenge; public HTML not yet captured**

This report is deliberately kept separate from implementation. Run the discovery script against a consenting public test profile, redact the resulting fixtures, then record observed behaviour here before Phase 2.

## Live capture: 2026-07-11

The consenting test profile supplied for discovery returned `HTTP 403` from all four routes. Each response was a Cloudflare interstitial with a `Just a moment...` title and no StoryGraph book/profile content. The inspector now classifies this as `anti_bot_challenge`, not as evidence that the profile is private.

No public StoryGraph HTML, stable identifiers, pagination behavior, or activity links were observable in this capture. The challenge responses were written outside the repository under `/tmp/storygraph-discovery-notcelery/` and were not committed as user fixtures.

## Capture checklist

- [ ] Public profile response captured without cookies
- [ ] `/profile/{username}` checked
- [ ] `/currently-reading/{username}` checked
- [ ] `/books-read/{username}` checked
- [ ] `/to-read/{username}` checked
- [ ] DNF, reviews, and Up Next links checked
- [ ] Pagination/infinite scroll/frame/JSON behaviour recorded
- [ ] Stable book and reading-instance identifiers identified
- [ ] ETag, Last-Modified, cache, and rate-limit headers recorded
- [ ] Missing, private, community-only, and empty profiles checked
- [ ] Fixtures redacted and reviewed

## Observations

Fill this section from the captured output. Do not infer selectors from an unofficial runtime package.

| Route/page | HTTP result | Public? | Pagination | Stable fields | Notes |
| --- | --- | --- | --- | --- | --- |
| profile | pending | pending | pending | pending | |
| currently-reading | pending | pending | pending | pending | |
| books-read | pending | pending | pending | pending | |
| to-read | pending | pending | pending | pending | |

## Decision gate

Implementation may proceed to typed parsing only after the fields needed for book identity, reading status, dates, rating, and review identity are evidenced in redacted public fixtures. If a field is not exposed reliably, document the limitation and do not promise the corresponding activity type.
