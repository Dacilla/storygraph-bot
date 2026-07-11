# StoryGraph Activity Discord Bot

A self-hosted Discord bot for sharing new, publicly visible StoryGraph reading activity with a private Discord server. This project is currently in **Phase 1: discovery**.

StoryGraph does not provide a documented public API or per-user RSS feed, so this project uses a conservative, unauthenticated HTML inspection workflow. It does not use StoryGraph passwords, cookies, browser automation, or private/community-only profiles.

## Current status

The repository currently contains:

- a standalone discovery script for testing public StoryGraph routes;
- safe HTML fixture sanitisation and response metadata capture;
- a `DISCOVERY.md` report template documenting what still needs to be verified;
- the initial test and operational scaffolding.

The Discord workflow and snapshot-difference engine intentionally wait until representative public HTML has been captured and reviewed. See [ProjectBrief.md](ProjectBrief.md) for the full phased plan.

## Discovery

Use a consenting public test username:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/discover_storygraph.py username --output-dir discovery-output
```

The script checks profile, currently-reading, books-read, and to-read routes, follows links to DNF/reviews/Up Next when present, records relevant response headers, and writes sanitised HTML fixtures. It makes no authenticated requests.

Do not commit captured fixtures containing personal information. Review and redact them before adding them to `tests/fixtures/`.

## Important limitations

This will be an unofficial integration dependent on StoryGraph's public HTML. Selectors may change without warning. Polling can miss activity that starts and finishes between scans, and backdated changes may look new. A failed or incomplete parse must never be treated as an empty reading list. Optional progress and Up Next events are not promised until discovery proves they are reliably public.

## Development

```bash
pytest
```

The eventual service will use Python 3.11+, `discord.py`, `aiohttp`, and SQLite. No StoryGraph credentials should be added to configuration.

