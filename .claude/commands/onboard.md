---
description: Set up this template for your project
---

# Onboard

Configure this template repo for a new project.

## Process

### 1. Prerequisites

Check `gh auth status`. If not authenticated, tell the user to run `gh auth login` before continuing — onboarding uses `gh` commands for repo configuration.

### 2. Read `README.md`

Read the post-fork checklist. This is the source of truth for what needs to change.

### 3. Interview

Ask the user in a single message for: project name, one-line description, primary language/framework, deployment target, GitHub org/repo, GitHub username, build/test/lint commands, license (MIT, Apache-2.0, proprietary, etc.), and any version corrections for training data. List the skills and agents that exist in `.claude/skills/` and `.claude/agents/` so the user can choose which to keep.

### 4. Confirm

Summarize what you understood and what changes you'll make. Wait for the user to confirm before proceeding.

### 5. Apply

Work through every Required checklist item that can be automated. Also:

- Replace the template README with a project README
- License: rename the chosen `LICENSE.<type>` file to `LICENSE`, delete the others, and fill in `[year]` and `[fullname]`. Available: `LICENSE.MIT`, `LICENSE.Apache-2.0`, `LICENSE.AGPL-3.0`. If the user wants a different license or proprietary, delete all three and create the appropriate file.
- Update `.devcontainer/devcontainer.json` — add/remove language features and extensions to match the chosen stack
- Update `.devcontainer/setup.sh` — add dependency installation for the chosen stack (e.g., `go mod download`, `cargo build`)
- Update `.gitignore` — add language-specific patterns for the chosen stack
- Update `.editorconfig` — adjust formatting rules for the chosen language (e.g., tabs for Go)
- When removing skills, also update any agent files that reference them in their `skills:` frontmatter
- Add `skillOverrides` to `.claude/settings.json` — disable installed plugin skills that don't match the chosen stack (language-specific skills for other languages, niche utilities, meta-skills). Keep universal skills enabled. If multiple plugins provide skills for the same domain, keep the more specific one and disable the other. Set disabled skills to `"off"`.

For questions the user didn't have answers to (e.g., version corrections, verify commands), leave the placeholder comments in place — they are written so that Claude will fill them in naturally when the information is discovered during normal development. Only replace placeholders that have actual answers.

### 6. Manual Steps

Present both the Required items that need manual action (adding secrets) and the Recommended checklist items that require manual action in GitHub Settings.

### 7. Cleanup

Ask the user if they want to delete this command file (`.claude/commands/onboard.md`). If yes, delete it.
