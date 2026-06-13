---
name: github-conventions
description: GitHub conventions — branch naming, commit format, issue/PR templates, and safe issue/PR referencing in comments.
when_to_use: Using gh CLI, creating commits, posting PR/issue comments, or referencing issues by number.
user-invocable: false
---

# GitHub Conventions

CRITICAL: When referencing numbered items in comments or posts, avoid `#<number>` format — GitHub auto-links these to issues/PRs. Use "Item 1:", "Finding 1:", etc.

## Branches

Feature branches: `feature/<description>` or `feature/issue-<number>`
Always check if a branch already exists for an issue before creating a new one.

For sub-issues of a larger feature, branch from the parent feature branch rather than main. Sub-issue work merges back into the parent feature branch, which eventually merges to main.

## Commits

Conventional commits format: `<type>: description`

Types: `feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `test:`, `chore:`
Optional scope: `feat(frontend): description`

## Issues

Templates in `.github/ISSUE_TEMPLATE/` — read them for section structure.
- **Bug reports**: must have label `bug`
- **Feature requests**: must have label `enhancement`

## Pull Requests

PR template at `.github/PULL_REQUEST_TEMPLATE.md` — read it for section structure.
Use `Closes #<number>` to link PRs to issues.

## Implementation Plans

Plans are posted as issue comments and saved to `.claude/workspace/`. See [plan-format.md](plan-format.md) for the recommended structure.
