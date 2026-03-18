# Agent A — Day 11: Voyage Law 2 Evaluation

## Mission
Run the full retrieval benchmark with Voyage Law 2 embeddings (legal-domain-specific) alongside the local models, comparing whether a legal-specific embedding model amplifies or diminishes LexiChunk's structural advantage.

## Context
Week 2 is complete: `make benchmark-embed` produces retrieval metrics with statistical significance using MiniLM and BGE-base. Agent B built the Voyage adapter (`src/scaffolder/embedding/voyage.py`) on Day 6. Today we integrate it and run the three-model comparison. This is the start of Week 3.

Agent B is working on Streamlit page_compare.py today. No dependency on their work for this day.

## Prerequisites
- `src/scaffolder/embedding/voyage.py` with `VoyageAdapter` implementing `Embedder` protocol (built by Agent B)
- `VOYAGE_API_KEY` environment variable set (or skip Voyage gracefully)
- Full pipeline from Day 10 working end-to-end
- `voyageai` installed (`pip install voyageai`)

## Checklist
- [ ] Verify Agent B's `VoyageAdapter` conforms to the `Embedder` protocol
- [ ] Add Voyage model to the `benchmark-embed` pipeline (graceful skip if no API key)
- [ ] Run full benchmark with all 3 models: MiniLM, BGE-base, Voyage Law 2
- [ ] Compare results: does the legal embedding model change the ranking of strategies?
- [ ] Update JSON export to include Voyage results
- [ ] Document findings in a structured format

## Implementation Details

### Verify VoyageAdapter

Check that `src/scaffolder/embedding/voyage.py` has:
```python
class VoyageAdapter:
    model_name = EmbeddingModelName.VOYAGE_LAW_2
    dimension = 1024

    def __init__(self, api_key: str | None = None) -> None:
        ...

    def embed_texts(self, texts: Sequence[str]) -> npt.NDArray[np.float32]:
        ...
```

If the adapter is missing or broken, create a minimal implementation:

```python
"""Voyage AI embedding adapter (requires VOYAGE_API_KEY)."""

from __future__ import annotations

import os
import logging
from typing import Sequence

import numpy as np
import numpy.typing as npt

from scaffolder.models import EmbeddingModelName

logger = logging.getLogger(__name__)


class VoyageAdapter:
    """Embedding adapter for Voyage AI's voyage-law-2 model.

    Requires VOYAGE_API_KEY environment variable. If not set,
    embed_texts() raises RuntimeError.
    """

    model_name = EmbeddingModelName.VOYAGE_LAW_2
    dimension = 1024

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("VOYAGE_API_KEY")
        self._client = None

    def _get_client(self):
        if self._client is None:
            if not self._api_key:
                raise RuntimeError(
                    "VOYAGE_API_KEY not set. Set it as an environment variable "
                    "or pass api_key to VoyageAdapter()."
                )
            import voyageai
            self._client = voyageai.Client(api_key=self._api_key)
        return self._client

    def embed_texts(self, texts: Sequence[str]) -> npt.NDArray[np.float32]:
        """Embed texts using voyage-law-2.

        Batches in groups of 128 (Voyage API limit).
        """
        client = self._get_client()
        texts_list = list(texts)

        all_embeddings: list[list[float]] = []
        batch_size = 128

        for i in range(0, len(texts_list), batch_size):
            batch = texts_list[i : i + batch_size]
            result = client.embed(
                batch,
                model="voyage-law-2",
                input_type="document",
            )
            all_embeddings.extend(result.embeddings)

        return np.array(all_embeddings, dtype=np.float32)
```

### Graceful Voyage Toggling

Update `__main__.py` to handle Voyage availability:

