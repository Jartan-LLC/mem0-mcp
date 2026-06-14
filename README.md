# mem0-mcp

MCP server exposing self-hosted mem0 long-term memory as tools over streamable HTTP.

AI clients (Claude Code, OpenClaw, etc.) connect to this server and share one long-term memory pool backed by your own mem0 instance.

## Features

- Semantic search, list, add, update, delete memories
- Flat filter support (agent_id, run_id, metadata)
- Bearer token auth gate (ASGI middleware)
- Stateless HTTP transport — safe behind reverse proxies

## Setup

### Requirements

- Python 3.13+
- A running [mem0](https://github.com/mem0ai/mem0) self-hosted instance

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `MEM0_API_BASE` | Yes | Base URL of your mem0 REST API |
| `MEM0_API_KEY` | Yes | API key for the mem0 server |
| `SHIM_AUTH_TOKEN` | No | Bearer token clients must present (unset = open) |
| `MEM0_USER_ID` | No | Fixed user ID for all calls (default: `default_user`) |
| `MEM0_DEFAULT_TOP_K` | No | Default search result count (default: `100`) |
| `HOST` | No | Bind address (default: `0.0.0.0`) |
| `PORT` | No | Bind port (default: `8080`) |

### Run

```bash
pip install -r requirements.txt
python server.py
```

### Connect from Claude Code

```json
{
  "mcpServers": {
    "mem0": {
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

| Tool | Description |
|---|---|
| `add_memory` | Store a durable fact, preference, or decision |
| `search_memory` | Semantic search across stored memories |
| `list_memories` | List memories (optionally scoped by agent/run) |
| `get_memory` | Fetch a single memory by ID |
| `update_memory` | Replace a memory's text and metadata |
| `delete_memory` | Delete a single memory |
| `delete_all_memories` | Delete all memories within a scope |
| `list_entities` | List agent/run scopes with counts |
| `get_memory_history` | View change history for a memory |

## Development

```bash
ruff check .
ruff format --check .
pytest -x
```

## License

AGPL-3.0 — see [LICENSE](LICENSE).
