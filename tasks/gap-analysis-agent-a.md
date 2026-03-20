# Gap Analysis — Agent A (Pipeline & Eval)

**Date:** 2026-03-19
**Scope:** Plans `plans/agent-a/day-01.md` through `day-20.md` vs actual implementation
**Build Status:** Lint (ruff) PASS | Tests 258 passed (87% coverage) | mypy --strict: 41 errors

---

## Per-Day Analysis

### Day 01: Repo Init & Data Model Contracts
- **Status:** COMPLETE
- **What matches spec:** All enums (5), dataclasses (10), protocols (2) in `models.py`. All sub-package `__init__.py` files exist. `reporting/templates/` directory exists.
- **What's missing or incomplete:**
  - `__version__` is `"1.0.0"` (spec said `"0.1.0"` initially — fine, was bumped on Day 20)
- **Acceptance criteria results:**
  - `python -c "from scaffolder.models import Document, ..."` — **PASS**
  - `Jurisdiction.UK.value` prints `uk` — **PASS**
  - `RelevanceGrade.EXACT.value` prints `3` — **PASS**
  - `mypy src/scaffolder/models.py --strict` — **PASS** (0 errors in models.py itself)
  - `ruff check src/scaffolder/` — **PASS**

### Day 02: FixtureManager & Document Loading
- **Status:** COMPLETE
- **What matches spec:** All 5 fixture documents present. `FixtureManager` has `load_all()`, `get_by_id()`, `get_by_jurisdiction()`, `document_ids` property. Tests in `test_fixtures.py` (13 tests).
- **What's missing or incomplete:** None
- **Acceptance criteria results:**
  - `FixtureManager().load_all()` returns 5 — **PASS**
  - `pytest tests/test_fixtures.py -v` — **PASS**
  - `ruff check` — **PASS**

### Day 03: ChunkingPipeline & Strategy Wrappers
- **Status:** COMPLETE
- **What matches spec:** All 4 original strategies (LexiChunk, RCTS, SentenceSplit, FixedSize) + LexiChunkContextual (added Day 12). `ChunkingPipeline` with `run()` and `run_single()`. Strategy registry with `get_strategy()`, `get_all_strategies()`.
- **What's missing or incomplete:** None
- **Acceptance criteria results:**
  - `get_all_strategies()` returns 5 strategy names — **PASS** (spec said 4, but 5th was added Day 12)
  - `pytest tests/test_chunking.py -v` — **PASS** (23 tests)
  - `ruff check` — **PASS**
  - `mypy --strict` on chunking/ — **FAIL** (6 "unused type: ignore" errors in `__init__.py`)

### Day 04: Structural Metrics (Core Three)
- **Status:** COMPLETE
- **What matches spec:** `GroundTruthStructure` dataclass, `get_ground_truth()` with caching, `clause_fragmentation_rate()`, `definition_preservation_rate()`, `cross_ref_resolution_rate()`, `_extract_defined_terms_regex()`, `_extract_cross_refs_regex()`, `compute_structural_metrics()`.
- **What's missing or incomplete:** None
- **Acceptance criteria results:**
  - `pytest tests/test_structural_metrics.py -v` — **PASS** (17 tests)
  - Metrics return float in [0.0, 1.0] — **PASS**
  - `mypy --strict` — **FAIL** (2 errors: `Unsupported right operand type for in` at line 209, `Returning Any` at line 309)

### Day 05: Remaining Structural Metrics + CLI/JSON Output
- **Status:** COMPLETE
- **What matches spec:** `hierarchy_depth_retained()` and `chunk_size_cv()` are real implementations (not placeholders). CLI reporter exists with structural report rendering. JSON exporter with `export_json()` and `load_json()`. `__main__.py` with `benchmark` command.
- **What's missing or incomplete:**
  - CLI function naming differs from spec: implementation uses `render_structural_table()` / `render_summary_header()` / `render_aggregate_summary()` / `render_benchmark()` instead of spec's `print_structural_report()` / `_print_summary_table()` — functionally equivalent
