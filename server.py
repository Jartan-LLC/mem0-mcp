"""
mem0 MCP shim — reference implementation (single file, built to be split).

Exposes a self-hosted mem0 REST API (e.g. https://brain-api.jartan.dev) as MCP
tools over streamable-HTTP, so AI clients (Claude Code, OpenClaw, etc.) share one
long-term memory pool.

This file is deliberately a monolith for reference. Each banner-delimited section
maps to a future module:
    CONFIG        -> config.py
    API CLIENT    -> client.py
    FILTERS       -> filters.py
    ERRORS        -> errors.py
    INSTRUCTIONS  -> instructions.py
    TOOLS         -> tools/*.py
    AUTH GATE     -> auth.py (ASGI middleware)
    ENTRYPOINT    -> server.py / __main__

Design decisions are pinned to OBSERVED backend behavior (verified via probes),
not assumptions. Where a workaround exists, the comment says what it's for.

Credential model (three keys, none ever visible to the model):
  - MEM0_API_KEY    : X-API-Key the shim sends to the mem0 server (server-side only)
  - SHIM_AUTH_TOKEN : bearer token clients must present to the shim (transport header)
  - (cloud m0- key  : NOT used; this shim talks only to your self-hosted server)
"""

import hmac
import logging
import os
import re
from typing import Any, Optional

import httpx
import uvicorn
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIG  -> config.py
# =============================================================================


def _require_env(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        raise SystemExit(f"ERROR: Required environment variable {name} is not set.")
    return val


MEM0_API_BASE = _require_env("MEM0_API_BASE").rstrip("/")
MEM0_API_KEY = _require_env("MEM0_API_KEY")
SHIM_AUTH_TOKEN = os.environ.get(
    "SHIM_AUTH_TOKEN"
)  # if unset, the gate is OPEN (dev only)

# Fixed, single-pool user. Injected into every call; never a tool parameter and
# never mentioned in tool descriptions — clients have no concept of "user" here.
USER_ID = os.environ.get("MEM0_USER_ID", "default_user")

DEFAULT_TOP_K = int(os.environ.get("MEM0_DEFAULT_TOP_K", "100"))

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8080"))

# Keys that would form a nested boolean filter. The backend 502s on nested
# {"AND":[...]}/{"OR":[...]} envelopes (verified), so we forbid them structurally.
_NESTED_FILTER_KEYS = {"AND", "OR", "NOT", "and", "or", "not"}

_MEMORY_ID_RE = re.compile(r"^[a-zA-Z0-9_\-]{1,128}$")


def _validate_memory_id(memory_id: str) -> str:
    if not _MEMORY_ID_RE.match(memory_id):
        raise ValueError(
            "Invalid memory_id format. Expected alphanumeric, hyphens, or "
            "underscores (max 128 chars)."
        )
    return memory_id


# =============================================================================
# API CLIENT  -> client.py
#
# Thin wrapper over the mem0 REST API. One method per endpoint. Raises
# MemoryAPIError on any non-2xx; returns parsed JSON (which may be None for a
# 200-null body) otherwise. No business logic here — just transport + shape.
# =============================================================================


class MemoryAPIError(RuntimeError):
    """Non-2xx from the mem0 server. Carries status + raw body for the caller."""

    def __init__(self, status: int, body: str):
        self.status = status
        self.body = body
        super().__init__(f"mem0 API {status}: {body[:500]}")


class MemoryClient:
    def __init__(self, base_url: str, api_key: str):
        # X-API-Key is the verified auth header for this server (Bearer is for JWTs).
        self._http = httpx.Client(
            base_url=base_url,
            headers={"X-API-Key": api_key},
            timeout=httpx.Timeout(30.0),
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict] = None,
        json: Optional[dict] = None,
    ) -> Any:
        resp = self._http.request(method, path, params=params, json=json)
        if resp.status_code >= 400:
            raise MemoryAPIError(resp.status_code, resp.text)
        # 200 with empty body -> None; 200 with JSON null -> None (both meaningful).
        return resp.json() if resp.content else None

    # --- writes ---
    def add(self, payload: dict) -> Any:
        return self._request("POST", "/memories", json=payload)

    def update(self, memory_id: str, text: str, metadata: Optional[dict]) -> Any:
        body: dict[str, Any] = {"text": text}
        if metadata is not None:
            body["metadata"] = metadata
        return self._request("PUT", f"/memories/{memory_id}", json=body)

    def delete(self, memory_id: str) -> Any:
        return self._request("DELETE", f"/memories/{memory_id}")

    def delete_all(self, params: dict) -> Any:
        return self._request("DELETE", "/memories", params=params)

    # --- reads ---
    def search(self, payload: dict) -> Any:
        return self._request("POST", "/search", json=payload)

    def list(self, params: dict) -> Any:
        return self._request("GET", "/memories", params=params)

    def get(self, memory_id: str) -> Any:
        return self._request("GET", f"/memories/{memory_id}")

    def history(self, memory_id: str) -> Any:
        return self._request("GET", f"/memories/{memory_id}/history")

    def entities(self) -> Any:
        return self._request("GET", "/entities")

    def close(self) -> None:
        self._http.close()


