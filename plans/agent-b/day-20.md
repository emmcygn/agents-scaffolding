# Agent B — Day 20: v1.0.0 Tag, Final Verification & Post-v1 Issues (PAIR with Agent A)

## Mission
Pair with Agent A to perform final end-to-end verification, tag v1.0.0, and write post-v1 GitHub issues documenting the roadmap for future enhancements.

## Context
Day 19 completed the dependency audit and CI configuration. All code is written, tested, documented, and deployment-ready. Today is the release day — we verify everything works end-to-end, create the v1.0.0 git tag, and plan what comes next. This is a pairing day: both agents work together to catch any last issues and ensure the release is solid.

## Prerequisites
- All tests passing: `make ci` (Day 19 verified)
- `README.md` complete (Day 18)
- `EXTENSIBILITY.md` complete (Day 16)
- CI workflows configured (Day 19)
- Dashboard deployable (Day 14)
- All dependency licenses verified (Day 19)

## Checklist
- [ ] Task 1 — End-to-end smoke test: full benchmark run (structural only)
- [ ] Task 2 — End-to-end smoke test: full benchmark run (with embeddings)
- [ ] Task 3 — Dashboard verification: all 3 pages work with real data
- [ ] Task 4 — CLI verification: output is correct and well-formatted
- [ ] Task 5 — Update version to 1.0.0 in `pyproject.toml` and `__init__.py`
- [ ] Task 6 — Create git tag v1.0.0
- [ ] Task 7 — Write post-v1 GitHub issues
- [ ] Task 8 — Final README review (both agents)

## Implementation Details

### End-to-end smoke test

Run the complete benchmark pipeline and verify all outputs:

```bash
# 1. Clean state
make clean

# 2. Install everything
pip install -e ".[all]"

# 3. Verify imports
python -c "
import scaffolder
from scaffolder.config import BenchmarkConfig
from scaffolder.models import Document, Chunk, ChunkSet, StructuralResult, RetrievalResult, BenchmarkResult
from scaffolder.queries import load_queries
from scaffolder.reporting.cli import render_benchmark
from scaffolder.reporting.json_export import export_json
from scaffolder.embedding import Embedder, create_embedder
from scaffolder.embedding.voyage import VoyageEmbedder
print(f'All imports OK. Version: {scaffolder.__version__}')
"

# 4. Structural benchmark (no embeddings — fast)
python -m scaffolder benchmark --no-embed
# Expected: CLI output with structural metrics table, JSON written to results/

# 5. Full benchmark with embeddings (slower — needs sentence-transformers)
python -m scaffolder benchmark
# Expected: CLI output with structural + retrieval metrics, JSON + HTML output

# 6. Verify outputs
ls -la results/
# Should contain: benchmark_TIMESTAMP.json (and optionally .html)

# 7. Dashboard
streamlit run src/scaffolder/dashboard/app.py &
# Navigate to each page and verify:
# - Compare Chunks: select fixture, run chunking, see side-by-side
# - Retrieval Demo: select query, run search, see ranked results
# - Metrics Dashboard: load results JSON, see headline metrics + charts
```

### Verification checklist (both agents check)

| Check | Agent A | Agent B | Status |
|-------|---------|---------|--------|
| `make lint` passes | [ ] | [ ] | |
| `make typecheck` passes | [ ] | [ ] | |
| `make test` passes (80%+ coverage) | [ ] | [ ] | |
| Structural benchmark produces correct output | [ ] | [ ] | |
| Retrieval benchmark produces correct output | [ ] | [ ] | |
| JSON export is valid and loadable | [ ] | [ ] | |
| CLI output is well-formatted with colours | [ ] | [ ] | |
| Dashboard Compare page works | [ ] | [ ] | |
| Dashboard Retrieval page works | [ ] | [ ] | |
| Dashboard Metrics page works | [ ] | [ ] | |
| README renders correctly on GitHub | [ ] | [ ] | |
| EXTENSIBILITY.md links all work | [ ] | [ ] | |
| `pip install -e "."` works (minimal) | [ ] | [ ] | |
| `pip install -e ".[all]"` works (full) | [ ] | [ ] | |

### Version bump

Update two files:

**pyproject.toml:**
```toml
version = "1.0.0"
```

**src/scaffolder/__init__.py:**
```python
__version__ = "1.0.0"
```

### Git tag

```bash
# Commit the version bump
git add pyproject.toml src/scaffolder/__init__.py
git commit -m "chore: bump version to 1.0.0"

# Create annotated tag
git tag -a v1.0.0 -m "v1.0.0 — Initial release

Evaluation harness proving LexiChunk improves RAG retrieval quality
over general-purpose chunking strategies for legal documents.

Features:
- 4 chunking strategies: LexiChunk, LangChain RCTS, sentence-split, fixed-512
- 5 structural metrics: clause fragmentation, definition preservation,
  cross-ref resolution, hierarchy depth, chunk size statistics
- 5 retrieval metrics: P@k, R@k, MRR, NDCG@10, DRM rate
- Statistical significance testing (paired t-tests)
- 25+ annotated queries across 5 legal fixtures (UK, US, EU)
- Local embeddings (MiniLM, BGE) + Voyage AI (voyage-law-2)
- CLI output (rich tables), JSON export, HTML report (Jinja2)
- Interactive Streamlit dashboard with 3 pages
- Comprehensive extensibility guide
"

# Push tag (only when ready)
git push origin v1.0.0
```

