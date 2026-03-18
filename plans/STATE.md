# Agent State Tracker

Both agents read and write this file. It is the single source of truth for progress.

**Rules:**
- Update YOUR section after completing each day
- Check the OTHER agent's section before starting a new day (for dependency resolution)
- On pairing days (1, 18, 20): check that the other agent is ready before proceeding
- If blocked, write the blocker here — the other agent checks this file at day boundaries

---

## Agent A — Pipeline & Eval

| Day | Status | Completed | Notes |
|-----|--------|-----------|-------|
| 01  | completed | 2026-03-18 | PAIR day — models.py, protocol interfaces, directory structure, all __init__.py |
| 02  | not_started | | |
| 03  | not_started | | |
| 04  | not_started | | |
| 05  | not_started | | |
| 06  | not_started | | |
| 07  | not_started | | |
| 08  | not_started | | Depends on Agent B queries (Day 3-4) |
| 09  | not_started | | |
| 10  | not_started | | |
| 11  | not_started | | Depends on Agent B Voyage adapter (Day 6) |
| 12  | not_started | | |
| 13  | not_started | | |
| 14  | not_started | | |
| 15  | not_started | | |
| 16  | not_started | | |
| 17  | not_started | | |
| 18  | not_started | | PAIR day |
| 19  | not_started | | |
| 20  | not_started | | PAIR day |

### Current Blockers
_(none)_

---

## Agent B — UI & Reports

| Day | Status | Completed | Notes |
|-----|--------|-----------|-------|
| 01  | completed | 2026-03-18 | PAIR day — pyproject.toml, config.py, Makefile, .gitignore, all __init__.py files |
| 02  | not_started | | |
| 03  | not_started | | |
| 04  | not_started | | |
| 05  | not_started | | |
| 06  | not_started | | |
| 07  | not_started | | Depends on Agent A ChunkingPipeline (Day 3) |
| 08  | not_started | | |
| 09  | not_started | | Depends on Agent A RetrievalSimulator (Day 8) |
| 10  | not_started | | Depends on Agent A retrieval metrics (Day 9) |
| 11  | not_started | | |
| 12  | not_started | | Depends on Agent A retrieval metrics (Day 9) |
| 13  | not_started | | |
| 14  | not_started | | |
| 15  | not_started | | |
| 16  | not_started | | |
| 17  | not_started | | |
| 18  | not_started | | PAIR day |
| 19  | not_started | | |
| 20  | not_started | | PAIR day |

### Current Blockers
_(none)_

---

## Shared Artifacts

Track key files that both agents depend on. When these change, note it here.

| File | Last Modified By | Day | What Changed |
|------|-----------------|-----|--------------|
| `src/scaffolder/models.py` | Agent A | 01 | Created all data contracts, enums, protocols (ChunkingStrategy, Embedder) |
| `src/scaffolder/config.py` | Agent B | 01 | Created BenchmarkConfig dataclass with from_yaml, from_env, resolve_paths |
| `queries/*.yaml` | — | — | — |
