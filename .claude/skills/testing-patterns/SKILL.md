---
name: testing-patterns
description: Integration test philosophy — test observable behavior, fixture composition, canary markers for library internals.
when_to_use: Writing tests, reviewing test code, or deciding between unit and integration tests.
user-invocable: false
---

# Testing Philosophy

## Integration Tests Verify Behavior, Not Internals

Integration tests must verify **observable behavior through endpoints**, not implementation details.

**Good integration tests:**
- Drive endpoints with an HTTP client
- Assert status codes and response bodies
- Verify side effects (emails sent, database rows created, audit entries logged)
- Test cross-cutting concerns (middleware, auth, rate limiting)

**Bad integration tests:**
- Calling internal service functions for behavior already observable via HTTP
- Using DB queries as the primary assertion surface (DB is for post-assertion verification)
- Testing internal query functions or utility functions — those belong in unit tests
- Duplicating coverage already exercised by another test

## Prefer Fixture Composition

If a test starts with boilerplate setup (register a user, log in, configure a setting), that belongs in a fixture. Test bodies should stay focused on what they're actually testing.

Build fixture stacks: `user` -> `logged_in_user` -> `admin_user`. Each level adds one concern. Tests request the level they need.

## Canary Markers for Library Internals

When code depends on a library's private or poorly-documented internals, add a **canary test** that asserts the internal's shape directly — don't rewrite production code to avoid the dependency when doing so would cost real accuracy or capability.

The canary turns an upstream rename or shape change into a loud test failure instead of a silent runtime bug.

Canary practices:
- Assert the specific attribute/method and the shape of its return value — not just "no exception raised"
- Name the test so the failure message makes the breakage obvious (e.g., `test_library_rate_limit_contract`), since it'll likely be read by whoever just bumped a dep
- Place it close to the module that uses the internal
