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
| 02  | completed | 2026-03-18 | FixtureManager + 5 legal documents + 13 tests |
| 03  | completed | 2026-03-18 | ChunkingPipeline + 4 strategy wrappers + registry + 23 tests |
| 04  | completed | 2026-03-18 | Structural metrics: fragmentation, definition preservation, cross-ref resolution + 12 tests |
| 05  | completed | 2026-03-18 | Hierarchy depth + chunk CV metrics, __main__.py CLI, make benchmark e2e |
| 06  | completed | 2026-03-18 | EmbeddingPipeline + SentenceTransformerAdapter + disk cache + 12 tests |
| 07  | completed | 2026-03-18 | VectorIndex (FAISS), IndexRegistry, build_all_indices + 14 tests |
| 08  | completed | 2026-03-18 | RetrievalSimulator + query bridge + relevance matching + 10 tests |
| 09  | completed | 2026-03-18 | P@k, R@k, MRR, NDCG@10, DRM rate + compute_retrieval_metrics + 21 tests |
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
| 02  | completed | 2026-03-18 | Config system complete: validation, YAML, env vars, scaffolder.yaml.example, 26 tests |
| 03  | completed | 2026-03-18 | Query schema, 8 queries (uk_sa + us_msa), queries.py loader |
| 04  | completed | 2026-03-18 | 22 queries across all 5 fixtures, CLI reporter, test_queries.py |
| 05  | completed | 2026-03-18 | JSON export, CLI polish, Streamlit skeleton (3 pages + components) |
| 06  | completed | 2026-03-18 | Voyage adapter with rate limiting, Embedder protocol, 12 tests |
| 07  | completed | 2026-03-18 | Streamlit page_compare: fixture/upload/paste, side-by-side chunks, metrics |
| 08  | completed | 2026-03-18 | Chunk viewer: clause-type colours, term badges, hierarchy, size chart |
| 09  | completed | 2026-03-18 | Retrieval page stub with query browser, ready for RetrievalSimulator |
| 10  | not_started | | Depends on Agent A retrieval metrics (Day 9) |
| 11  | completed | 2026-03-18 | Dashboard polish: CSS, cache mgmt, error helpers, session invalidation |
| 12  | not_started | | Depends on Agent A retrieval metrics (Day 9) |
| 13  | not_started | | Depends on Days 10, 12 |
| 14  | completed | 2026-03-18 | Deployment: requirements-dashboard.txt, compat.py, .streamlit/config.toml, streamlit_app.py |
| 15  | completed | 2026-03-18 | EXTENSIBILITY.md outline + sections 1-2 |
| 16  | completed | 2026-03-18 | EXTENSIBILITY.md complete (8 sections) |
| 17  | completed | 2026-03-18 | Edge case hardening: upload validation, encoding, size limits |
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
| `src/scaffolder/config.py` | Agent B | 02 | Full config: validation, YAML merging, env vars, load(), to_dict() |
| `queries/*.yaml` | Agent B | 04 | 22 queries across all 5 fixtures, 2 cross-doc contamination |
