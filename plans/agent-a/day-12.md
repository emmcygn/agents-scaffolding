# Agent A — Day 12: Contextual Retrieval Comparison

## Mission
Run LexiChunk with `build_embedded_text()` (context headers ON) vs LexiChunk with raw chunk text (headers OFF) to quantify the improvement from contextual retrieval, directly testing Anthropic's contextual retrieval hypothesis on legal documents.

## Context
Days 6-11 built the full retrieval benchmark. We have LexiChunk vs 3 baselines across 3 embedding models. Now we add a 5th "strategy" -- LexiChunk with contextual headers -- and measure whether enriching chunk text with section hierarchy, defined terms, and cross-reference context improves retrieval. This tests the core hypothesis from Anthropic's contextual retrieval research.

Agent B is working on Streamlit page_retrieval.py today.

## Prerequisites
- Full benchmark pipeline from Day 10 working
- `lexichunk` installed with `build_embedded_text()` function available
- `src/scaffolder/models.py` has `StrategyName.LEXICHUNK_CONTEXTUAL`
- `src/scaffolder/chunking/__init__.py` has `_STRATEGY_REGISTRY`

## Checklist
- [ ] Implement `LexiChunkContextualStrategy` in `src/scaffolder/chunking/strategies.py`
- [ ] Register it in `_STRATEGY_REGISTRY` as `LEXICHUNK_CONTEXTUAL`
- [ ] Run full benchmark with 5 strategies (4 original + contextual)
- [ ] Compare LexiChunk raw vs LexiChunk contextual retrieval metrics
- [ ] Run significance test between the two LexiChunk variants
- [ ] Update CLI output to highlight contextual vs raw comparison

## Implementation Details

### LexiChunkContextualStrategy (`src/scaffolder/chunking/strategies.py`)

```python
class LexiChunkContextualStrategy:
    """LexiChunk with contextual retrieval headers.

    Uses lexichunk.build_embedded_text() to prepend context headers to each
    chunk before embedding. The headers include:
    - Document title / section hierarchy path
    - Clause type classification
    - Defined terms present in this chunk
    - Cross-reference targets

    This is the "contextual retrieval" approach from Anthropic's research:
    enriching chunk text with surrounding context to improve embedding quality.
    """

    name = StrategyName.LEXICHUNK_CONTEXTUAL

    def __init__(self, **kwargs: Any) -> None:
        from lexichunk import LegalChunker
        self._chunker = LegalChunker(**kwargs)

    def chunk(self, document: Document) -> ChunkSet:
        start = time.perf_counter()
        legal_chunks = self._chunker.chunk(document.text, document_id=document.id)
        elapsed = time.perf_counter() - start

        chunks: list[Chunk] = []
        for i, lc in enumerate(legal_chunks):
            # Build contextual embedded text
            try:
                from lexichunk import build_embedded_text
                embedded_text = build_embedded_text(lc)
            except (ImportError, AttributeError):
                # Fallback: build context header manually
                embedded_text = _build_context_header(lc) + lc.text

            metadata: dict[str, Any] = {"contextual": True}
            for attr in ("clause_type", "confidence", "section_hierarchy"):
                if hasattr(lc, attr) and getattr(lc, attr) is not None:
                    metadata[attr] = getattr(lc, attr)
            for list_attr in ("defined_terms", "cross_references"):
                if hasattr(lc, list_attr) and getattr(lc, list_attr):
                    metadata[list_attr] = list(getattr(lc, list_attr))
            # Store original text for structural metrics
            metadata["original_text"] = lc.text

            chunks.append(Chunk(
                id=f"lexichunk_ctx_{document.id}_{i}",
                text=embedded_text,  # contextual text for embedding
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


def _build_context_header(legal_chunk: Any) -> str:
    """Manually build context header when build_embedded_text is unavailable.

    Format:
    [Section: 2.1 | Type: obligation | Terms: Service Provider, Client]
    <original chunk text>
    """
    parts: list[str] = []

    if hasattr(legal_chunk, "section_hierarchy") and legal_chunk.section_hierarchy:
        if isinstance(legal_chunk.section_hierarchy, (list, tuple)):
            parts.append(f"Section: {'.'.join(str(s) for s in legal_chunk.section_hierarchy)}")
        else:
            parts.append(f"Section: {legal_chunk.section_hierarchy}")

    if hasattr(legal_chunk, "clause_type") and legal_chunk.clause_type:
        parts.append(f"Type: {legal_chunk.clause_type}")

    if hasattr(legal_chunk, "defined_terms") and legal_chunk.defined_terms:
        terms = ", ".join(sorted(legal_chunk.defined_terms)[:5])  # limit to 5
        parts.append(f"Terms: {terms}")

    if hasattr(legal_chunk, "cross_references") and legal_chunk.cross_references:
        refs = [str(r) for r in legal_chunk.cross_references[:3]]
        parts.append(f"Refs: {', '.join(refs)}")

    if parts:
        return f"[{' | '.join(parts)}]\n"
    return ""
```

