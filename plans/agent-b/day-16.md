# Agent B — Day 16: Complete EXTENSIBILITY.md

## Mission
Write the remaining 6 sections of EXTENSIBILITY.md with comprehensive step-by-step instructions, code examples, and registration patterns for every extension point in the scaffolder.

## Context
Day 15 outlined EXTENSIBILITY.md and wrote sections 1-2 (Architecture Overview, Adding Test Fixtures). Today we complete sections 3-8: Adding Chunking Strategies, Adding Embedding Models, Adding Metrics, Adding Query Sets, Adding Output Formats, and Configuration Reference. This document is the primary guide for users who want to extend the scaffolder beyond the built-in defaults.

## Prerequisites
- `EXTENSIBILITY.md` with sections 1-2 (Day 15)
- Understanding of all extension points in the codebase
- `src/scaffolder/embedding/__init__.py` with `Embedder` protocol (Day 6)
- `src/scaffolder/queries.py` with YAML schema (Day 3)
- `src/scaffolder/config.py` with `BenchmarkConfig` (Day 2)

## Checklist
- [ ] Task 1 — Write section 3: Adding Chunking Strategies
- [ ] Task 2 — Write section 4: Adding Embedding Models
- [ ] Task 3 — Write section 5: Adding Metrics
- [ ] Task 4 — Write section 6: Adding Query Sets
- [ ] Task 5 — Write section 7: Adding Output Formats
- [ ] Task 6 — Write section 8: Configuration Reference

## Implementation Details

### Section 3: Adding Chunking Strategies

```markdown
## Adding Chunking Strategies

Chunking strategies are wrappers that take a `Document` and return a `ChunkSet`.
The scaffolder ships with four strategies; you can add your own.

### The Strategy Interface

A chunking strategy is any callable that matches this signature:

```python
from scaffolder.models import Document, Chunk, ChunkSet

def my_strategy(document: Document, **kwargs: Any) -> ChunkSet:
    """Chunk a document using my custom strategy."""
    chunks: list[Chunk] = []

    # Your chunking logic here
    # ...

    return ChunkSet(
        strategy="my_strategy",
        document_id=document.id,
        chunks=chunks,
        duration_ms=elapsed_ms,
        chunk_count=len(chunks),
        avg_chunk_size=avg_size,
    )
```

### Step-by-Step Example: Adding Chonkie

[Chonkie](https://github.com/chonkie-ai/chonkie) is a chunking library.
Here's how to add it as a strategy:

**Step 1:** Create `src/scaffolder/chunking/chonkie_strategy.py`:

```python
"""Chonkie chunking strategy wrapper."""

from __future__ import annotations

import time
from typing import Any

from scaffolder.models import Chunk, ChunkSet, Document


def chonkie_strategy(document: Document, **kwargs: Any) -> ChunkSet:
    """Chunk using Chonkie's semantic chunker."""
    from chonkie import SemanticChunker

    start = time.perf_counter()

    chunker = SemanticChunker(
        chunk_size=kwargs.get("chunk_size", 512),
        threshold=kwargs.get("threshold", 0.5),
    )
    raw_chunks = chunker.chunk(document.text)

    chunks = [
        Chunk(
            id=f"{document.id}_chonkie_{i}",
            text=rc.text,
            document_id=document.id,
            strategy="chonkie",
            index=i,
            metadata={"source": "chonkie"},
        )
        for i, rc in enumerate(raw_chunks)
    ]

    elapsed = (time.perf_counter() - start) * 1000
    avg_size = sum(len(c.text) for c in chunks) / max(len(chunks), 1) / 4

    return ChunkSet(
        strategy="chonkie",
        document_id=document.id,
        chunks=chunks,
        duration_ms=elapsed,
        chunk_count=len(chunks),
        avg_chunk_size=avg_size,
    )
```

**Step 2:** Register the strategy in `src/scaffolder/chunking/strategies.py`:

```python
from scaffolder.chunking.chonkie_strategy import chonkie_strategy

STRATEGY_REGISTRY["chonkie"] = chonkie_strategy
```

**Step 3:** Add to config:

```yaml
# scaffolder.yaml
strategies:
  - lexichunk
  - langchain_rcts
  - chonkie
```

**Step 4:** Update `VALID_STRATEGIES` in `config.py`:

```python
VALID_STRATEGIES = frozenset({
    "lexichunk", "langchain_rcts", "sentence_split", "fixed_512", "chonkie",
})
```

**Step 5:** Test it:

```bash
scaffolder benchmark --strategies lexichunk,chonkie
```
```

### Section 4: Adding Embedding Models

