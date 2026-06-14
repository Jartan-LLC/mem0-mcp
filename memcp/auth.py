"""Bearer token authentication — ASGI middleware.

Raw ASGI (not BaseHTTPMiddleware) to avoid buffering MCP streaming responses.
Requires Authorization: Bearer <token> on HTTP requests. Non-HTTP scopes
(lifespan) pass through so startup works.
"""

from __future__ import annotations

import hmac
import json
from typing import Any

from memcp.types import canonical_error


class BearerGate:
    """ASGI middleware that validates bearer tokens."""

    def __init__(self, app: Any, token: str | None):
        self.app = app
        self.token = token

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] != "http" or not self.token:
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        provided = headers.get(b"authorization", b"").decode()
        expected = f"Bearer {self.token}"

        if not hmac.compare_digest(provided, expected):
            err = canonical_error("unauthorized", "Invalid or missing token")
            body = json.dumps(err).encode()
            await send(
                {
                    "type": "http.response.start",
                    "status": 401,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"www-authenticate", b"Bearer"),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": body})
            return

        await self.app(scope, receive, send)
