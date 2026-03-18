# Autonomous Agent Orchestration Protocol

This document defines how two Claude Code terminals operate as Agent A and Agent B, working through 20 days of implementation autonomously.

---

## Terminal Setup

### Terminal 1 — Agent A
Start the session with:
```
You are Agent A (Pipeline & Eval). Read plans/ORCHESTRATOR.md for your execution protocol, then check plans/STATE.md for your current day and begin work.
```

### Terminal 2 — Agent B
Start the session with:
```
You are Agent B (UI & Reports). Read plans/ORCHESTRATOR.md for your execution protocol, then check plans/STATE.md for your current day and begin work.
```

---

## Execution Loop (per agent)

Every agent follows this loop continuously until Day 20 is complete:

```
┌─────────────────────────────────────────────┐
│  1. READ plans/STATE.md                     │
│     → Find my next not_started day          │
│     → Check if dependencies are met         │
│        (other agent's status for blocking   │
│         days noted in the table)            │
│                                             │
│  2. IF dependency not met:                  │
│     → Work on non-blocking tasks from the   │
│       current day (queries, docs, tests)    │
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
│  6. VERIFY Acceptance Criteria              │
│     → Run the exact commands listed         │
│     → If failing, fix before proceeding     │
│                                             │
│  7. POST-DAY PROTOCOL                       │
│     → Run: make lint && make test           │
│     → Update STATE.md: status → completed   │
│     → Write HANDOFF.md entry if other agent │
│       depends on today's work               │
│     → Commit all changes with message:      │
│       "Agent {A|B} Day XX: {title}"         │
│                                             │
│  8. LOOP → back to step 1                   │
└─────────────────────────────────────────────┘
```

---

## Git Protocol

Both agents work on the **same branch** (master). To avoid conflicts:

1. **Pull before starting each day:** `git pull --rebase` (if remote is set up) or just check for uncommitted changes
2. **Commit after each day** with message format: `Agent {A|B} Day {XX}: {day title from plan file}`
3. **Never force push.** If there's a merge conflict, resolve it — don't overwrite.
4. **Agents own different files** — conflicts should be rare. The only shared files are:
   - `plans/STATE.md` — both write (different sections)
   - `plans/HANDOFF.md` — both write (append-only)
   - `tasks/lessons.md` — both write (append-only)
   - `src/scaffolder/models.py` — Day 1 only (pairing), then read-only for Agent B
   - `src/scaffolder/config.py` — Agent B owns, Agent A reads

5. **If a merge conflict occurs on STATE.md or HANDOFF.md:** take both changes (these files are append-only by design)

---

## Pairing Day Protocol

Days 1, 18, and 20 require both agents to coordinate.

### Day 1 (Data Models + Repo Init)
- **Agent A** creates: `models.py`, protocol interfaces, `__init__.py` files, directory structure
- **Agent B** creates: `pyproject.toml`, `config.py`, `Makefile`, `.gitignore`
- **Coordination:** Agent A commits first (models.py is the contract). Agent B then commits, importing from models.py.
- **Both agents must verify:** `make lint` and `make test` pass after both commits.

### Day 18 (README)
- **Agent A** writes: quickstart, benchmark results, methodology sections
- **Agent B** writes: installation, dashboard usage, screenshots, deployment sections
- **Coordination:** One agent creates `README.md` with section headers. The other fills in their sections. Use Edit tool to avoid overwriting.

### Day 20 (v1.0.0 Tag)
- **Agent A** runs: final benchmark, results verification, files post-v1 issues
- **Agent B** runs: final deployment verification, version bump, files post-v1 issues
- **Coordination:** Agent A tags v1.0.0 after both agents confirm STATE.md shows all days complete.

---

## Dependency Resolution

When a day has a dependency (noted in STATE.md), the agent must:

1. Check STATE.md — is the dependency day marked `completed`?
2. Check HANDOFF.md — is there a handoff entry with file paths?
3. If YES to both → proceed with the day
4. If NO → skip to the next non-blocked day, or work on parts of the current day that don't require the dependency

**Critical dependencies:**
| Agent B Day | Depends on Agent A | What's needed |
|-------------|-------------------|---------------|
| 7 (Streamlit compare) | Day 3 (ChunkingPipeline) | `from scaffolder.chunking import ChunkingPipeline` |
| 9 (Streamlit retrieval) | Day 8 (RetrievalSimulator) | `from scaffolder.retrieval import RetrievalSimulator` |
| 10 (CLI retrieval metrics) | Day 9 (RetrievalMetrics) | `from scaffolder.metrics import RetrievalMetrics` |
| 12 (Metrics dashboard) | Day 9 (RetrievalMetrics) | Same as above |

| Agent A Day | Depends on Agent B | What's needed |
|-------------|-------------------|---------------|
| 8 (RetrievalSimulator) | Day 3-4 (Query YAML files) | `queries/*.yaml` must exist |
| 11 (Voyage eval) | Day 6 (Voyage adapter) | `from scaffolder.embedding.voyage import VoyageEmbedder` |

---

## Session Recovery

If a terminal crashes or context is lost:

1. Start a new Claude Code session
2. Send the identity prompt: "You are Agent {A|B}..."
3. The agent reads `plans/STATE.md` → finds the last completed day → resumes from the next one
4. The agent reads `plans/HANDOFF.md` → catches up on what the other agent has delivered
5. The agent reads `tasks/lessons.md` → loads any corrections from prior sessions

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

Both agents have completed Day 20. STATE.md shows all 40 rows as `completed`. v1.0.0 is tagged. The following commands all succeed:

```bash
make lint
make test
make benchmark
make benchmark-embed  # requires [local] extra installed
make report
make dashboard        # requires [dashboard] extra installed
```
