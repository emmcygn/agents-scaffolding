# Parallel AI Agent Orchestration Guide

How to set up two Claude Code agents to build a software project in parallel, autonomously, from a standing start. Extracted from the LexiChunk Scaffolder project where this pattern was developed and validated.

---

## Table of Contents

1. [The Pattern in One Page](#the-pattern-in-one-page)
2. [Phase 1: Research & Understand](#phase-1-research--understand)
3. [Phase 2: Create a Proposal](#phase-2-create-a-proposal)
4. [Phase 3: Scope to Team & Timeline](#phase-3-scope-to-team--timeline)
5. [Phase 4: Write Atomic Daily Plans](#phase-4-write-atomic-daily-plans)
6. [Phase 5: Set Up Orchestration Files](#phase-5-set-up-orchestration-files)
7. [Phase 6: Configure CLAUDE.md](#phase-6-configure-claudemd)
8. [Phase 7: Launch & Monitor](#phase-7-launch--monitor)
9. [Daily Plan File Format](#daily-plan-file-format)
10. [Orchestration File Reference](#orchestration-file-reference)
11. [Coordination Patterns](#coordination-patterns)
12. [Failure Modes & Fixes](#failure-modes--fixes)
13. [Checklist: Before You Walk Away](#checklist-before-you-walk-away)

---

## The Pattern in One Page

```
1. Research the project deeply (use subagents to explore repos, fetch docs, search web)
2. Create a visual proposal (HTML with Mermaid diagrams, tables, tradeoffs)
3. Scope to your team: N engineers × M weeks
4. Write atomic daily plans: 1 file per engineer per day, fully self-contained
5. Set up orchestration files: STATE.md, HANDOFF.md, ISSUES.md, ORCHESTRATOR.md
6. Configure CLAUDE.md with agent execution protocol
7. Open N terminals, paste identity prompts, set permissions, walk away
```

**Why it works:** Each agent gets a complete, self-contained work order for each day. They don't need to understand the whole project — just today's file. Coordination happens through simple text files on disk (STATE.md, HANDOFF.md, ISSUES.md) that both agents read and write.

**Key insight:** The daily plan files are the real innovation. They contain enough context, implementation detail, and acceptance criteria that an AI agent can execute a full day of engineering work without human intervention. The orchestration files (STATE/HANDOFF/ISSUES) solve the multi-agent coordination problem through append-only logs.

---

## Phase 1: Research & Understand

Before writing any plans, deeply understand what you're building. This session used three inputs:

### 1a. Explore the target (if extending/testing existing code)
Use a subagent to thoroughly explore the codebase:
```
Launch an Explore agent: "Thoroughly explore [repo URL]. I need to understand:
1. What it does (purpose, core functionality)
2. Full file/directory structure
3. Key source files and their contents
4. The API surface — what functions/classes/methods are exposed
5. Any existing tests
6. Dependencies and packaging"
```

### 1b. Research best practices
Use a general-purpose subagent to research the domain:
```
Launch a research agent: "Research current best practices for [domain].
I need comprehensive, actionable findings on:
1. Industry-standard tools and frameworks
2. Key metrics used in production
3. Competitive landscape
4. Published benchmarks"
```

### 1c. Incorporate existing context
Read any existing research docs, PRDs, or prior work the user provides. These contain decisions already made and constraints already identified.

**Output of Phase 1:** A deep understanding of what exists, what's missing, and what best practices say. This informs every subsequent decision.

---

## Phase 2: Create a Proposal

Write an HTML proposal document with:

1. **Phase overview** — what gets built in what order, with a visual timeline
2. **System architecture** — Mermaid flowcharts showing data flow and component interaction
3. **Pipeline flow table** — left-to-right, each stage with inputs/outputs/owner/phase
4. **Tech stack** — every dependency justified with "why this" and "why not alternative"
5. **Repo structure** — proposed directory layout
6. **Metrics/success criteria** — how you know it works
7. **Tradeoffs** — decisions made with pros/cons documented
8. **Grounding** — how each decision maps to best practices/research

### Why HTML, not Markdown?
- Mermaid diagrams render natively (via CDN script tag)
- Professional dark-theme styling makes it demo-ready
- Tables, cards, and timelines are easier to lay out
- The user can open it in a browser immediately

### Proposal iteration
Start broad (v1), then scope down to the actual team/timeline (v2). The v2 proposal should have:
- Explicit "what we cut and why" section
- Explicit "what we kept and why" section
- Week-by-week goals with demo checkpoints

---

## Phase 3: Scope to Team & Timeline

Take the proposal and map it to your actual constraints:

### Team split principles
- **Split by layer, not by feature** — one agent owns backend/pipeline, the other owns UI/reports. This minimizes file conflicts.
- **Identify the critical path** — which agent's work blocks the other? Front-load their work.
- **Identify parallel work** — what can the non-critical agent do while waiting? (Config, docs, query annotations, UI layout against mock data)
- **Plan pairing days** — Day 1 (shared data models), near-end (README), final day (release). These are the only days both agents touch the same files.

### What to cut for smaller teams/timelines
Cut in this order (least to most painful):
1. Additional variants (extra embedding models, extra chunking strategies)
2. Publication-grade benchmarks (LegalBench-RAG scale) — curated queries are enough
3. LLM-judge evaluation — deterministic metrics are the primary proof
4. Streamlit pages (merge 4 pages into 2)
5. HTML report (Streamlit IS the visual report)

### Create a longer-term roadmap (optional)
If the project has a larger vision (3-month, 3-engineer version), write it as a separate `ROADMAP.md`. This gives context for what the 4-week scope is sacrificing and what comes next.

---

## Phase 4: Write Atomic Daily Plans

This is the most important phase. Each day file must be **fully self-contained** — an AI agent picking it up cold can execute the day's work without reading any other plan file.

### How to generate them
Use two parallel subagents (one per agent role), each with a comprehensive prompt containing:

1. **Full project context** — what the project is, tech stack, repo structure
2. **The agent's role** — what they own, what the other agent owns
3. **Shared data models** — the exact interface contracts both agents depend on
4. **Day-by-day breakdown** — what each day accomplishes (1-2 sentences per day)
5. **The file format** — exact template they must follow (see below)
6. **Instruction to be thorough** — "Include specific class/method signatures, import paths, data structures, and key algorithms"

### Key principle: implementation details must be specific enough to code from
Bad: "Implement the chunking pipeline"
Good: "Create `ChunkingPipeline` class with `run(documents: list[Document]) -> list[StrategyResult]` method. It iterates over `self.strategies: dict[str, ChunkingStrategy]`, calls `strategy.chunk(text, document_id)` for each document, wraps results in `StrategyResult(strategy=name, document_id=doc.id, chunk_set=chunks, duration_ms=elapsed)`. Time each strategy with `time.perf_counter()`."

### Daily plans should include:
- Exact file paths to create/modify
- Class and method signatures with types
- Import paths the other agent will use
- Edge cases to handle
- Test cases to write
- Acceptance criteria (specific commands + expected output)

---

## Phase 5: Set Up Orchestration Files

Five files coordinate the agents:

### `plans/STATE.md` — Progress Tracker
```markdown
## Agent A — Pipeline & Eval
| Day | Status | Completed | Notes |
|-----|--------|-----------|-------|
| 01  | not_started | | PAIR day |
| 02  | not_started | | |
...

### Current Blockers
_(none)_
```

Rules:
- Each agent updates ONLY their section
- Status values: `not_started`, `in_progress`, `completed`, `blocked`
- Note dependencies in the Notes column at creation time
- Ground truth for "where am I?" after session recovery

### `plans/HANDOFF.md` — Delivery Log
```markdown
### Agent A → Agent B | Day 03 Complete
**What's ready:** ChunkingPipeline with 4 strategies
**Files:** src/scaffolder/chunking/pipeline.py, strategies.py
**Import paths:** `from scaffolder.chunking import ChunkingPipeline`
**Breaking changes:** None
```

Rules:
- Write an entry when you complete something the other agent depends on
- Include exact import paths so the other agent can use it immediately
- Append-only — never edit previous entries

### `plans/ISSUES.md` — Cross-Agent Bug Queue
```markdown
### ISSUE-001 | BUG: StrategyName enum values don't match config strings
**Filed by:** Agent B
**Assigned to:** Agent A
**Status:** open
**File(s):** src/scaffolder/models.py
**Problem:** Config uses "lexichunk" but enum is LEXICHUNK
**Impact:** Streamlit strategy dropdown breaks
**Suggested fix:** Add a classmethod `from_config_string()` on the enum
```

Severity levels:
- **BLOCKER** — I cannot continue until this is fixed
- **BUG** — Something is wrong but I can work around it
- **WARN** — Potential problem, not blocking yet
- **REQUEST** — I need a change to a file you own

Rules:
- Check this file BEFORE starting each new day
- Fix assigned issues BEFORE starting new work
- Mark resolved (don't delete)

### `plans/ORCHESTRATOR.md` — Execution Protocol
The full loop each agent follows:
```
0. READ ISSUES.md → fix assigned issues first
1. READ STATE.md → find next not_started day
2. Check dependencies → is blocking day completed?
3. READ day plan file → self-contained work order
4. CHECK prerequisites → verify files exist
5. EXECUTE checklist → work through tasks
5b. CROSS-VALIDATE → smoke-test other agent's modules you depend on
6. VERIFY acceptance criteria → run listed commands
7. POST-DAY: make lint && make test → update STATE.md → write HANDOFF.md → commit
8. LOOP → back to step 0
```

### `plans/BOOTSTRAP.md` — Pre-flight Checklist
One-time setup: Python version, dependencies installed, fixtures in place. Both agents verify before Day 1.

### `tasks/lessons.md` — Shared Learning Log
Corrections and patterns discovered during development. Both agents write here, both review at session start.

---

## Phase 6: Configure CLAUDE.md

CLAUDE.md must contain:

### Project context
What the project is, source layout, key claim to prove.

### Build commands
The exact `make` targets. Agents run these constantly for verification.

### Architecture overview
Data flow, component ownership, shared contracts.

### Agent execution model
- Agent A and Agent B roles + ownership boundaries
- Pointers to orchestration files (STATE, HANDOFF, ISSUES, ORCHESTRATOR)
- The day execution loop (abbreviated — ORCHESTRATOR.md has the full version)
- Coordination rules: pairing days, interface boundary (models.py), critical path
- Session recovery protocol

### Workflow preferences
Your personal working style preferences (plan-first, subagent strategy, self-improvement loop, verification standards, etc.) These persist across projects.

---

## Phase 7: Launch & Monitor

### Terminal startup prompts

**Terminal 1 — Agent A:**
```
You are Agent A (Pipeline & Eval). Your job is to build [specific responsibilities].

Read these files in order, then begin autonomous execution:
1. plans/BOOTSTRAP.md — run the pre-flight checks
2. plans/ORCHESTRATOR.md — your execution protocol
3. plans/STATE.md — find your current day

Then read plans/agent-a/day-01.md and start working. After each day, update STATE.md, write HANDOFF.md if needed, commit with "Agent A Day XX: {title}", and immediately proceed to the next day. Do not stop until all 20 days are complete or you hit an unresolvable blocker.

Day 1 is a PAIR day — [specific Day 1 coordination instructions].
```

**Terminal 2 — Agent B:**
```
You are Agent B (UI & Reports). Your job is to build [specific responsibilities].

[Same structure, Agent B specifics]
```

### Permissions
Set auto-allow so agents don't block on permission prompts:
```
/permissions add Bash(*) Edit(*) Write(*) Read(*) Glob(*) Grep(*)
```

Or in `~/.claude/settings.json`:
```json
{
  "permissions": {
    "allow": [
      "Bash(*)", "Edit(*)", "Write(*)",
      "Read(*)", "Glob(*)", "Grep(*)"
    ]
  }
}
```

### Monitoring
Check progress without interrupting:
- Read `plans/STATE.md` — see day completion status
- Run `git log --oneline` — see commit trail
- Read `plans/ISSUES.md` — see cross-agent problems
- Read `plans/HANDOFF.md` — see delivery log

---

## Daily Plan File Format

Every daily plan file follows this exact structure:

```markdown
# Agent {A|B} — Day XX: [Title]

## Mission
[One sentence: what this day accomplishes and why it matters]

## Context
[Where we are in the project. What exists from previous days.
What the other agent is doing today that's relevant.]

## Prerequisites
[Files/modules that must exist before this day starts.
Check these first — if missing, check HANDOFF.md or file an ISSUE.]

## Checklist
- [ ] Task 1 — description
- [ ] Task 2 — description
- [ ] Task 3 — description

## Implementation Details

### [Task group name]
[Specific implementation guidance: file paths, class signatures,
method signatures, key patterns to follow, edge cases to handle.
Enough detail that an AI agent can write the code without ambiguity.]

### [Task group name]
[More implementation details...]

## Outputs
[Exact list of files created or modified]

## Acceptance Criteria
[How to verify the day is done.
Specific commands to run and expected results.]

## Handoff Notes
[What the other agent needs to know.
What the next day depends on.
Any decisions made today that affect future days.]
```

### What makes a good daily plan:
- **Mission** is one sentence, not a paragraph
- **Context** mentions what the OTHER agent is doing (dependency awareness)
- **Prerequisites** are specific file paths, not vague descriptions
- **Checklist** is 4-8 items (a day should be a day, not a week)
- **Implementation Details** include actual code signatures and patterns
- **Acceptance Criteria** are runnable commands with expected output
- **Handoff Notes** include exact import paths the other agent will use

---

## Coordination Patterns

### The Interface Boundary Pattern
One file (e.g., `models.py`) defines all shared data contracts. Both agents agree on it Day 1. After that:
- Agent A produces data in these shapes
- Agent B consumes data in these shapes
- If the interface needs to change, the changer files an ISSUE for the other agent

### The Critical Path Pattern
Identify which agent's work gates the other. Front-load their work. The non-critical agent works on independent tasks (config, docs, UI layout against contracts) while waiting.

### The Pairing Day Pattern
Some days require both agents (Day 1: shared models, final days: README, release). For these:
- Define who creates the file first
- Define which sections each agent owns
- Use Edit tool (not Write) to avoid overwriting each other

### The Cross-Validation Pattern
After implementing, each agent should smoke-test modules they depend on from the other agent:
- Import it
- Call a basic function
- Verify the return type matches the contract
- If broken: file ISSUES.md, don't silently work around it

### The Session Recovery Pattern
If a terminal crashes:
1. Start new session with identity prompt
2. Read ISSUES.md → fix open issues first
3. Read STATE.md → find last completed day
4. Read HANDOFF.md → catch up on deliveries
5. Read lessons.md → load corrections
6. Resume from next day

---

## Failure Modes & Fixes

### Agents keep asking for permission
**Fix:** Set `/permissions add Bash(*) Edit(*) Write(*) Read(*) Glob(*) Grep(*)` in each terminal before launching.

### Agent's plan doesn't match the other agent's actual implementation
**Expected behavior.** Plans are guides, not gospel. The agent should read the actual code (via imports, file reads) and adapt. If the mismatch is significant, file an ISSUE.

### Agents edit the same file simultaneously
**Prevention:** Ownership rules. Each agent owns specific directories. Shared files (STATE.md, HANDOFF.md, ISSUES.md) are append-only by design, making merge conflicts trivial to resolve.

### Agent gets stuck in a loop
If an agent is repeatedly failing on the same thing, it should:
1. Write the problem to `tasks/lessons.md`
2. Write a BLOCKER issue in ISSUES.md
3. Skip to the next non-blocked day
4. Inform the user if completely stuck

### Agent finishes early (completes all non-blocked days)
Write remaining blockers in STATE.md. Work on tests, documentation, or polish for already-completed days. Do not invent new work not in the plan.

### Context window fills up
Each day is self-contained. If context fills mid-day, the agent can start a new session, read STATE.md, and resume. The daily plan file has all the context needed.

### Git merge conflicts
Rare with proper ownership splits. If they occur on append-only files (STATE.md, HANDOFF.md, ISSUES.md), take both changes. For code files, the owning agent's version wins.

---

## Checklist: Before You Walk Away

Before leaving agents to run unattended:

- [ ] Both terminals have identity prompts pasted and running
- [ ] Permissions are set to auto-allow in both terminals (`/permissions`)
- [ ] `plans/STATE.md` exists with all days listed for both agents
- [ ] `plans/ORCHESTRATOR.md` exists with the execution loop
- [ ] `plans/HANDOFF.md` exists (empty, ready for entries)
- [ ] `plans/ISSUES.md` exists (empty, ready for entries)
- [ ] `plans/BOOTSTRAP.md` exists with pre-flight checks
- [ ] `tasks/lessons.md` exists (empty, ready for entries)
- [ ] All daily plan files exist (`plans/agent-a/day-01.md` through `day-20.md`)
- [ ] `CLAUDE.md` references all orchestration files and has the agent execution model
- [ ] Day 1 pairing instructions are explicit in both terminal prompts
- [ ] Dependencies between agents are noted in STATE.md
- [ ] Git repo is initialized with an initial commit

### Expectations
- Agents will complete roughly 1 day per 15-30 minutes (varies by complexity)
- In 2 hours, expect 4-8 days complete per agent
- Check `git log --oneline` and `plans/STATE.md` to see progress
- The agents WILL discover mismatches between plans and reality — this is healthy
- The agents WILL adapt their implementations to match actual code — this is correct

---

## Reproducing This Pattern for a New Project

1. **Start a fresh Claude Code session** in your project repo
2. **Research phase:** Have Claude explore the target codebase/domain deeply
3. **Proposal phase:** "Create an HTML proposal with phases, architecture, tech stack, and tradeoffs"
4. **Scope phase:** "If we had N engineers and M weeks, how would you build this?"
5. **Planning phase:** "Create atomic daily plans for each engineer in `plans/agent-a/` and `plans/agent-b/`"
6. **Orchestration phase:** "Set up STATE.md, HANDOFF.md, ISSUES.md, ORCHESTRATOR.md, and BOOTSTRAP.md"
7. **CLAUDE.md phase:** "Update CLAUDE.md with agent execution model and coordination rules"
8. **Launch:** Open N terminals, paste identity prompts, set permissions, walk away

The entire setup (phases 1-7) takes one Claude Code session of ~1-2 hours. The execution (phase 8) runs autonomously after that.
