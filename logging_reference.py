"""Application logging configuration — see docs/operations/LOGGING.md."""

import json
import logging
import logging.config
import time
from datetime import UTC, datetime
from typing import Any

from app.core.audit.middleware import audit_context
from app.core.config import settings


class RequestContextFilter(logging.Filter):
    """Attach request correlation fields from audit_context to every record.

    Values default to "-" when not in a request context so plain-format
    output always has a stable column count.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        ctx = audit_context.get() or {}
        record.request_id = ctx.get("request_id") or "-"
        record.ip_address = ctx.get("ip_address") or "-"
        record.user_agent = ctx.get("user_agent") or "-"
        return True


class JsonFormatter(logging.Formatter):
    """Format records as a single-line JSON object.

    Schema is intentionally fixed — any change breaks downstream aggregator
    queries. Fields: timestamp, level, logger, message, request_id,
    ip_address, user_agent, and exc (only when exc_info is set).
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
            "ip_address": getattr(record, "ip_address", "-"),
            "user_agent": getattr(record, "user_agent", "-"),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


_PLAIN_FORMAT = (
    "%(asctime)s %(levelname)s %(name)s request_id=%(request_id)s %(message)s"
)


class PlainFormatter(logging.Formatter):
    """Plain-text formatter that escapes control chars to block log injection.

    An attacker-controlled field (e.g. ``X-Request-ID: abc\\nERROR ...``)
    would otherwise produce a forged log line that parsers read as fresh.
    Covers the full C0 control range + DEL (per OWASP log-injection guidance):
    newlines close line-splitting attacks; ANSI ESC (0x1B) closes terminal
    colour/positioning injection seen in ``tail -f``; NUL (0x00) closes
    shipper-truncation attacks. TAB (0x09) is left as a legitimate format
    character. Only the main rendered line is escaped — exception tracebacks
    stay multiline because they're appended separately and aren't user-controlled.
    """

    _ESCAPES = str.maketrans(
        {
            **{c: f"\\x{c:02x}" for c in range(0x20) if c != 0x09},
            0x0A: "\\n",
            0x0D: "\\r",
            0x7F: "\\x7f",
        }
    )

    def __init__(self) -> None:
        super().__init__(fmt=_PLAIN_FORMAT)

    def formatMessage(self, record: logging.LogRecord) -> str:
        return super().formatMessage(record).translate(self._ESCAPES)


def setup_logging() -> None:
    """Configure stdlib logging from Settings.

    Call as the first executable statement of each entry point (main.py,
    manage.py, alembic/env.py) so uvicorn's own loggers and every app log
    call flow through our handlers.
    """
    # Render all timestamps in UTC so plain-format output aligns with the
    # UTC ISO-8601 timestamps in JSON output and in ActivityLog rows.
    logging.Formatter.converter = time.gmtime

    formatter_name = "json" if settings.log_format == "json" else "plain"
    uvicorn_propagate_false = {
        "level": settings.uvicorn_log_level,
        "handlers": ["stdout"],
        "propagate": False,
    }

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "request_context": {"()": RequestContextFilter},
            },
            "formatters": {
                "plain": {"()": PlainFormatter},
                "json": {"()": JsonFormatter},
            },
            "handlers": {
                "stdout": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                    "formatter": formatter_name,
                    "filters": ["request_context"],
                },
            },
            "loggers": {
                "app": {
                    "level": settings.log_level,
                    "handlers": ["stdout"],
                    "propagate": False,
                },
                "uvicorn": uvicorn_propagate_false,
                "uvicorn.error": uvicorn_propagate_false,
                "uvicorn.access": uvicorn_propagate_false,
                "sqlalchemy": {
                    "level": settings.sqlalchemy_log_level,
                    "handlers": ["stdout"],
                    "propagate": False,
                },
            },
            "root": {
                "level": settings.log_level,
                "handlers": ["stdout"],
            },
        }
    )
