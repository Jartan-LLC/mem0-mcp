---
name: logging-patterns
description: Logging conventions — level usage, formatting style, structured output.
when_to_use: Writing code that logs events, configuring log output, or choosing log levels.
user-invocable: false
---

# Logging Conventions

## Setup

One logger per module, at module level:

```python
import logging

logger = logging.getLogger(__name__)
```

## Formatting

Use `%s`-style formatting arguments, not f-strings — the message template is preserved for structured aggregator queries:

```python
logger.info("Cleaned up %d expired sessions", count)                # yes
logger.error("SMTP send failed for %s", email, exc_info=True)       # yes
logger.info(f"Cleaned up {count} expired sessions")                 # no
```

## Level Conventions

| Level | Use for |
|---|---|
| `DEBUG` | Cache hit/miss, slow-path internals (opt-in only) |
| `INFO` | Startup/shutdown, admin bootstrap, cleanup counts, rate limit hits |
| `WARNING` | Recoverable anomalies, swallowed exceptions, degraded operation |
| `ERROR` | Unexpected exceptions on operational paths — always with `exc_info=True` |
| `CRITICAL` | Reserved for unusable state |

## Output

One record per line on stdout. Let the container runtime (Docker, k8s) capture it — no file sinks or log rotation in-app.

Support two formats via config:
- **`plain`** — Readable for local dev
- **`json`** — Stable single-line object per record for log aggregators (Loki, Datadog, ELK, CloudWatch)

Timestamps in UTC in both formats.
