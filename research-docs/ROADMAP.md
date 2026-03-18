# LexiChunk Scaffolder — 3-Month Roadmap

**Team:** 3 engineers · **Duration:** 12 weeks (2026-03-18 → 2026-06-12)
**Goal:** Production-grade evaluation platform that proves legal-aware chunking measurably improves RAG retrieval, with an interactive demo compelling enough to convert skeptics.

---

## Team Structure

| Role | Focus | Owns |
|------|-------|------|
| **Eng 1 — Evaluation Core** | Metrics, benchmarking, statistical rigor | Chunking pipeline, structural metrics, retrieval metrics, statistical testing, LegalBench-RAG integration, LLM-judge |
| **Eng 2 — Infra & Data** | Embedding pipeline, vector storage, data management | Fixture framework, embedding adapters, FAISS indexing, caching, query annotation, CLI/JSON output, CI/CD |
| **Eng 3 — UI & Reporting** | Streamlit dashboard, HTML reports, visualisation | Dashboard pages, chunk visualiser, report templates, Plotly charts, deployment, UX polish |

All three engineers contribute to architecture decisions, code review, and test coverage. Roles overlap at boundaries — the split is about primary ownership, not silos.

---

## Month 1: Foundation + Structural Proof (Weeks 1–4)

The goal is a working CLI benchmark that produces structural quality numbers comparing LexiChunk against baselines. No embeddings yet — pure deterministic metrics.

### Week 1: Skeleton + Core Models

**All engineers (collaborative)**

- Initialise repo: `pyproject.toml`, `src/scaffolder/`, CI with ruff + mypy + pytest
- Agree on data models: `Document`, `Chunk`, `ChunkSet`, `StrategyResult`, `BenchmarkConfig`
- Agree on protocol interfaces: `ChunkingStrategy`, `Embedder`, `MetricFn`
- Set up pre-commit hooks, branch protection, PR template
- Copy 5 fixture documents from LexiChunk repo

**Deliverable:** Green CI, importable package, shared data model contracts.

### Week 2: Chunking Pipeline + Fixture Framework

**Eng 1** — `ChunkingPipeline` orchestrator
- Strategy registry pattern: register a name + callable, pipeline runs all strategies against all documents
- LexiChunk wrapper (clause-aware, with and without context enrichment)
- LangChain RCTS wrapper (multiple chunk sizes: 256, 512, 1024)
- Sentence-split wrapper (using NLTK or spaCy sentence tokeniser)
- Fixed-size wrapper (token-based, 256/512/1024)
- Timing instrumentation per strategy per document

**Eng 2** — `FixtureManager` + data loading
- Auto-discovery of `.txt` files in `fixtures/documents/`
- Document metadata: jurisdiction, document type, source
- Validation: non-empty, reasonable size, encoding checks
- Query annotation schema design (YAML format)
- Write first 5 query files (3–5 queries each = ~20 total)

**Eng 3** — Output scaffolding
- `rich` CLI reporter: table of strategies × documents × basic stats (chunk count, avg size, timing)
- JSON export schema design
- Stub Streamlit app with upload page (just file upload + raw text preview)

**Deliverable:** `python -m scaffolder benchmark --fixtures all` produces a CLI table comparing chunk counts and sizes across 6 strategies on 5 documents.

### Week 3: Structural Metrics

**Eng 1** — Core structural metrics
- Clause fragmentation rate: use LexiChunk's structure parser as ground truth, check if baseline chunks split across clause boundaries
- Definition preservation rate: extract defined terms via LexiChunk, check accessibility per chunk per strategy
- Cross-reference resolution rate: detect cross-refs, check if target is in same chunk or linked
- Hierarchy depth retained: average hierarchy path length per chunk

**Eng 2** — Query annotation + extended fixtures
- Complete query annotations for all 5 fixtures (target: 25 queries with graded relevance)
- Add query validation (ensure referenced sections exist in fixture)
- Chunk size distribution analysis (mean, median, p95, min, max per strategy)
- Clause type coverage metric (% chunks with classification confidence > 0.5)

