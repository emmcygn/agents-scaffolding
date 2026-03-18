# Agent B — Day 18: README Rewrite (PAIR with Agent A)

## Mission
Pair with Agent A to write a comprehensive README.md that serves as both landing page and quickstart guide, with Agent B focusing on installation, dashboard usage, screenshots, and deployment sections.

## Context
The project is feature-complete. EXTENSIBILITY.md is done (Day 16), deployment is configured (Day 14), and screenshots are captured (Day 15). Today both agents collaborate on the README — the most important documentation file. Agent A writes quickstart, benchmark results, and methodology sections. Agent B writes installation (with extras groups), dashboard usage, screenshots, and deployment.

## Prerequisites
- All code complete and working
- `EXTENSIBILITY.md` complete (Day 16)
- Screenshots in `docs/screenshots/` (Day 15)
- `pyproject.toml` with finalized dependencies (Day 1)
- `docs/deployment.md` (Day 14)

## Checklist
- [ ] Task 1 — Write README header with project description and hero image/GIF
- [ ] Task 2 — Write Installation section with extras groups
- [ ] Task 3 — Write Dashboard section with screenshots
- [ ] Task 4 — Write Deployment section
- [ ] Task 5 — Write Configuration section (brief, link to EXTENSIBILITY.md)
- [ ] Task 6 — PAIR: Review Agent A's quickstart and methodology sections
- [ ] Task 7 — Coordinate on overall README structure

## Implementation Details

### README structure (agreed with Agent A)

```markdown
# LexiChunk Scaffolder

> Evaluation harness proving LexiChunk measurably improves RAG retrieval
> quality over general-purpose alternatives for legal documents.

![Demo](docs/screenshots/demo.gif)

## Highlights

- Compares LexiChunk against 3 baselines (LangChain RCTS, sentence-split, fixed-512)
- 5 structural metrics + 5 retrieval metrics with statistical significance
- 25+ annotated legal queries across 5 fixture documents
- Interactive Streamlit dashboard with side-by-side comparison
- CLI output with rich tables and colour-coded results
- Supports local embeddings (MiniLM, BGE) and Voyage AI (voyage-law-2)

## Installation                    ← Agent B
## Quick Start                     ← Agent A
## Dashboard                       ← Agent B
## Benchmark Results               ← Agent A
## Methodology                     ← Agent A
## Configuration                   ← Agent B
## Deployment                      ← Agent B
## Extending the Scaffolder        ← Agent B (link to EXTENSIBILITY.md)
## Contributing                    ← Agent B
## License                         ← Agent B
```

### Agent B's sections

#### Installation

```markdown
## Installation

### Basic (structural metrics only)

```bash
pip install -e .
```

### With local embeddings (recommended)

```bash
pip install -e ".[embed]"
```

This installs `sentence-transformers` and `faiss-cpu` for local embedding
models (all-MiniLM-L6-v2, bge-base-en-v1.5).

### With Voyage AI embeddings

```bash
pip install -e ".[voyage]"
export VOYAGE_API_KEY=your-key-here
```

Enables the `voyage-law-2` model, optimized for legal text.
Get a key at [dash.voyageai.com](https://dash.voyageai.com/).

### With Streamlit dashboard

```bash
pip install -e ".[dashboard]"
```

### Everything

```bash
pip install -e ".[all]"
```

### Development

```bash
pip install -e ".[all]"
make lint       # ruff check
make typecheck  # mypy strict
make test       # pytest with 80% coverage target
```

### Requirements

- Python 3.10+
- ~500MB disk for embedding models (if using local embeddings)
- 2GB+ RAM recommended for embedding + FAISS indexing
```

#### Dashboard

