"""Unauthenticated StoryGraph route inspection and fixture capture."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup

BASE_URL = "https://app.thestorygraph.com"
ROUTES = ("profile/{username}", "currently-reading/{username}", "books-read/{username}", "to-read/{username}")
LINK_HINTS = ("dnf", "did-not-finish", "review", "up-next", "up_next")


@dataclass(frozen=True)
class ResponseRecord:
    route: str
    url: str
    status: int | None
    final_url: str | None
    headers: dict[str, str]
    content_hash: str | None
    fixture: str | None
    error: str | None = None


def normalise_username(username: str) -> str:
    value = username.strip()
    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_-]{0,63}", value):
        raise ValueError("username must contain only letters, numbers, underscores, or hyphens")
    return value


def route_url(username: str, route: str) -> str:
    return f"{BASE_URL}/{route.format(username=normalise_username(username))}"


def sanitise_html(html: str) -> str:
    """Remove scripts, styles, and metadata likely to contain personal details."""
    soup = BeautifulSoup(html, "html.parser")
    for element in soup(("script", "style", "noscript", "template")):
        element.decompose()
    for element in soup.find_all(True):
        for attribute in ("id", "data-user", "data-username", "data-email"):
            element.attrs.pop(attribute, None)
    return soup.prettify()


def discover_links(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for anchor in soup.find_all("a", href=True):
        href = urljoin(base_url, anchor["href"])
        haystack = f"{anchor.get_text(' ', strip=True)} {href}".lower()
        if any(hint in haystack for hint in LINK_HINTS):
            links.add(href)
    return sorted(links)


async def inspect(username: str, output_dir: Path, user_agent: str, timeout_seconds: float = 20) -> list[ResponseRecord]:
    username = normalise_username(username)
    output_dir.mkdir(parents=True, exist_ok=True)
    timeout = aiohttp.ClientTimeout(total=timeout_seconds)
    headers = {"User-Agent": user_agent, "Accept": "text/html,application/xhtml+xml"}
    records: list[ResponseRecord] = []
    connector = aiohttp.TCPConnector(limit=2)
    async with aiohttp.ClientSession(timeout=timeout, headers=headers, connector=connector) as session:
        for route in ROUTES:
            url = route_url(username, route)
            try:
                async with session.get(url, allow_redirects=True) as response:
                    body = await response.text(errors="replace")
                    digest = hashlib.sha256(body.encode()).hexdigest()
                    safe_route = route.replace("/{username}", "").replace("/", "_")
                    fixture_name = f"{safe_route or 'profile'}.html"
                    (output_dir / fixture_name).write_text(sanitise_html(body), encoding="utf-8")
                    selected_headers = {
                        key: value
                        for key, value in response.headers.items()
                        if key.lower() in {"etag", "last-modified", "cache-control", "retry-after", "x-ratelimit-limit", "x-ratelimit-remaining"}
                    }
                    records.append(ResponseRecord(route, url, response.status, str(response.url), selected_headers, digest, fixture_name))
                    for link in discover_links(body, str(response.url)):
                        print(f"discovered link: {link}")
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                records.append(ResponseRecord(route, url, None, None, {}, None, None, type(exc).__name__))
    (output_dir / "report.json").write_text(json.dumps([asdict(record) for record in records], indent=2), encoding="utf-8")
    return records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("username")
    parser.add_argument("--output-dir", type=Path, default=Path("discovery-output"))
    parser.add_argument("--user-agent", default="PersonalStoryGraphDiscordBot/0.1 contact@example.com")
    parser.add_argument("--timeout", type=float, default=20)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = asyncio.run(inspect(args.username, args.output_dir, args.user_agent, args.timeout))
    summary = {"captured_at": datetime.now(UTC).isoformat(), "records": [asdict(record) for record in records]}
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

