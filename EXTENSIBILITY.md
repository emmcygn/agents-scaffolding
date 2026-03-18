# Extensibility Guide

This document describes how to extend the scaffolder with custom fixtures, chunking strategies, embedding models, metrics, queries, and output formats.

## 1. Architecture Overview

The scaffolder follows a plugin architecture:

```
Document → Chunking Strategies → ChunkSets → Embedding → FAISS Index → Retrieval → Metrics
```

Each stage is independently extensible through well-defined interfaces.

### Key Extension Points

| Component | Interface | Registration |
|-----------|----------|-------------|
| Chunking strategies | `ChunkingStrategy` protocol | `chunking/__init__.py` registry |
| Embedding models | `Embedder` protocol | `embedding/__init__.py` factory |
| Metrics | Functions in `metrics/` | Called by pipeline |
| Test fixtures | `.txt` files | `fixtures/documents/` + metadata |
| Queries | YAML files | `queries/*.yaml` |
| Output formats | Functions in `reporting/` | Config `output_formats` |

## 2. Adding Test Fixtures

### Step 1: Create the document file

Place a `.txt` file in `src/scaffolder/fixtures/documents/`:

```
src/scaffolder/fixtures/documents/my_contract.txt
```

### Step 2: Register metadata

Add an entry to `_FIXTURE_METADATA` in `src/scaffolder/fixtures/__init__.py`:

```python
_FIXTURE_METADATA["my_contract.txt"] = (Jurisdiction.US, DocumentType.MSA)
```

If you need new jurisdiction or document type values, add them to the enums in `models.py`.

### Step 3: Add queries

Create `queries/my_contract.yaml` following the schema in `queries/schema.md`.

## 3. Adding Chunking Strategies

### The Strategy Interface

A chunking strategy must implement the `ChunkingStrategy` protocol from `models.py`:

```python
from scaffolder.models import ChunkingStrategy, Document, ChunkSet, Chunk, StrategyName

class MyStrategy:
    name = StrategyName.LEXICHUNK  # Add your own enum value first

    def chunk(self, document: Document) -> ChunkSet:
        chunks = []
        # Your chunking logic here
        return ChunkSet(
            strategy=self.name,
            document_id=document.id,
            chunks=tuple(chunks),
            elapsed_seconds=0.0,
        )
```

### Registration

1. Add a new `StrategyName` enum value in `models.py`
2. Create your strategy class in `src/scaffolder/chunking/strategies.py` (or a new file)
3. Register in `src/scaffolder/chunking/__init__.py`:

```python
_STRATEGY_REGISTRY[StrategyName.MY_STRATEGY] = MyStrategy
```

4. Add the strategy name to `VALID_STRATEGIES` in `config.py`

## 4. Adding Embedding Models

### Local Models (sentence-transformers)

The `EmbeddingPipeline` in `embedding/pipeline.py` supports any sentence-transformers model. To add a new one:

1. Add a new `EmbeddingModelName` enum value in `models.py`
2. Add the HuggingFace model ID mapping in `embedding/pipeline.py`:

```python
_MODEL_IDS[EmbeddingModelName.MY_MODEL] = "org/my-model-name"
```

3. Add to `VALID_EMBEDDING_MODELS` in `config.py`

### API-Based Models

Follow the `VoyageEmbedder` pattern in `embedding/voyage.py`:

1. Implement `embed(texts)` and `embed_query(text)` methods
2. Handle rate limiting and error cases
3. Register in the `EmbeddingPipeline._get_adapter()` factory

## 5. Adding Metrics

### Structural Metrics

Add new metric functions in `src/scaffolder/metrics/structural.py`. Each function takes a `ChunkSet` and returns a float:

```python
def my_metric(chunk_set: ChunkSet, document: Document) -> float:
    """Compute my custom metric. Returns 0.0-1.0."""
    # Your logic here
    return score
```

Wire it into the `compute_structural_metrics()` pipeline function.

### Retrieval Metrics

Add to `src/scaffolder/metrics/` following the existing pattern. Retrieval metrics take `RetrievalResult` objects and compute precision, recall, etc.

## 6. Adding Query Sets

### YAML Schema

Each query file follows this schema (see `queries/schema.md` for full details):

```yaml
document_id: my_contract
queries:
  - id: my_q1
    text: "What are the payment terms?"
    failure_mode: clause_fragmentation
    relevant_sections:
      - section_id: "clause_payment"
        relevance: 3
        description: "Payment terms clause"
    notes: "Tests whether the chunker keeps payment terms together."
```

### Valid Failure Modes

- `clause_fragmentation` — clause split across chunks
- `orphaned_cross_refs` — cross-references lost
- `lost_definitions` — defined terms separated from usage
- `destroyed_hierarchy` — section hierarchy broken
- `cross_doc_contamination` — wrong document's content retrieved

### Adding Queries

1. Create `queries/<document_id>.yaml`
2. Follow the naming convention: `{jurisdiction}_{doc_abbrev}_q{N}` for query IDs
3. Each query must have at least one `relevant_section` with a `relevance` grade (3=exact, 2=partial, 1=background)

## 7. Adding Output Formats

### CLI Reporters

Add functions to `src/scaffolder/reporting/cli.py` that accept `BenchmarkResult` and render with Rich:

```python
def render_my_table(result: BenchmarkResult, console: Console | None = None) -> None:
    # Use Rich Table, Panel, etc.
    pass
```

### JSON Export

The JSON exporter in `reporting/json_export.py` uses `dataclasses.asdict()` — any new dataclass fields are automatically included.

### HTML Reports

Add Jinja2 templates to `src/scaffolder/reporting/templates/` and rendering functions to `reporting/html.py`.

## 8. Configuration Reference

All configuration is managed through `BenchmarkConfig` in `config.py`.

### Precedence (highest to lowest)
1. Environment variables (`SCAFFOLDER_*`)
2. YAML config file (`scaffolder.yaml`)
3. Defaults

### Key Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `strategies` | `list[str]` | All 4 | Chunking strategies to compare |
| `embedding_models` | `list[str]` | `["all-MiniLM-L6-v2"]` | Embedding models |
| `enable_voyage` | `bool` | `False` | Enable Voyage AI |
| `k_values` | `list[int]` | `[1,3,5,10]` | K values for P@k |
| `top_k` | `int` | `10` | Max results per query |
| `significance_level` | `float` | `0.05` | Statistical test threshold |
| `fixed_chunk_size` | `int` | `512` | Fixed-size baseline chunk size |
| `rcts_chunk_size` | `int` | `1000` | RCTS baseline chunk size |

### Environment Variables

All fields can be overridden with `SCAFFOLDER_` prefix:

```bash
export SCAFFOLDER_STRATEGIES="lexichunk,fixed_512"
export SCAFFOLDER_TOP_K=20
export SCAFFOLDER_ENABLE_VOYAGE=true
export VOYAGE_API_KEY=your-key-here
```
