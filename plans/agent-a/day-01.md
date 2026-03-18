# Agent A — Day 01: Repo Init & Data Model Contracts

## Mission
Establish the repository skeleton and define every shared data model and protocol interface so that both agents build against the same contracts from day one.

## Context
This is the very first day of the sdk-scaffolder project. Nothing exists yet. Agent A and Agent B are PAIRING today. Agent B will handle `pyproject.toml` authoring, `.gitignore`, `Makefile` skeleton, and `config.py`. Agent A owns the data models in `models.py` and the protocol interfaces. Both agents must agree on every field name and type before proceeding.

## Prerequisites
- Python 3.10+ installed
- `lexichunk` installable via pip (used as a reference for type signatures)
- Git initialized in the repo root

## Checklist
- [ ] Create directory structure: `src/scaffolder/`, all sub-packages with `__init__.py`
- [ ] Write `src/scaffolder/__init__.py` with package version
- [ ] Write `src/scaffolder/models.py` with all data classes and protocols
- [ ] Write stub `__init__.py` for every sub-package
- [ ] Verify imports work: `python -c "from scaffolder.models import Document, Chunk"`
- [ ] Coordinate with Agent B on pyproject.toml and config.py field names

## Implementation Details

### Directory Structure
Create the following directories, each with an `__init__.py`:

```
src/scaffolder/
src/scaffolder/fixtures/
src/scaffolder/fixtures/documents/
src/scaffolder/chunking/
src/scaffolder/embedding/
src/scaffolder/retrieval/
src/scaffolder/metrics/
src/scaffolder/reporting/
src/scaffolder/reporting/templates/
src/scaffolder/dashboard/
```

### Package Init (`src/scaffolder/__init__.py`)

```python
"""sdk-scaffolder: Evaluation harness for LexiChunk vs baseline chunking strategies."""

__version__ = "0.1.0"
```

### Data Models (`src/scaffolder/models.py`)

Use `dataclasses` with `__slots__` for performance. Use `typing.Protocol` for interfaces. All models are immutable (`frozen=True`) except where mutation is required.