```python
def _get_available_models() -> list[EmbeddingModelName]:
    """Return list of available embedding models.

    Always includes local models. Includes Voyage only if API key is set.
    """
    models = [EmbeddingModelName.MINILM, EmbeddingModelName.BGE_BASE]

    voyage_key = os.environ.get("VOYAGE_API_KEY")
    if voyage_key:
        logger.info("VOYAGE_API_KEY found, including voyage-law-2.")
        models.append(EmbeddingModelName.VOYAGE_LAW_2)
    else:
        logger.info("VOYAGE_API_KEY not set, skipping voyage-law-2.")

    return models
```

Update `run_retrieval_benchmark()` to use `_get_available_models()` instead of hardcoding the model list.

### Analysis: Embedding Model Comparison

After running the full benchmark with all 3 models, analyze:

1. **Does Voyage Law 2 improve all strategies equally?** If yes, the embedding model is a rising tide. If it helps LexiChunk more, there is a synergy between structural chunking and legal embeddings.

2. **MRR gap:** Compare the MRR gap (LexiChunk - baseline) across the 3 models. A larger gap with Voyage suggests LexiChunk chunks are better aligned with legal-domain vectors.

3. **DRM rate:** Does the legal embedding model reduce DRM (cross-document confusion)? LexiChunk's cross-reference resolution should help here.

4. **Cost-benefit:** Voyage is a paid API. If the improvement over free local models is marginal, note this.

### Document Findings

Add a summary to the JSON export under a `findings` key:

```python
result.config["findings"] = {
    "models_used": [m.value for m in models],
    "voyage_available": EmbeddingModelName.VOYAGE_LAW_2 in models,
    "best_model_for_lexichunk": "...",  # determined from results
    "legal_embedding_synergy": True/False,
}
```

### Tests

No new test file today -- this is primarily an integration/evaluation day. However:

- [ ] Verify `VoyageAdapter` satisfies `isinstance(adapter, Embedder)` check (runtime_checkable)
- [ ] Verify graceful skip when `VOYAGE_API_KEY` is not set
- [ ] Add a test that `_get_available_models()` returns 2 models without API key, 3 with

```python
# tests/test_voyage_toggle.py
def test_available_models_without_voyage(monkeypatch):
    monkeypatch.delenv("VOYAGE_API_KEY", raising=False)
    models = _get_available_models()
    assert len(models) == 2
    assert EmbeddingModelName.VOYAGE_LAW_2 not in models

def test_available_models_with_voyage(monkeypatch):
    monkeypatch.setenv("VOYAGE_API_KEY", "test-key")
    models = _get_available_models()
    assert len(models) == 3
    assert EmbeddingModelName.VOYAGE_LAW_2 in models
```

## Outputs
- `src/scaffolder/embedding/voyage.py` (verified or created)
- `src/scaffolder/__main__.py` (updated with Voyage toggle)
- `results/full_benchmark.json` (updated with Voyage results when available)
- `tests/test_voyage_toggle.py`

## Acceptance Criteria
1. `make benchmark-embed` works without `VOYAGE_API_KEY` (runs with 2 local models only).
2. With `VOYAGE_API_KEY` set, `make benchmark-embed` includes voyage-law-2 results.
3. JSON export includes results for all available models.
4. No crashes or errors when Voyage adapter is unavailable.
5. `pytest tests/test_voyage_toggle.py -v` -- all tests pass.
6. `ruff check src/scaffolder/` passes.

## Handoff Notes
- **To Agent B:** The `_get_available_models()` function checks for `VOYAGE_API_KEY`. If your Voyage adapter needs different initialization, update `EmbeddingPipeline._get_adapter()` accordingly. The adapter must implement: `model_name`, `dimension`, `embed_texts()`.
- **To Day 12:** With three embedding models compared, Day 12 adds the contextual retrieval experiment (LexiChunk with `build_embedded_text()` vs raw chunk text).
- **Observation to document:** Note whether Voyage Law 2 changes the *relative* ranking of strategies. If LexiChunk wins regardless of embedding model, the structural advantage is robust. If the gap narrows with Voyage, general embeddings might need LexiChunk more.