```markdown
## Adding Embedding Models

Embedding models implement the `Embedder` protocol defined in
`scaffolder.embedding`. There are two types: local models (sentence-transformers)
and API models (like Voyage AI).

### The Embedder Protocol

```python
from scaffolder.embedding import Embedder

class MyEmbedder:
    """Custom embedding adapter."""

    @property
    def model_name(self) -> str:
        return "my-model-v1"

    @property
    def dimension(self) -> int:
        return 768

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed documents."""
        # Your embedding logic
        return [[0.0] * self.dimension for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        """Embed a query (may differ from document embedding)."""
        return self.embed([text])[0]
```

### Example: Adding Nomic Embed

```python
# src/scaffolder/embedding/nomic.py
"""Nomic Embed adapter."""

from __future__ import annotations

from typing import Any


class NomicEmbedder:
    """Embedding adapter for Nomic's nomic-embed-text-v1.5."""

    def __init__(self, model_name: str = "nomic-embed-text-v1.5") -> None:
        self._model_name = model_name
        self._model: Any = None

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return 768

    def _get_model(self) -> Any:
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(
                self._model_name, trust_remote_code=True
            )
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        model = self._get_model()
        embeddings = model.encode(
            texts, convert_to_numpy=True, show_progress_bar=False
        )
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        return self.embed([text])[0]
```

Register in `scaffolder.embedding.__init__.py`:

```python
def create_embedder(model_name: str, config: object | None = None) -> Embedder:
    if model_name.startswith("voyage"):
        from scaffolder.embedding.voyage import VoyageEmbedder
        return VoyageEmbedder(model_name=model_name)
    elif model_name.startswith("nomic"):
        from scaffolder.embedding.nomic import NomicEmbedder
        return NomicEmbedder(model_name=model_name)
    else:
        from scaffolder.embedding.local import LocalEmbedder
        return LocalEmbedder(model_name=model_name)
```

Update `VALID_EMBEDDING_MODELS` in `config.py`.
```

### Section 5: Adding Metrics

```markdown
## Adding Metrics

### Structural Metrics

Structural metrics measure chunking quality without embeddings. They take a
`ChunkSet` and return a score.

```python
# src/scaffolder/metrics/custom_structural.py

from scaffolder.models import ChunkSet


def heading_preservation_rate(chunk_set: ChunkSet) -> float:
    """Measure how well section headings are preserved with their content.

    Returns 0.0-1.0 where 1.0 means all headings are in the same chunk
    as their first sub-section.
    """
    total_headings = 0
    preserved = 0

    for chunk in chunk_set.chunks:
        # Count headings in this chunk
        lines = chunk.text.split("\n")
        for i, line in enumerate(lines):
            if _is_heading(line):
                total_headings += 1
                # Check if the next non-empty line is also in this chunk
                remaining = "\n".join(lines[i + 1:]).strip()
                if remaining:
                    preserved += 1

    return preserved / max(total_headings, 1)
```

Register by adding to `scaffolder.metrics.structural`:

```python
STRUCTURAL_METRICS = {
    "clause_fragmentation_rate": clause_fragmentation_rate,
    "definition_preservation_rate": definition_preservation_rate,
    "cross_ref_resolution_rate": cross_ref_resolution_rate,
    "hierarchy_depth_retained": hierarchy_depth_retained,
    "heading_preservation_rate": heading_preservation_rate,  # new
}
```

### Retrieval Metrics

Retrieval metrics take a `RetrievalResult` and compute a score:

```python
def recall_at_k(result: RetrievalResult, k: int) -> float:
    """Compute recall@k for a retrieval result."""
    retrieved_top_k = set(result.retrieved_chunk_ids[:k])
    relevant = set(result.relevant_chunk_ids)
    if not relevant:
        return 0.0
    return len(retrieved_top_k & relevant) / len(relevant)
```
```

### Section 6: Adding Query Sets

```markdown
## Adding Query Sets

Query annotations define ground-truth relevance for evaluation queries.

### YAML Schema

```yaml
document_id: <document_id>
queries:
  - id: <unique_query_id>
    text: <natural_language_query>
    failure_mode: <clause_fragmentation|orphaned_cross_refs|lost_definitions|destroyed_hierarchy|cross_doc_contamination>
    relevant_sections:
      - section_id: <section_identifier>
        relevance: <3|2|1>  # 3=exact, 2=partial, 1=background
        description: <human_readable>
    notes: <explanation>
