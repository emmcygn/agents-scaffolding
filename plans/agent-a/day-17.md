# Agent A — Day 17: Edge Cases + Performance Optimization

## Mission
Handle edge cases (empty documents, single-clause documents, documents with no definitions or cross-references) and optimize performance so the full benchmark (no Voyage) completes in under 5 minutes.

## Context
Day 16 reached 80% test coverage. All core functionality works. Today we harden the code against degenerate inputs and optimize the hot paths. This day includes PAIRING with Agent B on README content.

Agent B is working on deployment config and will PAIR on README sections.

## Prerequisites
- All modules functional and tested at 80%+ coverage
- `make benchmark-embed` working end-to-end

## Checklist
- [ ] Handle empty documents (0 chars) in all pipeline stages
- [ ] Handle single-clause documents (only 1 chunk from LexiChunk)
- [ ] Handle documents with no defined terms
- [ ] Handle documents with no cross-references
- [ ] Handle documents with no section numbering (flat text)
- [ ] Handle queries with no relevant sections
- [ ] Handle empty query list
- [ ] Profile benchmark run and identify bottlenecks
- [ ] Optimize embedding batch sizes
- [ ] Optimize FAISS index building
- [ ] Optimize ground truth caching
- [ ] Ensure full benchmark (no Voyage) completes in < 5 minutes
- [ ] PAIR with Agent B on README content and structure

## Implementation Details

### Edge Case: Empty Document

Every stage must handle a document with `text = ""` or `text = " "`:

```python
# In each strategy's chunk() method:
def chunk(self, document: Document) -> ChunkSet:
    if not document.text.strip():
        return ChunkSet(
            strategy=self.name,
            document_id=document.id,
            chunks=(),
            elapsed_seconds=0.0,
        )
    # ... normal chunking logic
```

In structural metrics:
```python
def clause_fragmentation_rate(chunk_set: ChunkSet, document: Document) -> float:
    if not chunk_set.chunks:
        return 0.0  # no chunks = no fragmentation
    # ...
```

In embedding pipeline:
```python
def embed_texts(self, texts: Sequence[str], model_name: EmbeddingModelName) -> npt.NDArray[np.float32]:
    if not texts:
        adapter = self._get_adapter(model_name)
        return np.zeros((0, adapter.dimension), dtype=np.float32)
    # ...
```

In FAISS index:
```python
def add(self, chunks: Sequence[Chunk], embeddings: npt.NDArray[np.float32]) -> None:
    if len(chunks) == 0:
        return  # nothing to add
    # ...
```

### Edge Case: Single-Clause Document

A document with only one section/clause will produce:
- 1 chunk from LexiChunk (possibly 1 from baselines too)
- Fragmentation = 0.0 (only 1 clause, cannot be fragmented)
- chunk_size_cv = 0.0 (only 1 chunk)
- Metrics should still work correctly

Test with:
```python
SINGLE_CLAUSE_DOC = Document(
    id="single_clause",
    text="1. This agreement is governed by English law.",
    jurisdiction=Jurisdiction.UK,
    document_type=DocumentType.SERVICE_AGREEMENT,
    source="test_single.txt",
)
```

### Edge Case: No Definitions / No Cross-References / No Hierarchy

For documents without these features, the metrics should return vacuously true values:
- `definition_preservation_rate` = 1.0 (no terms to preserve)
- `cross_ref_resolution_rate` = 1.0 (no refs to resolve)
- `hierarchy_depth_retained` = 1.0 (flat = depth 1, any numbering matches)

### Edge Case: Empty Query List

```python
# In RetrievalSimulator.run():
def run(self, queries, strategies, models, k=10):
    if not queries:
        logger.warning("No queries provided.")
        return []
    # ...
```

### Edge Case: Queries with No Relevant Sections

```python
# Already handled: recall_at_k returns 1.0 for empty relevant_sections
# MRR returns 0.0 (no relevant hit to find)
# NDCG returns 0.0 (no relevant items)
# Verify these are consistent and documented
```

### Performance Profiling

Profile the benchmark run to find bottlenecks:

```bash
python -m cProfile -o benchmark.prof -m scaffolder benchmark-embed --json
# Or use time markers in the code
```

Expected bottlenecks and optimizations:

1. **Ground truth parsing** (LexiChunk called once per document per metric call):
   - Already cached in `_gt_cache`. Verify cache is working.
   - Ensure `get_ground_truth()` is called once per document, not once per (strategy, document).

2. **Embedding** (model loading + inference):
   - Model loading: happens once per model (lazy). No optimization needed.
   - Inference: batch all chunks from one strategy before calling `embed_texts()`.
   - Cache should prevent re-embedding on repeat runs.
   - Verify batch size is optimal (64 for MiniLM, 32 for BGE).

3. **FAISS index building**:
   - `IndexFlatIP.add()` is fast for <1000 vectors. No optimization needed.
   - Pre-normalize vectors before adding (sentence-transformers already does this).

4. **Retrieval simulation**:
   - Batch-embed all query texts at once (already done in simulator).
   - FAISS search is fast for flat index.

5. **Metric computation**:
   - Metrics are pure Python. If slow, consider:
     - Pre-computing lowercase texts
     - Caching word sets
   - For `_text_overlap_ratio`, consider caching word sets per chunk.

### Performance Optimization: Batch Processing

```python
# In structural metrics, avoid re-parsing ground truth:
def compute_all_structural_metrics(
    strategy_results: list[StrategyResult],
    documents: dict[str, Document],
) -> list[StructuralMetrics]:
    """Compute structural metrics for all strategy results efficiently.

    Pre-computes ground truth once per document, then reuses for all strategies.
    """
    # Pre-warm ground truth cache
    for doc in documents.values():
        get_ground_truth(doc)

    results: list[StructuralMetrics] = []
    for sr in strategy_results:
        for cs in sr.chunk_sets:
            doc = documents[cs.document_id]
            results.append(compute_structural_metrics(cs, doc))
    return results
```

