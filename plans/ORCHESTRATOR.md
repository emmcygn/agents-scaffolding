# Autonomous Agent Orchestration Protocol

This document defines how two Claude Code terminals operate as Agent A and Agent B, working through N days of implementation autonomously.

> **How to use this template:** Replace all `{{PLACEHOLDER}}` values with your project-specific details. Search for `{{` to find every customization point.

---

## Terminal Setup

### Terminal 1 — Agent A

Start the session with:
```
You are Agent A ({{AGENT_A_ROLE}}). Read plans/ORCHESTRATOR.md for your execution protocol, then check plans/STATE.md for your current day and begin work.
```

### Terminal 2 — Agent B

Start the session with:
```
You are Agent B ({{AGENT_B_ROLE}}). Read plans/ORCHESTRATOR.md for your execution protocol, then check plans/STATE.md for your current day and begin work.
```

---

## Execution Loop (per agent)

Every agent follows this loop continuously until the final day is complete:

```
┌─────────────────────────────────────────────┐
│  0. READ plans/ISSUES.md                    │
│     → Fix any open issues assigned to you   │
│     → This comes BEFORE starting new work   │
│                                             │
│  1. READ plans/STATE.md                     │
│     → Find my next not_started day          │
│     → Check if dependencies are met         │
│        (other agent's status for blocking   │
│         days noted in the table)            │
│                                             │
│  2. IF dependency not met:                  │
│     → Work on non-blocking tasks from the   │
│       current day (docs, tests, config)     │
│     → OR skip to next non-blocked day       │
│     → Write blocker in STATE.md             │
│                                             │
│  3. READ plans/agent-{a,b}/day-XX.md        │
│     → This is the self-contained work order │
│                                             │
│  4. CHECK Prerequisites section             │
│     → Verify listed files/modules exist     │
│     → If missing, check HANDOFF.md          │
│                                             │
│  5. EXECUTE Checklist                       │
│     → Work through tasks sequentially       │
│     → Use Implementation Details for specs  │
│     → Commit after each logical unit        │
│                                             │
│  5b. CROSS-VALIDATE                         │
│     → Import/smoke-test modules you depend  │
│       on from the other agent               │
│     → If something is broken, file an issue │
│       in plans/ISSUES.md with severity      │
│       (BLOCKER, BUG, WARN, REQUEST)         │
│     → If you CAN fix it quickly without     │
│       breaking ownership, fix it AND log    │
│       it in ISSUES.md so the owner knows    │
│                                             │
│  6. VERIFY Acceptance Criteria              │
│     → Run the exact commands listed         │
│     → If failing in YOUR code, fix it       │
│     → If failing in OTHER agent's code,     │
│       file ISSUES.md with BLOCKER severity  │
│                                             │
│  7. POST-DAY PROTOCOL                       │
│     → Run: {{VERIFY_COMMAND}}               │
│     → Update STATE.md: status → completed   │
│     → Write HANDOFF.md entry if other agent │
│       depends on today's work               │
│     → Commit all changes with message:      │
│       "Agent {A|B} Day XX: {title}"         │
│                                             │
│  8. LOOP → back to step 0                   │
└─────────────────────────────────────────────┘
```

---

## Git Protocol

Both agents work on the **same branch** (`main`). To avoid conflicts:

1. **Pull before starting each day:** `git pull --rebase` (if remote is set up) or just check for uncommitted changes
2. **Commit after each day** with message format: `Agent {A|B} Day {XX}: {day title from plan file}`
3. **Never force push.** If there's a merge conflict, resolve it — don't overwrite.
4. **Agents own different files** — conflicts should be rare. The only shared files are:
   - `plans/STATE.md` — both write (different sections)
   - `plans/HANDOFF.md` — both write (append-only)
   - `plans/ISSUES.md` — both write (append-only, numbered sequentially)
   - `tasks/lessons.md` — both write (append-only)
   - Any shared interface/contract files (see Shared Files below)

5. **If a merge conflict occurs on STATE.md, HANDOFF.md, or ISSUES.md:** take both changes (these files are append-only by design)

### Shared Files

List the files that both agents depend on and the ownership rules:

| File | Owner | Rule |
|------|-------|------|
| `{{SHARED_CONTRACT_FILE}}` | Agent A | Agent A creates on Day 1; Agent B reads. Changes require HANDOFF.md entry. |
| `{{SHARED_CONFIG_FILE}}` | Agent B | Agent B owns; Agent A reads. |

