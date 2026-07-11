# StoryGraph Activity Discord Bot

## 1. Project objective

Build a self-hosted Discord bot that monitors one or more consenting users’ public StoryGraph activity and posts new reading activity to configured Discord channels.

The application should be inspired by and structurally similar to the existing `Dacilla/letterboxd-bot` repository, while replacing its RSS ingestion with a resilient StoryGraph HTML-scraping and snapshot-difference system.

The bot is intended for personal, non-commercial use in a private Discord server.

## 2. Research-derived constraints

StoryGraph currently provides no documented public API or per-user RSS feed.

The integration must therefore be treated as:

* Unofficial.
* Read-only.
* Dependent on public HTML.
* Vulnerable to frontend changes.
* Subject to conservative polling and graceful failure.
* Prohibited from accessing private or community-only profiles.
* Free of StoryGraph passwords, session cookies, or login automation in the MVP.

The design must isolate StoryGraph parsing logic so selector changes can be repaired without modifying Discord, database, or event-detection code.

## 4. MVP activity types

Implement these activity types in priority order:

### Required

1. `started_reading`
2. `finished_reading`
3. `did_not_finish`
4. `reviewed`
5. `finished_and_reviewed`

### Optional after discovery

6. `progress_updated`
7. `added_to_up_next`
8. `rating_changed`
9. `review_edited`

Progress and Up Next must not be promised until the discovery spike confirms that they can be determined reliably from public per-user pages.

Do not post private reading-journal notes.

## 5. Content policy

The default MVP is metadata-only.

A Discord activity message may include:

* StoryGraph username and avatar, where permitted.
* Activity type.
* Book title.
* Author or authors.
* Public rating.
* Reading progress, if publicly available and enabled.
* Start, finish, or DNF date, when available.
* StoryGraph book link.
* StoryGraph profile or review link.
* A limited number of public genre and mood tags.
* Full review text.
* Private progress notes.
* Book descriptions.

All user-controlled text must be escaped so that StoryGraph usernames, titles, reviews, and authors cannot trigger Discord mentions or malformed Markdown.

## 6. Recommended technology

Use:

* Python 3.11 or newer.
* `discord.py`.
* `aiohttp`.
* `aiosqlite`.
* `beautifulsoup4`.
* `lxml`, if useful for faster or more tolerant parsing.
* `python-dotenv`.
* `pytest`.
* `pytest-asyncio`.
* An HTTP mocking library such as `aioresponses` or `respx`.

Do not use Selenium, Playwright, or another browser in the initial implementation unless the discovery spike proves that the relevant public data is unavailable in the server-rendered response.

Do not use unofficial StoryGraph packages as runtime dependencies. They may be consulted for selector and route research, but implement a small first-party client in this repository.

## 7. Proposed repository structure

```text
storygraph-bot/
├── bot.py
├── cogs/
│   └── storygraph.py
├── core/
│   ├── database.py
│   ├── models.py
│   ├── storygraph_client.py
│   ├── storygraph_parser.py
│   ├── activity_diff.py
│   ├── embeds.py
│   └── outbox.py
├── tests/
│   ├── fixtures/
│   │   ├── profile_public.html
│   │   ├── profile_private.html
│   │   ├── currently_reading.html
│   │   ├── books_read.html
│   │   ├── dnf.html
│   │   └── reviews.html
│   ├── test_parser.py
│   ├── test_activity_diff.py
│   ├── test_database.py
│   └── test_scanning.py
├── scripts/
│   └── capture_fixture.py
├── .env.example
├── requirements.txt
├── README.md
└── storygraph-bot.service.example
```

## 8. Discovery spike

Before building the complete Discord workflow, implement a small standalone inspection script.

The spike must:

1. Accept a StoryGraph username.
2. Request the public profile without cookies.
3. Test the following known route patterns:

   * `/profile/{username}`
   * `/currently-reading/{username}`
   * `/books-read/{username}`
   * `/to-read/{username}`
4. Discover links for:

   * DNF books.
   * Reviews.
   * Up Next.
5. Save representative HTML responses as test fixtures after removing unnecessary personal information.
6. Determine whether relevant list pages use:

   * Normal pagination.
   * Infinite scrolling.
   * Turbo or frame requests.
   * A JSON endpoint invoked by the frontend.