client = MemoryClient(MEM0_API_BASE, MEM0_API_KEY)
# REFACTOR: this (and the `mcp` instance below) is constructed at import time.
# Fine for a single-file reference, but it couples client.py to env at import and
# hurts testability. In production, build via a factory / app-context and inject
# into the tools rather than referencing module-level globals.


# =============================================================================
# FILTERS  -> filters.py
#
# Builds FLAT filter dicts only. Two invariants enforced here:
#   1. "*" and "" normalize to "omit this key" (backend ignores "*"; we make that
#      intentional so an agent that fat-fingers a wildcard gets broad results).
#   2. Nested AND/OR/NOT keys are rejected (they 502 the backend).
# Reads default broad: identifiers only narrow when explicitly provided.
# =============================================================================


def _norm(value: Any) -> Any:
    """Return None ('omit') for wildcard/empty string sentinels; pass through else."""
    if isinstance(value, str) and value.strip() in ("", "*"):
        return None
    return value


def _reject_nested(d: dict) -> None:
    bad = _NESTED_FILTER_KEYS & set(d)
    if bad:
        raise ValueError(
            f"Nested boolean filters are not supported ({sorted(bad)}). "
            "Use discrete agent_id / run_id / metadata fields instead."
        )


def build_search_filters(
    agent_id: Optional[str],
    run_id: Optional[str],
    metadata_filter: Optional[dict],
) -> dict:
    """Flat filter dict for POST /search. user_id always injected."""
    filters: dict[str, Any] = {"user_id": USER_ID}
    for key, val in (("agent_id", agent_id), ("run_id", run_id)):
        val = _norm(val)
        if val is not None:
            filters[key] = val
    if metadata_filter:
        _reject_nested(metadata_filter)
        for key, val in metadata_filter.items():
            # Don't normalize non-string metadata values (e.g. {"gte": 2}).
            val = _norm(val) if isinstance(val, str) else val
            if val is not None:
                filters[key] = val
    return filters


def build_identifier_params(agent_id: Optional[str], run_id: Optional[str]) -> dict:
    """Flat query params for GET /memories and DELETE /memories. user_id injected.
    NOTE: this backend's list endpoint does NOT filter by metadata (verified).
    REFACTOR: it also does NOT paginate today — it returns the full filtered set,
    which can be a large payload as the pool grows. We DO want pagination: add
    page/page_size to list_memories and have the backend honor them (the list
    endpoint currently ignores those params), or page client-side as a stopgap."""
    params: dict[str, Any] = {"user_id": USER_ID}
    for key, val in (("agent_id", agent_id), ("run_id", run_id)):
        val = _norm(val)
        if val is not None:
            params[key] = val
    return params


# =============================================================================
# ERRORS  -> errors.py
#
# The backend reports "memory not found" two non-obvious ways (verified):
#   - missing/deleted id  -> HTTP 200 with body `null`
#   - malformed id        -> HTTP 5xx (vector store throws on a non-UUID)
# Both mean "not found" to a caller, so single-id tools translate them uniformly
# instead of returning a silent null or surfacing a scary gateway error.
# =============================================================================

NOT_FOUND_MSG = (
    "No memory found for that memory_id. It may have been deleted, or the id "
    "may be malformed."
)


def lookup_by_id(call) -> Any:
    """Run a single-id API call; map both 'not found' signals to None.

    Returns the result on success, or None if the id is missing (200 null) or
    malformed (5xx). Re-raises genuine 4xx (auth, bad request) so they surface.
    """
    try:
        result = call()
    except MemoryAPIError as e:
        if e.status >= 500:
            return None  # malformed id -> treat as not found
        raise
    return result  # may legitimately be None (missing id -> 200 null)


# =============================================================================
# INSTRUCTIONS  -> instructions.py
#
# Server-level guidance, written fresh from verified behavior. NOT lifted from
# mem0's cloud `memory_assistant` prompt, which teaches the 502-causing nested
# AND/OR syntax, async event polling, rerank, and wildcards — none of which apply
# to this self-hosted backend.
# =============================================================================