**Eng 3** — CLI + JSON + HTML stub for structural results
- Expand CLI reporter to show structural metrics per strategy, colour-coded (green = best, red = worst)
- JSON export with full results
- Begin HTML report template (Jinja2): structural metrics comparison table, chunk size distribution chart

**Deliverable:** Structural quality report showing LexiChunk's fragmentation rate vs baselines. First hard numbers.

### Week 4: Polish + Structural Report

**Eng 1** — Statistical robustness
- Per-document breakdown (some documents may show different patterns)
- Edge case handling: what happens when fixture has no definitions? No cross-references?
- Document the metric methodology in `docs/metrics.md`

**Eng 2** — CI integration + test coverage
- Tests for all metrics (known input → known output)
- CI runs the full benchmark on every PR (fast — no embeddings)
- Coverage target: 80% enforced
- `Makefile` with `make benchmark`, `make report`, `make test`, `make lint`

**Eng 3** — HTML structural report
- Standalone HTML report with:
  - Strategy comparison table (sortable)
  - Chunk size distribution histogram (Plotly, embedded)
  - Per-document breakdown
  - Methodology section explaining each metric
- `make report` generates `results/structural_report.html`

**Deliverable:** Month 1 complete. CLI + JSON + HTML structural report. Publishable claim: "LexiChunk achieves <5% clause fragmentation vs 30–60% for RecursiveCharacterTextSplitter."

---

## Month 2: Retrieval Proof + Dashboard (Weeks 5–8)

The goal is embedding-backed retrieval evaluation — the real claim — plus an interactive Streamlit dashboard.

### Week 5: Embedding Pipeline

**Eng 1** — Retrieval metrics implementation
- Precision@k, Recall@k (k = 1, 3, 5, 10)
- MRR (Mean Reciprocal Rank)
- NDCG@10 with graded relevance
- DRM rate (Document-Level Retrieval Mismatch)
- All metrics as pure functions: `(retrieved_ids, relevant_ids) → float`

**Eng 2** — Embedding pipeline
- `EmbeddingPipeline` with pluggable model adapters
- Local adapter: `sentence-transformers` loading `all-MiniLM-L6-v2` and `bge-base-en-v1.5`
- Voyage adapter: `voyageai` SDK, `voyage-law-2` model, toggled via config flag
- Disk cache: hash(model + text) → embedding vector, stored in `.cache/embeddings/`
- Cache invalidation: if model or text changes, recompute

**Eng 3** — Streamlit app: upload + compare page
- Multi-page app structure (`pages/`)
- Page 1 — Upload: paste text or upload .txt, select jurisdiction
- Page 2 — Compare: side-by-side chunk view for LexiChunk vs selected baseline
- Chunk highlighting: colour-code by clause type, show hierarchy path
- Chunk boundary markers showing where each strategy splits

**Deliverable:** Embedding pipeline embeds all chunks, caches to disk. Streamlit shows side-by-side comparison.

### Week 6: Retrieval Simulation

**Eng 1** — `RetrievalSimulator`
- For each query: embed query, retrieve top-k from each strategy's FAISS index
- Collect retrieved chunk IDs, content, and scores
- Match against annotated relevant sections (using section ID overlap or character span overlap)
- Per-query result objects with full provenance

**Eng 2** — FAISS indexing + query execution
- `VectorIndex` wrapper around FAISS flat L2
- Build one index per (strategy, embedding_model, document) triple
- Multi-document index for DRM testing (index all 5 docs together)
- Query embedding using same model as chunk embedding

**Eng 3** — Streamlit retrieval page
- Page 3 — Retrieval: type a legal question, see which chunks each strategy retrieves
- Show retrieved chunks ranked, with relevance scores
- Highlight the "correct" chunks (from annotations) in green
- Side-by-side: LexiChunk retrieval vs baseline retrieval for same query

