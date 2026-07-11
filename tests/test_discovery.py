from storygraph.discovery import discover_links, normalise_username, route_url, sanitise_html


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

