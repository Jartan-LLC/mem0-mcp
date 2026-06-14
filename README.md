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
- A running [mem0](https://github.com/mem0ai/mem0) self-hosted instance

### Install

```bash
pip install -e ".[dev]"
```

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `MEM0_API_BASE` | Yes | Base URL of your mem0 REST API |
| `MEM0_API_KEY` | Yes | API key for the mem0 server |
| `SHIM_AUTH_TOKEN` | No | Bearer token clients must present (unset = open) |
| `MEM0_USER_ID` | No | Fixed user ID for all calls (default: `default_user`) |
| `MEMCP_HOST` | No | Bind address (default: `0.0.0.0`) |
| `MEMCP_PORT` | No | Bind port (default: `8080`) |
| `MEMCP_LOG_LEVEL` | No | Log level (default: `INFO`) |
| `MEMCP_LOG_FORMAT` | No | Log format: `json` or `plain` (default: `json`) |

### Run

```bash
python -m memcp
```

### Connect from Claude Code

```json
{
  "mcpServers": {
    "memcp": {
      "type": "streamable-http",
      "url": "https://your-host:8080/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_SHIM_AUTH_TOKEN"
      }
    }
  }
}
```

## MCP Tools

### Universal (always available)

| Tool | Description |
|---|---|
| `add_memory` | Store a durable fact, preference, or decision |
| `search_memory` | Semantic search across stored memories |
| `delete_memory` | Delete a single memory by ID |
| `delete_all_memories` | Delete all memories within a scope |
| `memory_status` | Server and backend information |

### Optional (backend-dependent)

| Tool | Description |
|---|---|
| `get_memory` | Fetch a single memory by ID |
| `update_memory` | Replace a memory's content |
| `list_memories` | List memories, optionally scoped |
| `memory_history` | Change history for a memory |
| `memory_entities` | Extracted entities and relationships |

## Development

```bash
ruff check memcp/ tests/
ruff format --check memcp/ tests/
pytest -x
```

## Pre-alpha

API will break. Not ready for production use.

## License

AGPL-3.0 — see [LICENSE](LICENSE).
