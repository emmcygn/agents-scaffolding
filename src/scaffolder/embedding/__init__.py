"""Embedding pipeline and model adapters."""

from scaffolder.embedding.pipeline import (
    EmbeddingCache,
    EmbeddingPipeline,
    SentenceTransformerAdapter,
)

__all__ = [
    "EmbeddingCache",
    "EmbeddingPipeline",
    "SentenceTransformerAdapter",
]
