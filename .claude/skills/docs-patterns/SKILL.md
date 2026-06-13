---
name: docs-patterns
description: Documentation writing conventions — style, structure, tone, and quality standards.
when_to_use: Writing, editing, or reviewing documentation files.
user-invocable: false
---

# Documentation Writing Patterns

Before writing, **read 2-3 existing docs in the same category** to match their tone and structure.

## Writing Style

**Tone:** Technical but accessible. Imperative for instructions ("Use X..."), declarative for specifications ("The User model has these fields..."). No marketing language.

**Brevity is paramount.** A doc that could be 100 lines should not be 300. Every paragraph must earn its place. If a table communicates it better than prose, use a table. If a link to another doc covers it, don't restate it. Be precise, not exhaustive.

## Section Structure

All docs follow a consistent pattern:

1. **H1 title** with a one-line description
2. **Overview** — brief intro, bullet list of capabilities/features
3. **Configuration** — tables for settings/env vars (Setting | Default | Description)
4. **Usage** — practical code examples showing realistic patterns
5. **Implementation details** — topic-specific sections as needed
6. **See Also** — related doc links

## Conventions

- **Tables** for reference content (settings, fields, endpoints). 3-4 columns max.
- **Code examples** in Usage sections — complete enough to copy-paste, with error handling where relevant.
- **Internal links** use relative markdown: `[Doc Name](FILENAME.md)`
- **No redundancy** — don't repeat information documented elsewhere. Link instead.
- **Code examples must work** — verify against actual project code.

## What to Avoid

- Verbose explanations where a table or code block would be clearer
- Repeating content from other docs (link to it)
- Obvious statements that don't add value
- Multiple ways of saying the same thing
- Documentation that doesn't match the actual code
