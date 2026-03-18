# Agent A — Day 03: ChunkingPipeline & Strategy Wrappers

## Mission
Build the ChunkingPipeline orchestrator and four strategy wrappers so that every document can be chunked by LexiChunk and three baselines, producing comparable `ChunkSet` instances with timing data.

## Context
Day 2 delivered `FixtureManager` with 5 loaded documents. The `Document`, `Chunk`, `ChunkSet`, `StrategyResult`, `StrategyName`, and `ChunkingStrategy` protocol are defined in `models.py` (Day 1). Today we build the actual chunking layer.

Agent B is working on the config system today (YAML loading, CLI overrides). No dependency on Agent B's work -- we use sensible defaults for chunk sizes and parameters.

## Prerequisites
- `src/scaffolder/models.py` with `Document`, `Chunk`, `ChunkSet`, `StrategyResult`, `StrategyName`, `ChunkingStrategy` protocol
- `src/scaffolder/fixtures/__init__.py` with working `FixtureManager`
- `lexichunk` installed (`pip install lexichunk`)
- `langchain-text-splitters` installed

## Checklist
- [ ] Implement `LexiChunkStrategy` wrapper in `src/scaffolder/chunking/strategies.py`
- [ ] Implement `RCTSStrategy` wrapper (RecursiveCharacterTextSplitter)
- [ ] Implement `SentenceSplitStrategy` wrapper (regex-based)
- [ ] Implement `FixedSizeStrategy` wrapper (fixed 512-char chunks)
- [ ] Implement `ChunkingPipeline` in `src/scaffolder/chunking/pipeline.py`
- [ ] Implement strategy registry in `src/scaffolder/chunking/__init__.py`
- [ ] Write tests in `tests/test_chunking.py`

## Implementation Details

### Strategy Wrappers (`src/scaffolder/chunking/strategies.py`)

Each wrapper must satisfy the `ChunkingStrategy` protocol: has a `name: StrategyName` attribute and a `chunk(document: Document) -> ChunkSet` method.

