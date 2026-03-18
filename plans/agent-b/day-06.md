# Agent B — Day 06: Voyage API Adapter

## Mission
Build the Voyage AI embedding adapter with rate limiting, error handling, and graceful degradation so the scaffolder can compare paid legal-specific embeddings (voyage-law-2) against local models.

## Context
Day 5 completed the JSON export and Streamlit skeleton. Agent A is finishing the local embedding pipeline (`EmbeddingPipeline` with sentence-transformers). The Voyage adapter must conform to the same protocol so it can be swapped in transparently. The adapter is toggled via `config.enable_voyage` and requires the `VOYAGE_API_KEY` environment variable. This is an optional paid feature — the scaffolder must work without it.

## Prerequisites
- `src/scaffolder/embedding/__init__.py` exists (Day 1)
- `src/scaffolder/config.py` has `enable_voyage`, `voyage_model` fields (Day 2)
- `pyproject.toml` has `voyageai>=0.2` in `[voyage]` extras
- Agent A's embedding protocol/interface (to be confirmed — at minimum, an `embed(texts: list[str]) -> list[list[float]]` method)

## Checklist
- [ ] Task 1 — Define the `Embedder` protocol in `src/scaffolder/embedding/__init__.py`
- [ ] Task 2 — Create `src/scaffolder/embedding/voyage.py` with `VoyageEmbedder`
- [ ] Task 3 — Implement rate limiting with exponential backoff
- [ ] Task 4 — Handle all error cases: missing API key, invalid key, rate limits, network errors
- [ ] Task 5 — Write `tests/test_voyage.py` with mocked API calls
- [ ] Task 6 — Update `src/scaffolder/embedding/__init__.py` with factory function

## Implementation Details

### Embedder protocol: src/scaffolder/embedding/__init__.py

```python
"""Embedding pipelines and adapters."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Embedder(Protocol):
    """Protocol for embedding adapters.

    All embedding adapters (local and API) must implement this protocol.
    """

    @property
    def model_name(self) -> str:
        """Return the model identifier."""
        ...

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        ...

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors, one per input text.
            Each vector is a list of floats with length == self.dimension.
        """
        ...

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query text.

        Some models (e.g., Voyage) distinguish between document and query
        embeddings. This method embeds a query.

        Default implementation calls embed() with a single text.
        """
        ...


def create_embedder(model_name: str, config: object | None = None) -> Embedder:
    """Factory function to create the appropriate embedder.

    Args:
        model_name: Model identifier (e.g., "all-MiniLM-L6-v2", "voyage-law-2").
        config: Optional BenchmarkConfig for adapter-specific settings.

    Returns:
        An Embedder implementation for the requested model.

    Raises:
        ImportError: If required dependencies are not installed.
        ValueError: If model_name is not recognized.
    """
    if model_name.startswith("voyage"):
        from scaffolder.embedding.voyage import VoyageEmbedder
        return VoyageEmbedder(model_name=model_name)
    else:
        # Agent A's local embedder — import will be added when available
        raise NotImplementedError(
            f"Local embedder for '{model_name}' — waiting for Agent A's implementation"
        )
```

### Voyage adapter: src/scaffolder/embedding/voyage.py

