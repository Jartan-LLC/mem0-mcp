# memcp

Backend-agnostic, multi-tenant MCP memory server. AI clients connect and get persistent long-term memory over streamable HTTP.

Currently wraps [mem0](https://github.com/mem0ai/mem0) as the first backend. Designed for backend agnosticism — additional backends (Cognee, etc.) planned.

## Features

- Semantic search, list, add, update, delete memories
- Flat scope-based filtering (agent_id, run_id)
- Bearer token auth gate (ASGI middleware)
- Stateless HTTP transport — safe behind reverse proxies
- In-memory backend for dev/testing (no external deps)

## Setup

### Requirements

- Python 3.12+
- A running [mem0](https://github.com/mem0ai/mem0) self-hosted instance (not needed for `MEMCP_BACKEND=in_memory`)

### Install

```bash
pip install -e ".[dev]"
```

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `MEMCP_BACKEND` | No | Backend: `mem0` (default) or `in_memory` |
| `MEM0_API_BASE` | mem0 | Base URL of your mem0 REST API |
| `MEM0_API_KEY` | mem0 | API key for the mem0 server |
| `MEMCP_AUTH_TOKENS` | No | Token-to-user mapping: `tok1:alice,tok2:bob` (unset or empty = unauthenticated) |
| `MEMCP_HOST` | No | Bind address (default: `0.0.0.0`) |
| `MEMCP_PORT` | No | Bind port (default: `8080`) |
| `MEMCP_LOG_LEVEL` | No | Log level (default: `INFO`) |
| `MEMCP_LOG_FORMAT` | No | Log format: `json` or `plain` (default: `json`) |

### Run

```bash
python -m memcp
```

### Quick start without mem0

```bash
MEMCP_BACKEND=in_memory python -m memcp
```

No external dependencies — memories are stored in-process (lost on restart). Useful for testing and development.

### Connect from Claude Code

```json
{
  "mcpServers": {
    "memcp": {
      "type": "streamable-http",
      "url": "https://your-host:8080/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN"
      }
    }
  }
}
```

## MCP Tools

### Universal (always available)

| Tool | Description |
|---|---|
| `add_memory` | Store a fact/preference/decision. Extracts facts by default; `infer=false` for verbatim |
| `search_memory` | Semantic search, ranked by relevance |
| `delete_memory` | Delete one memory by ID (confirm first) |
| `delete_all_memories` | Bulk-delete by scope structure, not content |
| `memory_status` | Server version, backend type, capabilities, scope keys |

### Optional (backend-dependent)

| Tool | Description |
|---|---|
| `get_memory` | Fetch one memory by ID with full content/scope/metadata |
| `update_memory` | Full-replace a memory's content (scope immutable) |
| `list_memories` | Browse memories, unranked, with pagination |
| `export_memories` | Export all memories as JSON (compatible with import) |
| `import_memories` | Batch-import from JSON with dedup (skip/overwrite/duplicate) |
| `memory_history` | Change log: timestamps + previous/current content |
| `memory_entities` | Knowledge graph: entities and relationships |

## Docker

```bash
cp .env.example .env   # fill in MEM0_API_BASE + MEM0_API_KEY
docker compose up -d
```

## Development

```bash
ruff check memcp/ tests/
ruff format --check memcp/ tests/
pyright memcp/
python -c "import memcp"
pytest -x
```

## Known Limitations

**mem0 backend (upstream constraints):**
- Nested boolean filters (AND/OR/NOT) return 502 — use flat scope keys
- List endpoint does not paginate server-side — full dataset loaded per request
- List endpoint does not filter by metadata
- Entities endpoint does not filter by user — post-filtered client-side
- Single-ID endpoints are globally scoped — ownership verified via fetch-then-verify

**General:**
- No date/time-based filtering on search or list
- In-memory backend loses all data on restart
- No rate limiting (configure at reverse proxy layer)
- `delete_all_memories` deletes by scope structure, not content match

## Status

v0.1.0 — API may change before v1.0. Suitable for development and early adoption.

## License

AGPL-3.0 — see [LICENSE](LICENSE).
