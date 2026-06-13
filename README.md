# Project Template

Starter template with dev container, Claude Code configuration, GitHub workflows, and project conventions.

## Getting Started

Run `/onboard` in Claude Code to set up this template for your project. It will interview you, configure all the files, and tell you which manual steps remain.

## What's Included

| Area | Contents |
|------|----------|
| `.devcontainer/` | Dev container with Claude Code CLI, Docker, GitHub CLI, desktop-lite |
| `.claude/` | Agents, commands, skills, settings with plugins |
| `.github/` | Issue forms, PR template, CI stub, Dependabot, Claude Code workflow, security policy |
| `CLAUDE.md` | AI assistant rules, verification commands, skill index |

## Post-Fork Checklist

If you prefer to set up manually instead of using `/onboard`:

### Required

- [ ] Update `CLAUDE.md` — replace placeholder comments:
  - Project name and description (line 1 and 3)
  - Verify commands with your actual build/test/lint commands
  - Corrections with any version-specific overrides for your stack
- [ ] Update `CLAUDE.md` Skills section — remove skills that don't apply to your project, add project-specific ones
- [ ] Update `.devcontainer/devcontainer.json` — change the desktop-lite password, add/remove language features and extensions for your stack
- [ ] Update `.devcontainer/setup.sh` — add dependency installation for your stack
- [ ] Update `.gitignore` — add language-specific patterns for your stack
- [ ] Update `.editorconfig` — adjust formatting rules for your language (e.g., tabs for Go)
- [ ] Update `.github/CODEOWNERS` — uncomment and set owner usernames/teams
- [ ] Update `.github/SECURITY.md` — set supported versions and response timeline
- [ ] Update `.github/ISSUE_TEMPLATE/config.yml` — replace `ORG/REPO` in contact link URLs with your GitHub org and repo name
- [ ] Update `.github/dependabot.yml` — remove ecosystems you don't use, add ones you need, adjust directories if not at root
- [ ] Fill in `.github/workflows/ci.yml` — replace TODO comments with your lint and test commands
- [ ] Create a `LICENSE` file
- [ ] When removing skills, update any agent files that reference them in their `skills:` frontmatter
- [ ] Add secrets to your repo:
  - `ANTHROPIC_API_KEY` — for the Claude Code workflow
  - `PAT` — a GitHub Personal Access Token with `repo` scope, used by the Claude Code workflow for checkout

### Recommended

- [ ] Enable GitHub Discussions (Settings > General > Features) — issue template config links to it
- [ ] Enable CodeQL default setup (Settings > Security > Code scanning)
- [ ] Enable secret scanning with push protection (Settings > Security > Secret Protection)
- [ ] Configure branch ruleset for `main` — require PR reviews, require CI to pass, block force pushes
- [ ] Enable auto-merge (Settings > General > Allow auto-merge) — Dependabot minor/patch PRs auto-merge after CI passes
- [ ] Review `.github/workflows/claude.yml` — uses `--dangerously-skip-permissions` which grants Claude unrestricted tool access in CI

### Cleanup

- [ ] Replace this README with your own
- [ ] Remove `.claude/skills/` entries that don't apply to your project type
- [ ] Remove `.claude/agents/` entries that don't apply (e.g., `frontend-reviewer` for a CLI project)
- [ ] Delete `.claude/commands/onboard.md`
