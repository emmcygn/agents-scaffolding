# LexiChunk Scaffolder

> Evaluation harness proving LexiChunk measurably improves RAG retrieval quality over general-purpose alternatives for legal documents.

## Highlights

- Compares LexiChunk against 3 baselines (LangChain RCTS, sentence-split, fixed-512)
- 5 structural metrics + retrieval metrics with statistical significance
- 22+ annotated legal queries across 5 fixture documents
- Interactive Streamlit dashboard with side-by-side comparison
- CLI output with rich tables and colour-coded results
- Supports local embeddings (MiniLM, BGE) and Voyage AI (voyage-law-2)

## Installation

### Basic (development)

```bash
git clone https://github.com/emmcygn/sdk-scaffolder.git
cd sdk-scaffolder
pip install -e ".[dev]"
```

### With local embeddings

```bash
pip install -e ".[embeddings,dev]"
```

### With Voyage AI

```bash
pip install -e ".[voyage,dev]"
export VOYAGE_API_KEY=your-key-here
```

### Everything

```bash
pip install -e ".[all]"
```

### Dependency Groups

| Extra | Packages | Use Case |
|-------|----------|----------|
| `dev` | ruff, mypy, pytest, pytest-cov | Development and testing |
| `embeddings` | sentence-transformers, faiss-cpu | Local embedding models |
| `voyage` | voyageai | Voyage AI API embeddings |
| `dashboard` | streamlit, plotly | Interactive dashboard |
| `all` | Everything above | Full installation |

## Quick Start

```bash
# Run structural benchmark (no embeddings needed)
make benchmark-structural

# Run full benchmark with embeddings
make benchmark

# View results in CLI
make report

# Launch dashboard
make dashboard
```

## Dashboard

The Streamlit dashboard provides three views:

### Compare Chunks
Side-by-side comparison of LexiChunk vs. baseline chunking on the same document. Select from built-in fixtures, upload your own, or paste text.

### Retrieval Demo
Ask a legal question and compare retrieval results across strategies. Uses annotated ground-truth queries to measure correctness.

### Metrics Dashboard
Summary panels with headline metrics, comparison charts, and statistical significance results.

```bash
# Launch locally
make dashboard

# Or directly
streamlit run src/scaffolder/dashboard/app.py
```

## Benchmark Results

LexiChunk consistently outperforms general-purpose chunking strategies across both structural quality and retrieval metrics on 5 legal documents (UK, US, EU jurisdictions).

### Structural Quality (averaged across 5 legal documents)

| Metric | LexiChunk | RCTS-512 | Sentence Split | Fixed-512 |
|--------|-----------|----------|----------------|-----------|
| Clause Fragmentation (lower=better) | **0.000** | 0.611 | 0.786 | 0.657 |
| Definition Preservation | **1.000** | 0.988 | 0.988 | 0.976 |
| Cross-Ref Resolution | **1.000** | 1.000 | 1.000 | 0.995 |
| Hierarchy Depth Retained | **1.00** | 0.55 | 0.55 | 0.55 |

LexiChunk achieves **zero clause fragmentation** across all documents, compared to 61-79% fragmentation for baselines. Hierarchy depth is fully preserved (1.00 vs 0.55).

### Architecture

```
Fixtures --> ChunkingPipeline --> EmbeddingPipeline --> FAISS Index
(5 docs)    (5 strategies)      (3 models)            (top-k search)
                                                           |
Reports <-- Significance <-- RetrievalMetrics <-- RetrievalSimulator
(CLI/JSON/   Testing         (P@k, R@k, MRR,      (22 queries)
 HTML)                        NDCG, DRM)
```

**Source layout:**
- `src/scaffolder/fixtures/` -- Document loading and management
- `src/scaffolder/chunking/` -- Strategy wrappers and pipeline
- `src/scaffolder/embedding/` -- Model adapters and caching
- `src/scaffolder/retrieval/` -- FAISS indexing and query simulation
- `src/scaffolder/metrics/` -- Structural, retrieval, and statistical metrics
- `src/scaffolder/reporting/` -- CLI (rich), JSON, HTML (Jinja2) output
- `src/scaffolder/dashboard/` -- Streamlit interactive dashboard

## Configuration

Copy and customize the example config:

```bash
cp scaffolder.yaml.example scaffolder.yaml
```

Key settings:

```yaml
strategies: [lexichunk, langchain_rcts, sentence_split, fixed_512]
embedding_models: [all-MiniLM-L6-v2]
k_values: [1, 3, 5, 10]
top_k: 10
significance_level: 0.05
```

Environment variable overrides use `SCAFFOLDER_` prefix:

```bash
export SCAFFOLDER_STRATEGIES="lexichunk,fixed_512"
export SCAFFOLDER_TOP_K=20
```

See [EXTENSIBILITY.md](EXTENSIBILITY.md) for the full configuration reference.

## Deployment

### Streamlit Community Cloud

1. Push to GitHub
2. Connect at share.streamlit.io
3. Set main file to `streamlit_app.py`
4. Set `VOYAGE_API_KEY` in Advanced Settings (optional)

### Docker

```bash
docker build -t scaffolder .
docker run -p 8501:8501 scaffolder
```

See [docs/deployment.md](docs/deployment.md) for detailed instructions.

## Extending the Scaffolder

The scaffolder is designed to be extended with custom:

- **Test fixtures** — add `.txt` documents to `fixtures/documents/`
- **Chunking strategies** — implement the `ChunkingStrategy` protocol
- **Embedding models** — add sentence-transformers or API adapters
- **Metrics** — add structural or retrieval quality metrics
- **Query sets** — add YAML annotation files to `queries/`
- **Output formats** — add CLI, JSON, or HTML reporters

See [EXTENSIBILITY.md](EXTENSIBILITY.md) for step-by-step guides.

## Development

```bash
# Install dev dependencies
make install

# Run linter
make lint

# Auto-format
make format

# Run tests
make test

# Run all CI checks
make ci
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Run `make ci` to verify all checks pass
4. Submit a pull request

## License

MIT
