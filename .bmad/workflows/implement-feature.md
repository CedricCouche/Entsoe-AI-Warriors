# Workflow: Implement a New Feature

**Trigger:** A user wants to add a new capability to the system.

---

## Overview

```
User request
     │
     ▼
[Analyst] → User Story written in docs/USER_STORIES.md
     │
     ├─ Architecture change needed? ──Yes──▶ [Architect] → ADR + spec update
     │                                               │
     │◀──────────────────────────────────────────────┘
     ▼
[Developer] → Implementation in src/
     │
     ▼
[QA] → Tests + validation
     │
     ├─ All criteria pass? ──Yes──▶ Story marked [DONE] ✓
     │
     └─ Defect found? ──────────▶ [Developer] → Fix → [QA] → Re-validate
```

---

## Step-by-Step

### Step 1 — Analyst: Write the Story

**Invoke:** `You are the Analyst agent. Read .bmad/agents/analyst.md for your role card. The user wants: {request}.`

**Agent actions:**
1. Read `docs/USER_STORIES.md` to find the next story ID
2. Read `docs/SPECIFICATION.md` to understand current behaviour
3. Write the story with acceptance criteria
4. Flag if architectural review is needed

**Exit condition:** Story written and saved to `docs/USER_STORIES.md`

---

### Step 2 — Architect: Review (only if flagged)

**Invoke:** `You are the Architect agent. Read .bmad/agents/architect.md for your role card. Review story US-{NNN} which requires architectural decisions.`

**Agent actions:**
1. Read the flagged story
2. Evaluate the architectural impact
3. Write an ADR in `docs/adr/ADR-{NNN}-{slug}.md`
4. Update `docs/SPECIFICATION.md` if the architecture changes
5. Add implementation guidance to the story

**Exit condition:** ADR written, spec updated, story annotated

---

### Step 3 — Developer: Implement

**Invoke:** `You are the Developer agent. Read .bmad/agents/developer.md for your role card. Implement story US-{NNN}.`

**Agent actions:**
1. Read the story and acceptance criteria
2. Read relevant spec sections and source files
3. Implement minimal code change
4. Verify each criterion manually
5. Mark story `[DONE]` in `docs/USER_STORIES.md`

**Exit condition:** Code written, story marked `[DONE]`

---

### Step 4 — QA: Validate

**Invoke:** `You are the QA agent. Read .bmad/agents/qa.md for your role card. Validate story US-{NNN}.`

**Agent actions:**
1. Read the story and each acceptance criterion
2. Review the implementation
3. Write tests for testable logic
4. Run `uv run pytest`
5. Confirm `[DONE]` or report defect

**Exit condition:** All criteria verified, tests pass

---

## How to Invoke an Agent in Claude Code

Paste this at the start of your message to set the agent context:

```
You are acting as the {AGENT_NAME} agent for the Entsoe-AI-Warriors project.
Read your role card at .bmad/agents/{agent_name}.md before doing anything.
Then: {specific task or story reference}.
```

Example:
```
You are acting as the Analyst agent for the Entsoe-AI-Warriors project.
Read your role card at .bmad/agents/analyst.md before doing anything.
Then write a user story for: adding a CO2 emissions chart to the Overview tab.
```

---

## Notes

- Each agent operates from documents, not from memory of previous conversations
- Always reference the story ID (US-NNN) when switching between agents
- The spec (`docs/SPECIFICATION.md`) is the ground truth — if code and spec disagree, flag it
- Work always happens on a feature branch, never directly on `main`