INSTRUCTIONS = """\
Long-term memory shared across your tools and sessions, backed by a self-hosted \
mem0 instance.

When to WRITE (add_memory): whenever a durable fact, preference, decision, or \
piece of context worth recalling later comes up — or when asked to remember \
something. Don't store transient one-off questions or throwaway debugging context.

When to SEARCH (search_memory): before answering anything that depends on what's \
already known about the user, their projects, preferences, or prior decisions. \
Search first; don't assume the pool is empty.

Scoping with tags (agent_id, run_id):
  - On WRITES, tagging is safe and encouraged — it never hides a memory from \
broad recall, but lets you slice or clean up later by tool or session.
  - On READS, omit tags to recall broadly (the default). Add a tag ONLY to \
deliberately narrow to that tool/session. Reading with a run_id you didn't write \
under will return nothing — so for cross-session recall, leave run_id off.

Extraction (infer): by default the server extracts salient facts and may store \
NOTHING if it finds no durable fact — add_memory will tell you when that happens. \
To store text exactly as given, pass infer=false.

Filters are flat only: narrow with discrete agent_id / run_id / metadata fields. \
Do not attempt nested boolean (AND/OR/NOT) filter expressions.

Destructive operations (delete_memory, delete_all_memories) should be confirmed \
with the user first; delete_all_memories additionally requires a scope.
"""


# =============================================================================
# MCP SERVER  -> server.py (assembly)
# =============================================================================

mcp = FastMCP(
    "mem0",
    instructions=INSTRUCTIONS,
    host=HOST,
    port=PORT,
    stateless_http=True,  # no session affinity; safe behind Traefik with many clients
)

READ_ONLY = {"readOnlyHint": True, "idempotentHint": True}
DESTRUCTIVE = {"destructiveHint": True}


# =============================================================================
# TOOLS  -> tools/*.py
#
# Each tool is thin: normalize inputs -> call client -> interpret result. All
# user_id injection and flat-filter discipline lives in the helpers above, so the
# tools never see plumbing and can't emit a filter shape the backend rejects.
#
# REFACTOR: only single-id tools interpret errors (via lookup_by_id). For
# add/search/list a MemoryAPIError propagates raw and MCP renders the exception
# string. Consider a uniform decorator over all tools that turns any
# MemoryAPIError into a structured, model-friendly message (status + hint).
# =============================================================================


@mcp.tool(
    description=(
        "Store a memory: a durable fact, preference, decision, or anything worth "
        "recalling later. Use whenever the user states something lasting about "
        "themselves, their work, or their preferences, or asks you to remember "
        "something. Provide `text` (a concise statement of what to remember), or "
        "`messages` for multi-turn conversation context. By default the server "
        "extracts salient facts and may store nothing if it finds none — set "
        "`infer` to false to store the text verbatim. Optionally tag with "
        "`agent_id`/`run_id`; tagging never hides the memory from broad recall."
    )
)
def add_memory(
    text: str,
    messages: Optional[list[dict]] = None,
    agent_id: Optional[str] = None,
    run_id: Optional[str] = None,
    metadata: Optional[dict] = None,
    infer: bool = True,
) -> Any:
    payload: dict[str, Any] = {
        "messages": messages or [{"role": "user", "content": text}],
        "user_id": USER_ID,
        "infer": infer,
    }
    if _norm(agent_id) is not None:
        payload["agent_id"] = agent_id
    if _norm(run_id) is not None:
        payload["run_id"] = run_id
    if metadata:
        payload["metadata"] = metadata

    result = client.add(payload)
    # infer=true can extract nothing -> {"results": []}. Surface that explicitly
    # rather than returning a success-looking empty result.
    results = (result or {}).get("results") if isinstance(result, dict) else result
    if not results:
        # REFACTOR: this string is model-facing guidance, not an API contract.
        # Tune the wording once you see how your agents react to it (e.g. whether
        # they reflexively retry with infer=false when you don't want them to).
        return (
            "No durable fact was extracted, so nothing was stored. If you intended "
            "to store this exactly as written, call add_memory again with infer=false."
        )
    return result


@mcp.tool(
    annotations=READ_ONLY,
    description=(
        "Semantically search stored memories by meaning. Use before answering "
        "anything that depends on what's already known about the user, their "
        "projects, preferences, or past decisions. Searches broadly by default; "
        "pass `agent_id`/`run_id` to narrow to a specific tool or session, or "
        "`metadata_filter` for flat tag-based narrowing. Returns memories ranked "
        "by relevance."
    ),
)
def search_memory(
    query: str,
    agent_id: Optional[str] = None,
    run_id: Optional[str] = None,
    metadata_filter: Optional[dict] = None,
    top_k: int = DEFAULT_TOP_K,
    threshold: float = 0.0,  # 0.0 = no similarity cutoff (recall over precision)
) -> Any:
    payload = {
        "query": query,
        "filters": build_search_filters(agent_id, run_id, metadata_filter),
        "top_k": top_k,
        "threshold": threshold,
    }
    return client.search(payload)