### Timing Target

Verify with:
```bash
time make benchmark-embed
# Target: < 5 minutes without Voyage (local models only)
# Breakdown:
#   Chunking: ~10s (all strategies x all docs)
#   Embedding: ~30-60s (MiniLM) + ~60-120s (BGE) = ~2-3 min total
#   Indexing: ~1s
#   Retrieval: ~5s
#   Metrics: ~10s
#   Reporting: ~2s
```

If embedding is the bottleneck (likely), ensure cache is working so subsequent runs are fast (~30s).

### PAIR with Agent B on README

Coordinate on README structure:
- Agent A provides: benchmark results summary, metric descriptions, architecture overview
- Agent B provides: installation, quickstart, CLI usage, screenshots, deployment

Key sections for Agent A:
```markdown
## Benchmark Results

LexiChunk consistently outperforms general-purpose alternatives:

| Metric | LexiChunk | RCTS | Sentence | Fixed-512 |
|--------|-----------|------|----------|-----------|
| NDCG@10 (MiniLM) | 0.XXX | 0.XXX | 0.XXX | 0.XXX |
| MRR (MiniLM) | 0.XXX | 0.XXX | 0.XXX | 0.XXX |
| Clause Fragmentation | 0.XXX | 0.XXX | 0.XXX | 0.XXX |
| Def Preservation | 0.XXX | 0.XXX | 0.XXX | 0.XXX |

All improvements are statistically significant (p < 0.05, paired t-test).
```

Fill in actual numbers from the benchmark run.

### Edge Case Tests (`tests/test_edge_cases.py`)

```python
"""Tests for edge cases: empty docs, single clause, no definitions, etc."""

import pytest
from scaffolder.models import Document, Jurisdiction, DocumentType, StrategyName
from scaffolder.chunking.strategies import (
    LexiChunkStrategy, RCTSStrategy, SentenceSplitStrategy, FixedSizeStrategy,
)
from scaffolder.metrics.structural import compute_structural_metrics

EMPTY_DOC = Document(
    id="empty", text="", jurisdiction=Jurisdiction.UK,
    document_type=DocumentType.SERVICE_AGREEMENT, source="empty.txt",
)

WHITESPACE_DOC = Document(
    id="whitespace", text="   \n\n  \t  ",
    jurisdiction=Jurisdiction.UK,
    document_type=DocumentType.SERVICE_AGREEMENT, source="whitespace.txt",
)

SINGLE_CLAUSE_DOC = Document(
    id="single", text="1. This agreement is governed by English law.",
    jurisdiction=Jurisdiction.UK,
    document_type=DocumentType.SERVICE_AGREEMENT, source="single.txt",
)

NO_DEFS_DOC = Document(
    id="no_defs",
    text="1. Obligations.\n1.1 The parties agree to cooperate.\n2. Termination.\n2.1 Either party may terminate.",
    jurisdiction=Jurisdiction.UK,
    document_type=DocumentType.SERVICE_AGREEMENT, source="no_defs.txt",
)

class TestEmptyDocument:
    @pytest.mark.parametrize("strategy_cls", [
        RCTSStrategy, SentenceSplitStrategy, FixedSizeStrategy,
    ])
    def test_empty_doc_returns_empty_chunkset(self, strategy_cls):
        strategy = strategy_cls()
        cs = strategy.chunk(EMPTY_DOC)
        assert cs.count == 0

    @pytest.mark.parametrize("strategy_cls", [
        RCTSStrategy, SentenceSplitStrategy, FixedSizeStrategy,
    ])
    def test_whitespace_doc_returns_empty_chunkset(self, strategy_cls):
        strategy = strategy_cls()
        cs = strategy.chunk(WHITESPACE_DOC)
        assert cs.count == 0

class TestSingleClause:
    def test_single_clause_no_fragmentation(self):
        strategy = FixedSizeStrategy(chunk_size=1000)  # larger than doc
        cs = strategy.chunk(SINGLE_CLAUSE_DOC)
        assert cs.count == 1

class TestNoDefinitions:
    def test_no_defs_preservation_is_one(self):
        strategy = FixedSizeStrategy()
        cs = strategy.chunk(NO_DEFS_DOC)
        sm = compute_structural_metrics(cs, NO_DEFS_DOC)
        assert sm.definition_preservation_rate == 1.0
```

## Outputs
- `src/scaffolder/chunking/strategies.py` (edge case handling)
- `src/scaffolder/metrics/structural.py` (edge case handling)
- `src/scaffolder/embedding/pipeline.py` (edge case handling)
- `src/scaffolder/retrieval/index.py` (edge case handling)
- `src/scaffolder/retrieval/simulator.py` (edge case handling)
- `tests/test_edge_cases.py`
- README content for Agent B (benchmark results table)

## Acceptance Criteria
1. All edge case tests pass: `pytest tests/test_edge_cases.py -v`
2. `make benchmark-embed` completes in < 5 minutes (no Voyage).
3. Second run with cache completes in < 1 minute.
4. No crashes or exceptions on degenerate inputs.
5. Coverage remains >= 80%: `pytest --cov=scaffolder --cov-fail-under=80`

## Handoff Notes
- **To Agent B (README PAIR):** The benchmark results table is ready with actual numbers. Insert it into the README under "## Benchmark Results". The architecture overview should reference: `FixtureManager -> ChunkingPipeline -> EmbeddingPipeline -> VectorIndex -> RetrievalSimulator -> Metrics -> Reporters`.
- **To Day 18:** Edge cases and performance are handled. Day 18 continues README work and sets up pyproject.toml extras.
