"""FAISS indexing and retrieval simulation."""

from scaffolder.retrieval.index import (
    IndexKey,
    IndexRegistry,
    VectorIndex,
    build_all_indices,
)
from scaffolder.retrieval.simulator import (
    RetrievalSimulator,
    load_queries_from_yaml,
)

__all__ = [
    "IndexKey",
    "IndexRegistry",
    "RetrievalSimulator",
    "VectorIndex",
    "build_all_indices",
    "load_queries_from_yaml",
]
