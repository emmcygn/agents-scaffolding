# Gap Analysis — Agent B (UI & Reports)

Generated: 2026-03-19
Baseline: All 20 Agent B days marked `completed` in STATE.md

---

## Day-by-Day Analysis

### Day 01: Repo Init, Config System & Makefile (PAIR)
- **Status:** COMPLETE
- **What matches spec:** pyproject.toml, Makefile, .gitignore, config.py stub, all `__init__.py` files, tests/conftest.py, directory structure
- **What's missing or incomplete:**
  - `pyproject.toml` `cov-fail-under` is `0` — spec says `80`. This was noted as intentional ("temporarily at 0%") in HANDOFF but was never raised back to 80.
  - `build-backend` changed from spec's `setuptools.backends._legacy:_Backend` to `setuptools.build_meta` (correct decision, not a gap)
- **Acceptance criteria results:** All pass. Version was later bumped to 1.0.0 per Day 20 plan.

### Day 02: Config System Completion
- **Status:** COMPLETE
- **What matches spec:** BenchmarkConfig with validation, YAML loading with unknown key rejection, env var overrides (full map), `from_env()`, `load()` precedence chain, `resolve_paths()`, `to_dict()`, `ConfigError`, `scaffolder.yaml.example`, VALID_STRATEGIES/VALID_EMBEDDING_MODELS/VALID_OUTPUT_FORMATS frozensets, chunking parameter fields (fixed_chunk_size, rcts_chunk_size, etc.), 26 tests in test_config.py
- **What's missing or incomplete:** None
- **Acceptance criteria results:** All pass

### Day 03: Query Annotation Schema & First 8 Queries
- **Status:** COMPLETE
- **What matches spec:** queries/schema.md, queries/uk_service_agreement.yaml, queries/us_msa.yaml, src/scaffolder/queries.py with `load_queries()`, `load_queries_for_document()`, `AnnotatedQuery`, `RelevantSection` dataclasses, VALID_FAILURE_MODES
- **What's missing or incomplete:** None
- **Acceptance criteria results:** All pass (8+ queries loaded)

### Day 04: Complete Query Annotations & Begin CLI Reporter
- **Status:** COMPLETE
- **What matches spec:** 22 queries across 5 fixtures (spec says 20+), 2 cross-doc contamination queries, CLI reporter with `render_structural_table()`, `render_summary_header()`, colour coding, tests/test_queries.py
- **What's missing or incomplete:**
  - CLI `render_structural_table()` uses `StructuralMetrics` (from models.py) instead of spec's `StructuralResult` — this is correct adaptation to Agent A's models, not a gap
  - Column header says "Hierarchy" instead of spec's "Hierarchy Depth", and "Size CV"/"Avg Chars" columns added vs spec's "Avg Size (tok)"/"Chunks" — minor cosmetic deviation, acceptable
- **Acceptance criteria results:** All pass

### Day 05: JSON Export, CLI Polish & Streamlit Skeleton
- **Status:** COMPLETE
- **What matches spec:** json_export.py with `export_json()`, `export_json_string()`, `load_json()`, CLI `render_aggregate_summary()` and `render_benchmark()`, dashboard/app.py skeleton, page_compare.py stub, page_retrieval.py stub, components.py stubs
- **What's missing or incomplete:** None — stubs later replaced by full implementations
- **Acceptance criteria results:** All pass

### Day 06: Voyage API Adapter
- **Status:** PARTIAL — Embedder protocol location differs from spec
- **What matches spec:** VoyageEmbedder with batching, exponential backoff retry, auth/bad-request non-retry, lazy client init, model_name/dimension properties, embed()/embed_query() methods, VoyageEmbedderError, 12 tests in test_voyage.py
- **What's missing or incomplete:**
  - **`Embedder` protocol class NOT in `embedding/__init__.py`** — spec says to define a `@runtime_checkable` Protocol class there. The actual `__init__.py` only re-exports from `pipeline.py`. The `Embedder` protocol is in `models.py` instead (Agent A put it there on Day 1). This is a spec deviation but functionally equivalent.
  - **`create_embedder()` factory function NOT in `embedding/__init__.py`** — spec defines a factory function. Not implemented. `EmbeddingPipeline` handles model selection directly instead.
