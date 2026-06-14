"""MCP tool registration — closure-based dependency injection.

All tool handlers are defined inside register_tools() as inner functions.
The closure captures backend and config, eliminating module-level globals.
"""

from __future__ import annotations

import logging
from typing import Any

from memcp.backend.base import MemoryBackend
from memcp.config import Config
from memcp.types import (
    NOT_FOUND_MSG,
    MemoryAPIError,
    canonical_error,
    validate_memory_id,
)

logger = logging.getLogger(__name__)

READ_ONLY = {"readOnlyHint": True, "idempotentHint": True}
DESTRUCTIVE = {"destructiveHint": True}


def register_tools(mcp: Any, backend: MemoryBackend, config: Config) -> None:
    """Register all MCP tools on the given server instance."""

    user_id = config.mem0_user_id

    # --- universal tools ---

    @mcp.tool(
        description=(
            "Store content in long-term memory. Use whenever a durable fact, "
            "preference, decision, or anything worth recalling later comes up. "
            "By default the server extracts salient facts and may store nothing "
            "if it finds none — set infer to false to store verbatim."
        )
    )
    async def add_memory(
        content: str,
        scope: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        infer: bool = True,
    ) -> Any:
        scope = _strip_user_id(scope)
        try:
            result = await backend.add(
                user_id, content, scope=scope, metadata=metadata, infer=infer
            )
        except MemoryAPIError as e:
            return canonical_error("backend_error", str(e), retry=e.status >= 500)

        if not result:
            return (
                "No durable fact was extracted, so nothing was stored. If you intended "
                "to store this exactly as written, call add_memory again with infer=false."
            )
        return _serialize_add_result(result)

    @mcp.tool(
        annotations=READ_ONLY,
        description=(
            "Semantically search stored memories by meaning. Use before answering "
            "anything that depends on what's already known about the user. "
            "Returns memories ranked by relevance."
        ),
    )
    async def search_memory(
        query: str,
        scope: dict[str, Any] | None = None,
        limit: int = 10,
        threshold: float = 0.0,
    ) -> Any:
        scope = _strip_user_id(scope)
        try:
            results = await backend.search(
                user_id, query, scope=scope, limit=limit, threshold=threshold
            )
        except MemoryAPIError as e:
            return canonical_error("backend_error", str(e), retry=e.status >= 500)

        return {"results": [_serialize_memory(m) for m in results]}

    @mcp.tool(
        annotations=DESTRUCTIVE,
        description=(
            "Delete a single memory by memory_id. Confirm with the user before deleting."
        ),
    )
    async def delete_memory(memory_id: str) -> Any:
        try:
            validate_memory_id(memory_id)
        except ValueError as e:
            return canonical_error("validation_error", str(e))
        try:
            result = await backend.delete(user_id, memory_id)
        except MemoryAPIError as e:
            if e.status in (404, 410):
                return canonical_error("not_found", NOT_FOUND_MSG)
            return canonical_error("backend_error", str(e), retry=e.status >= 500)
        return {"deleted": result}

    @mcp.tool(
        annotations=DESTRUCTIVE,
        description=(
            "Delete every memory within a given scope. Requires at least one scope "
            "key — unscoped deletion is not allowed. Confirm with the user first."
        ),
    )
    async def delete_all_memories(scope: dict[str, Any]) -> Any:
        scope = _strip_user_id(scope)
        if not scope:
            return canonical_error(
                "scope_required",
                "delete_all_memories requires at least one scope key.",
            )
        try:
            count = await backend.delete_all(user_id, scope)
        except MemoryAPIError as e:
            return canonical_error("backend_error", str(e), retry=e.status >= 500)
        return {"deleted_count": count}

    @mcp.tool(
        annotations=READ_ONLY,
        description="Server and backend information.",
    )
    async def memory_status() -> dict[str, Any]:
        return {
            "backend": config.backend_name,
            "version": config.version,
            "capabilities": sorted(backend.capabilities()),
            "scope_keys": backend.scope_keys(),
        }

    # --- optional tools (registered if backend declares capability) ---

    caps = backend.capabilities()

    if "get_memory" in caps:

        @mcp.tool(
            annotations=READ_ONLY,
            description="Fetch a single memory by its memory_id.",
        )
        async def get_memory(memory_id: str) -> Any:
            try:
                validate_memory_id(memory_id)
            except ValueError as e:
                return canonical_error("validation_error", str(e))
            try:
                result = await backend.get(user_id, memory_id)
            except MemoryAPIError as e:
                if e.status in (404, 410):
                    return canonical_error("not_found", NOT_FOUND_MSG)
                return canonical_error("backend_error", str(e), retry=e.status >= 500)
            if result is None:
                return canonical_error("not_found", NOT_FOUND_MSG)
            return _serialize_memory(result)

    if "update_memory" in caps:

        @mcp.tool(
            annotations={"idempotentHint": True, "destructiveHint": True},
            description=(
                "Replace a memory's content by memory_id. This is a full replace, not a patch."
            ),
        )
        async def update_memory(
            memory_id: str,
            content: str,
            metadata: dict[str, Any] | None = None,
        ) -> Any:
            try:
                validate_memory_id(memory_id)
            except ValueError as e:
                return canonical_error("validation_error", str(e))
            try:
                result = await backend.update(user_id, memory_id, content, metadata=metadata)
            except MemoryAPIError as e:
                if e.status in (404, 410):
                    return canonical_error("not_found", NOT_FOUND_MSG)
                return canonical_error("backend_error", str(e), retry=e.status >= 500)
            return _serialize_memory(result)

    if "list_memories" in caps:

        @mcp.tool(
            annotations=READ_ONLY,
            description=(
                "List stored memories, optionally scoped. For finding something "
                "specific, prefer search_memory."
            ),
        )
        async def list_memories(
            scope: dict[str, Any] | None = None,
            limit: int = 100,
            cursor: str | None = None,
        ) -> Any:
            scope = _strip_user_id(scope)
            try:
                result = await backend.list_memories(
                    user_id, scope=scope, limit=limit, cursor=cursor
                )
            except ValueError as e:
                return canonical_error("validation_error", str(e))
            except MemoryAPIError as e:
                return canonical_error("backend_error", str(e), retry=e.status >= 500)
            return {
                "memories": [_serialize_memory(m) for m in result.memories],
                "next_cursor": result.next_cursor,
            }

    if "memory_history" in caps:

        @mcp.tool(
            annotations=READ_ONLY,
            description="Change history for a single memory by memory_id.",
        )
        async def memory_history(memory_id: str) -> Any:
            try:
                validate_memory_id(memory_id)
            except ValueError as e:
                return canonical_error("validation_error", str(e))
            try:
                entries = await backend.history(user_id, memory_id)
            except MemoryAPIError as e:
                if e.status in (404, 410):
                    return canonical_error("not_found", NOT_FOUND_MSG)
                return canonical_error("backend_error", str(e), retry=e.status >= 500)
            return {
                "history": [
                    {
                        "action": e.action,
                        "timestamp": e.timestamp,
                        "content_before": e.content_before,
                        "content_after": e.content_after,
                    }
                    for e in entries
                ]
            }

    if "memory_entities" in caps:

        @mcp.tool(
            annotations=READ_ONLY,
            description="Extracted entities and relationships from stored memories.",
        )
        async def memory_entities(
            scope: dict[str, Any] | None = None,
            limit: int = 100,
        ) -> Any:
            scope = _strip_user_id(scope)
            try:
                result = await backend.entities(user_id, scope=scope, limit=limit)
            except MemoryAPIError as e:
                return canonical_error("backend_error", str(e), retry=e.status >= 500)
            return {
                "entities": result.entities,
                "relationships": result.relationships,
            }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _strip_user_id(scope: dict[str, Any] | None) -> dict[str, Any] | None:
    """Security invariant: remove user_id from scope dicts."""
    if scope and "user_id" in scope:
        logger.warning("Stripped user_id from scope dict (security invariant)")
        scope = {k: v for k, v in scope.items() if k != "user_id"}
    return scope


def _serialize_memory(m: Any) -> dict[str, Any]:
    return {
        "id": m.id,
        "content": m.content,
        "score": m.score,
        "scope": m.scope,
        "metadata": m.metadata,
        "created_at": m.created_at,
        "updated_at": m.updated_at,
    }


def _serialize_add_result(result: Any) -> Any:
    if isinstance(result, list):
        return {
            "results": [
                {"id": r.id, "status": r.status, "created_at": r.created_at} for r in result
            ]
        }
    return {"id": result.id, "status": result.status, "created_at": result.created_at}