7. Identify stable fields for each book:

   * StoryGraph book or edition UUID.
   * Title.
   * Authors.
   * Cover URL.
   * Rating.
   * Review URL or UUID.
   * Start and finish dates.
   * Current progress.
   * Reading status.
8. Check response headers for:

   * `ETag`.
   * `Last-Modified`.
   * Cache controls.
   * Rate-limit information.
9. Confirm the behaviour of:

   * A nonexistent username.
   * A private profile.
   * A community-only profile.
   * An empty reading list.
   * Paginated reading history.

The spike should produce a short `DISCOVERY.md` report before implementation continues.

## 9. StoryGraph client

Create an asynchronous `StoryGraphClient`.

Responsibilities:

* Construct and validate StoryGraph URLs.
* Make unauthenticated GET requests.
* Send a transparent User-Agent that names the bot and contains a contact address.
* Apply request timeouts.
* Limit concurrency to one or two requests.
* Support conditional requests using `ETag` or `Last-Modified` when available.
* Detect private profiles, missing users, redirects, and login pages.
* Handle `403`, `404`, `429`, and `5xx` responses.
* Honour `Retry-After`.
* Apply exponential backoff with jitter.
* Never retry aggressively.
* Return typed results rather than raw unstructured dictionaries.

Suggested default polling interval: 20 minutes.

For a small number of users, do not request every page on every poll. Fetch only the minimal pages necessary to identify recent changes.

## 10. Domain models

Use explicit dataclasses or typed models.

```python
@dataclass(frozen=True)
class Book:
    storygraph_id: str
    title: str
    authors: tuple[str, ...]
    url: str
    cover_url: str | None
    genres: tuple[str, ...]
    moods: tuple[str, ...]

@dataclass(frozen=True)
class ReadingInstance:
    book: Book
    status: ReadingStatus
    start_date: date | None
    finish_date: date | None
    progress_value: int | None
    progress_unit: str | None
    rating: Decimal | None
    review_id: str | None
    review_url: str | None
    review_text_hash: str | None

@dataclass(frozen=True)
class ActivityEvent:
    event_key: str
    username: str
    event_type: ActivityType
    book: Book
    occurred_at: datetime | None
    payload: dict[str, Any]
```

Use `Decimal` rather than binary floating point for quarter-star ratings.

## 11. Snapshot and difference model

StoryGraph does not provide an event feed that should be treated as authoritative. Each scan must collect the current public state and compare it with the last successful state.

Examples:

* A book newly appearing in currently-reading produces `started_reading`.
* A new read instance in reading history produces `finished_reading`.
* A new DNF instance produces `did_not_finish`.
* A newly discovered review identifier produces `reviewed`.
* A new read instance and review observed in the same scan may be combined into `finished_and_reviewed`.
* A changed public progress value may produce `progress_updated`.
* A changed review hash may update an existing Discord message or produce `review_edited`, depending on configuration.

Do not use title and author as primary identity. Use StoryGraph’s book or edition identifier.

A user may read the same edition multiple times. Reading instances therefore need an identity that incorporates available reading dates or another per-reading identifier.

Suggested deterministic event keys:

```text
{username}:start:{book_id}:{start_date_or_first_seen}
{username}:finish:{book_id}:{reading_instance_id}
{username}:dnf:{book_id}:{reading_instance_id}
{username}:review:{review_id}
{username}:progress:{book_id}:{reading_instance_id}:{progress_value}:{unit}
```

Document any case where StoryGraph does not expose enough information to construct a perfect identity.

## 12. Known detection limitations

The implementation and README must clearly state that:

* HTML selectors may change without warning.
* A book started and finished entirely between polls might not generate a separate start event.
* Completion may still be detected from reading history even when the start event was missed.
* Backdated changes can appear as newly detected events.
* Changing editions can resemble a removed and newly added book.
* Review edits and deletions may be difficult to distinguish from transient parsing failures.
* Up Next and progress events may not be reliably exposed on public per-user pages.
* The global Community feed is not a reliable primary source because it is high-volume, paginated, and not scoped to one username.

The global Community feed may be evaluated as an optional secondary source, but the application must not crawl large numbers of feed pages.

## 13. Database design

Use SQLite through `aiosqlite`.

Suggested tables:

### `followed_users`

```text
id
guild_id
storygraph_username
channel_id
enabled_event_types
created_at
last_success_at
last_error_at
consecutive_failures
```

Unique constraint:

```text
UNIQUE(guild_id, storygraph_username)
```

### `reading_instances`

```text
id
storygraph_username
instance_key
book_id
status
start_date
finish_date
progress_value
progress_unit
rating
review_id
review_text_hash
first_observed_at
last_observed_at
raw_metadata_json
```

### `activity_events`

```text
event_key PRIMARY KEY
guild_id
storygraph_username
event_type
book_id
payload_json
detected_at
status
attempt_count
last_attempt_at
discord_message_id
last_error
```

Allowed event states:

```text
pending
sending
sent
failed
suppressed
```

### `http_cache`

```text
url PRIMARY KEY
etag
last_modified
content_hash
last_success_at
```

Database migrations should be explicit and testable.

## 14. Transactional outbox

Do not mark an event permanently handled before Discord confirms the message was sent.

Workflow:

1. Parse the new snapshot.
2. Calculate events.
3. Insert new events with a unique event key and `pending` status.
4. Commit the database transaction.
5. Send pending events to Discord.
6. Store the Discord message ID and mark the event `sent`.
7. Retry failed sends with bounded backoff.

The unique event key must make retries and process restarts idempotent.

If an existing review is edited and the Discord message ID is known, prefer editing the original embed instead of posting another full message.

## 15. Discord commands

Use a `/storygraph` command group.

### `/storygraph follow`

Arguments:

* `username`
* Optional destination channel
* Optional event-type selection

Behaviour:

1. Defer the interaction.
2. Validate that the profile exists and is publicly accessible.
3. Fetch an initial snapshot.
4. Store that snapshot without posting historical events.
5. Confirm the profile and number of seeded records.
6. Explain which event types are enabled.

Permission: Manage Server.

### `/storygraph unfollow`

Stop following the named account in the current guild.

Permission: Manage Server.

### `/storygraph following`

List monitored users, destination channels, enabled event types, last successful scan, and error state.

### `/storygraph scan`

Perform an immediate scan for the current guild.

Permission: Manage Server.

### `/storygraph preview`

Display sample embeds for each supported event type without contacting StoryGraph.

### `/storygraph status`

Display:

* Last scheduled scan.
* Number of followed profiles.
* Pending or failed outbox events.
* Profiles currently in backoff.
* Parser version.
* Last successful StoryGraph request.

## 16. Discord presentation

Use one consistent visual design distinct from the Letterboxd bot while retaining its overall quality.

Example headings:

```text
Alex started reading The Left Hand of Darkness
Alex finished The Left Hand of Darkness
Alex did not finish The Left Hand of Darkness
Alex reviewed The Left Hand of Darkness — 4.25 stars
```

An embed may contain:

* Author.
* Rating.
* Progress.
* Finish date.
* Genres and moods.
* Link to the StoryGraph book.
* Link to the public review.
* StoryGraph profile attribution.

Keep fields concise.

Use a neutral fallback when cover images or avatars are unavailable.

Do not expose raw scraper errors or private configuration in Discord responses.

## 17. Rate limiting and failure behaviour

The bot must be a low-impact client.

Requirements:

* Default poll interval of 20 minutes.
* Random jitter between user scans.
* Maximum two concurrent StoryGraph requests.
* No tight retries.
* Exponential backoff after failures.
* Extended backoff after `403` or `429`.
* Suspend an individual profile after repeated failures while allowing other profiles to continue.
* Never interpret a failed or incomplete parse as the user deleting all their books.
* Validate each parsed page before applying snapshot differences.

A snapshot should only replace the previous successful snapshot when minimum validation checks pass.

Example checks:

* Expected page heading exists.
* Username matches.
* No login form or access-denied marker.
* Recognised book containers are present, unless the page explicitly represents an empty list.
* Pagination completed successfully when required.

## 18. Tests

Use captured HTML fixtures rather than making live StoryGraph requests in normal tests.

Required parser fixtures:

* Public profile.
* Private profile.
* Missing profile.
* Empty currently-reading list.
* Multiple currently-reading books.
* Read history with dates.
* Reread of the same book.
* DNF entry.
* Rating without written review.
* Written review.
* Quarter-star rating.
* Multiple authors.
* Missing cover.
* Pagination.
* Minor irrelevant HTML changes.
* Login or Cloudflare response accidentally returned with HTTP 200.

Required difference-engine tests:

* Initial snapshot creates no events.
* Newly started book.
* Finished book.
* DNF transition.
* Review added after finishing.
* Finish and review in one scan.
* Rating edited.
* Review edited.
* Progress changed.
* Same snapshot processed twice.
* Process restart.
* Reread.
* Backdated read.
* Edition changed.
* Failed parse does not generate removal events.

Required outbox tests:

* Successful delivery.
* Discord timeout.
* Retry after restart.
* Unique-key collision.
* Message edit for updated review.
* Permanent channel or permission failure.

## 19. Logging and operations

Use structured logs with:

* Username.
* Guild ID.
* Page type.
* HTTP status.
* Request duration.
* Parsed record count.
* New event count.
* Backoff state.
* Error category.

Do not log:

* Discord tokens.
* StoryGraph cookies.
* Complete private page bodies.
* Full review text unless explicitly needed for debugging and redacted.

Provide:

* `.env.example`.
* A systemd unit example.
* Graceful shutdown.
* Database backup instructions.
* A parser-maintenance section in the README.
* A procedure for replacing HTML fixtures after StoryGraph changes.

## 20. Configuration

```dotenv
DISCORD_TOKEN=
DB_PATH=storygraph.db
POLL_INTERVAL_MINUTES=20
STORYGRAPH_USER_AGENT=PersonalStoryGraphDiscordBot/1.0 contact@example.com
LOG_LEVEL=INFO

ENABLE_REVIEW_TEXT=false
ENABLE_COVER_IMAGES=false
ENABLE_PROGRESS_EVENTS=false
ENABLE_UP_NEXT_EVENTS=false
```

No StoryGraph account credentials or session-cookie variables should exist in the MVP.

## 21. Development phases

### Phase 1: Permission and discovery

* Contact StoryGraph.
* Inspect a consenting public test profile.
* Capture fixtures.
* Produce `DISCOVERY.md`.
* Confirm stable identifiers and route behaviour.

### Phase 2: Parser and models

* Implement the HTTP client.
* Implement typed models.
* Parse profile, currently-reading, read history, DNF, and reviews.
* Add comprehensive fixture tests.

### Phase 3: Snapshot differences

* Implement event synthesis.
* Handle rereads and combined finish/review events.
* Add deterministic event keys.
* Add database migrations.

### Phase 4: Discord integration

* Port the useful structure from `Dacilla/letterboxd-bot`.
* Implement the command group.
* Implement seed-on-follow.
* Implement embeds.

### Phase 5: Reliability

* Add the transactional outbox.
* Add rate limiting and backoff.
* Add health/status reporting.
* Test restarts and Discord failures.

### Phase 6: Optional capabilities

Only after the MVP is stable:

* Progress updates.
* Up Next events.
* Review-message editing.
* Cover images.
* Review excerpts.
* Shared infrastructure with the Letterboxd bot.

## 22. MVP acceptance criteria

The MVP is complete when:

1. A server administrator can follow a public StoryGraph username.
2. Existing activity is seeded without flooding the channel.
3. New starts, finishes, DNFs, and reviews are detected within one polling cycle when publicly observable.
4. Activity is posted to the selected Discord channel.
5. Restarting the application produces no duplicate messages.
6. Discord delivery failures are retried without losing the event.
7. Private and missing profiles are handled clearly.
8. StoryGraph errors or changed HTML do not produce false mass activity.
9. Rereading the same book can create a separate completion event.
10. All parser and difference logic is covered by fixture-based tests.
11. The application runs under systemd.
12. No StoryGraph credentials are stored.
13. The README clearly documents that this is an unofficial integration and lists its detection limitations.

## 23. Explicit non-goals

Do not implement:

* Writing or updating data on StoryGraph.
* Monitoring private profiles.
* Capturing private notes.
* High-frequency polling.
* Bulk crawling of the global Community feed.
* A general-purpose public StoryGraph API.
* Recommendation generation.
* Book matching through an external metadata service unless later required.
* Cross-posting full historical libraries.

## 24. First Codex task

Begin with Phase 1 only.

Inspect the existing `Dacilla/letterboxd-bot` codebase for reusable structure, then create a new repository skeleton and a standalone StoryGraph discovery script.

Do not implement the complete Discord bot until:

* Representative public HTML has been captured.
* Stable identifiers have been documented.
* The snapshot strategy has been validated.
* `DISCOVERY.md` has been reviewed.