**Deliverable:** `python -m scaffolder benchmark --embed --model minilm` runs full retrieval evaluation. Streamlit lets you query interactively.

### Week 7: Statistical Rigour + Multi-Model

**Eng 1** — Statistical testing + multi-model evaluation
- Paired t-tests: LexiChunk vs each baseline, per metric
- Confidence intervals on all aggregate metrics
- Run full evaluation across both local models (MiniLM, BGE)
- Ensure results generalise across models (the key credibility claim)
- If Voyage toggle is ready, run one evaluation with `voyage-law-2`

**Eng 2** — Full CLI + JSON retrieval report
- Extend CLI reporter: retrieval metrics table per strategy per model
- JSON export: full results including per-query scores
- Significance markers: * for p < 0.05, ** for p < 0.01
- Summary statistics: % improvement LexiChunk vs best baseline

**Eng 3** — Streamlit metrics page + HTML retrieval report
- Page 4 — Metrics: aggregate metrics dashboard, strategy comparison charts
- Plotly bar charts: P@5, MRR, NDCG per strategy, grouped by model
- DRM rate visualisation
- HTML report: extend structural report with retrieval metrics section

**Deliverable:** Full retrieval evaluation across 2 models with statistical significance. The headline number exists.

### Week 8: Integration + Demo Polish

**All engineers — polish sprint**

**Eng 1:**
- End-to-end test: `make benchmark-full` runs structural + retrieval + generates all reports
- Documentation: `README.md` with quickstart, output examples, methodology
- Benchmark reproducibility: pin random seeds, document exact versions

**Eng 2:**
- Config documentation: all toggles, environment variables, model selection
- Embedding cache management: `make clean-cache`, cache size reporting
- Performance: ensure full benchmark completes in < 10 minutes on a laptop

**Eng 3:**
- Streamlit UX polish: loading states, error handling, responsive layout
- Deploy to Streamlit Community Cloud (or document deployment steps)
- Screenshot/GIF generation for README

**Deliverable:** Month 2 complete. Fully working evaluation platform with CLI + JSON + HTML + Streamlit. The retrieval improvement claim is proven with statistical significance across multiple embedding models.

---

## Month 3: Gold Standard + Production Grade (Weeks 9–12)

The goal is publication-grade benchmarking (LegalBench-RAG), LLM-judge evaluation, and the polish that separates "impressive" from "unassailable."

### Week 9: LegalBench-RAG Integration

**Eng 1** — Dataset loader + evaluation
- Download LegalBench-RAG from HuggingFace (`theatticusproject/legalbench-rag`)
- Parse character-level span annotations into our query format
- Start with mini version (776 queries) for iteration
- Run full evaluation: 776 queries × 6 strategies × 2 models
- Compute Token-IoU (character-level precision metric specific to LegalBench-RAG)

**Eng 2** — Scale infrastructure
- Ensure embedding pipeline handles 776+ queries efficiently
- Batch embedding (encode N texts at once, not one-by-one)
- Progress bars and ETA for long benchmark runs
- Results versioning: each benchmark run gets a timestamped ID

**Eng 3** — Results visualisation
- LegalBench-RAG results page in Streamlit
- Per-category breakdown (NDAs, M&A, commercial, privacy)
- Comparison with published baselines from the LegalBench-RAG paper
- Update HTML report with LegalBench-RAG section

**Deliverable:** LegalBench-RAG benchmark complete. Results comparable to published baselines.

### Week 10: LLM-Judge + Voyage Evaluation

**Eng 1** — DeepEval LLM-judge integration
- `LLMEvaluator` using DeepEval's faithfulness + answer relevancy metrics
- GPT-4o-mini as judge (configurable)
- Run on 100-query subset from curated queries
- Toggled off by default, activated via `--llm-judge` flag or config
- Cost tracking: log token usage and estimated cost per run

