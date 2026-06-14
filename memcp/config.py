"""Configuration — loaded from environment variables at startup, never at import time."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Server configuration. All values come from environment variables."""

    model_config = {"env_prefix": ""}

    mem0_api_base: str
    mem0_api_key: str

    shim_auth_token: str | None = None

    mem0_user_id: str = "default_user"
    mem0_default_top_k: int = 100

    host: str = "0.0.0.0"
    port: int = 8080

    log_level: str = "INFO"
    log_format: str = "json"

    @property
    def backend_name(self) -> str:
        return "mem0"

    @property
    def version(self) -> str:
        from memcp import __version__

        return __version__
