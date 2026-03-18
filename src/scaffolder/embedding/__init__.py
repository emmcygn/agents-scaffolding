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
        """
        ...


def create_embedder(model_name: str) -> Embedder:
    """Factory function to create the appropriate embedder.

    Args:
        model_name: Model identifier (e.g., "all-MiniLM-L6-v2", "voyage-law-2").

    Returns:
        An Embedder implementation for the requested model.

    Raises:
        ImportError: If required dependencies are not installed.
        ValueError: If model_name is not recognized.
    """
    if model_name.startswith("voyage"):
        from scaffolder.embedding.voyage import VoyageEmbedder

        return VoyageEmbedder(model_name=model_name)

    raise NotImplementedError(
        f"Local embedder for '{model_name}' — waiting for Agent A's implementation"
    )
