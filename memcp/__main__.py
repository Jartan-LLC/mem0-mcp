"""python -m memcp entrypoint."""

from __future__ import annotations

import asyncio
import logging

import uvicorn

from memcp.config import Config
from memcp.logging import setup_logging
from memcp.server import create_app

logger = logging.getLogger(__name__)


def main() -> None:
    config = Config()  # type: ignore[call-arg]
    setup_logging(level=config.log_level, fmt=config.log_format)

    if not config.shim_auth_token:
        logger.warning("SHIM_AUTH_TOKEN is unset — the MCP endpoint is UNAUTHENTICATED.")

    app, backend = create_app(config)

    try:
        uvicorn.run(app, host=config.host, port=config.port)
    finally:
        asyncio.run(backend.close())


if __name__ == "__main__":
    main()
