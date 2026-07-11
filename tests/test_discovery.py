from storygraph.discovery import classify_page, discover_links, inspect_page_signals, normalise_username, route_url, sanitise_html


def test_route_url_validates_and_builds_public_route():
    assert route_url("alice_reader", "profile/{username}") == "https://app.thestorygraph.com/profile/alice_reader"


def test_invalid_username_is_rejected():
    try:
        normalise_username("alice reader")
    except ValueError:
        pass
    else:
        raise AssertionError("invalid username accepted")


def test_sanitise_html_removes_scripts_and_user_attributes():
    result = sanitise_html('<html><script>secret()</script><div id="user-1" data-email="x">Book</div></html>')
    assert "secret" not in result
    assert "data-email" not in result
    assert "Book" in result


def test_discover_links_finds_activity_links():
    html = '<a href="/reviews/123">My review</a><a href="/books/1">Book</a><a href="/up-next">Up Next</a>'
    assert discover_links(html, "https://app.thestorygraph.com/profile/a") == [
        "https://app.thestorygraph.com/reviews/123",
        "https://app.thestorygraph.com/up-next",
    ]


def test_private_and_missing_pages_are_classified_without_parsing_as_empty():
    assert classify_page(404, "https://app.thestorygraph.com/profile/missing", "") == "missing"
    assert classify_page(200, "https://app.thestorygraph.com/profile/private", "<h1>Private profile</h1>") == "private_or_denied"


def test_discovery_records_pagination_and_login_signals():
    html = '<form action="/login"><input></form><a rel="next" href="?page=2">Next</a><turbo-frame id="books"></turbo-frame>'
    assert inspect_page_signals(html) == ("login_marker", "pagination_marker", "turbo_frame")


def test_cloudflare_challenge_is_not_treated_as_a_private_profile():
    html = '<title>Just a moment...</title><script src="https://challenges.cloudflare.com/x.js"></script>'
    assert classify_page(403, "https://app.thestorygraph.com/profile/a", html) == "anti_bot_challenge"
