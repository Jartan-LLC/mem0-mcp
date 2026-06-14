# memcp

Backend-agnostic, multi-tenant MCP memory server. Python, FastMCP, deployed behind Traefik.

## Rules

### Always
- Read README.md and relevant docs before modifying unfamiliar code
- Run Verify commands before declaring work done
- Update docs and skills alongside code changes
- Write plans to `.claude/workspace/` in the project root for non-trivial changes

### Anti-patterns
- Don't wrap things the underlying library already expresses clearly
- Don't speculate about fixes — investigate first, then propose
- Don't hardcode derived counts in comments — they drift silently

### Ask first
- Changing public API signatures or database schemas
- Deleting files or removing features

### Never
- Commit or push unless explicitly asked or instructed by a command
- Add dependencies without stating the reason
- Put secrets or credentials in tracked files

## Corrections

- FastMCP uses `mcp.server.fastmcp.FastMCP`, not `fastmcp.FastMCP`
- mem0 self-hosted REST API does NOT support nested boolean filters (AND/OR/NOT) — they 502
- mem0 self-hosted list endpoint does NOT filter by metadata and does NOT paginate
- mem0 PUT /memories/{id} returns `{"message": "..."}`, not the memory — must GET after PUT
- mem0 GET /entities does NOT filter by user_id — server post-filters for tenant isolation
- mem0 single-ID endpoints (GET/DELETE) are global — adapter does fetch-then-verify for ownership

## Skills

Project conventions live in `.claude/skills/`. Check the relevant skill when working in an unfamiliar area:

- **api-error-patterns** — MCP tool error format, canonical error codes
- **claude-config** — agents vs skills vs commands
- **docs-patterns** — writing style, structure, brevity
- **github-conventions** — branches, commits, issue/PR templates
- **logging-patterns** — log levels, formatting, structured output
- **testing-patterns** — integration tests, fixture composition, canary markers

When adding a new skill, add an entry here.

## Verify

```bash
ruff check memcp/ tests/
ruff format --check memcp/ tests/
python -c "import memcp"
pytest -x
```
