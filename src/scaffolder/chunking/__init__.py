"""Chunking pipeline and strategy wrappers."""

from __future__ import annotations

from scaffolder.chunking.pipeline import ChunkingPipeline
from scaffolder.chunking.strategies import (
    FixedSizeStrategy,
    LexiChunkContextualStrategy,
    LexiChunkStrategy,
    RCTSStrategy,
    SentenceSplitStrategy,
)
from scaffolder.models import ChunkingStrategy, StrategyName

_STRATEGY_REGISTRY: dict[StrategyName, type] = {
    StrategyName.LEXICHUNK: LexiChunkStrategy,
    StrategyName.LEXICHUNK_CONTEXTUAL: LexiChunkContextualStrategy,
    StrategyName.RCTS: RCTSStrategy,
    StrategyName.SENTENCE_SPLIT: SentenceSplitStrategy,
    StrategyName.FIXED_SIZE: FixedSizeStrategy,
}


def get_strategy(name: StrategyName, **kwargs: object) -> ChunkingStrategy:
    """Instantiate a chunking strategy by name."""
    if name not in _STRATEGY_REGISTRY:
        msg = f"Unknown strategy: {name}. Available: {list(_STRATEGY_REGISTRY.keys())}"
        raise ValueError(msg)
    cls = _STRATEGY_REGISTRY[name]
    strategy: ChunkingStrategy = cls(**kwargs)
    return strategy


def get_all_strategies(**kwargs: object) -> list[ChunkingStrategy]:
    """Instantiate all registered strategies (excludes unregistered ones)."""
    return [get_strategy(name, **kwargs) for name in _STRATEGY_REGISTRY]


__all__ = [
    "ChunkingPipeline",
    "FixedSizeStrategy",
    "LexiChunkContextualStrategy",
    "LexiChunkStrategy",
    "RCTSStrategy",
    "SentenceSplitStrategy",
    "get_all_strategies",
    "get_strategy",
]