```python
"""Voyage AI embedding adapter with rate limiting and error handling."""

from __future__ import annotations

import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

# Voyage API limits (as of 2025)
_DEFAULT_BATCH_SIZE = 128  # Max texts per API call
_DEFAULT_RPM = 300  # Requests per minute
_MIN_RETRY_DELAY = 1.0  # Seconds
_MAX_RETRY_DELAY = 60.0  # Seconds
_MAX_RETRIES = 3

# Model dimensions
_MODEL_DIMENSIONS: dict[str, int] = {
    "voyage-law-2": 1024,
    "voyage-3": 1024,
    "voyage-3-lite": 512,
}


class VoyageEmbedderError(Exception):
    """Raised when Voyage embedding fails."""


class VoyageEmbedder:
    """Embedding adapter using Voyage AI's API.

    Requires the VOYAGE_API_KEY environment variable to be set.
    Uses voyage-law-2 by default, which is optimized for legal text.

    Features:
    - Automatic batching (respects API batch size limits)
    - Exponential backoff on rate limit errors
    - Separate document vs query embedding (Voyage supports input_type)
    - Clear error messages for common issues
    """

    def __init__(
        self,
        model_name: str = "voyage-law-2",
        api_key: str | None = None,
        batch_size: int = _DEFAULT_BATCH_SIZE,
        max_retries: int = _MAX_RETRIES,
    ) -> None:
        self._model_name = model_name
        self._batch_size = batch_size
        self._max_retries = max_retries

        # Resolve API key
        self._api_key = api_key or os.getenv("VOYAGE_API_KEY")
        if not self._api_key:
            raise VoyageEmbedderError(
                "Voyage API key not found. Set the VOYAGE_API_KEY environment variable "
                "or pass api_key to VoyageEmbedder. Get a key at https://dash.voyageai.com/"
            )

        # Resolve dimension
        if model_name not in _MODEL_DIMENSIONS:
            logger.warning(
                "Unknown Voyage model '%s'. Assuming dimension 1024. "
                "Known models: %s",
                model_name,
                list(_MODEL_DIMENSIONS.keys()),
            )
        self._dimension = _MODEL_DIMENSIONS.get(model_name, 1024)

        # Initialize client lazily
        self._client: Any = None

    def _get_client(self) -> Any:
        """Lazy-initialize the Voyage client."""
        if self._client is None:
            try:
                import voyageai
            except ImportError:
                raise VoyageEmbedderError(
                    "voyageai package not installed. Install with: "
                    "pip install 'scaffolder[voyage]'"
                ) from None
            self._client = voyageai.Client(api_key=self._api_key)
        return self._client

    @property
    def model_name(self) -> str:
        """Return the Voyage model identifier."""
        return self._model_name

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        return self._dimension

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts as documents.

        Automatically batches requests and handles rate limits.
        """
        return self._embed_batched(texts, input_type="document")

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query text.

        Uses input_type='query' which Voyage optimizes differently
        from document embeddings.
        """
        results = self._embed_batched([text], input_type="query")
        return results[0]

    def _embed_batched(
        self, texts: list[str], input_type: str
    ) -> list[list[float]]:
        """Embed texts in batches with rate limiting.

        Args:
            texts: List of texts to embed.
            input_type: Either "document" or "query".

        Returns:
            List of embedding vectors.
        """
        if not texts:
            return []

        all_embeddings: list[list[float]] = []
        client = self._get_client()

        for i in range(0, len(texts), self._batch_size):
            batch = texts[i : i + self._batch_size]
            embeddings = self._embed_with_retry(client, batch, input_type)
            all_embeddings.extend(embeddings)

        return all_embeddings

    def _embed_with_retry(
        self,
        client: Any,
        texts: list[str],
        input_type: str,
    ) -> list[list[float]]:
        """Embed a single batch with exponential backoff retry.

        Retries on:
        - Rate limit errors (429)
        - Server errors (5xx)
        - Transient network errors

        Does NOT retry on:
        - Authentication errors (401/403)
        - Bad request errors (400)
        """
        delay = _MIN_RETRY_DELAY

        for attempt in range(self._max_retries + 1):
            try:
                result = client.embed(
                    texts,
                    model=self._model_name,
                    input_type=input_type,
                )
                return result.embeddings  # type: ignore[no-any-return]

            except Exception as e:
                error_str = str(e).lower()

                # Don't retry auth errors
                if "401" in error_str or "403" in error_str or "unauthorized" in error_str:
                    raise VoyageEmbedderError(
                        f"Voyage API authentication failed. Check your VOYAGE_API_KEY. "
                        f"Error: {e}"
                    ) from e

                # Don't retry bad requests
                if "400" in error_str or "bad request" in error_str:
                    raise VoyageEmbedderError(
                        f"Voyage API bad request. Check input texts. Error: {e}"
                    ) from e

                # Retry on rate limits and server errors
                if attempt < self._max_retries:
                    if "429" in error_str or "rate" in error_str:
                        logger.warning(
                            "Voyage rate limit hit. Retrying in %.1fs (attempt %d/%d)",
                            delay,
                            attempt + 1,
                            self._max_retries,
                        )
                    else:
                        logger.warning(
                            "Voyage API error: %s. Retrying in %.1fs (attempt %d/%d)",
                            e,
                            delay,
                            attempt + 1,
                            self._max_retries,
                        )
                    time.sleep(delay)
                    delay = min(delay * 2, _MAX_RETRY_DELAY)
                else:
                    raise VoyageEmbedderError(
                        f"Voyage API failed after {self._max_retries + 1} attempts. "
                        f"Last error: {e}"
                    ) from e

        # Should not reach here, but satisfy type checker
        raise VoyageEmbedderError("Unexpected retry loop exit")
```

### tests/test_voyage.py