- **Acceptance criteria results:** All pass (VoyageEmbedder imports, creates instance, tests pass)

### Day 07: Streamlit Page 1 — Side-by-Side Chunk Comparison
- **Status:** COMPLETE
- **What matches spec:** Document loading (fixture/upload/paste), chunking via strategies, side-by-side display, session state caching, error handling, summary metrics row
- **What's missing or incomplete:**
  - Implementation adapted to actual model API (uses `get_strategy(StrategyName)` instead of spec's `ChunkingPipeline().chunk(doc, strategy)`) — correct adaptation
  - Uses `Document` with enum fields (`Jurisdiction.UK`, `DocumentType.SERVICE_AGREEMENT`) instead of spec's raw strings — correct adaptation
- **Acceptance criteria results:** All pass

### Day 08: Chunk Viewer Component with Clause-Type Colour Coding
- **Status:** COMPLETE
- **What matches spec:** CLAUSE_TYPE_COLORS (24 entries), render_chunk_card() with colour borders/hierarchy/term badges, render_chunk_list() with stats, render_chunk_size_chart() with Plotly, _highlight_terms(), page_compare.py updated to use components
- **What's missing or incomplete:** None
- **Acceptance criteria results:** All pass

### Day 09: Streamlit Page 2 — Retrieval Demo
- **Status:** PARTIAL — Several spec features missing or simplified
- **What matches spec:** Query input (free text + annotated), retrieval pipeline wiring, per-strategy results display, query browser fallback, session state caching
- **What's missing or incomplete:**
  - **No P@k comparison Plotly bar chart** (`_render_metrics_chart()` from spec) — results shown as expanders with scores, not a chart
  - **No metrics table** (`_render_metrics_table()` with MRR/NDCG/DRM per strategy from spec) — not implemented
  - **No "RELEVANT" highlighting** with green borders for annotated correct chunks — results show chunk text but without relevance annotations
  - **No per-strategy tabs** (`st.tabs()`) — uses `st.columns()` instead
  - Implementation is simpler: shows ranked chunk text per strategy in columns, not the rich annotated view from spec
- **Acceptance criteria results:**
  - PASS: Page renders, query input works, retrieval runs
  - FAIL: No P@k chart, no metrics table, no relevance highlighting

### Day 10: CLI Retrieval Metrics & Streamlit Embedding Model Toggle
- **Status:** COMPLETE
- **What matches spec:** `render_retrieval_table()` with colour coding and significance markers, `_get_significance_marker()`, `render_benchmark()` updated with retrieval section, Voyage toggle in sidebar, embedding model selectbox, tests in test_cli_retrieval.py
- **What's missing or incomplete:**
  - CLI `_get_significance_marker()` takes `list[SignificanceResult]` instead of spec's `dict[str, Any]` — adapted to Agent A's actual model. Functionally correct.
  - `render_retrieval_table()` takes `list[RetrievalMetrics]` instead of spec's `list[RetrievalResult]` — adapted to actual models
- **Acceptance criteria results:** All pass

### Day 11: Streamlit Polish — Spinners, Errors & Session State
- **Status:** PARTIAL — Core polish done, some features skipped
- **What matches spec:** Session state invalidation (`_invalidate_on_change()`), responsive CSS, "Clear All Caches" button with stats, error helper functions in components.py (`render_error`, `render_dependency_error`, `render_api_key_error`)
- **What's missing or incomplete:**
  - **No `st.progress()` bars** for multi-step operations — still uses `st.spinner()` only
  - **No `st.toast()` notifications** after completed operations
  - **No timing information** displayed for operations
- **Acceptance criteria results:**
  - PASS: Session invalidation, clear cache, error messages, responsive layout
  - FAIL: No progress bars, no toast notifications

### Day 12: Metrics Summary Panel & Embedding Model Comparison
- **Status:** COMPLETE
- **What matches spec:** page_metrics.py with headline cards (clause frag, def preservation, xref, hierarchy), structural comparison grouped bar chart, retrieval comparison chart, embedding model heatmap, data source (latest file + upload JSON), refresh button, wired into app.py
- **What's missing or incomplete:** None significant
- **Acceptance criteria results:** All pass

### Day 13: Filtered Retrieval Demo & Export Functionality
- **Status:** COMPLETE
- **What matches spec:** Filtered retrieval section in page_retrieval.py, clause type filtering, "Baseline: Not possible" warning, keyword search comparison, render_export_section() in components.py with JSON + HTML download
- **What's missing or incomplete:** None
- **Acceptance criteria results:** All pass

### Day 14: Streamlit Deployment & Dependency Management
- **Status:** PARTIAL — Most done, some docs missing
- **What matches spec:** requirements-dashboard.txt, compat.py with feature flags, .streamlit/config.toml, streamlit_app.py entry point, docs/deployment.md
- **What's missing or incomplete:**
  - **No `_render_demo_mode()` function** in page_retrieval.py — spec describes a demo mode with JSON upload for when embeddings are unavailable. Instead, the page shows a query browser fallback (`_render_query_browser()`), which is a simpler approach.
  - `_check_retrieval_available()` exists and shows warning, but doesn't offer JSON upload demo mode
- **Acceptance criteria results:**
  - PASS: streamlit_app.py works, requirements install, .streamlit/config.toml applied
  - PARTIAL: Graceful degradation works but demo mode is simpler than spec

### Day 15: Screenshots, GIFs & EXTENSIBILITY.md Outline
- **Status:** PARTIAL — EXTENSIBILITY.md done, screenshots skipped
- **What matches spec:** EXTENSIBILITY.md with sections 1-2 (later completed fully on Day 16)
- **What's missing or incomplete:**
  - **`docs/screenshots/` directory does not exist**
  - **`scripts/capture_screenshots.py` does not exist**
  - **`docs/screenshots/manifest.yaml` does not exist**
  - No screenshots or GIFs were captured (these are manual/visual artifacts that AI agents cannot produce)
- **Acceptance criteria results:**
  - PASS: EXTENSIBILITY.md outline + first 2 sections
  - FAIL: No screenshot directory, script, or manifest

### Day 16: Complete EXTENSIBILITY.md
- **Status:** COMPLETE
- **What matches spec:** All 8 sections present: Architecture Overview, Adding Test Fixtures, Adding Chunking Strategies, Adding Embedding Models, Adding Metrics, Adding Query Sets, Adding Output Formats, Configuration Reference. Code examples in each section. 5-step strategy registration documented.
- **What's missing or incomplete:**
  - EXTENSIBILITY.md references actual code patterns (StrategyName enum, protocol from models.py) rather than spec's simplified patterns — correct adaptation
- **Acceptance criteria results:** All pass

### Day 17: Streamlit Edge Cases & Robustness
- **Status:** COMPLETE
- **What matches spec:** _validate_upload() with size/encoding/length checks, _validate_document() with empty/short/binary detection, MIN_DOCUMENT_CHARS/MAX_UPLOAD_SIZE_BYTES/MAX_DOCUMENT_CHARS constants, multi-encoding fallback, tests/test_dashboard_edge_cases.py
- **What's missing or incomplete:**
  - **No `_check_legal_structure()` function** — spec describes warning when document has no legal structure. Not implemented.
  - Voyage-specific error handling in page_retrieval.py is simpler than spec's detailed handler
- **Acceptance criteria results:** All core acceptance criteria pass

### Day 18: README Rewrite (PAIR)
- **Status:** PARTIAL — README exists but smaller than spec
- **What matches spec:** README.md exists (211 lines), has installation, dashboard, configuration, deployment, contributing sections
- **What's missing or incomplete:**
  - **No LICENSE file** — README references MIT but no LICENSE file exists in repo root
  - **No screenshot references** in README (because screenshots don't exist from Day 15)
  - README is 211 lines (spec targets <500, so length is fine, but some sections may be thinner than spec)
- **Acceptance criteria results:**
  - PASS: README renders, installation commands work, configuration example present
  - FAIL: No LICENSE file, no screenshot references

### Day 19: Dependency Audit & CI Configuration
- **Status:** PARTIAL — CI exists, some artifacts missing
- **What matches spec:** pyproject.toml has pinned version ranges (`<X.0` ceilings), .github/workflows/ci.yml exists
- **What's missing or incomplete:**
  - **`.github/workflows/dashboard.yml` does not exist** — spec requires a separate dashboard smoke test workflow
  - **`requirements.lock` does not exist** — spec requires a lock file for reproducible builds
  - `pyproject.toml` `cov-fail-under` still at `0` — spec Day 1 says 80, Day 19 acceptance criteria say "80%+ coverage"
  - CI workflow not verified to match spec exactly (matrix Python versions, dependency-check job, license check)
- **Acceptance criteria results:**
  - PASS: Dependency pinning, CI workflow exists
  - FAIL: No dashboard.yml, no requirements.lock, coverage threshold at 0

### Day 20: v1.0.0 Tag, Final Verification & Post-v1 Issues (PAIR)
- **Status:** PARTIAL — Version bumped, no tag or issues
- **What matches spec:** Version is 1.0.0 in both pyproject.toml and __init__.py, tests pass (258 passed), lint clean
- **What's missing or incomplete:**
  - **No `v1.0.0` git tag** — `git tag -l 'v*'` returns nothing
  - **No post-v1 GitHub issues created** (7 issues specified in plan)
  - No verification checklist signed off
- **Acceptance criteria results:**
  - PASS: Version 1.0.0, tests pass, lint clean
  - FAIL: No git tag, no GitHub issues

---

## Summary

- **Total days fully matching spec:** 11/20
- **Days with gaps:**

| Day | Severity | Gap Description |
|-----|----------|-----------------|
| 01 | LOW | `cov-fail-under` at 0 instead of 80 |
| 06 | LOW | Embedder protocol in models.py not embedding/__init__.py; no create_embedder() factory |
| 09 | **MEDIUM** | Missing P@k chart, metrics table, relevance highlighting, tabs in retrieval page |
| 11 | LOW | No st.progress() bars or st.toast() notifications |
| 14 | LOW | No demo mode with JSON upload fallback |
| 15 | LOW | No screenshots directory, capture script, or manifest (visual artifacts) |
| 17 | LOW | No _check_legal_structure() warning function |
| 18 | **MEDIUM** | No LICENSE file in repo root |
| 19 | **MEDIUM** | No dashboard.yml workflow, no requirements.lock, cov-fail-under still 0 |
| 20 | **HIGH** | No v1.0.0 git tag, no post-v1 GitHub issues |

### Priority Items to Fix (ordered by impact)

1. **[HIGH] Create v1.0.0 git tag** (Day 20) — Release milestone not finalized
2. **[MEDIUM] Add LICENSE file** (Day 18) — Legal compliance gap, MIT referenced but no file
3. **[MEDIUM] Retrieval page P@k chart + metrics table** (Day 09) — Key demo feature missing visual comparison
4. **[MEDIUM] Coverage threshold** (Day 01/19) — `cov-fail-under=0` should be `80` per spec; current coverage is 87% so it would pass
5. **[MEDIUM] Dashboard CI workflow** (Day 19) — `.github/workflows/dashboard.yml` missing
6. **[LOW] requirements.lock** (Day 19) — Reproducible builds artifact missing
7. **[LOW] Progress bars and toasts** (Day 11) — UX polish items
8. **[LOW] Screenshots directory/assets** (Day 15) — Visual documentation; cannot be auto-generated
9. **[LOW] Post-v1 GitHub issues** (Day 20) — Roadmap documentation
10. **[LOW] Embedder protocol location + factory** (Day 06) — Architecturally divergent but functionally equivalent