### Post-v1 GitHub issues

Create these issues after tagging. Each issue should have a clear title, description, and labels.

**Issue 1: LegalBench-RAG Integration**
```
Title: feat: Integrate LegalBench-RAG benchmark suite
Labels: enhancement, v1.1

Description:
Integrate the LegalBench-RAG benchmark (https://huggingface.co/datasets/nguha/legalbench)
as an additional evaluation dataset. This would:

- Add 200+ legal QA pairs as query annotations
- Enable comparison against published baselines
- Strengthen the credibility of LexiChunk's performance claims

Tasks:
- [ ] Download and parse LegalBench-RAG dataset
- [ ] Convert to scaffolder query annotation YAML format
- [ ] Map relevance judgments to our graded relevance schema
- [ ] Run benchmark and add results to README
```

**Issue 2: LLM-as-Judge Evaluation**
```
Title: feat: Add LLM-as-judge evaluation mode
Labels: enhancement, v1.1

Description:
Add an LLM-based evaluation mode where GPT-4 or Claude judges whether
retrieved chunks answer the query correctly. This complements the
annotation-based evaluation.

Tasks:
- [ ] Design LLM judge prompt template
- [ ] Implement judge pipeline (support OpenAI + Anthropic)
- [ ] Add LLM-judge results to CLI and dashboard
- [ ] Compare LLM judgments vs human annotations
```

**Issue 3: HuggingFace Space (Gradio)**
```
Title: feat: Deploy as HuggingFace Space with Gradio
Labels: enhancement, deployment

Description:
Create a Gradio-based alternative to the Streamlit dashboard and deploy
on HuggingFace Spaces for public demo access.

Tasks:
- [ ] Build Gradio UI mirroring the Streamlit dashboard
- [ ] Configure HuggingFace Space deployment
- [ ] Pre-load benchmark results for instant demo
```

**Issue 4: MkDocs Documentation Site**
```
Title: docs: Build MkDocs documentation site
Labels: documentation, v1.1

Description:
Set up MkDocs with material theme for comprehensive documentation.
Current README + EXTENSIBILITY.md + metrics.md would become proper
doc pages with navigation, search, and better formatting.

Tasks:
- [ ] Configure mkdocs.yml with material theme
- [ ] Migrate README sections to dedicated pages
- [ ] Add API reference (auto-generated from docstrings)
- [ ] Deploy to GitHub Pages
```

**Issue 5: Additional Chunking Strategies**
```
Title: feat: Add Chonkie and Docling chunking strategies
Labels: enhancement, v1.1

Description:
Expand the baseline comparison to include:
- Chonkie (https://github.com/chonkie-ai/chonkie) — semantic chunker
- Docling (IBM's document processing) — document-aware chunker

This broadens the comparison beyond simple text splitters.

Tasks:
- [ ] Implement Chonkie strategy wrapper
- [ ] Implement Docling strategy wrapper
- [ ] Update config with new strategy options
- [ ] Run benchmarks and update results
```

**Issue 6: Additional Embedding Models**
```
Title: feat: Add Kanon 2 and nomic-embed embedding models
Labels: enhancement, v1.1

Description:
Expand embedding model support:
- Kanon 2 (legal-specific embeddings)
- nomic-embed-text-v1.5 (strong general-purpose)

Tasks:
- [ ] Implement Kanon 2 adapter
- [ ] Implement Nomic adapter
- [ ] Benchmark and add to model comparison heatmap
```

**Issue 7: CI Nightly Benchmarks**
```
Title: ci: Add nightly benchmark runs
Labels: ci, v1.1

Description:
Run the full benchmark suite nightly on CI to detect regressions
when dependencies are updated.

Tasks:
- [ ] Create .github/workflows/nightly.yml
- [ ] Store results as artifacts
- [ ] Alert on significant metric regressions
- [ ] Track results over time (simple CSV or SQLite)
```

### Creating issues via gh CLI

```bash
# Issue 1
gh issue create --title "feat: Integrate LegalBench-RAG benchmark suite" \
  --label "enhancement" \
  --body "Integrate the LegalBench-RAG benchmark as an additional evaluation dataset. See issue body for tasks."

# Repeat for issues 2-7...
```

## Outputs
- `pyproject.toml` (version 1.0.0)
- `src/scaffolder/__init__.py` (version 1.0.0)
- Git tag `v1.0.0`
- 7 GitHub issues for post-v1 roadmap

## Acceptance Criteria
1. `make ci` passes (lint + typecheck + test with 80%+ coverage)
2. Full benchmark runs without errors (structural + retrieval)
3. Dashboard pages all work with real benchmark data
4. Version is "1.0.0" everywhere: `python -c "import scaffolder; print(scaffolder.__version__)"` prints `1.0.0`
5. Git tag `v1.0.0` exists with descriptive annotation
6. 7 post-v1 GitHub issues created
7. Both agents have signed off on the verification checklist

## Handoff Notes
- **To future contributors:** The post-v1 issues are the roadmap. Start with Issue 5 (additional strategies) as it's the most straightforward extension. Issue 1 (LegalBench-RAG) is the highest impact for credibility.
- **Project complete.** The scaffolder is a standalone evaluation harness that proves LexiChunk measurably improves RAG retrieval quality for legal documents. All code is tested, documented, and deployable.