```markdown
## Dashboard

Launch the interactive Streamlit dashboard:

```bash
make dashboard
# or: streamlit run src/scaffolder/dashboard/app.py
```

### Chunk Comparison

![Chunk Comparison](docs/screenshots/chunk_comparison.png)

Compare how LexiChunk and baseline chunkers split the same document.
LexiChunk chunks are colour-coded by clause type, with hierarchy
breadcrumbs and defined term highlighting.

### Retrieval Demo

![Retrieval Results](docs/screenshots/retrieval_results.png)

Enter a legal question and see retrieval results ranked by relevance
score. Annotated correct chunks are highlighted in green. A Plotly
bar chart compares precision@k across strategies.

### Filtered Retrieval

![Filtered Retrieval](docs/screenshots/filtered_retrieval.png)

LexiChunk's clause type metadata enables targeted retrieval that
baselines cannot perform. Find all indemnification clauses, all
termination provisions, or any specific clause type.

### Metrics Dashboard

![Metrics Dashboard](docs/screenshots/metrics_dashboard.png)

Aggregate benchmark results with headline comparison cards,
structural metric charts, and embedding model comparison heatmaps.
Upload a results JSON or load from the latest benchmark run.
```

#### Configuration

```markdown
## Configuration

Create `scaffolder.yaml` in the repo root (or copy from `scaffolder.yaml.example`):

```yaml
strategies:
  - lexichunk
  - langchain_rcts
  - sentence_split
  - fixed_512

embedding_models:
  - all-MiniLM-L6-v2
  - bge-base-en-v1.5

k_values: [1, 3, 5, 10]
output_formats: [cli, json, html]
```

Environment variables override YAML settings:

```bash
export SCAFFOLDER_STRATEGIES=lexichunk,fixed_512
export SCAFFOLDER_TOP_K=20
```

See [EXTENSIBILITY.md](EXTENSIBILITY.md#configuration-reference) for the
full configuration reference.
```

#### Deployment

```markdown
## Deployment

### Streamlit Community Cloud

1. Push to GitHub
2. Visit [share.streamlit.io](https://share.streamlit.io)
3. Set main file: `streamlit_app.py`
4. Set Python version: 3.10+
5. Add `VOYAGE_API_KEY` in Secrets (optional)

### Docker

```bash
docker build -t scaffolder .
docker run -p 8501:8501 scaffolder
```

See [docs/deployment.md](docs/deployment.md) for detailed instructions.
```

#### Extending & Contributing

```markdown
## Extending the Scaffolder

See [EXTENSIBILITY.md](EXTENSIBILITY.md) for comprehensive guides on:

- Adding test fixtures and query annotations
- Adding chunking strategies (e.g., Chonkie, Docling)
- Adding embedding models (e.g., Nomic, Cohere)
- Adding custom metrics
- Adding output formats

## Contributing

1. Fork the repository
2. Create a feature branch
3. Install dev dependencies: `pip install -e ".[all]"`
4. Make changes
5. Run quality checks: `make ci`
6. Submit a pull request

## License

MIT License. See [LICENSE](LICENSE) for details.
```

### Coordination with Agent A

Before writing, agree on these points:
1. **Order of sections** — Installation before Quick Start (so users install first)
2. **Screenshot references** — Use relative paths from repo root
3. **No duplicate content** — Agent A's quickstart shows CLI usage; Agent B's dashboard section shows Streamlit usage
4. **Consistent formatting** — H2 for major sections, H3 for subsections, code blocks with language hints

## Outputs
- `README.md` (Agent B's sections: Installation, Dashboard, Configuration, Deployment, Extending, Contributing, License)
- Agent A contributes: Quick Start, Benchmark Results, Methodology sections

## Acceptance Criteria
1. README renders correctly on GitHub (check with `grip` or GitHub preview)
2. All screenshot references point to existing files (or placeholders)
3. Installation commands work: each `pip install -e ".[extras]"` succeeds
4. Dashboard section shows all 4 screenshots
5. Configuration example matches `scaffolder.yaml.example`
6. No broken links (EXTENSIBILITY.md, docs/deployment.md)
7. README is under 500 lines (concise, not overwhelming)

## Handoff Notes
- **To Agent A:** Coordinate on README structure. Agent B's sections are ready to merge. Your sections (Quick Start, Benchmark Results, Methodology) should reference the installation section for setup and the dashboard section for visual results.
- **To Day 19:** README is complete. Day 19 is dependency audit and CI configuration.
- **Decision:** We put Installation before Quick Start because users need to install before they can run anything. This is conventional for most README structures.
