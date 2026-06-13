---
name: api-error-patterns
description: API error response format — machine-readable codes, human-readable reasons, status code rules.
when_to_use: Writing API error handling, choosing HTTP status codes, designing error response shapes.
user-invocable: false
---

# API Error Conventions

## Response Format

All API error responses use a consistent format:

```json
{
  "detail": {
    "code": "UPPER_SNAKE_CASE_CODE",
    "reason": "Human-readable message."
  }
}
```

- **`code`**: Machine-readable identifier. Frontend uses this for branching logic (redirect to verification, show specific field errors).
- **`reason`**: User-facing message. Frontend can display directly. Always a complete sentence ending with a period.

## Status Code Rules

| Status | When to Use |
|--------|-------------|
| 200 | Successful operation that returns data |
| 201 | Resource created |
| 204 | Success with no body (logout, delete, disable) |
| 400 | Client sent bad data (invalid input, bad credentials) |
| 403 | Authenticated but forbidden (wrong password, disabled feature, insufficient role) |
| 404 | Resource not found |
| 409 | Conflict (duplicate resource) |
| 429 | Too many requests (rate limit exceeded) |
| 500 | Unexpected server error (never intentional except for genuine internal failures) |

## Adding New Error Codes

1. Use the `{"code": "...", "reason": "..."}` format
2. Reuse an existing code if the error is semantically identical
3. Use `UPPER_SNAKE_CASE` for codes
4. Write reasons as complete sentences the frontend can show to users
5. Use appropriate HTTP status codes per the table above
