# Agent A — Day 06: EmbeddingPipeline & Local Model Adapters

## Mission
Build the EmbeddingPipeline with pluggable model adapters and a disk cache, enabling all chunk texts to be embedded locally using all-MiniLM-L6-v2 and bge-base-en-v1.5 without hitting any paid API.

## Context
Week 1 is done: `make benchmark` produces structural metrics. Now we start Week 2 -- building the embedding and retrieval layer. Today we build the embedding infrastructure. Agent B is working on the Voyage adapter today (Day 6), which will plug into our `Embedder` protocol on Day 11.

The `Embedder` protocol from `models.py` defines: `model_name: EmbeddingModelName`, `dimension: int`, and `embed_texts(texts: Sequence[str]) -> np.ndarray`.

## Prerequisites
- `src/scaffolder/models.py` with `Embedder` protocol, `EmbeddingModelName` enum
- `sentence-transformers` installed (`pip install sentence-transformers`)
- `numpy` installed
- `src/scaffolder/embedding/__init__.py` exists (stub from Day 1)

## Checklist
- [ ] Implement `SentenceTransformerAdapter` in `src/scaffolder/embedding/pipeline.py`
- [ ] Implement `EmbeddingCache` with disk-based .npy storage
- [ ] Implement `EmbeddingPipeline` orchestrator
- [ ] Update `src/scaffolder/embedding/__init__.py` with exports
- [ ] Write tests in `tests/test_embedding.py`
- [ ] Verify both local models produce embeddings for a sample text

## Implementation Details

### SentenceTransformerAdapter (`src/scaffolder/embedding/pipeline.py`)

```python
"""Embedding pipeline with pluggable adapters and disk cache."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Sequence

import numpy as np
import numpy.typing as npt

from scaffolder.models import EmbeddingModelName, Embedder, Chunk

logger = logging.getLogger(__name__)

# Model name -> HuggingFace model ID mapping
_MODEL_IDS: dict[EmbeddingModelName, str] = {
    EmbeddingModelName.MINILM: "sentence-transformers/all-MiniLM-L6-v2",
    EmbeddingModelName.BGE_BASE: "BAAI/bge-base-en-v1.5",
}

# Known dimensions (avoids loading model just to check)
_MODEL_DIMS: dict[EmbeddingModelName, int] = {
    EmbeddingModelName.MINILM: 384,
    EmbeddingModelName.BGE_BASE: 768,
    EmbeddingModelName.VOYAGE_LAW_2: 1024,
}


class SentenceTransformerAdapter:
    """Local embedding adapter using sentence-transformers.

    Lazily loads the model on first embed_texts() call. Supports
    all-MiniLM-L6-v2 (384d) and bge-base-en-v1.5 (768d).
    """

    def __init__(self, model_name: EmbeddingModelName) -> None:
        if model_name not in _MODEL_IDS:
            raise ValueError(
                f"SentenceTransformerAdapter does not support {model_name}. "
                f"Use one of: {list(_MODEL_IDS.keys())}"
            )
        self.model_name = model_name
        self.dimension = _MODEL_DIMS[model_name]
        self._model_id = _MODEL_IDS[model_name]
        self._model = None  # lazy load

    def _load_model(self):
        """Load the sentence-transformers model (slow, cached after first call)."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading model: %s", self._model_id)
            self._model = SentenceTransformer(self._model_id)
        return self._model

    def embed_texts(self, texts: Sequence[str]) -> npt.NDArray[np.float32]:
        """Embed texts, returning (n, dimension) float32 array.

        For bge-base models, prepends the recommended query prefix
        "Represent this sentence: " only if not already present.
        """
        model = self._load_model()
        texts_list = list(texts)

        # BGE models recommend a prefix for better performance
        if self.model_name == EmbeddingModelName.BGE_BASE:
            texts_list = [
                t if t.startswith("Represent") else f"Represent this sentence: {t}"
                for t in texts_list
            ]

        embeddings = model.encode(
            texts_list,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=64,
        )
        return np.asarray(embeddings, dtype=np.float32)
```

### EmbeddingCache