```python
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Protocol, Sequence, runtime_checkable

import numpy as np


# -- Enums ------------------------------------------------------------------

class Jurisdiction(str, enum.Enum):
    UK = "uk"
    US = "us"
    EU = "eu"


class DocumentType(str, enum.Enum):
    SERVICE_AGREEMENT = "service_agreement"
    TERMS_CONDITIONS = "terms_conditions"
    MSA = "msa"
    TERMS_OF_SERVICE = "terms_of_service"
    GDPR_EXCERPT = "gdpr_excerpt"


class StrategyName(str, enum.Enum):
    LEXICHUNK = "lexichunk"
    LEXICHUNK_CONTEXTUAL = "lexichunk_contextual"
    RCTS = "rcts"
    SENTENCE_SPLIT = "sentence_split"
    FIXED_SIZE = "fixed_size"


class EmbeddingModelName(str, enum.Enum):
    MINILM = "all-MiniLM-L6-v2"
    BGE_BASE = "bge-base-en-v1.5"
    VOYAGE_LAW_2 = "voyage-law-2"


class RelevanceGrade(int, enum.Enum):
    EXACT = 3          # Chunk contains the exact answer passage
    SAME_SECTION = 2   # Chunk is from the correct section
    RELATED = 1        # Chunk is topically related
    IRRELEVANT = 0     # Chunk is not relevant


# -- Document ---------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Document:
    """A legal document loaded from fixtures."""
    id: str                      # e.g. "uk_service_agreement"
    text: str                    # full document text
    jurisdiction: Jurisdiction
    document_type: DocumentType
    source: str                  # filename, e.g. "uk_service_agreement.txt"
    char_count: int = field(init=False)
    line_count: int = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "char_count", len(self.text))
        object.__setattr__(self, "line_count", self.text.count("\n") + 1)


# -- Chunk ------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Chunk:
    """A single chunk produced by any strategy."""
    id: str                      # unique: f"{strategy}_{doc_id}_{index}"
    text: str
    document_id: str
    strategy: StrategyName
    index: int                   # position within the chunk set
    char_count: int = field(init=False)
    metadata: dict = field(default_factory=dict, hash=False)
    # metadata may include: clause_type, confidence, defined_terms,
    # cross_references, section_hierarchy, embedded_text (contextual)

    def __post_init__(self) -> None:
        object.__setattr__(self, "char_count", len(self.text))


# -- ChunkSet ---------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class ChunkSet:
    """All chunks produced by one strategy on one document."""
    strategy: StrategyName
    document_id: str
    chunks: tuple[Chunk, ...]     # immutable sequence
    elapsed_seconds: float        # wall-clock time for chunking

    @property
    def count(self) -> int:
        return len(self.chunks)

    @property
    def avg_chunk_size(self) -> float:
        if not self.chunks:
            return 0.0
        return sum(c.char_count for c in self.chunks) / len(self.chunks)


# -- Strategy Result --------------------------------------------------------

@dataclass(frozen=True, slots=True)
class StrategyResult:
    """Result of running one strategy across ALL documents."""
    strategy: StrategyName
    chunk_sets: tuple[ChunkSet, ...]  # one per document
    total_elapsed_seconds: float


# -- Structural Metrics -----------------------------------------------------

@dataclass(frozen=True, slots=True)
class StructuralMetrics:
    """Structural quality metrics for one ChunkSet."""
    strategy: StrategyName
    document_id: str
    clause_fragmentation_rate: float     # 0.0 = no fragmentation (best)
    definition_preservation_rate: float  # 1.0 = all preserved (best)
    cross_ref_resolution_rate: float     # 1.0 = all resolved (best)
    hierarchy_depth_retained: float      # 1.0 = full depth kept (best)
    chunk_size_cv: float                 # coefficient of variation (lower = more uniform)
    chunk_count: int
    avg_chunk_chars: float


# -- Retrieval Types --------------------------------------------------------

@dataclass(frozen=True, slots=True)
class RelevantSection:
    """A ground-truth relevant passage for a query."""
    document_id: str
    section_id: str              # e.g. "clause_5.2"
    text_snippet: str            # First 200 chars for fuzzy matching
    grade: RelevanceGrade


@dataclass(frozen=True, slots=True)
class AnnotatedQuery:
    """A query with human-annotated relevant chunks/sections."""
    id: str
    text: str
    document_ids: list[str]          # which documents this query targets
    jurisdiction: Jurisdiction
    relevant_sections: tuple[RelevantSection, ...]
    category: str                    # e.g. "definition_lookup", "clause_search"


@dataclass(frozen=True, slots=True)
class RetrievalHit:
    """A single retrieved chunk with its similarity score."""
    chunk: Chunk
    score: float
    rank: int


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    """Result of running one query against one strategy's index."""
    query: AnnotatedQuery
    strategy: StrategyName
    embedding_model: EmbeddingModelName
    hits: tuple[RetrievalHit, ...]           # ordered by rank
    relevant_retrieved: int                  # how many of top-k were relevant
    total_relevant: int                      # total annotated relevant


# -- Retrieval Metrics ------------------------------------------------------

@dataclass(frozen=True, slots=True)
class RetrievalMetrics:
    """Retrieval quality metrics for one query x one strategy x one model."""
    query_id: str
    strategy: StrategyName
    embedding_model: EmbeddingModelName
    precision_at_1: float
    precision_at_3: float
    precision_at_5: float
    precision_at_10: float
    recall_at_1: float
    recall_at_3: float
    recall_at_5: float
    recall_at_10: float
    mrr: float
    ndcg_at_10: float
    drm_hit: bool                 # Document Retrieval Mismatch: pulled from wrong doc?


# -- Statistical Significance -----------------------------------------------

@dataclass(frozen=True, slots=True)
class SignificanceResult:
    """Result of a paired t-test comparing two strategies."""
    metric_name: str
    strategy_a: StrategyName       # always LexiChunk
    strategy_b: StrategyName       # the baseline
    mean_a: float
    mean_b: float
    improvement_pct: float         # ((mean_a - mean_b) / mean_b) * 100
    t_statistic: float
    p_value: float
    significant: bool              # p < 0.05
    effect_size: float             # Cohen's d
    n_queries: int


# -- Benchmark Result -------------------------------------------------------

@dataclass(slots=True)
class BenchmarkResult:
    """Top-level result container for a full benchmark run."""
    timestamp: str                          # ISO 8601
    strategies: list[StrategyName] = field(default_factory=list)
    documents: list[str] = field(default_factory=list)
    models: list[EmbeddingModelName] = field(default_factory=list)
    structural_metrics: list[StructuralMetrics] = field(default_factory=list)
    retrieval_metrics: list[RetrievalMetrics] = field(default_factory=list)
    significance_results: list[SignificanceResult] = field(default_factory=list)
    strategy_results: list[StrategyResult] = field(default_factory=list)
    config: dict = field(default_factory=dict)


# -- Protocols --------------------------------------------------------------

@runtime_checkable
class ChunkingStrategy(Protocol):
    """Interface that every chunking strategy wrapper must implement."""
    name: StrategyName

    def chunk(self, document: Document) -> ChunkSet:
        """Chunk a document, returning a ChunkSet with timing info."""
        ...


@runtime_checkable
class Embedder(Protocol):
    """Interface for embedding adapters (local or API-based)."""
    model_name: EmbeddingModelName
    dimension: int

    def embed_texts(self, texts: Sequence[str]) -> np.ndarray:
        """Embed a batch of texts. Returns array of shape (n, dimension), dtype float32."""
        ...
```

