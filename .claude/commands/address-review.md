---
description: Work through review findings on a PR one at a time
argument-hint: PR number
---

# Address Review

Work through code review findings on a pull request, investigating each one and applying fixes where warranted.

**Always pause for the user's decision on each finding** — even in auto mode, even if the reviewer or your own assessment recommends skipping. Auto mode grants tool access, not decision authority; the user decides what to fix, skip, or adjust.

## Process

### 1. Load Review
Extract the PR number from `$ARGUMENTS`. Fetch the review comments:
```bash
gh pr view <pr-number> --comments
```
There may be multiple review comments in the history — use only the most recent one. Parse its findings into a numbered list grouped by severity (Critical > Important > Minor).

### 2. Check Out Branch
Ensure the PR's branch is checked out locally so fixes can be applied.

### 3. Walk Through Findings
Work through each finding sequentially. For each one:

1. **Investigate** — Read the relevant code. Understand whether the finding is a real problem, a theoretical concern, or a false positive. Check how the rest of the codebase handles the same pattern.
2. **Assess** — Present your assessment to the user: is it a real issue, valid but not applicable here, or wrong? Propose a specific fix or recommend skipping, with reasoning.
3. **Act on user decision** — Apply the fix, skip it, or adjust based on the user's response.

Do NOT blindly apply every suggestion. Investigate first — the reviewer may have missed context, flagged a pattern that's intentional, or suggested a fix that creates inconsistency with the rest of the codebase.

When the user agrees to skip a finding, post a brief PR comment explaining why it was declined:
```bash
gh pr comment <pr-number> --body "**Re: <finding title>** — <concise reason for skipping>"
```

### 4. Commit
The user may ask to commit at any point during the review — commit what's been done so far and continue with the remaining findings. Use the format:
```
fix(<scope>): address code review findings
```
Include a bulleted list of what was changed in the commit body. Never push unless the user explicitly asks.