```python
class EmbeddingCache:
    """Disk-based embedding cache using .npy files.

    Cache key: hash(model_name + text) -> .npy file.
    Cache directory: .cache/embeddings/{model_name}/

    This avoids re-embedding the same text when running benchmarks
    repeatedly. Cache is safe to delete at any time.
    """

    def __init__(self, cache_dir: Path | None = None) -> None:
        self._cache_dir = cache_dir or Path(".cache/embeddings")
        self._hits = 0
        self._misses = 0

    def _key(self, model_name: str, text: str) -> str:
        """Generate a cache key from model name + text."""
        content = f"{model_name}:{text}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

    def _path(self, model_name: str, key: str) -> Path:
        """Get the file path for a cache key."""
        model_dir = self._cache_dir / model_name.replace("/", "_")
        model_dir.mkdir(parents=True, exist_ok=True)
        return model_dir / f"{key}.npy"

    def get(self, model_name: str, text: str) -> npt.NDArray[np.float32] | None:
        """Look up a cached embedding. Returns None on miss."""
        key = self._key(model_name, text)
        path = self._path(model_name, key)
        if path.exists():
            self._hits += 1
            return np.load(path)
        self._misses += 1
        return None

    def put(self, model_name: str, text: str, embedding: npt.NDArray[np.float32]) -> None:
        """Store an embedding in the cache."""
        key = self._key(model_name, text)
        path = self._path(model_name, key)
        np.save(path, embedding)

    def get_batch(
        self, model_name: str, texts: Sequence[str]
    ) -> tuple[npt.NDArray[np.float32] | None, list[int]]:
        """Look up cached embeddings for a batch of texts.

        Returns:
            (cached_embeddings_or_None, list_of_uncached_indices)
            If all are cached, returns (full_array, []).
            If none are cached, returns (None, [0, 1, ...]).
        """
        dim: int | None = None
        cached: dict[int, npt.NDArray[np.float32]] = {}
        uncached: list[int] = []

        for i, text in enumerate(texts):
            emb = self.get(model_name, text)
            if emb is not None:
                cached[i] = emb
                if dim is None:
                    dim = emb.shape[0]
            else:
                uncached.append(i)

        if not cached:
            return None, uncached

        if dim is None:
            return None, uncached

        # Build full array with placeholders for uncached
        result = np.zeros((len(texts), dim), dtype=np.float32)
        for i, emb in cached.items():
            result[i] = emb

        return result, uncached

    @property
    def stats(self) -> dict[str, int]:
        return {"hits": self._hits, "misses": self._misses}

    def clear(self) -> None:
        """Delete all cached embeddings."""
        import shutil
        if self._cache_dir.exists():
            shutil.rmtree(self._cache_dir)
        self._hits = 0
        self._misses = 0
```

### EmbeddingPipeline

```python
class EmbeddingPipeline:
    """Orchestrates embedding chunks using multiple models with caching.

    Usage:
        pipeline = EmbeddingPipeline(
            models=[EmbeddingModelName.MINILM, EmbeddingModelName.BGE_BASE],
        )
        # Embed all chunks from a strategy result
        embeddings = pipeline.embed_chunks(chunks, model_name)
        # Returns: np.ndarray of shape (n_chunks, dim)
    """

    def __init__(
        self,
        models: Sequence[EmbeddingModelName] | None = None,
        cache_dir: Path | None = None,
        use_cache: bool = True,
    ) -> None:
        self._adapters: dict[EmbeddingModelName, Embedder] = {}
        self._cache = EmbeddingCache(cache_dir) if use_cache else None
        self._models = list(models or [EmbeddingModelName.MINILM])

    def _get_adapter(self, model_name: EmbeddingModelName) -> Embedder:
        """Get or create an adapter for the given model."""
        if model_name not in self._adapters:
            if model_name in (EmbeddingModelName.MINILM, EmbeddingModelName.BGE_BASE):
                self._adapters[model_name] = SentenceTransformerAdapter(model_name)
            elif model_name == EmbeddingModelName.VOYAGE_LAW_2:
                # Voyage adapter is built by Agent B on Day 6
                from scaffolder.embedding.voyage import VoyageAdapter
                self._adapters[model_name] = VoyageAdapter()
            else:
                raise ValueError(f"No adapter for model: {model_name}")
        return self._adapters[model_name]

    def embed_texts(
        self, texts: Sequence[str], model_name: EmbeddingModelName
    ) -> npt.NDArray[np.float32]:
        """Embed a list of texts using the specified model, with caching.

        Returns: np.ndarray of shape (n, dim), dtype float32.
        """
        adapter = self._get_adapter(model_name)
        texts_list = list(texts)

        if self._cache is None:
            return adapter.embed_texts(texts_list)

        # Check cache for batch
        cached_result, uncached_indices = self._cache.get_batch(
            model_name.value, texts_list
        )

        if not uncached_indices:
            # All cached
            assert cached_result is not None
            logger.info(
                "All %d embeddings served from cache (%s)",
                len(texts_list), model_name.value,
            )
            return cached_result

        # Embed uncached texts
        uncached_texts = [texts_list[i] for i in uncached_indices]
        logger.info(
            "Embedding %d texts (%d cached, %d new) with %s",
            len(texts_list),
            len(texts_list) - len(uncached_indices),
            len(uncached_indices),
            model_name.value,
        )
        new_embeddings = adapter.embed_texts(uncached_texts)

        # Store in cache
        for j, idx in enumerate(uncached_indices):
            self._cache.put(model_name.value, texts_list[idx], new_embeddings[j])

        # Merge cached + new
        if cached_result is not None:
            for j, idx in enumerate(uncached_indices):
                cached_result[idx] = new_embeddings[j]
            return cached_result
        else:
            # Nothing was cached, build fresh
            result = np.zeros(
                (len(texts_list), adapter.dimension), dtype=np.float32
            )
            for j, idx in enumerate(uncached_indices):
                result[idx] = new_embeddings[j]
            return result

    def embed_chunks(
        self, chunks: Sequence[Chunk], model_name: EmbeddingModelName
    ) -> npt.NDArray[np.float32]:
        """Convenience: embed chunk texts."""
        return self.embed_texts([c.text for c in chunks], model_name)

    @property
    def cache_stats(self) -> dict[str, int] | None:
        if self._cache:
            return self._cache.stats
        return None
```

