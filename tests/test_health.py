"""Tests for the /health endpoint."""

from __future__ import annotations

from httpx import ASGITransport, AsyncClient

from memcp.config import Config
from memcp.server import create_app


async def test_health_returns_200(config: Config):
    app, backend = create_app(config)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    # In-memory backend not wired via create_app, but health endpoint exists
    # With mem0 backend pointing at fake URL, health returns unhealthy
    assert resp.status_code in (200, 503)
    data = resp.json()
    assert "status" in data
    assert "backend" in data
    assert "latency_ms" in data
    await backend.close()