---

## Pairing Day Protocol

Some days require both agents to coordinate on shared files.

### Day 1 (Project Bootstrap)
- **Agent A** creates: {{AGENT_A_DAY1_DELIVERABLES}}
- **Agent B** creates: {{AGENT_B_DAY1_DELIVERABLES}}
- **Coordination:** Agent A commits first (shared contracts are the interface). Agent B then commits, importing from the shared contracts.
- **Both agents must verify:** `{{VERIFY_COMMAND}}` passes after both commits.

### Day N-2 (Documentation)
- **Agent A** writes: {{AGENT_A_DOCS_SECTIONS}}
- **Agent B** writes: {{AGENT_B_DOCS_SECTIONS}}
- **Coordination:** One agent creates the file with section headers. The other fills in their sections. Use Edit tool to avoid overwriting.

### Day N (Final Release)
- **Agent A** runs: final verification, results check
- **Agent B** runs: deployment verification, version bump
- **Coordination:** Agent A tags the release after both agents confirm STATE.md shows all days complete.

---

## Dependency Resolution

When a day has a dependency (noted in STATE.md), the agent must:

1. Check STATE.md — is the dependency day marked `completed`?
2. Check HANDOFF.md — is there a handoff entry with file paths?
3. If YES to both → proceed with the day
4. If NO → skip to the next non-blocked day, or work on parts of the current day that don't require the dependency

### Critical Dependencies

<!-- Fill in your project's cross-agent dependencies -->

| Agent B Day | Depends on Agent A | What's needed |
|-------------|-------------------|---------------|
| {{B_DAY}} | Day {{A_DAY}} ({{A_DELIVERABLE}}) | `{{IMPORT_PATH}}` |

| Agent A Day | Depends on Agent B | What's needed |
|-------------|-------------------|---------------|
| {{A_DAY}} | Day {{B_DAY}} ({{B_DELIVERABLE}}) | `{{IMPORT_PATH}}` |

---

## Validation Gate & Retry Protocol

After completing a day's checklist, the agent MUST pass the validation gate before marking the day complete.

### Validation Gate

```
RUN {{VERIFY_COMMAND}}
  │
  ├── PASS → proceed to post-day protocol (mark complete)
  │
  └── FAIL → enter retry protocol
```

### Retry Protocol

1. **Attempt 1:** Read the error output. Fix the root cause in YOUR code. Re-run.
2. **Attempt 2:** If same failure, re-think the approach — the implementation may be fundamentally wrong.
3. **Attempt 3:** If still failing, check if the failure is in the OTHER agent's code:
   - YES → file BLOCKER in `plans/ISSUES.md`, skip to non-blocked work
   - NO → write the problem in `plans/STATE.md` under "Current Blockers", move on
4. **Never:** Brute-force retry the same approach. If it failed twice, the approach is wrong.
5. **Never:** Mark a day complete if the validation gate has not passed.

### Failure in Other Agent's Code

If `{{VERIFY_COMMAND}}` fails due to code you don't own:
1. File an issue in `plans/ISSUES.md` with severity `BLOCKER` or `BUG`
2. If you can work around it without modifying their file, do so and file a `BUG`
3. If you must modify their file as an emergency fix, do so AND log it in both `plans/ISSUES.md` and `plans/HANDOFF.md`

---

## Session Recovery

If a terminal crashes or context is lost:

1. Start a new Claude Code session
2. Send the identity prompt: "You are Agent {A|B}..."
3. Run `plans/BOOTSTRAP.md` recovery checklist (verify environment still works)
4. The agent reads `plans/ISSUES.md` → fixes any open issues assigned to it FIRST
5. The agent reads `plans/STATE.md` → finds the last completed day → resumes from the next one
6. The agent reads `plans/HANDOFF.md` → catches up on what the other agent has delivered
7. The agent reads `tasks/lessons.md` → loads any corrections from prior sessions

STATE.md is the ground truth. If it says Day 7 is completed, trust it. Don't redo work.

---

## Escalation

If an agent is blocked for a reason not covered above:

1. Write the blocker in STATE.md under "Current Blockers"
2. Write a detailed description in HANDOFF.md explaining what's needed
3. Continue with any non-blocked work
4. If completely blocked with nothing to do → inform the user

---

## Success Condition

Both agents have completed all days. STATE.md shows all rows as `completed`. The release is tagged. The following commands all succeed:

```bash
{{SUCCESS_COMMANDS}}
```
