# Agent A — Day 07: VectorIndex — FAISS Wrapper

## Mission
Build the FAISS-based VectorIndex that stores embeddings for each (strategy, model) pair and supports top-k similarity search, enabling the retrieval simulation layer to query against chunked documents.

## Context
Day 6 delivered the `EmbeddingPipeline` with local adapters (MiniLM, BGE) and disk caching. We now have embeddings as `np.ndarray` of shape `(n_chunks, dim)`. Today we wrap FAISS to provide index-per-(strategy, model) storage with search. Agent B is working on query YAML annotations today, which we will consume on Day 8.

## Prerequisites
- `src/scaffolder/embedding/pipeline.py` with `EmbeddingPipeline` and `embed_chunks()`
- `src/scaffolder/models.py` with `Chunk`, `ChunkSet`, `StrategyName`, `EmbeddingModelName`, `RetrievalHit`
- `faiss-cpu` installed (`pip install faiss-cpu`)
- `numpy` installed

## Checklist
- [ ] Implement `VectorIndex` class in `src/scaffolder/retrieval/index.py`
- [ ] Implement `IndexRegistry` to manage indices per (strategy, model) pair
- [ ] Support multi-document indexing (all 5 docs in one index for DRM testing)
- [ ] Support single-document indexing (for per-doc analysis)
- [ ] Write tests in `tests/test_retrieval_index.py`

## Implementation Details

### VectorIndex (`src/scaffolder/retrieval/index.py`)

```python
"""FAISS-based vector index for similarity search."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Sequence

import faiss
import numpy as np
import numpy.typing as npt

from scaffolder.models import (
    Chunk,
    EmbeddingModelName,
    RetrievalHit,
    StrategyName,
)

logger = logging.getLogger(__name__)


class VectorIndex:
    """FAISS flat L2 index wrapping chunk embeddings.

    Stores chunk references alongside their vectors so search results
    can be mapped back to Chunk objects.

    Usage:
        index = VectorIndex(dimension=384)
        index.add(chunks, embeddings)  # embeddings: (n, 384)
        hits = index.search(query_vector, k=10)  # returns list[RetrievalHit]
    """

    def __init__(self, dimension: int) -> None:
        self._dimension = dimension
        # Use IndexFlatIP (inner product) since embeddings are normalized.
        # IP on normalized vectors = cosine similarity.
        self._index = faiss.IndexFlatIP(dimension)
        self._chunks: list[Chunk] = []

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def size(self) -> int:
        """Number of vectors in the index."""
        return self._index.ntotal

    def add(
        self,
        chunks: Sequence[Chunk],
        embeddings: npt.NDArray[np.float32],
    ) -> None:
        """Add chunks and their embeddings to the index.

        Args:
            chunks: Chunk objects (must be same length as embeddings).
            embeddings: (n, dimension) float32 array. Must be L2-normalized.

        Raises:
            ValueError: If chunks and embeddings have mismatched lengths or dimensions.
        """
        if len(chunks) != embeddings.shape[0]:
            raise ValueError(
                f"Chunks ({len(chunks)}) and embeddings ({embeddings.shape[0]}) "
                f"length mismatch."
            )
        if embeddings.shape[1] != self._dimension:
            raise ValueError(
                f"Embedding dimension ({embeddings.shape[1]}) != "
                f"index dimension ({self._dimension})."
            )

        # Ensure float32 and contiguous
        embeddings = np.ascontiguousarray(embeddings, dtype=np.float32)

        self._chunks.extend(chunks)
        self._index.add(embeddings)
        logger.debug("Added %d vectors to index (total: %d)", len(chunks), self.size)

    def search(
        self,
        query_vector: npt.NDArray[np.float32],
        k: int = 10,
    ) -> list[RetrievalHit]:
        """Search for the k most similar chunks to the query vector.

        Args:
            query_vector: (1, dimension) or (dimension,) float32 array.
            k: Number of results to return.

        Returns:
            List of RetrievalHit ordered by descending similarity score.
        """
        if self.size == 0:
            return []

        # Reshape to (1, d) if needed
        qv = query_vector.reshape(1, -1).astype(np.float32)
        qv = np.ascontiguousarray(qv)

        # Clamp k to index size
        actual_k = min(k, self.size)

        scores, indices = self._index.search(qv, actual_k)

        hits: list[RetrievalHit] = []
        for rank, (idx, score) in enumerate(zip(indices[0], scores[0])):
            if idx < 0:
                continue  # FAISS returns -1 for missing results
            hits.append(RetrievalHit(
                chunk=self._chunks[int(idx)],
                score=float(score),
                rank=rank + 1,  # 1-indexed
            ))

        return hits

    def reset(self) -> None:
        """Clear the index and all stored chunks."""
        self._index.reset()
        self._chunks.clear()
```

### IndexRegistry

Manages one `VectorIndex` per (strategy, model) combination:

