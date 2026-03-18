# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

**LexiChunk Scaffolder** — an evaluation harness and interactive demo proving that [LexiChunk](https://github.com/emmcygn/lexichunk) (a legal document chunking SDK) measurably improves RAG retrieval quality over general-purpose alternatives like LangChain's RecursiveCharacterTextSplitter.

- **Source layout:** `src/scaffolder/` (Python 3.10+, setuptools via `pyproject.toml`)
- **SDK under test:** `lexichunk` (pip-installable, zero-dependency legal chunking for RAG)
- **Outputs:** CLI (rich), JSON, HTML (Jinja2), Streamlit dashboard
- **Key claim to prove:** LexiChunk improves retrieval P@5 by 20%+ vs RCTS with statistical significance

## Build & Dev Commands

```bash
make test              # pytest + pytest-cov (80% minimum)
make lint              # ruff check + mypy --strict
make benchmark         # structural metrics only (no embeddings, fast)
make benchmark-embed   # full eval: structural + retrieval with embeddings
make report            # generate HTML report in results/
make dashboard         # launch Streamlit app on localhost:8501
```

Run a single test:
```bash
python -m pytest tests/test_metrics.py -v
python -m pytest tests/test_chunking.py::test_lexichunk_strategy -v
```

Install extras:
```bash
pip install -e ".[local]"       # sentence-transformers + faiss-cpu
pip install -e ".[voyage]"      # Voyage Law 2 API
pip install -e ".[dashboard]"   # Streamlit + Plotly
pip install -e ".[all]"         # everything
pip install -e ".[dev]"         # ruff, mypy, pytest
```

## Architecture

```
src/scaffolder/
├── config.py          # BenchmarkConfig dataclass — all toggles
├── models.py          # Document, Chunk, ChunkSet, BenchmarkResult (shared contracts)
├── fixtures/          # FixtureManager + 5 legal documents (.txt)
├── chunking/          # ChunkingPipeline + 4 strategy wrappers
├── embedding/         # EmbeddingPipeline (local) + Voyage adapter (toggled)
├── retrieval/         # FAISS VectorIndex + RetrievalSimulator
├── metrics/           # structural.py, retrieval.py, statistical.py
├── reporting/         # CLI (rich), JSON, HTML (Jinja2 template)
└── dashboard/         # Streamlit app (2 pages: compare + retrieval)
```

**Data flow:** Fixtures → ChunkingPipeline (4 strategies) → StructuralMetrics → EmbeddingPipeline → FAISS Index → RetrievalSimulator → RetrievalMetrics → Reports/Dashboard

**Strategies compared:** LexiChunk (clause-aware), RecursiveCharacterTextSplitter (512), sentence-split, fixed-size (512 tokens)

**Embedding models:** all-MiniLM-L6-v2 (free), bge-base-en-v1.5 (free), voyage-law-2 (paid, toggled via `config.enable_voyage`)

**Metrics:** Clause fragmentation rate, definition preservation, cross-ref resolution, hierarchy depth (structural); P@k, R@k, MRR, NDCG@10, DRM rate (retrieval); paired t-tests (statistical)

**Query annotations:** YAML files in `queries/` with graded relevance (exact=3, same_section=2, related=1) per fixture document.

## Agent Execution Model

This repo is built by **two AI agents working in parallel** with self-contained daily plans. All implementation is agent-first — Claude Code IS the engineering team.

### Agent A — Pipeline & Eval
**Owns:** FixtureManager, ChunkingPipeline, EmbeddingPipeline (local), FAISS indexing, RetrievalSimulator, all metrics, statistical testing, CLI + JSON output, HTML report, tests.
**Plans:** `plans/agent-a/day-01.md` through `day-20.md`

### Agent B — UI & Reports
**Owns:** Config system, Makefile, query annotations (YAML), Voyage API adapter, Streamlit dashboard, CLI reporter extensions, EXTENSIBILITY.md, deployment.
**Plans:** `plans/agent-b/day-01.md` through `day-20.md`

### How to Execute a Day

1. Read the day file (e.g., `plans/agent-a/day-07.md`) — it is fully self-contained
2. Check **Prerequisites** — verify the files/modules listed actually exist
3. Work through the **Checklist** sequentially, using **Implementation Details** for specifics
4. Validate against **Acceptance Criteria** (commands to run, expected results)
5. Read **Handoff Notes** to understand what the other agent or next day depends on

### Agent Coordination Rules

- **Day 1, 18, 20 are pairing days** — both agents work on the same files. Coordinate through `models.py` (the shared contract).
- **`models.py` is the interface boundary.** Agent A produces data in these shapes. Agent B consumes them. If a model changes, both agents must update.
- **Agent A is the critical path** for pipeline components (chunking → embedding → retrieval → metrics). Agent B can build Streamlit against the model contracts before Agent A's implementations land.
- **Agent B can work ahead** on query annotations, config, Streamlit layout, and EXTENSIBILITY.md at any time — these have no upstream dependency after Day 1.
- **Never modify the other agent's owned files** without noting it in handoff. If you need a change in a file you don't own, describe what you need in handoff notes.

### Agent Self-Verification

After completing any day's work:
```bash
make lint              # ruff + mypy must pass
make test              # all tests green, coverage holds
make benchmark         # structural pipeline still works (fast check)
```
If any of these fail, fix before moving to the next day. Do not accumulate broken state.

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
- Run `make lint` after every stage — zero ruff/mypy errors
- Run `make test` after every stage — all tests must pass
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
