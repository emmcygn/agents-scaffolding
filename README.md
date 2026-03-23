# Agentic Orchestration Scaffold

A reusable framework for coordinating two AI agents (Claude Code sessions) working in parallel on a software project. Born from a real production build where two agents completed 40 days of work autonomously with zero conflicts.

## What This Is

This repo contains the **coordination protocol** — not application code. It provides:

- **ORCHESTRATOR.md** — The execution loop each agent follows every day
- **STATE.md** — Single source of truth for progress (who's done what)
- **HANDOFF.md** — Append-only log of deliverables between agents
- **ISSUES.md** — Cross-agent bug tracker with severity levels
- **Day plan templates** — Self-contained daily work orders with checklists, specs, and acceptance criteria
- **CLAUDE.md** — Instructions that Claude Code loads automatically, embedding the orchestration protocol
- **Lessons log** — Shared corrections that persist across sessions

## Why Two Agents?

Splitting work across two agents enables:

1. **Parallelism** — Agent A builds the core pipeline while Agent B builds UI/config/deployment simultaneously
2. **Clear ownership** — Each agent owns specific files, reducing merge conflicts to near-zero
3. **Focused context** — Each agent's context window stays clean and relevant to its domain
4. **Cross-validation** — Agents test each other's modules at day boundaries, catching integration issues early

## How to Use

### 1. Fork this repo for your new project

```bash
git clone <this-repo> my-project
cd my-project
```

### 2. Customize the placeholders

Search for `{{` across all files. Replace every placeholder with your project-specific values:

| Placeholder | Example |
|------------|---------|
| `{{PROJECT_NAME}}` | `MyApp` |
| `{{AGENT_A_ROLE}}` | `Backend & API` |
| `{{AGENT_B_ROLE}}` | `Frontend & DevOps` |
| `{{VERIFY_COMMAND}}` | `make lint && make test` |
| `{{SHARED_CONTRACT_FILE}}` | `src/types.ts` |

### 3. Write your day plans

Create `plans/agent-a/day-01.md` through `day-NN.md` for each agent. Use the template in `plans/agent-a/day-01.md` as a starting point. Each day plan should be **self-contained** — an agent should be able to execute it with zero additional context.

**Day plan anatomy:**
```
Mission        → What and why (one sentence)
Context        → How it fits in the timeline
Prerequisites  → What must exist before starting
Checklist      → Ordered tasks (checkboxes)
Implementation → Detailed specs, pseudocode, data structures
Outputs        → Files created/modified
Acceptance     → Commands to verify success
Handoff        → What the other agent needs to know
```

### 4. Define dependencies in STATE.md

Fill in the dependency table in `plans/ORCHESTRATOR.md` so agents know when to wait vs. work ahead.

### 5. Launch the agents

**Option A — Two terminals:**
```
# Terminal 1
You are Agent A (Backend & API). Read plans/ORCHESTRATOR.md for your execution protocol, then check plans/STATE.md for your current day and begin work.

# Terminal 2
You are Agent B (Frontend & DevOps). Read plans/ORCHESTRATOR.md for your execution protocol, then check plans/STATE.md for your current day and begin work.
```

**Option B — Single orchestrator with subagents:**

Tell one Claude Code session to act as orchestrator, spawning Agent A and Agent B as background subagents. See `CLAUDE.md` for the full protocol.

## File Structure

```
├── CLAUDE.md                      # Auto-loaded instructions for Claude Code
├── README.md                      # This file
├── plans/
│   ├── ORCHESTRATOR.md            # Execution protocol (the "how")
│   ├── STATE.md                   # Progress tracker (the "where")
│   ├── HANDOFF.md                 # Inter-agent deliverable log
│   ├── ISSUES.md                  # Cross-agent issue queue
│   ├── agent-a/
│   │   └── day-01.md              # Day plan template for Agent A
│   └── agent-b/
│       └── day-01.md              # Day plan template for Agent B
└── tasks/
    └── lessons.md                 # Shared corrections log
```

## Design Principles

### Append-only coordination files
HANDOFF.md and ISSUES.md are append-only. This eliminates merge conflicts when two agents write simultaneously.

### File-level ownership
Each agent owns specific files. The shared contract file (e.g., `models.py`, `types.ts`) is the interface boundary — Agent A produces data in these shapes, Agent B consumes them.

### Self-contained day plans
Every day plan includes everything an agent needs: prerequisites, implementation details, test cases, acceptance criteria. No external context required. This enables session recovery — if context is lost, the agent reads STATE.md to find where it left off and picks up the next day plan.

### Cross-validation at boundaries
After completing a day, each agent smoke-tests modules it depends on from the other agent. Issues are filed immediately with severity levels (BLOCKER, BUG, WARN, REQUEST).

## Proven At Scale

This framework was used to build a complete evaluation harness (40 agent-days, 189+ tests, 80%+ coverage, full CLI/JSON/HTML/Streamlit outputs) with:
- Zero merge conflicts between agents
- 4 cross-agent issues filed and resolved autonomously
- Full session recovery after context loss
- Clean git history with semantic commits

## License

MIT
