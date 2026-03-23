# Agentic Orchestration Scaffold

A reusable framework for coordinating two AI agents (Claude Code sessions) working in parallel on a software project. Born from a real production build where two agents completed 40 days of work autonomously with zero conflicts.

## What This Is

This repo contains the **coordination protocol** — not application code. It provides:

- **ORCHESTRATOR.md** — The execution loop each agent follows per task
- **BOOTSTRAP.md** — Pre-flight checklist (environment, permissions, shared contracts)
- **STATE.md** — Single source of truth for progress (who's done what)
- **HANDOFF.md** — Append-only log of deliverables between agents (with provenance)
- **ISSUES.md** — Cross-agent bug tracker with severity levels
- **Task plan templates** — Self-contained self-contained work orders with checklists, specs, and acceptance criteria
- **CLAUDE.md** — Instructions that Claude Code loads automatically, embedding the orchestration protocol
- **TROUBLESHOOTING.md** — Battle-tested failure modes and fixes
- **Lessons log** — Shared corrections that persist across sessions

## Why Two Agents?

Splitting work across two agents enables:

1. **Parallelism** — Agent A builds the core pipeline while Agent B builds UI/config/deployment simultaneously
2. **Clear ownership** — Each agent owns specific files, reducing merge conflicts to near-zero
3. **Focused context** — Each agent's context window stays clean and relevant to its domain
4. **Cross-validation** — Agents test each other's modules at task boundaries, catching integration issues early

This maps to the **scatter-gather** pattern from distributed systems: tasks fan out to parallel agents, results consolidate through shared artifacts. Research from Anthropic, Microsoft, and academic literature confirms file-based coordination is well-suited for 2-5 agent systems where simplicity and durability matter more than latency.

## How to Use

### 1. Clone this repo for your new project

```bash
git clone https://github.com/emmcygn/agents-scaffolding my-project
cd my-project
```

### 2. Customize the placeholders

Run this to find every placeholder:
```bash
grep -rn '{{' plans/ CLAUDE.md TROUBLESHOOTING.md
```

Replace each `{{PLACEHOLDER}}` with your project-specific values:

| Placeholder | Where | Example |
|------------|-------|---------|
| `{{PROJECT_NAME}}` | CLAUDE.md | `MyApp` |
| `{{AGENT_A_ROLE}}` | ORCHESTRATOR, CLAUDE, STATE | `Backend & API` |
| `{{AGENT_B_ROLE}}` | ORCHESTRATOR, CLAUDE, STATE | `Frontend & DevOps` |
| `{{VERIFY_COMMAND}}` | ORCHESTRATOR, CLAUDE, BOOTSTRAP, TROUBLESHOOTING | `make lint && make test` |
| `{{TEST_COMMAND}}` | CLAUDE, BOOTSTRAP | `pytest` |
| `{{LINT_COMMAND}}` | CLAUDE, BOOTSTRAP | `ruff check src/` |
| `{{BUILD_COMMAND}}` | CLAUDE, BOOTSTRAP | `npm run build` |
| `{{INSTALL_COMMAND}}` | BOOTSTRAP | `pip install -e ".[dev]"` |
| `{{SHARED_CONTRACT_FILE}}` | ORCHESTRATOR, BOOTSTRAP | `src/models.py` |
| `{{SHARED_CONFIG_FILE}}` | ORCHESTRATOR, BOOTSTRAP | `src/config.py` |
| `{{src_directory}}` | CLAUDE, BOOTSTRAP | `src/myapp/` |
| `{{SOURCE_TREE}}` | CLAUDE | ASCII tree of your source layout |
| `{{SUCCESS_COMMANDS}}` | ORCHESTRATOR | `make lint && make test && make build` |
| `{{AGENT_A_DAY1_DELIVERABLES}}` | ORCHESTRATOR | `models.py, protocol interfaces, directory structure` |
| `{{AGENT_B_DAY1_DELIVERABLES}}` | ORCHESTRATOR | `pyproject.toml, config.py, Makefile` |
| `{{DAY_01_TITLE}}` | STATE | `Repo Init & Data Model Contracts` |
| `{{VERSION_CHECK_COMMAND}}` | BOOTSTRAP | `python --version` |
| Dependency placeholders | ORCHESTRATOR | Fill in the cross-agent dependency tables |

### 3. Write your task plans

Create `plans/agent-a/task-01.md` through `task-NN.md` for each agent. Use the templates in `plans/agent-a/task-01.md` and `plans/agent-b/task-01.md` as starting points.

Each task plan should be **self-contained** — an agent should be able to execute it with zero additional context beyond what's in the plan file itself.

**Task plan anatomy:**
```
Mission        -> What and why (one sentence)
Context        -> How it fits in the timeline
Prerequisites  -> What must exist before starting
Checklist      -> Ordered tasks (checkboxes)
Implementation -> Detailed specs, pseudocode, data structures
Outputs        -> Files created/modified
Acceptance     -> Commands to verify success
Handoff        -> What the other agent needs to know
```

**Tips for writing effective task plans:**
- Front-load Agent B's independent work (config, docs, UI scaffolding) so it has work to do while waiting on Agent A's pipeline
- Include exact code signatures and data structures — vague specs cause duplicate work (Anthropic's #1 finding from their multi-agent research system)
- Acceptance criteria should be runnable commands, not prose descriptions
- The implementation details section is where most of the value lives — be specific

### 4. Generating task plans with Claude

You don't have to write all task plans manually. Use Claude Code itself:

1. **Research phase:** Have Claude explore your problem space, dependencies, and prior art
2. **Proposal phase:** Ask Claude for an implementation proposal with module breakdown and timeline
3. **Planning phase:** Ask Claude to write task plan files, one at a time, using the template
4. **Review:** Read each plan. Challenge the task breakdown and dependency ordering
5. **Launch:** Once satisfied, start the agents

### 5. Set up permissions

**This step is critical.** Without it, agents block on every tool call:

```
/permissions add Bash(*) Edit(*) Write(*) Read(*) Glob(*) Grep(*)
```

See `plans/BOOTSTRAP.md` for full details.

### 6. Launch the agents

**Option A — Two terminals (recommended):**
```
# Terminal 1
You are Agent A (Backend & API). Read plans/ORCHESTRATOR.md for your execution protocol, then check plans/STATE.md for your current day and begin work.

# Terminal 2
You are Agent B (Frontend & DevOps). Read plans/ORCHESTRATOR.md for your execution protocol, then check plans/STATE.md for your current day and begin work.
```

**Option B — Single orchestrator with subagents:**

Tell one Claude Code session to act as orchestrator, spawning Agent A and Agent B as background subagents. See `CLAUDE.md` for the full protocol.

### 7. Monitor without interrupting

From a separate terminal (don't modify files while agents run):

```bash
cat plans/STATE.md          # Progress overview
git log --oneline -20       # Recent commits
cat plans/ISSUES.md         # Open issues
tail -50 plans/HANDOFF.md   # Latest handoffs
```

## Realistic Expectations

Based on production experience:

- Agents complete roughly **1 task per 15-30 minutes** of wall-clock time
- In 2 hours: expect **4-8 tasks complete per agent** (8-16 total)
- Agent B typically runs **2-3 tasks ahead** of Agent A (config/UI work is faster than core pipeline)
- Context window exhaustion happens around **10-15 tasks in a single session** — the recovery protocol handles this
- Budget for **1-2 pairing interventions** per full run (dependency issues, shared contract changes)

## File Structure

```
├── CLAUDE.md                      # Auto-loaded instructions for Claude Code
├── TROUBLESHOOTING.md             # Battle-tested failure modes and fixes
├── README.md                      # This file
├── plans/
│   ├── ORCHESTRATOR.md            # Execution protocol (the "how")
│   ├── BOOTSTRAP.md               # Pre-flight checklist (the "before")
│   ├── STATE.md                   # Progress tracker (the "where")
│   ├── HANDOFF.md                 # Inter-agent deliverable log
│   ├── ISSUES.md                  # Cross-agent issue queue
│   ├── agent-a/
│   │   └── task-01.md              # Task plan template for Agent A
│   └── agent-b/
│       └── task-01.md              # Task plan template for Agent B
└── tasks/
    ├── todo.md                    # Per-session task tracking
    └── lessons.md                 # Shared corrections log
```

## Design Principles

### Append-only coordination files
HANDOFF.md and ISSUES.md are append-only. This eliminates merge conflicts when two agents write simultaneously. This maps to the three-channel communication model from distributed systems research: STATE.md = task ledger, ISSUES.md = point-to-point, HANDOFF.md = broadcast.

### File-level ownership
Each agent owns specific files. The shared contract file (e.g., `models.py`, `types.ts`) is the interface boundary — Agent A produces data in these shapes, Agent B consumes them. Changes to shared contracts require explicit coordination (pairing days).

### Self-contained task plans
Every task plan includes everything an agent needs: prerequisites, implementation details, test cases, acceptance criteria. No external context required. This enables session recovery — if context is lost, the agent reads STATE.md to find where it left off and picks up the next task plan. This aligns with Anthropic's "Effective Harnesses" guidance: progress tracking files + git commits as recovery points.

### Validation gates
Agents cannot mark a task complete without passing `{{VERIFY_COMMAND}}`. If verification fails, a retry protocol guides the agent through diagnosis, re-think, and escalation. This prevents premature completion — the #1 failure mode identified in Anthropic's long-running agent research.

### Cross-validation at boundaries
After completing a day, each agent smoke-tests modules it depends on from the other agent. Issues are filed immediately with severity levels (BLOCKER, BUG, WARN, REQUEST). This is a manual implementation of the output validation pattern recommended by Microsoft, OpenAI, and Anthropic.

### Structured provenance
HANDOFF entries include timestamps, duration, and verification results. This creates an audit trail for debugging regressions and estimating throughput.

## Proven At Scale

This framework was used to build a complete evaluation harness (40 agent-tasks, 189+ tests, 80%+ coverage, full CLI/JSON/HTML/Streamlit outputs) with:
- Zero merge conflicts between agents
- 4 cross-agent issues filed and resolved autonomously
- Full session recovery after context loss
- Clean git history with semantic commits

## References

This scaffold incorporates patterns from:
- [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) — Anthropic
- [How We Built Our Multi-Agent Research System](https://www.anthropic.com/engineering/multi-agent-research-system) — Anthropic
- [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) — Anthropic
- [Effective Context Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) — Anthropic
- [Claude Code Subagents](https://code.claude.com/docs/en/sub-agents) — Anthropic
- [AI Agent Design Patterns](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns) — Microsoft
- [A Practical Guide to Building Agents](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf) — OpenAI

## License

MIT