```

### Writing Good Queries

1. **Target a specific failure mode** — each query should test one weakness
2. **Include multiple relevant sections** — at least 2, ideally 3+
3. **Use graded relevance** — not everything is equally relevant
4. **Write realistic queries** — ask what a lawyer would ask
5. **Include edge cases** — ambiguous queries, multi-clause answers

### Relevance Mapping

Section IDs in the YAML are human labels. The scaffolder maps them to
chunk IDs at evaluation time by finding chunks that overlap with the
annotated section text. The mapping uses:

1. Text overlap: chunks containing text from the annotated section
2. Section ID matching: chunks whose `hierarchy_path` includes the section ID
3. Fuzzy matching: for sections that span chunk boundaries

See `scaffolder.retrieval.simulator` for the mapping implementation.
```

### Section 7: Adding Output Formats

```markdown
## Adding Output Formats

### Creating a Custom Reporter

```python
# src/scaffolder/reporting/csv_export.py

import csv
from pathlib import Path
from scaffolder.models import BenchmarkResult


def export_csv(result: BenchmarkResult, output_path: str | Path) -> Path:
    """Export structural results as CSV."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "strategy", "document_id",
            "clause_fragmentation_rate", "definition_preservation_rate",
            "cross_ref_resolution_rate", "hierarchy_depth_retained",
        ])
        for r in result.structural_results:
            writer.writerow([
                r.strategy, r.document_id,
                r.clause_fragmentation_rate, r.definition_preservation_rate,
                r.cross_ref_resolution_rate, r.hierarchy_depth_retained,
            ])

    return output_path
```

Add to `VALID_OUTPUT_FORMATS` in `config.py` and wire into the
benchmark runner.
```

### Section 8: Configuration Reference

```markdown
## Configuration Reference

### All Configuration Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `strategies` | `list[str]` | `["lexichunk", "langchain_rcts", "sentence_split", "fixed_512"]` | Chunking strategies to compare |
| `embedding_models` | `list[str]` | `["all-MiniLM-L6-v2"]` | Embedding models for retrieval |
| `enable_voyage` | `bool` | `false` | Enable Voyage AI embeddings |
| `voyage_model` | `str` | `"voyage-law-2"` | Voyage model to use |
| `fixture_dir` | `str` | `"src/scaffolder/fixtures/documents"` | Path to fixture documents |
| `query_dir` | `str` | `"queries"` | Path to query annotations |
| `output_dir` | `str` | `"results"` | Path for output files |
| `k_values` | `list[int]` | `[1, 3, 5, 10]` | k values for P@k and R@k |
| `top_k` | `int` | `10` | Number of results to retrieve |
| `significance_level` | `float` | `0.05` | Threshold for statistical tests |
| `use_cache` | `bool` | `true` | Cache embeddings to disk |
| `cache_dir` | `str` | `".cache/embeddings"` | Embedding cache directory |
| `output_formats` | `list[str]` | `["cli", "json"]` | Output format(s) |
| `fixed_chunk_size` | `int` | `512` | Token size for fixed chunking |
| `fixed_chunk_overlap` | `int` | `50` | Overlap for fixed chunking |
| `rcts_chunk_size` | `int` | `1000` | Size for RCTS chunking |
| `rcts_chunk_overlap` | `int` | `200` | Overlap for RCTS chunking |

### Environment Variables

All fields can be overridden via `SCAFFOLDER_` prefixed env vars:

```bash
export SCAFFOLDER_STRATEGIES=lexichunk,fixed_512
export SCAFFOLDER_TOP_K=20
export SCAFFOLDER_OUTPUT_FORMATS=cli,json,html
export VOYAGE_API_KEY=your-key  # Auto-enables Voyage
```

### Precedence

1. Environment variables (highest)
2. YAML config file
3. Defaults (lowest)
```

## Outputs
- `EXTENSIBILITY.md` (complete — all 8 sections)

## Acceptance Criteria
1. EXTENSIBILITY.md has all 8 sections with complete content
2. Every section has at least one working code example
3. Adding a chunking strategy requires exactly 4 steps (documented)
4. Adding an embedding model requires exactly 3 steps (documented)
5. Configuration reference table covers all `BenchmarkConfig` fields
6. All code examples are syntactically valid Python
7. File renders correctly as GitHub markdown

## Handoff Notes
- **To Agent A:** EXTENSIBILITY.md references your modules: `FixtureManager.register()`, `ChunkingPipeline.register_strategy()`, `STRUCTURAL_METRICS` dict, `RetrievalSimulator` mapping logic. Make sure these extension points exist or adjust the docs to match your implementation.
- **To Day 17:** EXTENSIBILITY.md is done. Day 17 focuses on Streamlit edge cases and error handling.
- **Decision:** We documented extension points as they exist in the code today, plus a few aspirational ones (like `register_strategy()`) that may need Agent A to implement. The important thing is that the *pattern* is clear even if the exact API evolves.