```python
@dataclass(frozen=True, slots=True)
class IndexKey:
    """Key for looking up a VectorIndex."""
    strategy: StrategyName
    model: EmbeddingModelName


class IndexRegistry:
    """Registry of VectorIndex instances keyed by (strategy, model).

    Usage:
        registry = IndexRegistry()
        registry.build(strategy_name, model_name, chunks, embeddings, dim)
        index = registry.get(strategy_name, model_name)
        hits = index.search(query_vec, k=10)
    """

    def __init__(self) -> None:
        self._indices: dict[IndexKey, VectorIndex] = {}

    def build(
        self,
        strategy: StrategyName,
        model: EmbeddingModelName,
        chunks: Sequence[Chunk],
        embeddings: npt.NDArray[np.float32],
        dimension: int | None = None,
    ) -> VectorIndex:
        """Build and register a new index.

        If an index already exists for this key, it is replaced.
        """
        dim = dimension or embeddings.shape[1]
        key = IndexKey(strategy=strategy, model=model)

        index = VectorIndex(dimension=dim)
        index.add(chunks, embeddings)
        self._indices[key] = index

        logger.info(
            "Built index for %s/%s: %d vectors, %d dims",
            strategy.value, model.value, index.size, dim,
        )
        return index

    def get(self, strategy: StrategyName, model: EmbeddingModelName) -> VectorIndex:
        """Get a previously built index.

        Raises:
            KeyError: If no index exists for this (strategy, model) pair.
        """
        key = IndexKey(strategy=strategy, model=model)
        if key not in self._indices:
            available = [(k.strategy.value, k.model.value) for k in self._indices]
            raise KeyError(
                f"No index for ({strategy.value}, {model.value}). "
                f"Available: {available}"
            )
        return self._indices[key]

    def keys(self) -> list[IndexKey]:
        """Return all registered (strategy, model) keys."""
        return list(self._indices.keys())

    @property
    def count(self) -> int:
        return len(self._indices)
```

### Building Indices from Pipeline Results

Add a helper function that builds all indices from strategy results + embedding pipeline:

```python
def build_all_indices(
    strategy_results: list[StrategyResult],
    embedding_pipeline: EmbeddingPipeline,
    models: Sequence[EmbeddingModelName],
) -> IndexRegistry:
    """Build FAISS indices for every (strategy, model) pair.

    For each strategy, concatenates all chunks from all documents into
    a single index (multi-document). This is required for DRM testing
    where retrieval may pull from any document.

    Args:
        strategy_results: Output of ChunkingPipeline.run().
        embedding_pipeline: Configured EmbeddingPipeline.
        models: List of embedding models to use.

    Returns:
        IndexRegistry with one VectorIndex per (strategy, model).
    """
    from scaffolder.models import StrategyResult

    registry = IndexRegistry()

    for sr in strategy_results:
        # Collect all chunks across all documents for this strategy
        all_chunks: list[Chunk] = []
        for cs in sr.chunk_sets:
            all_chunks.extend(cs.chunks)

        if not all_chunks:
            logger.warning("No chunks for strategy %s, skipping.", sr.strategy.value)
            continue

        for model in models:
            embeddings = embedding_pipeline.embed_chunks(all_chunks, model)
            registry.build(sr.strategy, model, all_chunks, embeddings)

    return registry
```

### Package init (`src/scaffolder/retrieval/__init__.py`)

```python
"""FAISS indexing and retrieval simulation."""

from scaffolder.retrieval.index import (
    VectorIndex,
    IndexKey,
    IndexRegistry,
    build_all_indices,
)

__all__ = [
    "VectorIndex",
    "IndexKey",
    "IndexRegistry",
    "build_all_indices",
]
```

### Tests (`tests/test_retrieval_index.py`)

```python
"""Tests for VectorIndex and IndexRegistry."""

# Test with synthetic embeddings (random float32 arrays, normalized):

# 1. VectorIndex.add() accepts matching chunks and embeddings
# 2. VectorIndex.search() returns correct number of results (k)
# 3. VectorIndex.search() results are sorted by descending score
# 4. VectorIndex.search() with k > index size returns index size results
# 5. VectorIndex.size property matches number of added vectors
# 6. VectorIndex.reset() clears all data
# 7. Mismatched dimensions raise ValueError
# 8. Mismatched lengths raise ValueError
# 9. IndexRegistry.build() stores and retrieves indices
# 10. IndexRegistry.get() raises KeyError for unknown key
# 11. Searching for the same vector returns it as top-1 (score ~= 1.0)
# 12. Empty index search returns empty list

# Helper to create normalized random vectors:
def _random_embeddings(n: int, dim: int) -> np.ndarray:
    rng = np.random.default_rng(42)
    vecs = rng.standard_normal((n, dim)).astype(np.float32)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    return vecs / norms
```

## Outputs
- `src/scaffolder/retrieval/index.py`
- `src/scaffolder/retrieval/__init__.py` (updated)
- `tests/test_retrieval_index.py`

## Acceptance Criteria
1. `VectorIndex` correctly indexes and retrieves synthetic vectors.
2. `build_all_indices()` creates one index per (strategy, model) pair.
3. Search returns `RetrievalHit` objects with correct rank ordering.
4. `pytest tests/test_retrieval_index.py -v` -- all tests pass.
5. `mypy src/scaffolder/retrieval/ --strict` passes.
6. `ruff check src/scaffolder/retrieval/` passes.

## Handoff Notes
- **To Day 8:** The `IndexRegistry` is ready. `RetrievalSimulator` will load queries, embed them, and search against the indices. It needs: `registry.get(strategy, model).search(query_vec, k=10)`.
- **To Agent B:** The `build_all_indices()` function accepts any list of `EmbeddingModelName`. When Voyage is ready, just include `EmbeddingModelName.VOYAGE_LAW_2` in the models list.
- **Design note:** We use `IndexFlatIP` (inner product) rather than `IndexFlatL2` because our embeddings are L2-normalized (sentence-transformers does this by default). IP on normalized vectors equals cosine similarity, which is the standard metric for retrieval.
- **Performance note:** FAISS flat index is fine for our scale (~500 chunks per strategy). No need for IVF or HNSW.
