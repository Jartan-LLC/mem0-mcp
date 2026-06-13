---
name: claude-config
description: How agents, skills, and commands work in this project.
when_to_use: Creating or modifying files in .claude/ — agents, skills, commands, or settings.
user-invocable: false
---

# Claude Configuration Primitives

This project uses three distinct configuration types in `.claude/`. Each has a clear purpose — never conflate them.

## Agents = Roles

An agent defines **who you are**. It shapes focus, identity, and constraints for a subagent.

- Role identity ("You are a senior backend reviewer")
- Tool and permission constraints
- What the agent cares about (evaluation criteria, output format, confidence thresholds)
- Runs in an isolated subagent context

**Agents are not workflows.** They define a lens for approaching work, not steps to follow. A backend-reviewer says "you care about async correctness and session handling" — not "Step 1: read the diff."

**Good:** Role identity, focus areas, evaluation criteria, output format, what to read for context.
**Bad:** Step-by-step procedures, bash scripts, workflow orchestration.

## Skills = Context and Knowledge

A skill defines **what you know**. It provides conventions, recommendations, how-tos, and reference material.

- Reference knowledge ("Here's how migrations work in this project")
- Conventions ("Module files follow this structure")
- Recommendations ("When writing docs, prefer tables over prose")
- Templates and examples when they're the core value

**Skills are not workflows.** They provide knowledge for good decision-making.

A skill MAY include a sequence when it's critical reference — but as illustrative guidance, not a script to execute.

**Good:** Conventions, patterns, templates, recommendations, how-tos, reference material.
**Bad:** Rigid step-by-step procedures, orchestration logic, state management.

## Commands = Workflows

A command defines **what to do**. An explicit, purposeful sequence triggered by the user.

- Specific workflow with clear start and end
- Defines what happens in what order
- Has a trigger (`/command-name`) and expected output
- May include specific commands to run, but skills inform the how

**Commands are workflows.** They define *what* to do; skills inform *how* to do each step well.

**Good:** Step sequences, action triggers, workflow orchestration, expected outcomes.
**Bad:** General knowledge, conventions, recommendations unrelated to the workflow.

## How They Interact

- Commands trigger action, skills provide context, agents provide specialized focus
- Commands may invoke agents as part of their workflow
- Agents may preload skills for additional project context

## Naming

- **Agents** answer "who is this?" — `backend-reviewer`, `issue-planner`
- **Skills** answer "what does this teach?" — `logging-patterns`, `github-conventions`
- **Commands** answer "what does this do?" — `plan-issue`, `review-pr`

Naming should be predictable within a category but not forced into a single suffix.

## Testing the Distinction

1. **Defines a role identity?** -> Agent
2. **Provides knowledge or recommendations?** -> Skill
3. **Executes a sequence of actions?** -> Command

If a file does two of these, split it.
