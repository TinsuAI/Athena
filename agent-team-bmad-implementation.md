# Agent Team: BMAD Implementation Pipeline

This document defines the automated agent team workflow for implementing epics story-by-story.

## Team Composition

| Agent | Model | Role |
|-------|-------|------|
| **SM** (Scrum Master) | Opus 4.6 | Creates stories from epic backlog |
| **DEV 1** (Developer) | Opus 4.6 | Implements story code |
| **DEV 2** (Reviewer) | Sonnet 4.5 | Reviews code and auto-fixes issues |

## Pipeline Steps (per story)

### Step 1: Create Story
**Agent:** SM (Opus 4.6)
```
/bmad-bmm-create-story *story-number
```
- Generates the story file with acceptance criteria, tasks, and technical details
- Output: Story file ready for development

### Step 2: Develop Story
**Agent:** DEV 1 (Opus 4.6)
```
/bmad-bmm-dev-story *story-number
```
- Implements all code changes defined in the story
- Follows project conventions from CLAUDE.md
- Ensures tests are written and passing

### Step 3: Code Review & Auto-Fix
**Agent:** DEV 2 (Sonnet 4.5)
```
/bmad-bmm-code-review *story-number
```
- Reviews the implemented code for quality, conventions, and correctness
- Automatically fixes all identified issues
- Ensures code meets project standards

### Step 4: Commit Changes
- Stage and commit all changes from the story implementation
- Commit message references the story number

### Step 5: Repeat
- Move to the next story number and repeat from Step 1
- Continue until all stories in the epic are complete

## Execution Flow

```
┌─────────────────────────────────────────────────────┐
│                   For each story:                    │
│                                                      │
│  SM (Opus 4.6)                                       │
│  └─► /bmad-bmm-create-story *N                       │
│       │                                              │
│       ▼                                              │
│  DEV 1 (Opus 4.6)                                    │
│  └─► /bmad-bmm-dev-story *N                          │
│       │                                              │
│       ▼                                              │
│  DEV 2 (Sonnet 4.5)                                  │
│  └─► /bmad-bmm-code-review *N  (review + auto-fix)  │
│       │                                              │
│       ▼                                              │
│  Commit changes                                      │
│       │                                              │
│       ▼                                              │
│  Next story (N+1) ──► Loop back to top               │
└─────────────────────────────────────────────────────┘
```

## Context Management (Critical)

**Each agent MUST reset/clear their context after completing their step.** This is essential because:

- Story implementations can be large and consume significant context window
- Stale context from a previous story can cause confusion or hallucinations
- Fresh context ensures each story gets full attention and accurate work

### Reset Rule

After an agent finishes their step for a story, they must:
1. Complete their work and confirm it's done
2. **Reset their context** (terminate and respawn fresh for the next story)
3. On respawn, reload this file (`agent-team-bmad-implementation.md`) and `CLAUDE.md` before starting

This means for each story iteration, all three agents start with a **clean context** — only loading the project instructions and the current story they need to work on.

## Important Notes

- Each agent must load this file and CLAUDE.md into context before starting work
- Stories are processed sequentially — each story must complete all 4 steps before the next begins
- The pipeline runs continuously until all stories in the epic are implemented
- **Agents must NOT carry context between stories** — always reset after completing a step