**Eng 2** — Voyage Law 2 full evaluation
- Run complete benchmark with `voyage-law-2`
- Compare legal-specific vs general-purpose embeddings
- Document the MLEB finding: legal rankings ≠ general rankings
- Cost tracking for Voyage API usage

**Eng 3** — LLM-judge results in dashboard + reports
- Faithfulness + answer relevancy visualisation
- Comparison against Stanford baseline (17–33% hallucination)
- Cost breakdown display
- Update all report templates

**Deliverable:** LLM-judge evaluation complete. Voyage Law 2 comparison done. Full picture: structural + retrieval + faithfulness.

### Week 11: EXTENSIBILITY.md + Advanced Features

**Eng 1** — Extensibility design doc
- Write `EXTENSIBILITY.md`: complete standalone design document covering:
  - Adding new fixtures (document + query annotation walkthrough)
  - Adding chunking strategies (protocol, registration, examples)
  - Adding embedding models (local adapter vs API adapter)
  - Adding metrics (structural and retrieval)
  - Adding query sets (YAML schema, graded relevance)
  - Future: adding new datasets (beyond LegalBench-RAG)
  - Future: custom LLM judges (beyond DeepEval)
- Include architecture diagrams and code examples

**Eng 2** — Advanced features
- Contextual retrieval comparison: benchmark LexiChunk with vs without `build_embedded_text()` context headers
- Summary-Augmented Chunking comparison: implement SAC (prepend 150-char summary) as a strategy, compare against LexiChunk's approach
- Filtered retrieval test: "find all indemnification clauses" using LexiChunk's clause type metadata

**Eng 3** — Dashboard advanced features
- Embedding model comparison page: heatmap of strategy × model × metric
- Export functionality: download results as JSON/CSV from dashboard
- Shareable links: URL params encode selected strategy/model/document for bookmarking

**Deliverable:** EXTENSIBILITY.md complete. Advanced comparisons (contextual retrieval, SAC, filtered retrieval) run and visualised.

### Week 12: Final Polish + Launch Prep

**All engineers — ship it**

**Eng 1:**
- Final benchmark run: all strategies × all models × LegalBench-RAG + curated queries + LLM-judge
- Results review: sanity check all numbers, verify statistical significance holds
- Write methodology section for blog post / README
- Peer review of all metric implementations

**Eng 2:**
- CI/CD: full benchmark runs in CI (nightly, not per-PR — too slow)
- `pyproject.toml` extras: `pip install scaffolder[local]`, `[voyage]`, `[llm-judge]`, `[dashboard]`, `[all]`
- Final dependency audit: pin versions, check licenses
- Performance profiling: ensure no memory leaks on large benchmarks

**Eng 3:**
- Dashboard final polish: loading states, error messages, mobile responsiveness
- Deploy to Streamlit Community Cloud
- Generate screenshots and GIFs for README
- HTML report final design pass

**All:**
- `README.md` rewrite: quickstart, output examples, benchmark results summary, screenshots
- Code review sweep: ensure consistent style, no dead code, all TODOs resolved
- Tag `v1.0.0`

**Deliverable:** v1.0.0 tagged. Everything works. Ready for the blog post and public launch.

---

## Milestone Summary

