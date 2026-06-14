"""Tests for the /health endpoint."""

from __future__ import annotations

from httpx import ASGITransport, AsyncClient
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from memcp.backend.in_memory import InMemoryBackend
from memcp.config import Config
from memcp.server import create_app


async def test_health_endpoint_unhealthy(config: Config):
    app, backend = create_app(config)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 503
    data = resp.json()
    assert data["status"] == "unhealthy"
    assert data["backend"] == "mem0"
    assert "latency_ms" in data
    await backend.close()


async def test_health_endpoint_healthy(config: Config):
    """Test 200/healthy path with InMemoryBackend."""
    backend = InMemoryBackend()

    async def health(request: Request) -> JSONResponse:
        status = await backend.health()
        code = 200 if status.status == "healthy" else 503
        return JSONResponse(
            {"status": status.status, "backend": status.backend, "latency_ms": status.latency_ms},
            status_code=code,
        )

    app = Starlette(routes=[Route("/health", health)])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["backend"] == "in_memory"
    assert data["latency_ms"] == 0.0