```python
"""Chunking strategy wrappers for LexiChunk and baselines."""

from __future__ import annotations

import re
import time
import logging
from typing import Any

from scaffolder.models import (
    Chunk,
    ChunkSet,
    Document,
    StrategyName,
)

logger = logging.getLogger(__name__)


class LexiChunkStrategy:
    """Wrapper around LexiChunk's LegalChunker.

    Extracts rich metadata into Chunk.metadata:
    - clause_type: str (e.g. "definition", "obligation", "limitation")
    - confidence: float (0.0-1.0)
    - defined_terms: list[str]
    - cross_references: list[str | dict]
    - section_hierarchy: list[str] (e.g. ["1", "1.2", "1.2.1"])
    """

    name = StrategyName.LEXICHUNK

    def __init__(self, **kwargs: Any) -> None:
        from lexichunk import LegalChunker
        self._chunker = LegalChunker(**kwargs)

    def chunk(self, document: Document) -> ChunkSet:
        start = time.perf_counter()
        legal_chunks = self._chunker.chunk(document.text, document_id=document.id)
        elapsed = time.perf_counter() - start

        chunks: list[Chunk] = []
        for i, lc in enumerate(legal_chunks):
            metadata: dict[str, Any] = {}
            # Extract all available LexiChunk metadata
            for attr in ("clause_type", "confidence", "section_hierarchy"):
                if hasattr(lc, attr) and getattr(lc, attr) is not None:
                    metadata[attr] = getattr(lc, attr)
            for list_attr in ("defined_terms", "cross_references"):
                if hasattr(lc, list_attr) and getattr(lc, list_attr):
                    metadata[list_attr] = list(getattr(lc, list_attr))

            chunks.append(Chunk(
                id=f"lexichunk_{document.id}_{i}",
                text=lc.text,
                document_id=document.id,
                strategy=self.name,
                index=i,
                metadata=metadata,
            ))

        return ChunkSet(
            strategy=self.name,
            document_id=document.id,
            chunks=tuple(chunks),
            elapsed_seconds=elapsed,
        )


class RCTSStrategy:
    """Wrapper around LangChain's RecursiveCharacterTextSplitter.

    Default: 512-char chunks with 50-char overlap, splitting on paragraph
    and sentence boundaries.
    """

    name = StrategyName.RCTS

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50) -> None:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        self._chunk_size = chunk_size

    def chunk(self, document: Document) -> ChunkSet:
        start = time.perf_counter()
        texts = self._splitter.split_text(document.text)
        elapsed = time.perf_counter() - start

        chunks = tuple(
            Chunk(
                id=f"rcts_{document.id}_{i}",
                text=t,
                document_id=document.id,
                strategy=self.name,
                index=i,
                metadata={"chunk_size_param": self._chunk_size},
            )
            for i, t in enumerate(texts)
        )

        return ChunkSet(
            strategy=self.name,
            document_id=document.id,
            chunks=chunks,
            elapsed_seconds=elapsed,
        )


class SentenceSplitStrategy:
    """Split text on sentence boundaries using regex.

    Splits on: period/question/exclamation followed by whitespace + uppercase,
    OR double newline. Short fragments are merged into the previous chunk
    to avoid tiny chunks.
    """

    name = StrategyName.SENTENCE_SPLIT

    _SENTENCE_PATTERN = re.compile(
        r"(?<=[.!?])\s+(?=[A-Z])|(?:\n\s*\n)"
    )

    def __init__(self, min_chunk_chars: int = 100) -> None:
        self._min_chunk_chars = min_chunk_chars

    def chunk(self, document: Document) -> ChunkSet:
        start = time.perf_counter()
        raw_sentences = self._SENTENCE_PATTERN.split(document.text)

        # Merge short sentences to avoid tiny chunks
        merged: list[str] = []
        buffer = ""
        for sentence in raw_sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            if buffer and len(buffer) + len(sentence) < self._min_chunk_chars:
                buffer = buffer + " " + sentence
            else:
                if buffer:
                    merged.append(buffer)
                buffer = sentence
        if buffer:
            merged.append(buffer)

        elapsed = time.perf_counter() - start

        chunks = tuple(
            Chunk(
                id=f"sentence_split_{document.id}_{i}",
                text=t,
                document_id=document.id,
                strategy=self.name,
                index=i,
                metadata={},
            )
            for i, t in enumerate(merged)
        )

        return ChunkSet(
            strategy=self.name,
            document_id=document.id,
            chunks=chunks,
            elapsed_seconds=elapsed,
        )


class FixedSizeStrategy:
    """Fixed-size chunking at exactly N characters with no overlap.

    This is the simplest possible baseline. Chunks are cut at exact
    character boundaries with no regard for words or sentences.
    """

    name = StrategyName.FIXED_SIZE

    def __init__(self, chunk_size: int = 512) -> None:
        self._chunk_size = chunk_size

    def chunk(self, document: Document) -> ChunkSet:
        start = time.perf_counter()
        text = document.text
        texts: list[str] = []
        for i in range(0, len(text), self._chunk_size):
            segment = text[i : i + self._chunk_size]
            if segment.strip():  # skip empty trailing chunks
                texts.append(segment)
        elapsed = time.perf_counter() - start

        chunks = tuple(
            Chunk(
                id=f"fixed_size_{document.id}_{i}",
                text=t,
                document_id=document.id,
                strategy=self.name,
                index=i,
                metadata={"chunk_size_param": self._chunk_size},
            )
            for i, t in enumerate(texts)
        )

        return ChunkSet(
            strategy=self.name,
            document_id=document.id,
            chunks=chunks,
            elapsed_seconds=elapsed,
        )
```

### Strategy Registry (`src/scaffolder/chunking/__init__.py`)

