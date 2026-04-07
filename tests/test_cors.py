"""Tests that CORS headers are returned correctly for allowed and disallowed origins."""


ALLOWED = "http://localhost:5173"
DISALLOWED = "https://evil.example.com"


def test_cors_allowed_origin_returns_header(client):
    res = client.get("/docs", headers={"Origin": ALLOWED})
    assert res.headers.get("access-control-allow-origin") == ALLOWED


def test_cors_disallowed_origin_no_header(client):
    res = client.get("/docs", headers={"Origin": DISALLOWED})
    # FastAPI omits the header entirely for unlisted origins
    assert res.headers.get("access-control-allow-origin") != DISALLOWED


def test_cors_preflight_allowed_origin(client):
    res = client.options(
        "/owners",
        headers={
            "Origin": ALLOWED,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert res.status_code in (200, 204)
    assert res.headers.get("access-control-allow-origin") == ALLOWED
