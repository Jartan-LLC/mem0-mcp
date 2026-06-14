"""Tests for BearerGate ASGI middleware."""

from __future__ import annotations

import json

from memcp.auth import BearerGate


async def _make_request(app, headers: list[tuple[bytes, bytes]] | None = None):
    """Simulate a minimal ASGI HTTP request and capture the response."""
    response_started = {}
    response_body = b""

    async def receive():
        return {"type": "http.request", "body": b""}

    async def send(message):
        nonlocal response_body
        if message["type"] == "http.response.start":
            response_started.update(message)
        elif message["type"] == "http.response.body":
            response_body = message.get("body", b"")

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/mcp",
        "headers": headers or [],
    }
    await app(scope, receive, send)
    return response_started.get("status", 0), response_body


async def _dummy_app(scope, receive, send):
    """Downstream app that returns 200."""
    await send({"type": "http.response.start", "status": 200, "headers": []})
    await send({"type": "http.response.body", "body": b'{"ok": true}'})


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


async def test_valid_token_passes():
    gate = BearerGate(_dummy_app, "secret-token")
    status, _body = await _make_request(gate, [(b"authorization", b"Bearer secret-token")])
    assert status == 200


async def test_invalid_token_rejected():
    gate = BearerGate(_dummy_app, "secret-token")
    status, body = await _make_request(gate, [(b"authorization", b"Bearer wrong-token")])
    assert status == 401
    data = json.loads(body)
    assert data["error"]["code"] == "unauthorized"


async def test_missing_token_rejected():
    gate = BearerGate(_dummy_app, "secret-token")
    status, _body = await _make_request(gate, [])
    assert status == 401


async def test_no_bearer_prefix_rejected():
    gate = BearerGate(_dummy_app, "secret-token")
    status, _body = await _make_request(gate, [(b"authorization", b"secret-token")])
    assert status == 401


async def test_disabled_auth_passes():
    """When token is None, all requests pass through."""
    gate = BearerGate(_dummy_app, None)
    status, _body = await _make_request(gate, [])
    assert status == 200


async def test_lifespan_passes_through():
    """Non-HTTP scopes (lifespan) should pass through regardless."""
    gate = BearerGate(_dummy_app, "secret-token")
    called = False

    async def lifespan_app(scope, receive, send):
        nonlocal called
        called = True

    gate.app = lifespan_app
    await gate({"type": "lifespan"}, None, None)
    assert called