```python
"""Chunking pipeline and strategy wrappers."""

from __future__ import annotations

from scaffolder.models import ChunkingStrategy, StrategyName
from scaffolder.chunking.strategies import (
    LexiChunkStrategy,
    RCTSStrategy,
    SentenceSplitStrategy,
    FixedSizeStrategy,
)
from scaffolder.chunking.pipeline import ChunkingPipeline

# Registry maps StrategyName -> class. LEXICHUNK_CONTEXTUAL is added on Day 12.
_STRATEGY_REGISTRY: dict[StrategyName, type] = {
    StrategyName.LEXICHUNK: LexiChunkStrategy,
    StrategyName.RCTS: RCTSStrategy,
    StrategyName.SENTENCE_SPLIT: SentenceSplitStrategy,
    StrategyName.FIXED_SIZE: FixedSizeStrategy,
}


def get_strategy(name: StrategyName, **kwargs: object) -> ChunkingStrategy:
    """Instantiate a chunking strategy by name."""
    if name not in _STRATEGY_REGISTRY:
        raise ValueError(
            f"Unknown strategy: {name}. Available: {list(_STRATEGY_REGISTRY.keys())}"
        )
    return _STRATEGY_REGISTRY[name](**kwargs)  # type: ignore[return-value]


def get_all_strategies(**kwargs: object) -> list[ChunkingStrategy]:
    """Instantiate all registered strategies (excludes unregistered ones)."""
    return [get_strategy(name, **kwargs) for name in _STRATEGY_REGISTRY]


__all__ = [
    "ChunkingPipeline",
    "get_strategy",
    "get_all_strategies",
    "LexiChunkStrategy",
    "RCTSStrategy",
    "SentenceSplitStrategy",
    "FixedSizeStrategy",
]
```

Important: `get_all_strategies` iterates `_STRATEGY_REGISTRY` (not `StrategyName`), so `LEXICHUNK_CONTEXTUAL` is excluded until Day 12 registers it.

### ChunkingPipeline (`src/scaffolder/chunking/pipeline.py`)

```python
"""ChunkingPipeline: orchestrates running all strategies on all documents."""

from __future__ import annotations

import logging
import time
from typing import Sequence

from scaffolder.models import (
    ChunkingStrategy,
    Document,
    StrategyResult,
    StrategyName,
)

logger = logging.getLogger(__name__)


class ChunkingPipeline:
    """Runs multiple chunking strategies across multiple documents.

    Usage:
        strategies = get_all_strategies()
        pipeline = ChunkingPipeline(strategies)
        results = pipeline.run(documents)
        # results: list[StrategyResult], one per strategy
    """

    def __init__(self, strategies: Sequence[ChunkingStrategy]) -> None:
        self._strategies = list(strategies)
        if not self._strategies:
            raise ValueError("At least one strategy is required.")

    def run(self, documents: Sequence[Document]) -> list[StrategyResult]:
        """Run all strategies on all documents.

        Returns:
            One StrategyResult per strategy, each containing ChunkSets
            for every document.
        """
        results: list[StrategyResult] = []

        for strategy in self._strategies:
            logger.info("Running strategy: %s", strategy.name.value)
            total_start = time.perf_counter()
            chunk_sets = []

            for doc in documents:
                logger.info(
                    "  Chunking %s (%d chars)...",
                    doc.id,
                    doc.char_count,
                )
                cs = strategy.chunk(doc)
                chunk_sets.append(cs)
                logger.info(
                    "    -> %d chunks in %.3fs (avg %.0f chars/chunk)",
                    cs.count,
                    cs.elapsed_seconds,
                    cs.avg_chunk_size,
                )

            total_elapsed = time.perf_counter() - total_start
            results.append(StrategyResult(
                strategy=strategy.name,
                chunk_sets=tuple(chunk_sets),
                total_elapsed_seconds=total_elapsed,
            ))

        return results

    def run_single(
        self, strategy_name: StrategyName, documents: Sequence[Document]
    ) -> StrategyResult:
        """Run a single named strategy on all documents."""
        for strategy in self._strategies:
            if strategy.name == strategy_name:
                total_start = time.perf_counter()
                chunk_sets = []
                for doc in documents:
                    chunk_sets.append(strategy.chunk(doc))
                total_elapsed = time.perf_counter() - total_start
                return StrategyResult(
                    strategy=strategy.name,
                    chunk_sets=tuple(chunk_sets),
                    total_elapsed_seconds=total_elapsed,
                )
        raise ValueError(
            f"Strategy '{strategy_name}' not found in pipeline. "
            f"Available: {[s.name for s in self._strategies]}"
        )
```

