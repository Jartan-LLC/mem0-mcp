"""In-memory backend adapter — for conformance tests, dev mode, and demos.

Stores memories in plain dicts. No persistence, no extraction, no vector search.
Search uses substring matching on content as a trivial approximation.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from memcp.types import (
    AddResult,
    EntitiesResult,
    HealthStatus,
    HistoryEntry,
    ListResult,
    Memory,
    MemoryAPIError,
    paginate,
)

from .base import MemoryBackend


class InMemoryBackend(MemoryBackend):
    """Trivial in-memory implementation of the MemoryBackend protocol."""

    def __init__(self) -> None:
        # {memory_id: {user_id, content, scope, metadata, created_at, updated_at}}
        self._store: dict[str, dict[str, Any]] = {}
        # {memory_id: [HistoryEntry, ...]}
        self._history: dict[str, list[dict[str, Any]]] = {}

    # --- required ---

    async def add(
        self,
        user_id: str,
        content: str,
        *,
        scope: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        infer: bool = True,
    ) -> list[AddResult]:
        memory_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()
        self._store[memory_id] = {
            "user_id": user_id,
            "content": content,
            "scope": scope or {},
            "metadata": metadata or {},
            "created_at": now,
            "updated_at": None,
        }
        self._history[memory_id] = [
            {
                "action": "created",
                "timestamp": now,
                "content_before": None,
                "content_after": content,
            }
        ]
        return [AddResult(id=memory_id, status="ready", created_at=now)]

    async def search(
        self,
        user_id: str,
        query: str,
        *,
        scope: dict[str, Any] | None = None,
        limit: int = 10,
        threshold: float = 0.0,
    ) -> list[Memory]:
        results = []
        query_lower = query.lower()
        for mid, entry in self._store.items():
            if entry["user_id"] != user_id:
                continue
            if scope:
                entry_scope = entry.get("scope", {})
                if not all(entry_scope.get(k) == v for k, v in scope.items()):
                    continue
            content_lower = entry["content"].lower()
            # Trivial relevance: count query word matches
            words = query_lower.split()
            matches = sum(1 for w in words if w in content_lower)
            if matches == 0 and query_lower not in content_lower:
                continue
            score = matches / max(len(words), 1)
            results.append((score, mid, entry))
        results.sort(key=lambda x: x[0], reverse=True)
        return [
            Memory(
                id=mid,
                content=entry["content"],
                score=score,
                scope=entry.get("scope", {}),
                metadata=entry.get("metadata", {}),
                created_at=entry["created_at"],
                updated_at=entry.get("updated_at"),
            )
            for score, mid, entry in results[:limit]
        ]

    async def delete(self, user_id: str, memory_id: str) -> bool:
        entry = self._store.get(memory_id)
        if entry is None:
            raise MemoryAPIError(404, "Not found")
        if entry["user_id"] != user_id:
            raise MemoryAPIError(404, "Not found")
        now = datetime.now(UTC).isoformat()
        if memory_id in self._history:
            self._history[memory_id].append(
                {
                    "action": "deleted",
                    "timestamp": now,
                    "content_before": entry["content"],
                    "content_after": None,
                }
            )
        del self._store[memory_id]
        return True

    async def delete_all(self, user_id: str, scope: dict[str, Any]) -> int:
        to_delete = []
        for mid, entry in self._store.items():
            if entry["user_id"] != user_id:
                continue
            entry_scope = entry.get("scope", {})
            if all(entry_scope.get(k) == v for k, v in scope.items()):
                to_delete.append(mid)
        for mid in to_delete:
            del self._store[mid]
            self._history.pop(mid, None)
        return len(to_delete)

    async def health(self) -> HealthStatus:
        return HealthStatus(status="healthy", backend="in_memory", latency_ms=0.0)

    def capabilities(self) -> set[str]:
        return {
            "get_memory",
            "update_memory",
            "list_memories",
            "memory_history",
            "memory_entities",
        }

    def scope_keys(self) -> list[str]:
        return ["agent_id", "run_id"]

    # --- optional ---

    async def get(self, user_id: str, memory_id: str) -> Memory | None:
        entry = self._store.get(memory_id)
        if entry is None or entry["user_id"] != user_id:
            return None
        return Memory(
            id=memory_id,
            content=entry["content"],
            scope=entry.get("scope", {}),
            metadata=entry.get("metadata", {}),
            created_at=entry["created_at"],
            updated_at=entry.get("updated_at"),
        )

    async def update(
        self,
        user_id: str,
        memory_id: str,
        content: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> Memory:
        entry = self._store.get(memory_id)
        if entry is None or entry["user_id"] != user_id:
            raise MemoryAPIError(404, "Not found")
        now = datetime.now(UTC).isoformat()
        old_content = entry["content"]
        entry["content"] = content
        entry["updated_at"] = now
        if metadata is not None:
            entry["metadata"] = metadata
        if memory_id in self._history:
            self._history[memory_id].append(
                {
                    "action": "updated",
                    "timestamp": now,
                    "content_before": old_content,
                    "content_after": content,
                }
            )
        return Memory(
            id=memory_id,
            content=content,
            scope=entry.get("scope", {}),
            metadata=entry.get("metadata", {}),
            created_at=entry["created_at"],
            updated_at=now,
        )

    async def list_memories(
        self,
        user_id: str,
        *,
        scope: dict[str, Any] | None = None,
        limit: int = 100,
        cursor: str | None = None,
    ) -> ListResult:
        memories = []
        for mid, entry in self._store.items():
            if entry["user_id"] != user_id:
                continue
            if scope:
                entry_scope = entry.get("scope", {})
                if not all(entry_scope.get(k) == v for k, v in scope.items()):
                    continue
            memories.append(
                Memory(
                    id=mid,
                    content=entry["content"],
                    scope=entry.get("scope", {}),
                    metadata=entry.get("metadata", {}),
                    created_at=entry["created_at"],
                    updated_at=entry.get("updated_at"),
                )
            )
        return paginate(memories, cursor, limit)

    async def history(self, user_id: str, memory_id: str) -> list[HistoryEntry]:
        entry = self._store.get(memory_id)
        if entry is None or entry["user_id"] != user_id:
            return []
        raw = self._history.get(memory_id, [])
        return [
            HistoryEntry(
                action=h["action"],
                timestamp=h["timestamp"],
                content_before=h.get("content_before"),
                content_after=h.get("content_after"),
            )
            for h in raw
        ]

    async def entities(
        self,
        user_id: str,
        *,
        scope: dict[str, Any] | None = None,
        limit: int = 100,
    ) -> EntitiesResult:
        count = sum(1 for e in self._store.values() if e["user_id"] == user_id)
        if count == 0:
            return EntitiesResult(entities=[], relationships=[])
        return EntitiesResult(
            entities=[{"id": user_id, "type": "user", "total_memories": count}],
            relationships=[],
        )

    async def close(self) -> None:
        self._store.clear()
        self._history.clear()