### Package init (`src/scaffolder/embedding/__init__.py`)

```python
"""Embedding pipeline and model adapters."""

from scaffolder.embedding.pipeline import (
    EmbeddingPipeline,
    EmbeddingCache,
    SentenceTransformerAdapter,
)

__all__ = [
    "EmbeddingPipeline",
    "EmbeddingCache",
    "SentenceTransformerAdapter",
]
```

### Tests (`tests/test_embedding.py`)

```python
"""Tests for EmbeddingPipeline and adapters."""

# Key test cases:
# 1. SentenceTransformerAdapter returns correct shape for MINILM: (n, 384)
# 2. SentenceTransformerAdapter returns correct shape for BGE_BASE: (n, 768)
# 3. Embeddings are normalized (L2 norm ~= 1.0)
# 4. EmbeddingCache: put then get returns same array
# 5. EmbeddingCache: get on miss returns None
# 6. EmbeddingCache: get_batch with mixed hits/misses
# 7. EmbeddingPipeline: embed_texts with caching produces correct output
# 8. EmbeddingPipeline: second call to embed_texts is a cache hit
# 9. EmbeddingPipeline: embed_chunks works with Chunk objects
# 10. Invalid model name raises ValueError
```

Use a small set of texts (2-3 short sentences) to keep tests fast. The first run will download models (~90MB for MiniLM, ~440MB for BGE); subsequent runs use the HuggingFace cache.

Mark slow tests with `@pytest.mark.slow` and skip in CI if needed:
```python
@pytest.mark.slow
def test_bge_base_dimensions():
    ...
```

## Outputs
- `src/scaffolder/embedding/pipeline.py`
- `src/scaffolder/embedding/__init__.py` (updated)
- `tests/test_embedding.py`

## Acceptance Criteria
1. `python -c "from scaffolder.embedding import EmbeddingPipeline; p = EmbeddingPipeline(); print(p.embed_texts(['test'], EmbeddingModelName.MINILM).shape)"` prints `(1, 384)`.
2. Cache produces `.npy` files in `.cache/embeddings/`.
3. Second embed call for the same text is served from cache (check `cache_stats`).
4. `pytest tests/test_embedding.py -v` -- all tests pass.
5. `mypy src/scaffolder/embedding/ --strict` passes.
6. `ruff check src/scaffolder/embedding/` passes.

## Handoff Notes
- **To Agent B:** The `EmbeddingPipeline._get_adapter()` method tries to import `from scaffolder.embedding.voyage import VoyageAdapter` when `VOYAGE_LAW_2` is requested. Please build the `VoyageAdapter` class in `src/scaffolder/embedding/voyage.py` implementing the `Embedder` protocol. It needs: `model_name = EmbeddingModelName.VOYAGE_LAW_2`, `dimension = 1024`, and `embed_texts()` calling the Voyage API.
- **To Day 7:** Embeddings are ready. Day 7 builds the FAISS index that stores these vectors and supports top-k search.
- **Performance note:** MiniLM embeds ~1000 texts/sec on CPU. BGE is ~500/sec. With 5 documents and ~50-100 chunks each, embedding takes <1 second per model. The cache makes re-runs instant.