### Tests (`tests/test_chunking.py`)

Test each strategy independently and the pipeline as a whole. Use a small fake document for speed:

```python
"""Tests for ChunkingPipeline and strategy wrappers."""

import pytest
from scaffolder.models import Document, Jurisdiction, DocumentType, StrategyName

TINY_DOC = Document(
    id="test_doc",
    text=(
        '1. Definitions.\n'
        '1.1 "Service Provider" means the party providing services under this Agreement.\n'
        '1.2 "Client" means the party receiving services.\n'
        '2. Obligations.\n'
        '2.1 The Service Provider shall deliver services as defined in Section 1.1.\n'
        '2.2 Subject to Clause 3, the Client shall pay the fees set out in Schedule 1.\n'
        '3. Payment Terms.\n'
        '3.1 Fees are due within 30 days of invoice date.\n'
        '3.2 Late payments shall accrue interest at 4% above the base rate.\n'
    ),
    jurisdiction=Jurisdiction.UK,
    document_type=DocumentType.SERVICE_AGREEMENT,
    source="test.txt",
)
```

Tests to include:
- Each strategy returns a `ChunkSet` with at least 1 chunk
- `ChunkSet.document_id` matches input document
- `Chunk.strategy` matches the strategy name
- `Chunk.id` follows the naming convention (`{strategy}_{doc_id}_{index}`)
- `elapsed_seconds > 0`
- Pipeline `run()` returns one `StrategyResult` per strategy
- Pipeline `run_single()` returns only the requested strategy
- Pipeline with empty strategies list raises `ValueError`
- Fixed-size chunks are all <= 512 chars (except possibly zero-length trailing)
- LexiChunk chunks have metadata keys (at minimum, non-empty metadata dict for some chunks)
- Sentence-split produces chunks of at least `min_chunk_chars` length (except the last)
- RCTS produces chunks of roughly the configured size

## Outputs
- `src/scaffolder/chunking/strategies.py`
- `src/scaffolder/chunking/pipeline.py`
- `src/scaffolder/chunking/__init__.py` (updated with registry)
- `tests/test_chunking.py`

## Acceptance Criteria
1. `python -c "from scaffolder.chunking import get_all_strategies; print([s.name.value for s in get_all_strategies()])"` prints all four strategy names.
2. `pytest tests/test_chunking.py -v` -- all tests pass.
3. Integration test: load all fixtures via `FixtureManager`, run `ChunkingPipeline` with all strategies, verify each `StrategyResult` has 5 `ChunkSet`s with non-zero chunk counts.
4. `mypy src/scaffolder/chunking/ --strict` passes.
5. `ruff check src/scaffolder/chunking/` passes.

## Handoff Notes
- **To Day 4:** `ChunkingPipeline.run()` returns `list[StrategyResult]`. Each `StrategyResult` contains `tuple[ChunkSet, ...]`. Structural metrics functions will take `(ChunkSet, Document)` pairs.
- **To Agent B:** The strategy registry is extensible. To add a new strategy, implement the `ChunkingStrategy` protocol, add it to `_STRATEGY_REGISTRY` in `chunking/__init__.py`, and add a `StrategyName` enum value in `models.py`.
- **Note:** The `LexiChunkStrategy` extracts metadata (clause_type, defined_terms, cross_references, section_hierarchy) into `Chunk.metadata`. This metadata is critical for structural metrics on Day 4.
- **Note:** `get_all_strategies()` only instantiates strategies that are in `_STRATEGY_REGISTRY`, not all `StrategyName` enum members. `LEXICHUNK_CONTEXTUAL` will be added in Day 12.
