"""Shared data types and error helpers used by tools and backends."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

_MEMORY_ID_RE = re.compile(r"^[a-zA-Z0-9_\-]{1,128}$")
_NESTED_FILTER_KEYS = frozenset({"AND", "OR", "NOT", "and", "or", "not"})


def validate_memory_id(memory_id: str) -> str:
    if not _MEMORY_ID_RE.match(memory_id):
        raise ValueError(
            "Invalid memory_id format. Expected alphanumeric, hyphens, or "
            "underscores (max 128 chars)."
        )
    return memory_id


def reject_nested_filters(d: dict[str, Any]) -> None:
    bad = _NESTED_FILTER_KEYS & set(d)
    if bad:
        raise ValueError(
            f"Nested boolean filters are not supported ({sorted(bad)}). "
            "Use discrete scope keys or metadata fields instead."
        )


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class MemoryAPIError(RuntimeError):
    """Non-2xx from a memory backend. Carries status + raw body."""

    def __init__(self, status: int, body: str):
        self.status = status
        self.body = body
        super().__init__(f"Backend API {status}: {body[:500]}")


NOT_FOUND_MSG = (
    "No memory found for that memory_id. It may have been deleted, or the id may be malformed."
)


def canonical_error(code: str, message: str, *, retry: bool = False) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "retry": retry}}


# ---------------------------------------------------------------------------
# Canonical data shapes
# ---------------------------------------------------------------------------


@dataclass
class Memory:
    id: str
    content: str
    score: float | None = None
    scope: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str | None = None


@dataclass
class AddResult:
    id: str
    status: str = "ready"
    created_at: str = ""


@dataclass
class ListResult:
    memories: list[Memory] = field(default_factory=list)
    next_cursor: str | None = None


def paginate(memories: list[Memory], cursor: str | None, limit: int) -> ListResult:
    """Cursor-based pagination over a full list of memories."""
    if cursor:
        try:
            start = int(cursor)
        except ValueError:
            raise ValueError(f"Invalid cursor: {cursor}") from None
    else:
        start = 0
    page = memories[start : start + limit]
    next_cursor = str(start + limit) if start + limit < len(memories) else None
    return ListResult(memories=page, next_cursor=next_cursor)


@dataclass
class HistoryEntry:
    action: str
    timestamp: str
    content_before: str | None = None
    content_after: str | None = None


@dataclass
class EntitiesResult:
    entities: list[dict[str, Any]] = field(default_factory=list)
    relationships: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class HealthStatus:
    status: str
    backend: str
    latency_ms: float | None = None