| Week | Milestone | Key Artifact |
|------|-----------|-------------|
| 1 | Repo skeleton + data models | Green CI, shared contracts |
| 2 | Chunking pipeline works | `make benchmark` produces chunk comparison |
| 3 | Structural metrics computed | First hard numbers: fragmentation rates |
| 4 | **Month 1 done** | HTML structural report, publishable structural claims |
| 5 | Embeddings working | Chunks embedded + cached |
| 6 | Retrieval simulation working | Interactive Streamlit retrieval |
| 7 | Statistical rigour + multi-model | Significance-tested retrieval improvement |
| 8 | **Month 2 done** | Full evaluation platform, the headline retrieval number |
| 9 | LegalBench-RAG integrated | Publication-grade benchmark |
| 10 | LLM-judge + Voyage eval | Faithfulness scores, legal embedding comparison |
| 11 | Extensibility doc + advanced features | EXTENSIBILITY.md, SAC comparison, filtered retrieval |
| 12 | **Month 3 done — v1.0.0** | Everything polished, deployed, launch-ready |

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| LexiChunk retrieval improvement is smaller than expected | Medium | High | Structural metrics are the fallback — clause integrity is provable regardless. Also test with context enrichment ON, which should boost retrieval. |
| Embedding pipeline is slow on large corpora | Medium | Medium | Aggressive caching. Batch encoding. MiniLM is fast (~14K sentences/sec on CPU). Only Voyage requires API calls. |
| LegalBench-RAG annotations don't map cleanly to our query format | Low | Medium | Start with mini version (776 queries). Character-span overlap matching is flexible. Worst case: use only our curated 25 queries for primary claims. |
| Streamlit performance with large documents | Low | Low | Pagination. Lazy loading. Cap document size at 100KB for interactive mode (batch benchmark has no cap). |
| Voyage API costs exceed budget | Low | Low | Toggle is off by default. Run once on curated queries (25 queries × ~6 strategies = ~150 embeddings = pennies). Only expensive at LegalBench-RAG scale. |
| DeepEval/GPT-4o-mini judge scores are noisy | Medium | Low | Run on fixed subset, report mean ± std. Deterministic retrieval metrics are the primary evidence; LLM-judge is supplementary. |

---

## What's Out of Scope (and Why)

| Feature | Why Not |
|---------|---------|
| PDF parsing / OCR | Solved problem. Users should use Docling/PyMuPDF upstream. Adds massive scope for zero evaluation signal. |
| Fine-tuning embedding models | We evaluate existing models, not train new ones. Fine-tuning is a separate research project. |
| Multi-language support | UK/US/EU English covers the target market. Philippine legal docs could be a v2 extension. |
| Real-time API server | This is a benchmark + demo tool, not a production service. Streamlit serves the interactive use case. |
| Custom vector database integration | FAISS flat index is deterministic and sufficient. ChromaDB/Qdrant add operational complexity with no benchmark benefit. |
| Automated CI benchmarking with regression alerts | Nice-to-have for v2. Week 12 adds nightly benchmark runs, but automated regression detection is over-engineering at this stage. |

---

## Dependencies Between Engineers

```
Eng 2 (FixtureManager) ──blocks──→ Eng 1 (ChunkingPipeline)
Eng 1 (ChunkingPipeline) ──blocks──→ Eng 3 (Streamlit compare page)
Eng 1 (Metrics) ──blocks──→ Eng 3 (Metrics visualisation)
Eng 2 (EmbeddingPipeline) ──blocks──→ Eng 1 (RetrievalSimulator)
Eng 1 (RetrievalSimulator) ──blocks──→ Eng 3 (Streamlit retrieval page)
```

**Critical path:** FixtureManager → ChunkingPipeline → EmbeddingPipeline → RetrievalSimulator → RetrievalMetrics → Reports/Dashboard. This chain runs through Eng 2 → Eng 1 → Eng 2 → Eng 1 → Eng 3, which is why Week 1's collaborative model agreement is essential — it decouples the interfaces from the implementations.

---

## Success Metrics for the Project Itself

| Metric | Target | How We Know |
|--------|--------|-------------|
| Structural proof | <5% clause fragmentation for LexiChunk vs 30–60% baselines | Month 1 report |
| Retrieval proof | >20% P@5 improvement vs RCTS, p < 0.05 | Month 2 report |
| Generalisation | Improvement holds across ≥2 embedding models | Month 2 multi-model evaluation |
| Publication-grade | LegalBench-RAG results comparable to or better than published baselines | Month 3 benchmark |
| Demo readiness | Non-technical person can upload a contract and see the difference in <60 seconds | Month 2 Streamlit |
| Extensibility | New fixture + queries addable in <30 minutes following EXTENSIBILITY.md | Month 3 doc |
