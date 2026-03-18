"""FAISS indexing and retrieval simulation."""

from scaffolder.retrieval.index import (
    IndexKey,
    IndexRegistry,
    VectorIndex,
    build_all_indices,
)

__all__ = [
    "IndexKey",
    "IndexRegistry",
    "VectorIndex",
    "build_all_indices",
]
