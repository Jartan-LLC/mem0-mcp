"""Tests for the /health endpoint."""

from __future__ import annotations

from httpx import ASGITransport, AsyncClient

from memcp.config import Config
from memcp.server import create_app


async def test_health_endpoint_returns_canonical_shape(config: Config):
    app, backend = create_app(config)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    # Backend points at fake URL so health returns 503/unhealthy
    assert resp.status_code == 503
    data = resp.json()
    assert data["status"] == "unhealthy"
    assert data["backend"] == "mem0"
    assert "latency_ms" in data
    await backend.close()
