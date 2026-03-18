"""Chunking pipeline and strategy wrappers."""

from __future__ import annotations

from scaffolder.chunking.pipeline import ChunkingPipeline
from scaffolder.chunking.strategies import (
    FixedSizeStrategy,
    LexiChunkStrategy,
    RCTSStrategy,
    SentenceSplitStrategy,
)
from scaffolder.models import ChunkingStrategy, StrategyName

# Registry maps StrategyName -> class. LEXICHUNK_CONTEXTUAL is added on Day 12.
_STRATEGY_REGISTRY: dict[StrategyName, type[ChunkingStrategy]] = {
    StrategyName.LEXICHUNK: LexiChunkStrategy,  # type: ignore[dict-item]
    StrategyName.RCTS: RCTSStrategy,  # type: ignore[dict-item]
    StrategyName.SENTENCE_SPLIT: SentenceSplitStrategy,  # type: ignore[dict-item]
    StrategyName.FIXED_SIZE: FixedSizeStrategy,  # type: ignore[dict-item]
}


def get_strategy(name: StrategyName, **kwargs: object) -> ChunkingStrategy:
    """Instantiate a chunking strategy by name."""
    if name not in _STRATEGY_REGISTRY:
        msg = f"Unknown strategy: {name}. Available: {list(_STRATEGY_REGISTRY.keys())}"
        raise ValueError(msg)
    return _STRATEGY_REGISTRY[name](**kwargs)  # type: ignore[return-value]


def get_all_strategies(**kwargs: object) -> list[ChunkingStrategy]:
    """Instantiate all registered strategies (excludes unregistered ones)."""
    return [get_strategy(name, **kwargs) for name in _STRATEGY_REGISTRY]


__all__ = [
    "ChunkingPipeline",
    "FixedSizeStrategy",
    "LexiChunkStrategy",
    "RCTSStrategy",
    "SentenceSplitStrategy",
    "get_all_strategies",
    "get_strategy",
]
