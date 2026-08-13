---
name: beforepush
description: Use when preparing to push changes to the git repository (before `git push` or `npm run push`). Run this to verify all tests pass locally, understand what features were added or changed since the last push, sync CLAUDE.md, CONTEXT.md, and thought-partner-prompt.md with reality, and log feature ideas discussed in chat to the backlog.
---

# Before Push

A pre-push ritual that keeps the repository healthy and the project's documentation truthful. Run this skill before every `git push`.

## When to Use
- Right before any `git push` (or `npm run push`) to the repository
- After completing a feature or fixing a bug, before integrating the work
- If tests fail during this skill: STOP — fix the tests before continuing

## Overview

Run in this order:

1. **Run all tests locally** — the whole suite must pass before anything else.
2. **Understand the changes** — read the diff vs `origin/main` plus any spec/plan docs under `docs/superpowers/` to know what features were added, changed, or removed.
3. **Sync the three living docs** — update `CLAUDE.md`, `CONTEXT.md`, and `thought-partner-prompt.md` so their "Implemented/Status" sections reflect the actual current state of the code. Keep them consistent with each other and with the code.
4. **Update the feature idea backlog** — evaluate new ideas discussed in the CLI chat (and any noted in specs/plans), add accepted ones to `featureIdeas.md`, and move now-implemented ideas out.
5. **Report** — summarize test results, doc updates, and backlog changes to the user before they push.

## Step-by-Step

### 1. Run all tests locally

From the repo root:

```bash
npm test
```

This runs backend pytest first, then Playwright E2E (auto-starts the Vite dev server). Use the venv: `..\.venv\Scripts\python`.

**On failure:** Stop. Report the failing tests. Do not continue to doc sync or allow a push until tests are green.

### 2. Understand the changes

Gather the full picture of what happened since the last push:

```bash
git status
git diff origin/main...HEAD
git log origin/main..HEAD --oneline
```

Also read:
- Recently added/modified files listed in the diff
- `docs/superpowers/specs/**` and `docs/superpowers/plans/**` for the most recent design documents — these often capture feature intent and ideas not yet reflected in code or docs

From this, build a list of: **added features**, **changed features**, **removed features**, and **known-limitations/next-steps** mentioned in code or docs.

### 3. Sync the three living docs

Update all three files so their status sections describe the current state, not the state at last push. Keep the three consistent with each other.

| File | Sections to keep truthful |
|------|--------------------------|
| `CLAUDE.md` | Feature statuses ("Implemented"), Architecture Decisions, Core Features, Data Model (if schema changed), Project Structure (if files moved), Testing |
| `CONTEXT.md` | "Status" header line, "What I'm Building", Tech Stack table, Deployment notes |
| `thought-partner-prompt.md` | Tech Stack, "Two Core Functions" (mark Implemented / not yet), "Current Status", "Next steps" |

Rules:
- Mark features as Implemented only if the code actually implements them
- If a feature's behavior changed (e.g. auto-save flow, auth method), update the description to match
- Update "Next steps" to remove completed items and keep real remaining work
- Do not invent details not verifiable from the diff/code

### 4. Update the feature idea backlog

In `featureIdeas.md`, maintain a curated list of ideas (from chat discussions, specs, plans) that are not yet implemented.

- **Add** new ideas discussed in the CLI chat since the last push. One line per idea: short title + 1-line description. Only add ideas the user seemed to want (accepted/relevant), not every tangent.
- **Remove or mark done** ideas that were implemented since the last push.
- **Dedupe** — don't duplicate existing entries.

### 5. Report

Give the user a concise summary before they push:
- Test results (passed/failed)
- Features added/changed identified
- Which doc files were updated and how
- Feature ideas added to / removed from the backlog
- proposal for the git commit message accorting to the changes

Then let the user decide to push.

## Common Mistakes
- Updating docs from memory instead of reading the diff — always read the actual changes
- Marking a feature "Implemented" when only part of it shipped
- Forgetting `thought-partner-prompt.md` — all three docs must stay in sync
- Skipping the test run to save time — this is the core purpose of the skill
- Adding every half-mentioned idea to the backlog — only add ideas the user actually wants to pursue

## Red Flags — STOP
- Tests failing, considering pushing anyway
- "I'll update the docs later"
- Updating only CLAUDE.md but not CONTEXT.md / thought-partner-prompt.md