Key design decisions:
- Enums inherit from `str` for JSON serialization friendliness.
- `RelevanceGrade` inherits from `int` so `.value` returns the numeric grade directly for NDCG.
- `Chunk.metadata` is a plain dict so LexiChunk-specific fields (clause_type, defined_terms, etc.) live there without polluting the base class.
- `ChunkSet.chunks` is a tuple (immutable). Same for `StrategyResult.chunk_sets`.
- `BenchmarkResult` is NOT frozen because it accumulates results over a run.
- Protocols use `runtime_checkable` so we can assert at registration time.
- All floats in metrics are 0.0-1.0 unless otherwise noted (chunk_size_cv can exceed 1.0).
- `SignificanceResult` includes `improvement_pct` and `effect_size` (Cohen's d) for practical significance.

### Sub-package `__init__.py` Stubs

Each sub-package `__init__.py` should re-export its main classes. For Day 1 these are empty except for a docstring:

- `src/scaffolder/fixtures/__init__.py`: `"""Fixture loading and document management."""`
- `src/scaffolder/chunking/__init__.py`: `"""Chunking pipeline and strategy wrappers."""`
- `src/scaffolder/embedding/__init__.py`: `"""Embedding pipeline and model adapters."""`
- `src/scaffolder/retrieval/__init__.py`: `"""FAISS indexing and retrieval simulation."""`
- `src/scaffolder/metrics/__init__.py`: `"""Structural and retrieval quality metrics."""`
- `src/scaffolder/reporting/__init__.py`: `"""CLI, JSON, and HTML report generation."""`
- `src/scaffolder/dashboard/__init__.py`: `"""Streamlit dashboard (owned by Agent B)."""`

## Outputs
- `src/scaffolder/__init__.py`
- `src/scaffolder/models.py`
- `src/scaffolder/fixtures/__init__.py`
- `src/scaffolder/fixtures/documents/` (empty directory, placeholder)
- `src/scaffolder/chunking/__init__.py`
- `src/scaffolder/embedding/__init__.py`
- `src/scaffolder/retrieval/__init__.py`
- `src/scaffolder/metrics/__init__.py`
- `src/scaffolder/reporting/__init__.py`
- `src/scaffolder/reporting/templates/` (empty directory)
- `src/scaffolder/dashboard/__init__.py`

## Acceptance Criteria
1. `python -c "from scaffolder.models import Document, Chunk, ChunkSet, StrategyResult, BenchmarkResult, StrategyName, ChunkingStrategy, Embedder"` succeeds.
2. `python -c "from scaffolder.models import Jurisdiction; print(Jurisdiction.UK.value)"` prints `uk`.
3. `python -c "from scaffolder.models import RelevanceGrade; print(RelevanceGrade.EXACT.value)"` prints `3`.
4. `mypy src/scaffolder/models.py --strict` passes with zero errors.
5. `ruff check src/scaffolder/` passes with zero warnings.
6. Agent B confirms `pyproject.toml` installs the package in editable mode (`pip install -e ".[dev]"`).

## Handoff Notes
- **To Agent B:** The `BenchmarkResult.config` dict will hold whatever your `config.py` produces. We should agree on the schema: at minimum `strategies: list[str]`, `embedding_models: list[str]`, `k_values: list[int]`, `significance_alpha: float`. Your `BenchmarkConfig` dataclass should live in `config.py` and import `StrategyName`, `EmbeddingModelName` from `models.py`.
- **To Day 2:** The `Document` dataclass is ready. `FixtureManager` will create `Document` instances from `.txt` files. The `jurisdiction` and `document_type` fields must be inferred from filenames using a mapping dict. Note that `Document` now has both `char_count` and `line_count` computed fields.
- **Decision:** We use tuples (not lists) for immutable sequences in frozen dataclasses. This avoids hash issues and signals immutability.
- **Decision:** `StrategyName` has 5 members including `LEXICHUNK_CONTEXTUAL` for Day 12. Strategies that are not yet implemented simply won't be registered.
- **Decision:** `AnnotatedQuery.document_ids` is a list (not single ID) to support cross-document queries for DRM testing.
