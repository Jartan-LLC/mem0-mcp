# mem0-mcp

MCP server exposing self-hosted mem0 long-term memory as tools over streamable HTTP. Python, FastMCP, deployed behind Traefik.

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

## Skills

Project conventions live in `.claude/skills/`. Check the relevant skill when working in an unfamiliar area:

- **api-error-patterns** — error response format, status codes
- **claude-config** — agents vs skills vs commands
- **docs-patterns** — writing style, structure, brevity
- **frontend-patterns** — design tokens, mobile-first, component isolation
- **github-conventions** — branches, commits, issue/PR templates
- **logging-patterns** — log levels, formatting, structured output
- **testing-patterns** — integration tests, fixture composition, canary markers

When adding a new skill, add an entry here.

## Verify

```bash
ruff check .
ruff format --check .
python -m py_compile server.py
pytest -x
```
