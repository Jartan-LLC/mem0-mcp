---
name: api-error-patterns
description: MCP tool error response format — canonical error object, standard codes, retry semantics.
when_to_use: Writing tool error handling, choosing error codes, designing error responses.
user-invocable: false
---

# MCP Tool Error Conventions

## Response Format

All tool errors use the canonical error object:

```json
{
  "error": {
    "code": "snake_case_code",
    "message": "Human-readable description.",
    "retry": false
  }
}
```

- **`code`**: Machine-readable. Clients branch on this.
- **`message`**: Human/LLM-readable. Describes what went wrong.
- **`retry`**: Whether retrying the same call might succeed. Only `true` for transient failures (5xx, timeouts).

Use `canonical_error(code, message, retry=False)` from `memcp.types`.

## Standard Codes

| Code | When | Retry |
|------|------|-------|
| `not_found` | memory_id doesn't exist or belongs to another user | false |
| `not_supported` | optional tool not available on this backend | false |
| `scope_required` | delete_all called without scope keys | false |
| `invalid_scope` | scope contains unknown keys | false |
| `unauthorized` | invalid or missing bearer token | false |
| `backend_error` | upstream backend returned an error | status >= 500 |
| `validation_error` | invalid or malformed parameters | false |
| `nested_filter` | nested boolean filters (AND/OR/NOT) attempted | false |
| `timeout` | backend did not respond in time | true |

## Rules

1. Every tool failure returns the canonical error object — never raw strings or exceptions
2. `retry` is `true` only for transient failures (`e.status >= 500`)
3. 404 from backends maps to `not_found`, not `backend_error`
4. Validation errors are caught before backend calls
5. `MemoryAPIError` is the only exception type tool handlers catch from backends
