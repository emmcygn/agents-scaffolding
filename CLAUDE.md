# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

**{{PROJECT_NAME}}** — {{one-line description of what the project does and why}}.

- **Source layout:** `{{src_directory}}` ({{language/runtime version}})
- **Build system:** {{build tool, e.g., setuptools via pyproject.toml, cargo, npm}}
- **Key deliverables:** {{what the project produces — CLI, API, dashboard, library, etc.}}

## Build & Dev Commands

```bash
{{VERIFY_COMMAND}}       # lint + type check + test (the "must pass" gate)
{{TEST_COMMAND}}          # run tests
{{LINT_COMMAND}}           # run linter
{{BUILD_COMMAND}}         # build the project
```

## Architecture

```
{{SOURCE_TREE}}
```

**Data flow:** {{describe the pipeline or data flow in one line}}

---

## Agent Execution Model

This repo is built by **two AI agents working in parallel** with self-contained daily plans. All implementation is agent-first — Claude Code IS the engineering team.

**Full orchestration protocol:** `plans/ORCHESTRATOR.md`
**Progress tracker:** `plans/STATE.md` (single source of truth for what's done)
**Inter-agent comms:** `plans/HANDOFF.md` (append-only log of delivered work)
**Cross-agent issues:** `plans/ISSUES.md` (bugs, blockers, and requests between agents)
**Shared lessons:** `tasks/lessons.md` (corrections and patterns)

### Execution Modes

**Option 1 — Two terminals (parallel):**
Open two Claude Code sessions. Tell Terminal 1 "You are Agent A" and Terminal 2 "You are Agent B". Each reads `plans/ORCHESTRATOR.md` and runs autonomously through all days. They coordinate via STATE.md and HANDOFF.md on disk.

**Option 2 — One terminal with subagents (orchestrated):**
One Claude Code session acts as orchestrator, spawning Agent A and Agent B as background subagents (via the Agent tool with `run_in_background: true`). The orchestrator:
1. Runs Day 1 as a pairing day (both agents, same context)
2. Launches Agent A Day 2 and Agent B Day 2 as parallel background agents
3. Waits for completion notifications, checks STATE.md
4. Resolves dependencies (if Agent B Day N needs Agent A Day M, waits for A to finish)
5. Continues launching the next day for each agent as they complete
6. Handles pairing days in the main context

### Agent A — {{AGENT_A_ROLE}}
**Owns:** {{list of modules/files Agent A is responsible for}}
**Plans:** `plans/agent-a/day-01.md` through `day-NN.md`

### Agent B — {{AGENT_B_ROLE}}
**Owns:** {{list of modules/files Agent B is responsible for}}
**Plans:** `plans/agent-b/day-01.md` through `day-NN.md`

### How to Execute a Day

1. Read `plans/ISSUES.md` → fix any open issues assigned to you FIRST
2. Read `plans/STATE.md` → find your next `not_started` day
3. Check dependencies — is the blocking day marked `completed`?
4. Read the day file (e.g., `plans/agent-a/day-07.md`) — it is fully self-contained
5. Check **Prerequisites** — verify the files/modules listed actually exist
6. Work through the **Checklist** sequentially, using **Implementation Details** for specifics
7. **Cross-validate:** After implementing, import and smoke-test any modules you depend on from the other agent. If something is broken, file an issue in `plans/ISSUES.md`.
8. Validate against **Acceptance Criteria** (commands to run, expected results)
9. Run `{{VERIFY_COMMAND}}` — fix any failures before proceeding. If a failure is in the OTHER agent's code, file an issue in `plans/ISSUES.md` with severity BLOCKER or BUG.
10. Update `plans/STATE.md` — mark day as `completed` with timestamp
11. Write `plans/HANDOFF.md` entry if the other agent depends on today's output
12. Commit: `Agent {A|B} Day {XX}: {title}`
13. Loop → back to step 1

### Agent Coordination Rules

- **Pairing days** — both agents work on shared files. Coordinate through the shared contract file (the interface boundary).
- **The shared contract file is the interface boundary.** Agent A produces data in these shapes. Agent B consumes them. If a model changes, both agents must update.
- **Agent A is the critical path** for core pipeline components. Agent B can build UI/reporting against the model contracts before Agent A's implementations land.
- **Agent B can work ahead** on configuration, documentation, UI scaffolding, and deployment at any time — these typically have no upstream dependency after Day 1.
- **Never modify the other agent's owned files** without noting it in handoff. If you need a change in a file you don't own, describe what you need in handoff notes.
- **Session recovery:** If context is lost, re-read `plans/STATE.md` → find last completed day → resume from next. Read `plans/HANDOFF.md` to catch up on what the other agent delivered.

---

## Workflow Orchestration

### 1. Plan Node Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately — don't keep pushing
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity
- The daily plan files (`plans/agent-{a,b}/day-XX.md`) are the master plans — consult them before each task

### 2. Subagent Strategy
- Use subagents liberally to keep main context window clean
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One task per subagent for focused execution

### 3. Self-Improvement Loop
- After ANY correction from the user: update `tasks/lessons.md` with the pattern
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review lessons at session start for relevant project

### 4. Verification Before Done
- Never mark a task complete without proving it works
- Run `{{LINT_COMMAND}}` after every stage — zero errors
- Run `{{TEST_COMMAND}}` after every stage — all tests must pass
- Diff behaviour between main and your changes when relevant
- Ask yourself: "Would this survive a code review from a senior engineer?"

### 5. Demand Elegance (Balanced)
- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes — don't over-engineer
- Challenge your own work before presenting it

### 6. Autonomous Bug Fixing
- When given a bug report: just fix it. Don't ask for hand-holding
- Point at logs, errors, failing tests — then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how

---

## Task Management

1. **Plan First**: Write plan to `tasks/todo.md` with checkable items per daily plan
2. **Verify Plan**: Check in before starting implementation
3. **Trade-off and Risk**: Always include a trade-off and risk audit in your check-in for users to give guidance
4. **Track Progress**: Mark items complete as you go
5. **Explain Changes**: High-level summary at each step
6. **Document Results**: Add review section to `tasks/todo.md`
7. **Capture Lessons**: Update `tasks/lessons.md` after corrections

---

## Core Principles
- **Simplicity First**: Make every change as simple as possible. Impact minimal code.
- **No Laziness**: Find root causes. No temporary fixes. Senior developer standards.
- **Minimal Impact**: Changes should only touch what's necessary. Avoid introducing bugs.