### Register in Strategy Registry

Update `src/scaffolder/chunking/__init__.py`:

```python
from scaffolder.chunking.strategies import (
    LexiChunkStrategy,
    LexiChunkContextualStrategy,  # NEW
    RCTSStrategy,
    SentenceSplitStrategy,
    FixedSizeStrategy,
)

_STRATEGY_REGISTRY: dict[StrategyName, type] = {
    StrategyName.LEXICHUNK: LexiChunkStrategy,
    StrategyName.LEXICHUNK_CONTEXTUAL: LexiChunkContextualStrategy,  # NEW
    StrategyName.RCTS: RCTSStrategy,
    StrategyName.SENTENCE_SPLIT: SentenceSplitStrategy,
    StrategyName.FIXED_SIZE: FixedSizeStrategy,
}
```

### Structural Metrics Note

For structural metrics on contextual chunks, use the `original_text` from metadata if available. The context header should NOT count toward structural metrics (it would artificially inflate definition preservation and cross-ref resolution). Update `compute_structural_metrics()` if needed:

```python
# In structural.py, when computing metrics for LEXICHUNK_CONTEXTUAL:
# Use chunk.metadata.get("original_text", chunk.text) for structural analysis
```

### Significance Testing: Raw vs Contextual

Add a special comparison in the significance report -- LexiChunk raw vs LexiChunk contextual:

```python
# In compute_all_significance(), also compare LEXICHUNK vs LEXICHUNK_CONTEXTUAL
# This is the key experiment: does contextual text improve retrieval?

# Expected findings:
# - Contextual should improve MRR and NDCG@10 by 5-20%
# - The improvement should be larger for definition_lookup queries
# - The improvement may be smaller for Voyage (already legal-aware embeddings)
```

### Tests

```python
# tests/test_contextual.py

# 1. LexiChunkContextualStrategy produces chunks with "contextual" in metadata
# 2. Contextual chunk text is longer than raw chunk text (has header)
# 3. Contextual chunk metadata has "original_text" key
# 4. _build_context_header produces non-empty string for chunks with metadata
# 5. _build_context_header produces empty string for bare chunks
# 6. Both LexiChunk variants produce same number of chunks for same document
```

## Outputs
- `src/scaffolder/chunking/strategies.py` (added LexiChunkContextualStrategy)
- `src/scaffolder/chunking/__init__.py` (registered new strategy)
- `src/scaffolder/metrics/structural.py` (handle contextual chunks)
- `tests/test_contextual.py`

## Acceptance Criteria
1. `make benchmark-embed` now runs 5 strategies instead of 4.
2. CLI output includes `lexichunk_contextual` in all tables.
3. Significance table includes LexiChunk vs LexiChunk Contextual comparison.
4. Contextual retrieval shows measurable improvement on at least MRR or NDCG.
5. `pytest tests/test_contextual.py -v` -- all tests pass.
6. `mypy src/scaffolder/chunking/ --strict` passes.

## Handoff Notes
- **To Agent B:** There are now 5 strategies in the benchmark. Update Streamlit dashboard to include `lexichunk_contextual` in all charts and comparisons. The key story is: LexiChunk (raw) > baselines, and LexiChunk (contextual) > LexiChunk (raw).
- **To Day 13:** All metrics and comparisons are complete. Day 13 starts the HTML report template.
- **Key finding to highlight:** The contextual vs raw comparison directly validates Anthropic's contextual retrieval hypothesis. Document the percentage improvement and which query categories benefit most.