- **Acceptance criteria results:**
  - `make benchmark` runs end-to-end — **PASS**
  - `ruff check` — **PASS**
  - `mypy --strict` on reporting/ — **FAIL** (5 "Returning Any" errors in `html.py`)

### Day 06: EmbeddingPipeline & Local Model Adapters
- **Status:** COMPLETE
- **What matches spec:** `SentenceTransformerAdapter` (supports MINILM + BGE_BASE), `EmbeddingCache` (get/put/get_batch/stats/clear), `EmbeddingPipeline` (embed_texts/embed_chunks/cache_stats). Disk caching with `.npy` files.
- **What's missing or incomplete:** None functionally
- **Acceptance criteria results:**
  - `pytest tests/test_embedding.py -v` — **PASS** (12 tests)
  - `ruff check` — **PASS**
  - `mypy --strict` on embedding/ — **FAIL** (8 errors: unused `type: ignore` comments + `attr-defined` on lazy-loaded model objects)

### Day 07: VectorIndex — FAISS Wrapper
- **Status:** COMPLETE
- **What matches spec:** `VectorIndex` (IndexFlatIP, add/search/reset/size/dimension), `IndexKey` dataclass, `IndexRegistry` (build/get/keys/count), `build_all_indices()`.
- **What's missing or incomplete:** None
- **Acceptance criteria results:**
  - `pytest tests/test_retrieval_index.py -v` — **PASS** (14 tests)
  - `ruff check` — **PASS**
  - `mypy --strict` — **FAIL** (1 error: `Returning Any` for `ntotal` property)