```python
"""Tests for Voyage AI embedding adapter."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from scaffolder.embedding.voyage import VoyageEmbedder, VoyageEmbedderError


class TestVoyageEmbedderInit:
    """Test initialization and configuration."""

    def test_missing_api_key_raises(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("VOYAGE_API_KEY", None)
            with pytest.raises(VoyageEmbedderError, match="VOYAGE_API_KEY"):
                VoyageEmbedder()

    def test_explicit_api_key(self) -> None:
        embedder = VoyageEmbedder(api_key="test-key")
        assert embedder.model_name == "voyage-law-2"
        assert embedder.dimension == 1024

    def test_env_api_key(self) -> None:
        with patch.dict(os.environ, {"VOYAGE_API_KEY": "env-key"}):
            embedder = VoyageEmbedder()
            assert embedder.model_name == "voyage-law-2"

    def test_custom_model(self) -> None:
        embedder = VoyageEmbedder(
            model_name="voyage-3-lite", api_key="test-key"
        )
        assert embedder.dimension == 512


class TestVoyageEmbedderEmbed:
    """Test embedding with mocked API calls."""

    def _make_embedder(self) -> VoyageEmbedder:
        return VoyageEmbedder(api_key="test-key", batch_size=2, max_retries=1)

    def test_embed_empty_list(self) -> None:
        embedder = self._make_embedder()
        result = embedder.embed([])
        assert result == []

    def test_embed_single_batch(self) -> None:
        embedder = self._make_embedder()
        mock_client = MagicMock()
        mock_client.embed.return_value = MagicMock(
            embeddings=[[0.1, 0.2], [0.3, 0.4]]
        )
        embedder._client = mock_client

        result = embedder.embed(["text1", "text2"])
        assert len(result) == 2
        mock_client.embed.assert_called_once_with(
            ["text1", "text2"],
            model="voyage-law-2",
            input_type="document",
        )

    def test_embed_multiple_batches(self) -> None:
        embedder = self._make_embedder()
        mock_client = MagicMock()
        mock_client.embed.side_effect = [
            MagicMock(embeddings=[[0.1], [0.2]]),
            MagicMock(embeddings=[[0.3]]),
        ]
        embedder._client = mock_client

        result = embedder.embed(["t1", "t2", "t3"])
        assert len(result) == 3
        assert mock_client.embed.call_count == 2

    def test_embed_query_uses_query_type(self) -> None:
        embedder = self._make_embedder()
        mock_client = MagicMock()
        mock_client.embed.return_value = MagicMock(
            embeddings=[[0.1, 0.2]]
        )
        embedder._client = mock_client

        result = embedder.embed_query("test query")
        assert result == [0.1, 0.2]
        mock_client.embed.assert_called_once_with(
            ["test query"],
            model="voyage-law-2",
            input_type="query",
        )

    def test_auth_error_not_retried(self) -> None:
        embedder = self._make_embedder()
        mock_client = MagicMock()
        mock_client.embed.side_effect = Exception("401 Unauthorized")
        embedder._client = mock_client

        with pytest.raises(VoyageEmbedderError, match="authentication failed"):
            embedder.embed(["test"])
        assert mock_client.embed.call_count == 1  # No retry

    def test_rate_limit_retried(self) -> None:
        embedder = self._make_embedder()
        mock_client = MagicMock()
        mock_client.embed.side_effect = [
            Exception("429 rate limit exceeded"),
            MagicMock(embeddings=[[0.1]]),
        ]
        embedder._client = mock_client

        with patch("scaffolder.embedding.voyage.time.sleep"):
            result = embedder.embed(["test"])
        assert len(result) == 1
        assert mock_client.embed.call_count == 2

    def test_max_retries_exceeded(self) -> None:
        embedder = self._make_embedder()
        mock_client = MagicMock()
        mock_client.embed.side_effect = Exception("500 internal server error")
        embedder._client = mock_client

        with patch("scaffolder.embedding.voyage.time.sleep"):
            with pytest.raises(VoyageEmbedderError, match="failed after"):
                embedder.embed(["test"])


class TestVoyageEmbedderProtocol:
    """Test that VoyageEmbedder conforms to the Embedder protocol."""

    def test_conforms_to_protocol(self) -> None:
        from scaffolder.embedding import Embedder
        embedder = VoyageEmbedder(api_key="test-key")
        assert isinstance(embedder, Embedder)
```

## Outputs
- `src/scaffolder/embedding/__init__.py` (updated with `Embedder` protocol and factory)
- `src/scaffolder/embedding/voyage.py`
- `tests/test_voyage.py`

## Acceptance Criteria
1. `python -c "from scaffolder.embedding.voyage import VoyageEmbedder"` imports without error
2. `VoyageEmbedder(api_key='test')` creates an instance without calling the API
3. All tests in `tests/test_voyage.py` pass (mocked — no API key needed)
4. `make lint` and `make typecheck` pass on `voyage.py`
5. `VoyageEmbedder()` without API key raises `VoyageEmbedderError` with a helpful message

## Handoff Notes
- **To Agent A:** The `Embedder` protocol is now defined in `scaffolder.embedding`. Your local embedders (sentence-transformers) should implement `model_name`, `dimension`, `embed(texts)`, and `embed_query(text)`. The factory function `create_embedder()` in `__init__.py` has a placeholder for local models — update it when your local embedder is ready.
- **To Day 7:** Streamlit page_compare.py will use Agent A's `ChunkingPipeline` (not the Voyage adapter). The Voyage adapter is used on Day 9 (retrieval page) and Day 10 (embedding model dropdown).
- **Decision:** We distinguish `embed()` (for documents) from `embed_query()` (for queries) because Voyage optimizes differently for each. Local models can just call `embed()` from `embed_query()`.
