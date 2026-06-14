"""Shared test fixtures."""

from __future__ import annotations

import pytest

from memcp.config import Config


@pytest.fixture
def config() -> Config:
    """Minimal config for testing — no real backend needed."""
    return Config(
        mem0_api_base="http://localhost:9999",
        mem0_api_key="test-key",
        shim_auth_token="test-token",
        mem0_user_id="test_user",
    )
