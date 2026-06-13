---
description: Create a GitHub issue using the appropriate template
argument-hint: Description of the bug or feature request
---

# Create Issue

Create a GitHub issue from a description.

## Process

### 1. Gather Context
Use the conversation context and `$ARGUMENTS` to understand what needs to be filed. If this is being called from within an existing issue or PR, gather relevant context from it — the new issue may be a spin-off for something discovered during that work.

### 2. Determine Type
From the gathered context, determine whether this is a bug report or feature request.

### 3. Read Template
Read the appropriate template from `.github/ISSUE_TEMPLATE/`:
- Bug -> `bug_report.yml`
- Feature -> `feature_request.yml`

### 4. Create Issue
Create the issue following the template structure, with the correct label:
- Bug: label `bug`
- Feature: label `enhancement`

```bash
gh issue create --title "<title>" --label "<label>" --body "<body following template>"
```