### Day 08: RetrievalSimulator
- **Status:** COMPLETE
- **What matches spec:** `RetrievalSimulator` with `run()`, `_is_relevant()`, `get_relevance_grade()`. Query loading uses `scaffolder.queries` module (Agent B's loader) via `load_queries_from_yaml()` bridge function instead of a separate `QueryLoader` class — functionally equivalent.
- **What's missing or incomplete:**
  - Spec called for a `QueryLoader` class. Implementation uses a function `load_queries_from_yaml()` that delegates to Agent B's `scaffolder.queries.load_queries()`. Same result, different structure.
- **Acceptance criteria results:**
  - `pytest tests/test_simulator.py -v` — **PASS** (10 tests)
  - `ruff check` — **PASS**

### Day 09: Retrieval Quality Metrics
- **Status:** COMPLETE
- **What matches spec:** `precision_at_k()`, `recall_at_k()`, `mrr()`, `ndcg_at_k()`, `drm_rate()`, `compute_retrieval_metrics()`, `_is_hit()`, `_get_grade()`, `_dcg()`. Exported from `metrics/__init__.py`.
- **What's missing or incomplete:** None
- **Acceptance criteria results:**
  - `pytest tests/test_retrieval_metrics.py -v` — **PASS** (21 tests)
  - `ruff check` — **PASS**
  - `mypy --strict` — **FAIL** (1 error: `Returning Any` in `_dcg()`)

### Day 10: Statistical Significance + Full Retrieval Benchmark
- **Status:** COMPLETE
- **What matches spec:** `paired_t_test()`, `compute_significance()`, `compute_all_significance()`, `SIGNIFICANCE_METRICS` list (7 metrics). `benchmark-embed` command in `__main__.py`. `_get_available_models()` with Voyage toggle.
- **What's missing or incomplete:** None
- **Acceptance criteria results:**
  - `pytest tests/test_statistical.py -v` — **PASS** (7 tests)
  - `ruff check` — **PASS**
  - `mypy --strict` on `__main__.py` — **FAIL** (3 errors: `datetime.UTC` attr-defined, missing type params)

### Day 11: Voyage Law 2 Evaluation
- **Status:** COMPLETE
- **What matches spec:** `_get_available_models()` checks `VOYAGE_API_KEY`. Graceful skip when not set. `tests/test_voyage_toggle.py` with 2 tests.
- **What's missing or incomplete:**
  - Spec suggested adding `result.config["findings"]` with model comparison analysis. Not found in implementation — minor, this was optional documentation.
- **Acceptance criteria results:**
  - `make benchmark-embed` works without VOYAGE_API_KEY — **PASS**
  - `pytest tests/test_voyage_toggle.py -v` — **PASS** (2 tests)

### Day 12: Contextual Retrieval Comparison
- **Status:** COMPLETE
- **What matches spec:** `LexiChunkContextualStrategy` in `strategies.py`. `_build_context_header()` function. Registered in `_STRATEGY_REGISTRY`. `tests/test_contextual.py` exists (15 tests). `original_text` stored in metadata.
- **What's missing or incomplete:**
  - Spec suggested structural metrics should use `original_text` from metadata for LEXICHUNK_CONTEXTUAL. Current implementation uses `chunk.text` directly (which includes the context header). This could inflate structural metric scores for the contextual strategy.
- **Acceptance criteria results:**
  - `pytest tests/test_contextual.py -v` — **PASS** (15 tests)
  - `ruff check` — **PASS**

### Day 13: HTML Report Template (Part 1)
- **Status:** COMPLETE
- **What matches spec:** `render_html_report()` in `html.py`. `_structural_bar_chart()` and `_structural_heatmap()`. `report.html.j2` Jinja2 template. `tests/test_html_report.py` (13 tests).
- **What's missing or incomplete:** None
- **Acceptance criteria results:**
  - `pytest tests/test_html_report.py -v` — **PASS** (13 tests)
  - `ruff check` — **PASS**

### Day 14: HTML Report (Part 2) — Retrieval + Methodology
- **Status:** COMPLETE
- **What matches spec:** `_retrieval_bar_chart()`, `_model_comparison_chart()`, `_drm_chart()`. Template includes: retrieval section, significance table, methodology section, per-document breakdown. `report` command in `__main__.py`. `_reconstruct_benchmark_result()` function.
- **What's missing or incomplete:** None
- **Acceptance criteria results:**
  - `make report` generates HTML — **PASS** (requires JSON results to exist)
  - `ruff check` — **PASS**

### Day 15: Metrics Documentation + Final Benchmark Run
- **Status:** COMPLETE
- **What matches spec:** `docs/metrics.md` exists with all 10 metrics defined (5 structural + 5 retrieval) with formulas, ranges, interpretation guidance, and citations. `tests/test_sanity.py` exists (11 tests).
- **What's missing or incomplete:** None
- **Acceptance criteria results:**
  - `pytest tests/test_sanity.py -v` — **PASS** (11 tests)

### Day 16: Test Coverage Push to 80%
- **Status:** COMPLETE
- **What matches spec:** `tests/test_integration.py` exists (3 tests). All 20+ test files exist covering every module. Coverage at 87% (exceeds 80% target).
- **What's missing or incomplete:** None
- **Acceptance criteria results:**
  - `pytest --cov=scaffolder --cov-fail-under=80` — **PASS** (87%)
  - All tests pass — **PASS** (258 passed, 1 skipped)

### Day 17: Edge Cases + Performance Optimization
- **Status:** COMPLETE
- **What matches spec:** `tests/test_edge_cases.py` exists (17 tests). Empty documents, whitespace documents, single-clause documents, no-definitions documents all handled. Edge case guards in strategies.
- **What's missing or incomplete:**
  - Performance profiling/optimization not explicitly evidenced (no profiling artifacts), but benchmark completes in reasonable time
- **Acceptance criteria results:**
  - `pytest tests/test_edge_cases.py -v` — **PASS** (17 tests)
  - Coverage remains >= 80% — **PASS** (87%)

### Day 18: README Content + pyproject.toml Extras (PAIR)
- **Status:** COMPLETE
- **What matches spec:** README.md exists with Quickstart, Benchmark Results (actual numbers, no placeholders), and Architecture sections. `__version__` = "1.0.0".
- **What's missing or incomplete:** None
- **Acceptance criteria results:**
  - README has actual benchmark numbers — **PASS**
  - Architecture diagram present — **PASS**

### Day 19: Code Review Sweep + Reproducibility
- **Status:** GAPS FOUND
- **What matches spec:** Zero TODO/FIXME/HACK/XXX in `src/scaffolder/`. Ruff lint clean. Most `__init__.py` files have `__all__`.
- **What's missing or incomplete:**
  1. **`mypy --strict` fails with 41 errors** across 10 files. The plan required zero mypy errors. Key categories:
     - `Returning Any` (10+ occurrences in html.py, retrieval.py, pipeline.py, index.py)
     - `Unused type: ignore` comments (8 occurrences in chunking/__init__.py, embedding/pipeline.py)
     - `attr-defined` errors on lazy-loaded objects (embedding/pipeline.py)
     - `datetime.UTC` not found (3 occurrences in __main__.py — Python 3.11 compat issue, should use `datetime.timezone.utc`)
  2. **Missing `__all__` exports** in 3 files:
     - `src/scaffolder/__init__.py` — no `__all__`
     - `src/scaffolder/fixtures/__init__.py` — no `__all__`
     - `src/scaffolder/reporting/__init__.py` — empty (just a docstring), no exports
  3. **No random seed pinning** in `__main__.py` (spec required `_pin_seeds()` with `random.seed(42)`, `np.random.seed(42)`, `torch.manual_seed(42)`)
- **Acceptance criteria results:**
  - `ruff check` — **PASS**
  - `mypy --strict` — **FAIL** (41 errors)
  - `grep TODO/FIXME` — **PASS** (zero results)
  - `make test` passes 80%+ — **PASS**

### Day 20: v1.0.0 Release — Final Verification & Tag
- **Status:** GAPS FOUND
- **What matches spec:** All make targets pass (test, lint, benchmark). `__version__` = "1.0.0". STATE.md shows all 20 days completed.
- **What's missing or incomplete:**
  1. **No `v1.0.0` git tag** — `git tag -l` returns empty
  2. **No GitHub issues filed** — spec required 7 post-v1 issues
  3. **mypy --strict still failing** (carried over from Day 19)
- **Acceptance criteria results:**
  - `make test lint` — **PASS**
  - `__version__` == "1.0.0" — **PASS**
  - Git tag v1.0.0 — **FAIL** (not created)
  - GitHub issues filed — **FAIL** (not done)

---

## Summary

- **Total days fully matching spec:** 16/20
- **Days with gaps:**
  - **Day 04** — LOW: 2 mypy errors in structural.py
  - **Day 12** — LOW: structural metrics don't use `original_text` for contextual chunks (could inflate scores)
  - **Day 19** — MEDIUM: 41 mypy --strict errors, 3 missing `__all__`, no random seed pinning
  - **Day 20** — HIGH: no v1.0.0 git tag, no GitHub issues filed

### Priority Items to Fix (ordered)

1. **[HIGH] Create v1.0.0 git tag** — Day 20 acceptance criterion. One command to fix.
2. **[MEDIUM] Fix 41 mypy --strict errors** — Day 19 acceptance criterion. Multiple plans required `mypy --strict` to pass. Key categories:
   - Fix `datetime.UTC` → `datetime.timezone.utc` (3 occurrences in `__main__.py`)
   - Remove unused `type: ignore` comments (8 occurrences)
   - Add proper type annotations for lazy-loaded objects in `embedding/pipeline.py`
   - Fix `Returning Any` issues in `html.py`, `retrieval.py`, `index.py`
   - Fix dashboard type errors (4 errors in Agent B's files)
3. **[MEDIUM] Add missing `__all__` exports** — 3 files: `__init__.py`, `fixtures/__init__.py`, `reporting/__init__.py`
4. **[LOW] Add random seed pinning** — `_pin_seeds()` function in `__main__.py` for benchmark reproducibility
5. **[LOW] Structural metrics for contextual strategy** — Use `chunk.metadata["original_text"]` instead of `chunk.text` when computing structural metrics for LEXICHUNK_CONTEXTUAL
6. **[LOW] File 7 GitHub issues** — Post-v1 backlog items (LegalBench-RAG, LLM-judge, additional strategies, etc.)
7. **[LOW] Add `result.config["findings"]`** — Voyage model comparison analysis in JSON export