@mcp.tool(
    annotations=READ_ONLY,
    description=(
        "List stored memories without a search query — useful for an overview or "
        "audit. Optionally narrow by `agent_id`/`run_id`. To find something "
        "specific, prefer search_memory. (Metadata does not filter this listing.)"
    ),
)
def list_memories(agent_id: Optional[str] = None, run_id: Optional[str] = None) -> Any:
    return client.list(build_identifier_params(agent_id, run_id))


@mcp.tool(
    annotations=READ_ONLY,
    description="Fetch a single memory by its memory_id.",
)
def get_memory(memory_id: str) -> Any:
    _validate_memory_id(memory_id)
    result = lookup_by_id(lambda: client.get(memory_id))
    return result if result is not None else NOT_FOUND_MSG


@mcp.tool(
    annotations={"idempotentHint": True},
    description=(
        "Replace a memory's text (required) and optionally its metadata, by "
        "memory_id. Note: text cannot be omitted — this is a replace, not a "
        "metadata-only patch."
    ),
)
def update_memory(
    memory_id: str,
    text: str,
    metadata: Optional[dict] = None,
) -> Any:
    _validate_memory_id(memory_id)
    result = lookup_by_id(lambda: client.update(memory_id, text, metadata))
    return result if result is not None else NOT_FOUND_MSG


@mcp.tool(
    annotations=DESTRUCTIVE,
    description=(
        "Delete a single memory by memory_id. Confirm the id with the user before "
        "deleting."
    ),
)
def delete_memory(memory_id: str) -> Any:
    _validate_memory_id(memory_id)
    result = lookup_by_id(lambda: client.delete(memory_id))
    return result if result is not None else NOT_FOUND_MSG


@mcp.tool(
    annotations=DESTRUCTIVE,
    description=(
        "Delete every memory within a given scope. Requires at least one of "
        "`agent_id` or `run_id` — a scope is mandatory so the whole pool can't be "
        "wiped at once. Destructive; confirm with the user first."
    ),
)
def delete_all_memories(
    agent_id: Optional[str] = None,
    run_id: Optional[str] = None,
) -> Any:
    # Shim-level guard (the backend also 400s on this, but we fail fast and clear).
    if _norm(agent_id) is None and _norm(run_id) is None:
        return (
            "Refused: delete_all_memories requires at least one scope (agent_id or "
            "run_id). Deleting the entire pool at once is not allowed."
        )
    return client.delete_all(build_identifier_params(agent_id, run_id))


@mcp.tool(
    annotations=READ_ONLY,
    description=(
        "List the agent and run scopes that currently hold memories, with a count "
        "per scope. Use it to discover which scopes exist before narrowing a "
        "search or list."
    ),
)
def list_entities() -> Any:
    return client.entities()


@mcp.tool(
    annotations=READ_ONLY,
    description=(
        "Return the change history (additions, updates, deletions) for a single "
        "memory by memory_id."
    ),
)
def get_memory_history(memory_id: str) -> Any:
    _validate_memory_id(memory_id)
    result = lookup_by_id(lambda: client.history(memory_id))
    return result if result is not None else NOT_FOUND_MSG


# =============================================================================
# AUTH GATE  -> auth.py
#
# Raw ASGI middleware (NOT BaseHTTPMiddleware, which buffers and would break MCP's
# streaming responses). Requires `Authorization: Bearer <SHIM_AUTH_TOKEN>` on HTTP
# requests. Non-HTTP scopes (lifespan) pass straight through so startup works.
# =============================================================================


class BearerGate:
    def __init__(self, app, token: Optional[str]):
        self.app = app
        self.token = token

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not self.token:
            await self.app(scope, receive, send)
            return
        headers = dict(scope.get("headers") or [])
        provided = headers.get(b"authorization", b"").decode()
        expected = f"Bearer {self.token}"
        if not hmac.compare_digest(provided, expected):
            await send(
                {
                    "type": "http.response.start",
                    "status": 401,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"www-authenticate", b"Bearer"),
                    ],
                }
            )
            await send(
                {"type": "http.response.body", "body": b'{"error":"unauthorized"}'}
            )
            return
        await self.app(scope, receive, send)


# =============================================================================
# ENTRYPOINT  -> __main__
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    if not SHIM_AUTH_TOKEN:
        logger.warning(
            "SHIM_AUTH_TOKEN is unset — the MCP endpoint is UNAUTHENTICATED."
        )
    app = BearerGate(mcp.streamable_http_app(), SHIM_AUTH_TOKEN)
    try:
        uvicorn.run(app, host=HOST, port=PORT)
    finally:
        client.close()
