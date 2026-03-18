# Parallel AI Agent Orchestration Guide

How to set up two Claude Code agents to build a software project in parallel, autonomously, from a standing start. Extracted from the LexiChunk Scaffolder project (2026-03-18) where this pattern was developed and validated in a single session.

---

## Table of Contents

1. [The Pattern in One Page](#the-pattern-in-one-page)
2. [What This Session Actually Produced](#what-this-session-actually-produced)
3. [Phase 1: Research & Understand](#phase-1-research--understand)
4. [Phase 2: Create a Proposal](#phase-2-create-a-proposal)
5. [Phase 3: Scope to Team & Timeline](#phase-3-scope-to-team--timeline)
6. [Phase 4: Write Atomic Daily Plans](#phase-4-write-atomic-daily-plans)
7. [Phase 5: Set Up Orchestration Files](#phase-5-set-up-orchestration-files)
8. [Phase 6: Configure CLAUDE.md](#phase-6-configure-claudemd)
9. [Phase 7: Launch & Monitor](#phase-7-launch--monitor)
10. [Daily Plan File Format — With Real Examples](#daily-plan-file-format--with-real-examples)
11. [Orchestration File Reference — With Real Examples](#orchestration-file-reference--with-real-examples)
12. [Coordination Patterns — What Actually Happened](#coordination-patterns--what-actually-happened)
13. [Failure Modes & Fixes — From This Session](#failure-modes--fixes--from-this-session)
14. [The Conversation Flow That Produced This](#the-conversation-flow-that-produced-this)
15. [Exact Prompts Used](#exact-prompts-used)
16. [Checklist: Before You Walk Away](#checklist-before-you-walk-away)
17. [Reproducing This Pattern for a New Project](#reproducing-this-pattern-for-a-new-project)

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

## What This Session Actually Produced

In one Claude Code orchestration session (~2.5 hours of setup, then autonomous execution):

### Setup phase (human + orchestrator Claude):
- Explored LexiChunk GitHub repo via subagent (56 tool uses, ~4 min)
- Researched legaltech RAG best practices via subagent (22 tool uses, ~4.5 min)
- Read 2 compass research artifacts (user's prior work)
- Created proposal v1 (HTML, 4-phase architecture)
- Created 3-month/3-engineer roadmap (ROADMAP.md)
- Created proposal v2 (HTML, scoped to 2 engineers/4 weeks)
- Generated 40 daily plan files via 2 parallel subagents (~25 min each)
- Created 5 orchestration files (STATE, HANDOFF, ISSUES, ORCHESTRATOR, BOOTSTRAP)
- Configured CLAUDE.md with agent execution model

### Autonomous execution phase (2 agents running in parallel):
Within the first ~90 minutes of autonomous execution:

| | Agent A (Pipeline) | Agent B (UI/Reports) |
|---|---|---|
| Days completed | 5 of 20 | 8 of 20 |
| Commits | 5 | 8 |
| Tests written | ~48 | ~48 |
| Files created | ~20 | ~30 |
| Blockers hit | 0 | 0 |

**Commit trail (actual):**
```
e54a3a8 Add comprehensive agent orchestration guide
abb829d Agent B Day 08: Chunk viewer with clause-type colour coding
09c5bb7 Agent B Day 07: Streamlit chunk comparison page
1bbb076 Agent B Day 06: Voyage API adapter
c28da96 Agent B Day 05: JSON export, CLI polish & Streamlit skeleton
567f45a Agent A Day 04: Structural metrics (core three)
c6edd9d Agent B Day 04: Complete query annotations & CLI reporter
343b65b Agent A Day 03: ChunkingPipeline & strategy wrappers
f710c2c Add cross-agent issue queue and cross-validation step
ca35220 Agent B Day 03: Query annotation schema & first 8 queries
08e8e66 Agent A Day 02: FixtureManager & document loading
9d87194 Agent B Day 02: Config system completion
9131b75 Agent B Day 01: Repo init, config system & Makefile
```

**Key observation:** Agent B consistently ran ~2 days ahead of Agent A because Agent B's early work (config, queries, Streamlit skeleton) had no upstream dependencies. Agent A's work was sequentially dependent (fixtures → pipeline → metrics → CLI). This is the critical path pattern working as designed.

**Key observation:** Agent B's Day 7 (Streamlit compare page) required reading Agent A's actual ChunkingPipeline implementation. Agent B discovered that the plan's assumed API (`pipeline.chunk(doc, strategy)`) didn't match the real API. Agent B adapted by reading the real code, discovering `get_strategy()` and `strategy.chunk(document)`. This is healthy — plans are guides, implementations are truth.

---

## Phase 1: Research & Understand

Before writing any plans, deeply understand what you're building. This session used three research inputs, all run in parallel where possible.

### 1a. Explore the target codebase (if extending/testing existing code)

In this session, we explored the LexiChunk GitHub repo using an Explore subagent. The exact prompt used:

```
Thoroughly explore the GitHub repository at https://github.com/emmcygn/lexichunk/tree/master.
I need to understand:
1. What the SDK does (purpose, core functionality)
2. The full file/directory structure
3. Key source files and their contents
4. The API surface — what functions/classes/methods are exposed
5. Any existing tests
6. Dependencies and how it's packaged
7. README and documentation
8. Configuration files (package.json, tsconfig, etc.)

Use WebFetch to read the repo. Start with the root, then drill into every directory
and read every significant source file. Be very thorough — read the actual code,
not just file names. Return a comprehensive summary of everything you find.
```

**Result:** 56 tool uses over ~4 minutes. Returned a comprehensive summary covering: 8-stage pipeline, 3 jurisdictions (UK/US/EU), 24+ clause types, LegalChunker API surface, all parser/enrichment/strategy modules, 31 test modules, 5 test fixtures, zero runtime dependencies, LangChain + LlamaIndex integrations.

**Why this matters:** The scaffolder needs to test LexiChunk's API. Without understanding the exact method signatures (`chunk()`, `chunk_with_metrics()`, `get_defined_terms()`, `parse_structure()`, `build_embedded_text()`), the daily plans would have wrong API calls.

### 1b. Research best practices in the domain

The exact prompt used:

```
Research the current state of the art for evaluating RAG systems specifically
for legal documents. I need comprehensive, actionable findings on:
1. Enterprise legaltech RAG evaluation frameworks (RAGAS, LangSmith, DeepEval, etc.)
2. Key metrics used in production RAG evaluation
3. Legal document chunking best practices
4. Competitive landscape for legal document chunking
5. Embedding models commonly used for legal text

Use WebSearch and WebFetch to find recent (2024-2026) information.
Focus on practical, implementable findings rather than academic theory.
```

**Result:** 22 tool uses over ~4.5 minutes. Returned findings on: RAGAS framework (95% human agreement on faithfulness), MLEB benchmark (legal embedding rankings — Kanon 2 > Voyage 3 > OpenAI), LegalBench-RAG (6,858 queries with character-level ground truth), Summary-Augmented Chunking (50% DRM reduction), Stanford hallucination study (17-33% in commercial legal tools), optimal chunk sizes for legal text (512-1024 tokens).

**Why this matters:** Every metric, embedding model choice, and benchmark dataset in the proposal is grounded in this research. "We use NDCG@10 because it's the primary metric in MLEB" is more credible than "we use NDCG@10 because it seems good."

### 1c. Incorporate existing user context

The user provided two compass research artifacts:
- `compass_artifact_wf-e39acb5a...` — Legal RAG gap analysis: market size, document volumes, failure modes of existing chunkers, 5 specific gaps to target
- `compass_artifact_wf-3dd433ca...` — 4-week build playbook: week-by-week execution plan, benchmarking strategy, blog post template, visibility tactics

These contained decisions already made (e.g., target UK/US contracts first, use LegalBench-RAG for formal benchmarking, $20 budget for LLM-judge evaluation) that constrained the proposal.

**Lesson:** Always ask if the user has prior research. It saves hours and ensures alignment.

---

## Phase 2: Create a Proposal

### What was actually built

**Proposal v1** (`research-docs/proposal.html`): 12-section HTML document with:
1. Phase overview — 4 phases with visual timeline
2. System architecture — 2 Mermaid flowcharts (end-to-end + component interaction)
3. Pipeline flow table — 10 stages, left-to-right, with inputs/outputs/phase
4. Tech stack — 15 dependencies, each with "why this" and "why not alternative"
5. Repo structure — full proposed directory layout
6. Metrics framework — 3 tiers (structural, retrieval, LLM-judge)
7. Query strategy — 2 tiers (curated vs LegalBench-RAG)
8. Tradeoffs — 7 decisions with pros/cons
9. Grounding — 8 best practices mapped to implementation decisions
10. Build sequence — Gantt chart + dependency graph (Mermaid)
11. Extensibility roadmap — 6 extension points
12. Success criteria — target numbers with research justification

### Why HTML, not Markdown

- Mermaid diagrams render natively via CDN: `<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>`
- Dark theme with CSS custom properties looks professional
- Cards, timelines, metric displays, and colour-coded tables are trivial in HTML
- The user opens it in a browser and sees something that looks like a product spec
- Mermaid `flowchart LR`, `flowchart TD`, and `gantt` chart types were all used

### Proposal HTML structure pattern

```html
<head>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        :root { --bg: #0a0a0f; --surface: #12121a; --accent: #6c8cff; ... }
        /* Dark theme, Inter font, card-grid layout */
    </style>
</head>
<body>
    <div class="hero"><!-- Title, subtitle, meta tags --></div>
    <div class="container">
        <section><!-- Each numbered section --></section>
    </div>
    <script>
        mermaid.initialize({ startOnLoad: true, theme: 'dark', ... });
    </script>
</body>
```

### Proposal iteration: v1 → v2

The user asked: "If we had 2 engineers and 4 weeks, how would you build this?"

**Proposal v2** (`research-docs/proposal-v2.html`) was a scoped-down version with explicit sections for:
- "What we kept and why" (structural + retrieval metrics, multi-model comparison, Streamlit)
- "What we cut and why" (LegalBench-RAG → deferred, LLM-judge → deferred, 6 strategies → 4, 4 Streamlit pages → 2)
- Week-by-week swim-lane tables (Day column, Eng A column, Eng B column)
- Updated dependency graph with ownership colours (green = Eng A, blue = Eng B, purple = shared)

**The scoping conversation mattered.** The user's requirements were:
1. 80% demos to others, 20% self-validation
2. Include actual embedding step (retrieval simulation, not just structural metrics)
3. Use 5 existing fixtures + extensibility framework
4. All three output formats (CLI, JSON, HTML) plus Streamlit dashboard
5. Professional GUI in later phase
6. Grounded against real legaltech RAG best practices
7. Paid embedding API (Voyage) as a toggle

### The 3-month roadmap (separate document)

Before scoping to 4 weeks, the user also asked for a 3-engineer/3-month version. This was written as `research-docs/ROADMAP.md` with:
- Team structure (Eng 1: evaluation core, Eng 2: infra/data, Eng 3: UI/reports)
- Month-by-month breakdown with weekly milestones
- Risk register (6 risks with likelihood/impact/mitigation)
- Out-of-scope list with justifications
- Engineer dependency graph
- Success metrics for the project itself

**Why this was useful:** Even though we built the 4-week version, the 3-month roadmap shows what's sacrificed and what comes next. It informed the "post-v1 backlog" section of proposal v2.

---

## Phase 3: Scope to Team & Timeline

### Team split: the actual decision

**Agent A — Pipeline & Eval** owns everything in the data flow:
- `src/scaffolder/fixtures/` — document loading
- `src/scaffolder/chunking/` — pipeline + 4 strategy wrappers
- `src/scaffolder/embedding/pipeline.py` — local embedding adapters + cache
- `src/scaffolder/retrieval/` — FAISS index + query simulation
- `src/scaffolder/metrics/` — structural, retrieval, statistical
- `src/scaffolder/reporting/cli.py` (initial), `json_export.py`, `html.py`
- `tests/` (most test files)

**Agent B — UI & Reports** owns everything the user sees:
- `pyproject.toml`, `Makefile`, `.gitignore`
- `src/scaffolder/config.py`
- `queries/*.yaml` — all query annotation files
- `src/scaffolder/embedding/voyage.py` — paid API adapter
- `src/scaffolder/dashboard/` — all Streamlit code
- `src/scaffolder/reporting/cli.py` (extensions)
- `EXTENSIBILITY.md`

### Why split by layer, not by feature

If you split by feature (Agent A builds chunking + its UI, Agent B builds retrieval + its UI), every feature requires touching files in multiple directories. Both agents end up editing `dashboard/`, `reporting/`, and `tests/` constantly → merge conflicts.

Layer split means Agent A never touches `dashboard/` and Agent B never touches `metrics/`. The interface boundary is `models.py` — Agent A produces `ChunkSet`, `StrategyResult`, `BenchmarkResult` objects; Agent B consumes them.

### The critical path

```
Agent A: FixtureManager → ChunkingPipeline → EmbeddingPipeline → FAISS Index →
         RetrievalSimulator → RetrievalMetrics → Reports
```

This is sequential — each step depends on the previous. Agent A is always on the critical path.

Agent B's early work (config, queries, Streamlit skeleton, Voyage adapter) has no upstream dependency after Day 1. This is why Agent B ran 2-3 days ahead — it could work in parallel on independent tasks while Agent A built the pipeline sequentially.

### Dependencies that were pre-identified

| Agent B Day | Waits for Agent A | What's needed |
|-------------|-------------------|---------------|
| 7 (Streamlit compare) | Day 3 (ChunkingPipeline) | `from scaffolder.chunking import ChunkingPipeline` |
| 9 (Streamlit retrieval) | Day 8 (RetrievalSimulator) | `from scaffolder.retrieval import RetrievalSimulator` |
| 10 (CLI retrieval metrics) | Day 9 (RetrievalMetrics) | Retrieval metric functions |
| 12 (Metrics dashboard) | Day 9 (RetrievalMetrics) | Same |

| Agent A Day | Waits for Agent B | What's needed |
|-------------|-------------------|---------------|
| 8 (RetrievalSimulator) | Day 3-4 (Queries) | `queries/*.yaml` files |
| 11 (Voyage eval) | Day 6 (Voyage adapter) | `VoyageEmbedder` class |

### Pairing days

- **Day 1:** Both agents create shared infrastructure. Agent A: `models.py`, directory structure. Agent B: `pyproject.toml`, `config.py`, `Makefile`. Agent A commits first (models.py is the contract).
- **Day 18:** README. Agent A writes methodology/results. Agent B writes installation/dashboard/deployment. One creates the file, other edits sections.
- **Day 20:** Release. Both verify, tag v1.0.0.

---

## Phase 4: Write Atomic Daily Plans

### How they were generated

Two subagents were launched in parallel, each with a ~3000-word prompt containing:

1. Full project context (what LexiChunk is, all API methods, all test fixtures)
2. Complete repo structure (every directory and file)
3. Tech stack with specific package names
4. The agent's role and ownership boundaries
5. The other agent's role (so each knows what they DON'T own)
6. Shared data models (exact dataclass definitions with field types)
7. Day-by-day breakdown (1-3 sentences per day describing the goal)
8. The exact file format template to follow
9. Instruction: "Write all 20 files with THOROUGH implementation details"

**Generation time:** ~22-25 minutes per subagent (ran in parallel)
**Output:** 20 files per agent, ~12-20KB each, totaling ~245KB (Agent A) and ~258KB (Agent B)

### What makes these plans effective

**Real example from Agent A Day 01** (the actual file that was executed):

```markdown
# Agent A — Day 01: Repo Init & Data Model Contracts

## Mission
Establish the repository skeleton and define every shared data model and protocol
interface so that both agents build against the same contracts from day one.

## Context
This is the very first day of the sdk-scaffolder project. Nothing exists yet.
Agent A and Agent B are PAIRING today. Agent B will handle pyproject.toml,
.gitignore, Makefile skeleton, and config.py. Agent A owns the data models
in models.py and the protocol interfaces.

## Prerequisites
- Python 3.10+ installed
- lexichunk installable via pip
- Git initialized in the repo root

## Checklist
- [ ] Create directory structure: src/scaffolder/, all sub-packages with __init__.py
- [ ] Write src/scaffolder/__init__.py with package version
- [ ] Write src/scaffolder/models.py with all data classes and protocols
- [ ] Write stub __init__.py for every sub-package
- [ ] Verify imports work: python -c "from scaffolder.models import Document, Chunk"
- [ ] Coordinate with Agent B on pyproject.toml and config.py field names

## Implementation Details

### Data Models (src/scaffolder/models.py)
Use dataclasses with __slots__ for performance. Use typing.Protocol for interfaces.

[...then provides exact Python code for every dataclass, every enum,
every Protocol, with field names, types, and docstrings...]
```

**Real example from Agent B Day 07** (adapting to Agent A's real code):

```markdown
## Prerequisites
- src/scaffolder/dashboard/page_compare.py stub exists (Day 5)
- src/scaffolder/chunking/pipeline.py with ChunkingPipeline class (Agent A, Day 3)
- src/scaffolder/fixtures/__init__.py with FixtureManager (Agent A, Day 2)
- src/scaffolder/models.py with Document, Chunk, ChunkSet (Agent A, Day 1)
```

The prerequisites explicitly list which files come from the OTHER agent and which day they were created. This is critical — when Agent B reads Day 7, it knows to check that Agent A's Day 3 is complete in STATE.md before proceeding.

### Key principle: plans must be specific enough to code from

**Bad plan detail:**
```
Implement the embedding pipeline with caching.
```

**Good plan detail (what we actually wrote):**
```
Create EmbeddingPipeline class with:
- __init__(self, model_name: str = "all-MiniLM-L6-v2", cache_dir: str = ".cache/embeddings")
- embed_chunks(self, chunks: list[Chunk]) -> np.ndarray
  → calls self.model.encode(texts, show_progress_bar=True, batch_size=32)
  → caches result: hash(model_name + sorted(texts)) → .npy file
- embed_query(self, query: str) -> np.ndarray
  → single text, no caching (queries are fast)

Cache implementation:
- Key: hashlib.sha256(f"{model_name}:{text}".encode()).hexdigest()[:16]
- Store: np.save(cache_dir / f"{key}.npy", embeddings)
- Load: np.load(cache_dir / f"{key}.npy") if exists
```

### What each day file costs

Each file is 12-20KB of markdown. 20 files × 2 agents = 40 files, ~500KB total. This sounds like a lot, but each file is read exactly once (by one agent, on one day). The investment pays for itself immediately in reduced agent confusion and rework.

---

## Phase 5: Set Up Orchestration Files

Five files were created. Here's what each actually looks like in practice, with real data from this session.

### `plans/STATE.md` — Progress Tracker

**What it looked like after Day 8 of execution:**

```markdown
## Agent A — Pipeline & Eval
| Day | Status | Completed | Notes |
|-----|--------|-----------|-------|
| 01  | completed | 2026-03-18 | PAIR day — models.py, protocol interfaces |
| 02  | completed | 2026-03-18 | FixtureManager + 5 legal documents + 13 tests |
| 03  | completed | 2026-03-18 | ChunkingPipeline + 4 strategy wrappers + 23 tests |
| 04  | completed | 2026-03-18 | Structural metrics: fragmentation, definition preservation |
| 05  | completed | 2026-03-18 | Hierarchy depth + chunk CV, __main__.py CLI, make benchmark |
| 06  | not_started | | |
...

## Agent B — UI & Reports
| Day | Status | Completed | Notes |
|-----|--------|-----------|-------|
| 01  | completed | 2026-03-18 | PAIR day — pyproject.toml, config.py, Makefile |
| 02  | completed | 2026-03-18 | Config system: validation, YAML, env vars, 26 tests |
| 03  | completed | 2026-03-18 | Query schema, 8 queries, queries.py loader |
| 04  | completed | 2026-03-18 | 22 queries across all 5 fixtures, CLI reporter |
| 05  | completed | 2026-03-18 | JSON export, CLI polish, Streamlit skeleton |
| 06  | completed | 2026-03-18 | Voyage adapter with rate limiting, 12 tests |
| 07  | completed | 2026-03-18 | Streamlit compare page with side-by-side chunks |
| 08  | completed | 2026-03-18 | Chunk viewer: clause-type colours, term badges |
| 09  | not_started | | Depends on Agent A RetrievalSimulator (Day 8) |
...
```

**Design decision:** Each agent updates ONLY their own section. This prevents merge conflicts. The Notes column captures what was actually delivered (not what was planned), making it useful for session recovery.

### `plans/HANDOFF.md` — Delivery Log

**Real entries from this session:**

```markdown
### Agent A → Agent B | Day 03 Complete
**What's ready:** ChunkingPipeline with 4 strategies and strategy registry.
**Files:** src/scaffolder/chunking/strategies.py, pipeline.py, __init__.py
**Import paths:**
- from scaffolder.chunking import ChunkingPipeline, get_all_strategies, get_strategy
- from scaffolder.chunking import LexiChunkStrategy, RCTSStrategy, ...
**Usage:** pipeline = ChunkingPipeline(get_all_strategies()); results = pipeline.run(docs)
**Breaking changes:** None. Agent B's Streamlit Day 7 dependency is now unblocked.
```

```markdown
### Agent B → Agent A | Day 06 Complete
**What's ready:** Voyage AI embedding adapter with rate limiting, Embedder protocol
**Files:** src/scaffolder/embedding/__init__.py, voyage.py, tests/test_voyage.py
**Import paths:**
- from scaffolder.embedding import Embedder, create_embedder
- from scaffolder.embedding.voyage import VoyageEmbedder
**Breaking changes:** embedding/__init__.py now has Embedder protocol. Agent A's
local embedder should implement: model_name (property), dimension (property),
embed(texts), embed_query(text).
```

**Critical detail:** The "Breaking changes" field is essential. When Agent B's Day 6 added the `Embedder` protocol to `embedding/__init__.py`, it changed the interface Agent A would need to implement. Without this note, Agent A might build an incompatible local embedder.

### `plans/ISSUES.md` — Cross-Agent Bug Queue

Created mid-session when we observed Agent B discovering API mismatches but having no structured way to report them. The format:

```markdown
### ISSUE-001 | BUG: StrategyName enum values don't match config strings
**Filed by:** Agent B
**Assigned to:** Agent A
**Found on:** Day 07
**Status:** open
**File(s):** src/scaffolder/models.py
**Problem:** Config uses "lexichunk" but StrategyName enum is LEXICHUNK
**Impact:** Streamlit strategy dropdown breaks when trying to match config to enum
**Suggested fix:** Add from_config_string() classmethod on StrategyName enum
**Resolution:** [filled in by Agent A when fixed]
```

**Why this was added mid-session:** We observed Agent B reading Agent A's code on Day 7 and discovering mismatches. Without ISSUES.md, Agent B would either silently work around it (hiding a bug) or mention it in HANDOFF.md (wrong file — HANDOFF is for deliveries, not bugs). ISSUES.md gives problems their own structured home.

### `plans/ORCHESTRATOR.md` — Execution Protocol

The full loop, as it evolved during the session:

```
0. READ ISSUES.md → fix assigned issues FIRST
1. READ STATE.md → find next not_started day, check dependencies
2. IF dependency not met → skip to next non-blocked day, write blocker
3. READ daily plan file → self-contained work order
4. CHECK prerequisites → verify files exist, check HANDOFF.md
5. EXECUTE checklist → work through tasks sequentially
5b. CROSS-VALIDATE → smoke-test other agent's modules you depend on
6. VERIFY acceptance criteria → run listed commands
7. POST-DAY: make lint && make test → update STATE.md → write HANDOFF.md → commit
8. LOOP → back to step 0
```

**Step 0 and Step 5b were added mid-session.** The original loop (steps 1-8) didn't include cross-validation. When we observed Agent B finding API mismatches without a structured reporting mechanism, we added ISSUES.md (step 0) and cross-validation (step 5b). This was committed as `f710c2c`.

### `plans/BOOTSTRAP.md` — Pre-flight Checklist

Added when we realized agents would fail on Day 1 if Python, LexiChunk, or LangChain weren't installed. Contains:
- Python version check
- `pip install lexichunk` verification
- `pip install langchain-text-splitters` verification
- How to get the 5 fixture documents (from LexiChunk repo or PyPI install)
- What Day 1 creates (so agents know the expected state after bootstrapping)

### `tasks/lessons.md` — Shared Learning Log

Referenced in CLAUDE.md's "Self-Improvement Loop" workflow. Both agents write here when they discover patterns. Format:

```markdown
### [DATE] — [SHORT TITLE]
**Agent:** A | B
**Trigger:** What went wrong or what was discovered
**Lesson:** The rule to follow going forward
**Applies to:** Which files/modules/patterns this affects
```

In this session, lessons.md stayed empty because the agents haven't hit major corrections yet. It becomes valuable in later sessions when patterns emerge.

---

## Phase 6: Configure CLAUDE.md

### What CLAUDE.md must contain for agent-first development

The CLAUDE.md in this project has these sections:

1. **Project Context** — one paragraph explaining what the scaffolder does and its key claim
2. **Build & Dev Commands** — exact `make` targets (test, lint, benchmark, benchmark-embed, report, dashboard) plus `pip install -e ".[extra]"` variants
3. **Architecture** — directory tree, data flow one-liner, strategies, embedding models, metrics list, query annotation format
4. **Agent Execution Model** — the core section:
   - Pointers to all orchestration files (STATE, HANDOFF, ISSUES, ORCHESTRATOR)
   - Two execution modes (two terminals vs one orchestrator with subagents)
   - Agent A and Agent B role definitions with ownership boundaries
   - The day execution loop (13 steps including cross-validation)
   - Coordination rules (pairing days, interface boundary, critical path, ownership)
   - Session recovery protocol
5. **Workflow Orchestration** — personal preferences (plan-first, subagent strategy, self-improvement loop, verification, elegance, autonomous bug fixing)
6. **Task Management** — plan → verify → track → explain → document → capture lessons
7. **Core Principles** — simplicity first, no laziness, minimal impact

### Key CLAUDE.md decisions

- **Build commands must be real and runnable.** Agents run `make lint && make test` after every day. If these don't work, agents stall.
- **Agent identity is NOT in CLAUDE.md.** CLAUDE.md is shared. Agent identity comes from the terminal startup prompt ("You are Agent A...").
- **Workflow preferences are agent-agnostic.** "Enter plan mode for non-trivial tasks" applies to both agents equally.

### What was migrated from a previous project

This repo's CLAUDE.md originally contained Perry document collaboration tool content (Plate.js, TypeScript, React). The workflow sections (plan-first, subagent strategy, self-improvement loop, etc.) were the user's personal preferences and were kept. Everything project-specific (TypeScript commands, Plate.js patterns, Perry references) was replaced.

**Lesson:** If the user has an existing CLAUDE.md from another project, keep the workflow/preference sections and replace the project-specific content. Ask before deleting anything.

---

## Phase 7: Launch & Monitor

### The exact terminal prompts used

**Terminal 1 — Agent A:**
```
You are Agent A (Pipeline & Eval). Your job is to build the LexiChunk evaluation
harness — fixtures, chunking pipeline, embedding pipeline, retrieval simulation,
metrics, and reports.

Read these files in order, then begin autonomous execution:
1. plans/BOOTSTRAP.md — run the pre-flight checks
2. plans/ORCHESTRATOR.md — your execution protocol
3. plans/STATE.md — find your current day

Then read plans/agent-a/day-01.md and start working. After each day, update
STATE.md, write HANDOFF.md if needed, commit with "Agent A Day XX: {title}",
and immediately proceed to the next day. Do not stop until all 20 days are
complete or you hit an unresolvable blocker.

Day 1 is a PAIR day — Agent B will be creating pyproject.toml, config.py,
and Makefile in parallel. You focus on: models.py (data contracts), protocol
interfaces, directory structure, and __init__.py files. Commit your Day 1
work first so Agent B can import from models.py.
```

**Terminal 2 — Agent B:**
```
You are Agent B (UI & Reports). Your job is to build the config system, query
annotations, Voyage adapter, Streamlit dashboard, CLI reporter, and
EXTENSIBILITY.md for the LexiChunk evaluation harness.

Read these files in order, then begin autonomous execution:
1. plans/BOOTSTRAP.md — run the pre-flight checks
2. plans/ORCHESTRATOR.md — your execution protocol
3. plans/STATE.md — find your current day

Then read plans/agent-b/day-01.md and start working. After each day, update
STATE.md, write HANDOFF.md if needed, commit with "Agent B Day XX: {title}",
and immediately proceed to the next day. Do not stop until all 20 days are
complete or you hit an unresolvable blocker.

Day 1 is a PAIR day — Agent A will be creating models.py and directory
structure in parallel. You focus on: pyproject.toml (with all dependency
groups), config.py, Makefile, and .gitignore. Wait for Agent A's commit
before importing from models.py.
```

### Permissions issue (hit immediately)

Both agents immediately started asking for permission on every tool call. Fix:

```
/permissions add Bash(*) Edit(*) Write(*) Read(*) Glob(*) Grep(*)
```

Or permanently in `~/.claude/settings.json`:
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

**This must be done BEFORE walking away.** Otherwise agents stop at the first tool call and wait for human approval.

### Monitoring without interrupting

Check progress by reading files from a third terminal or the orchestrator session:

```bash
# Quick status check
cat plans/STATE.md

# Commit trail
git log --oneline -20

# Any cross-agent issues?
cat plans/ISSUES.md

# What has each agent delivered to the other?
cat plans/HANDOFF.md

# Any lessons learned?
cat tasks/lessons.md
```

---

## Daily Plan File Format — With Real Examples

### The template

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

## Implementation Details

### [Task group name]
[Specific guidance: file paths, class signatures, method signatures,
key patterns, edge cases.]

## Outputs
[Exact list of files created or modified]

## Acceptance Criteria
[Specific commands to run and expected results.]

## Handoff Notes
[What the other agent needs to know. Exact import paths.]
```

### Quality checklist for daily plans

- [ ] **Mission** is one sentence
- [ ] **Context** mentions what the OTHER agent is doing today
- [ ] **Prerequisites** list specific file paths with the day/agent that creates them
- [ ] **Checklist** has 4-8 items (not 1, not 20)
- [ ] **Implementation Details** include actual Python class/method signatures with types
- [ ] **Implementation Details** include import paths the other agent will use
- [ ] **Acceptance Criteria** include runnable commands (`python -c "from scaffolder.X import Y"`, `make test`)
- [ ] **Handoff Notes** include exact import paths and note any breaking changes

---

## Coordination Patterns — What Actually Happened

### Pattern 1: Interface Boundary via models.py

`models.py` was created on Day 1 by Agent A. It defined:
- `Document`, `Chunk`, `ChunkSet`, `StrategyResult`, `BenchmarkResult` (data classes)
- `StrategyName`, `EmbeddingModelName`, `Jurisdiction`, `DocumentType`, `RelevanceGrade` (enums)
- `ChunkingStrategy`, `Embedder` (Protocol interfaces)
- `StructuralMetrics`, `RetrievalMetrics`, `SignificanceResult` (result types)
- `AnnotatedQuery`, `RelevantSection`, `RetrievalHit`, `RetrievalResult` (query types)

After Day 1, Agent B only imports from models.py — never modifies it. Agent A can add fields to dataclasses but must note it in HANDOFF.md.

### Pattern 2: Agent B working ahead on independent tasks

Agent B completed Days 1-6 before Agent A finished Day 5. Agent B's independent work:
- Day 2: Config system (no dependencies)
- Day 3: Query schema + 8 queries (no dependencies)
- Day 4: 14 more queries + CLI reporter (depends only on models.py from Day 1)
- Day 5: JSON export + Streamlit skeleton (depends only on models.py)
- Day 6: Voyage API adapter (depends only on Embedder protocol from Day 1)

Agent B only hit its first dependency on Day 7 (needed Agent A's ChunkingPipeline from Day 3, which was already complete by then).

### Pattern 3: Adapting plans to real implementations

Agent B Day 7 plan assumed `pipeline.chunk(doc, strategy)` API. The real API from Agent A was `get_strategy(name)` returning a strategy object, then `strategy.chunk(text, document_id)` returning a `ChunkSet`. Agent B:
1. Read Agent A's actual `pipeline.py` and `strategies.py`
2. Discovered the API mismatch
3. Adapted the Streamlit code to use the real API
4. Did NOT file an issue (the plan was wrong, not the code)

**Lesson:** Plans are guides. Real code is truth. Agents should always read the actual implementation before coding against it.

### Pattern 4: HANDOFF entries as living documentation

Each HANDOFF entry became a mini-API doc. When Agent B needed Agent A's ChunkingPipeline on Day 7, it could read the Day 3 HANDOFF entry:
```
**Import paths:**
- from scaffolder.chunking import ChunkingPipeline, get_all_strategies, get_strategy
**Usage:** pipeline = ChunkingPipeline(get_all_strategies()); results = pipeline.run(docs)
```

This was faster than reading the full source code and served as the de facto API documentation during development.

---

## Failure Modes & Fixes — From This Session

### Agents keep asking for permission
**When it happened:** Immediately on launch
**Fix:** `/permissions add Bash(*) Edit(*) Write(*) Read(*) Glob(*) Grep(*)` in each terminal
**Prevention:** Set permissions BEFORE pasting the identity prompt

### Plans don't match real APIs
**When it happened:** Agent B Day 7 (Streamlit compare page)
**What happened:** Plan assumed `pipeline.chunk(doc, strategy)`, real API was `get_strategy(name).chunk(text, doc_id)`
**How agent handled it:** Read real source code, adapted implementation
**Lesson:** This is expected and healthy. Plans are written before code exists. Agents should always verify against real implementations.

### No mechanism for agents to report bugs in each other's code
**When it happened:** Observed during Agent B Day 7
**What happened:** Agent B found enum naming mismatches but had no structured way to report them
**Fix:** Created `plans/ISSUES.md` with severity levels (BLOCKER/BUG/WARN/REQUEST) and added step 0 (check issues) and step 5b (cross-validate) to the execution loop
**Prevention:** Include ISSUES.md in the initial setup, not as an afterthought

### Agent B runs far ahead, then hits dependency wall
**When it happened:** Agent B completed Day 8 while Agent A was on Day 5
**What happened:** Agent B Day 9 depends on Agent A Day 8 (RetrievalSimulator)
**How to handle:** Agent B should skip to the next non-blocked day. If all remaining days are blocked, work on tests, documentation, or polish for completed days.

### Two terminals both trying to modify the same file
**Prevention by design:** Agents own different directories. The only shared files are append-only (STATE.md, HANDOFF.md, ISSUES.md, lessons.md). On the rare occasion both agents need to modify the same file (pairing days), the plan specifies who commits first.

---

## The Conversation Flow That Produced This

This section documents the exact sequence of interactions between the user and the orchestrator Claude that produced the entire setup. Future sessions can follow this flow.

### Turn 1: User provides the goal
> "We are now planning to create the scaffolding/test interface for my new SDK, https://github.com/emmcygn/lexichunk. I want to understand the repo, see what's inside, and come up with a discussion as to how we can create a high signal scaffolding to test the effectiveness of the SDK"

**Orchestrator action:** Launched Explore subagent to thoroughly crawl the LexiChunk repo.

### Turn 2: User provides requirements
> "1. demos to potential users... 2. include an actual embedding step... 3. use 5 existing fixtures but write an extensibility roadmap... 4. all three [output formats]... 5. live in its own repo"
> "I also want you to do this against real web researched best practices for production legaltech RAG systems"

**Orchestrator action:** Launched research subagent for legaltech RAG best practices.

### Turn 3: User provides prior research
> "Read these as well [two compass artifact files]"

**Orchestrator action:** Read both files, synthesized with research findings.

### Turn 4: User adds interactive tool idea
> "Additional ideas include an interactive research tool — Streamlit or Gradio app"

**Orchestrator action:** Incorporated into proposal, recommended Streamlit over Gradio (multi-page dashboard > simple demo).

### Turn 5: Proposal v1 created
Orchestrator created `tasks/proposal.html` with 12 sections, Mermaid diagrams, tech stack justification, grounding against research.

### Turn 6: User asks for team scaling
> "Say a team of 3 engineers had 3 months to build this, how would you tackle this?"

**Orchestrator action:** Created `tasks/ROADMAP.md` (3-engineer/3-month plan).

### Turn 7: User asks for middle ground
> "If we were to make a middle ground between the 2 plans of 2 engineers over 4 weeks?"

**Orchestrator action:** Created `tasks/proposal-v2.html` with scoped-down version, explicit cuts/keeps, swim-lane tables.

### Turn 8: User requests atomic daily plans
> "Create atomic weekly plans for each engineer with individual checklists and self-contained loops. 2 folders, agent A and agent B, days 1-20 of individual files"

**Orchestrator action:** Launched 2 parallel subagents (one per agent), each generating 20 daily plan files. ~25 min each, ran simultaneously.

### Turn 9: User requests orchestration infrastructure
> "Spin up CLAUDE.md's instructions, we should have a lessons and tracking file... I'm aiming for being able to spin two separate terminals and have the agents work non-stop until all 20 days are done"

**Orchestrator action:** Created STATE.md, HANDOFF.md, ORCHESTRATOR.md, BOOTSTRAP.md, lessons.md. Updated CLAUDE.md with agent execution model.

### Turn 10: User asked about two terminals vs one orchestrator
> "Would it be better to have one claude in the terminal spin off two subagents?"

**Orchestrator analysis:** Two terminals is better — each gets full context window, independent recovery, direct git access. One orchestrator + subagents has timeout limits, can't commit independently, single point of failure.

### Turn 11: User launches agents
> "They're running, but they keep asking for permission for everything"

**Fix:** `/permissions add Bash(*) Edit(*) Write(*) Read(*) Glob(*) Grep(*)`

### Turn 12: Orchestrator observes cross-validation gap
> "I think they're not fully learning how to fix each other's work"

**Orchestrator action:** Created ISSUES.md, added step 0 (check issues) and step 5b (cross-validate) to the execution loop in both ORCHESTRATOR.md and CLAUDE.md.

### Turn 13: User requests this guide
> "Create an agents-orchestration-guide.md. I want future claude code sessions to be able to repeat everything we've done so far"

---

## Exact Prompts Used

### Subagent prompt for generating Agent A's 20 daily plans

The prompt was ~3000 words and included:
- Full project context paragraph
- Complete LexiChunk API surface (every class, method, property)
- Complete repo structure (every directory and file)
- All 13 tech stack packages with versions
- Agent A's ownership list (fixtures, chunking, embedding/local, retrieval, metrics, reports, tests)
- Agent B's ownership list (so Agent A knows what NOT to build)
- Shared data model definitions (exact Python dataclass code)
- Day-by-day breakdown (20 entries, 1-3 sentences each describing goal)
- The file format template
- "Write all 20 files with THOROUGH implementation details"

The subagent prompt for Agent B was similar but with:
- Agent B's ownership list
- Streamlit-specific instructions (page layouts, component patterns, session state)
- Query annotation schema and example YAML
- Voyage API adapter details
- EXTENSIBILITY.md section outline

### Identity prompt structure (for terminal launch)

```
You are Agent {A|B} ({Role Name}). Your job is to build {specific list of what they own}.

Read these files in order, then begin autonomous execution:
1. plans/BOOTSTRAP.md — run the pre-flight checks
2. plans/ORCHESTRATOR.md — your execution protocol
3. plans/STATE.md — find your current day

Then read plans/agent-{a|b}/day-01.md and start working. After each day,
update STATE.md, write HANDOFF.md if needed, commit with
"Agent {A|B} Day XX: {title}", and immediately proceed to the next day.
Do not stop until all 20 days are complete or you hit an unresolvable blocker.

Day 1 is a PAIR day — {specific coordination instructions for Day 1}.
```

---

## Checklist: Before You Walk Away

- [ ] Both terminals have identity prompts pasted and running
- [ ] Permissions are set to auto-allow in both terminals
- [ ] `plans/STATE.md` exists with all days listed and dependencies noted
- [ ] `plans/ORCHESTRATOR.md` exists with the execution loop
- [ ] `plans/HANDOFF.md` exists (empty, ready for entries)
- [ ] `plans/ISSUES.md` exists (empty, ready for entries)
- [ ] `plans/BOOTSTRAP.md` exists with pre-flight checks
- [ ] `tasks/lessons.md` exists (empty, ready for entries)
- [ ] All daily plan files exist (N files per agent)
- [ ] `CLAUDE.md` references all orchestration files and has the agent execution model
- [ ] Day 1 pairing instructions are explicit in both terminal prompts
- [ ] Dependencies between agents are noted in STATE.md Notes column
- [ ] Git repo is initialized with an initial commit containing all plans

### Realistic Expectations
- Agents complete roughly 1 day per 15-30 minutes (varies by complexity)
- In 2 hours: expect 4-8 days complete per agent (validated in this session: Agent A did 5, Agent B did 8)
- Agent B (UI/Reports) will typically run 2-3 days ahead of Agent A (Pipeline) due to fewer upstream dependencies
- The agents WILL discover mismatches between plans and reality — this is healthy
- The agents WILL adapt their implementations to match actual code — this is correct
- ISSUES.md may stay empty if the interface boundary (models.py) is clean
- Check `git log --oneline` and `plans/STATE.md` to see progress

---

## Reproducing This Pattern for a New Project

1. **Start a fresh Claude Code session** in your project repo
2. **Research phase:** "Explore [target repo/codebase]. I need to understand [what it does, API surface, tests, dependencies]." If the domain requires it: "Research best practices for [domain]."
3. **Context phase:** Read any existing research docs, PRDs, or prior work.
4. **Proposal phase:** "Create an HTML proposal with phases, system architecture (Mermaid), pipeline flow table, tech stack with justifications, tradeoffs, and success criteria."
5. **Scope phase:** "If we had N engineers and M weeks, how would you build this? Create a proposal-v2 with explicit cuts/keeps and week-by-week swim lanes."
6. **Planning phase:** "Create atomic daily plans for each engineer in `plans/agent-a/` and `plans/agent-b/`. Each day gets its own file with mission, context, prerequisites, checklist, implementation details, outputs, acceptance criteria, and handoff notes."
7. **Orchestration phase:** "Set up plans/STATE.md, plans/HANDOFF.md, plans/ISSUES.md, plans/ORCHESTRATOR.md, plans/BOOTSTRAP.md, and tasks/lessons.md."
8. **CLAUDE.md phase:** "Update CLAUDE.md with agent execution model, coordination rules, and build commands."
9. **Commit:** `git add . && git commit -m "Initial project setup with plans and orchestration"`
10. **Launch:** Open N terminals, paste identity prompts, set permissions, walk away.
11. **Monitor:** Check `plans/STATE.md` and `git log --oneline` periodically.

The entire setup (steps 1-9) takes one Claude Code session of ~1-2 hours. The execution (steps 10-11) runs autonomously after that.
