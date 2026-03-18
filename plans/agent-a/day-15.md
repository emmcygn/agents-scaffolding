# Agent A — Day 15: Metrics Documentation + Final Benchmark Run

## Mission
Write `docs/metrics.md` with formal definitions, formulas, and interpretation guidance for all 10 metrics, then run a final benchmark with all available models and perform a sanity check on every number.

## Context
Weeks 1-2 built the full pipeline. Days 13-14 completed the HTML report. All code is functional. Today is about documentation quality and numerical correctness before the Week 4 hardening phase. This is the last day of Week 3.

Agent B is working on EXTENSIBILITY.md today.

## Prerequisites
- All metrics implemented and tested (structural: Days 4-5, retrieval: Day 9, statistical: Day 10)
- `make benchmark-embed` runs end-to-end
- `make report` generates HTML

## Checklist
- [ ] Write `docs/metrics.md` with formal definitions for all 10 metrics
- [ ] Include LaTeX-style formulas (GitHub-renderable)
- [ ] Include interpretation guidance for each metric
- [ ] Include citation references
- [ ] Run final benchmark with all models (MiniLM + BGE + Voyage if available)
- [ ] Sanity check: verify all metric values are in expected ranges
- [ ] Sanity check: verify LexiChunk consistently outperforms baselines
- [ ] Sanity check: verify significance results have correct p-values
- [ ] Fix any anomalies discovered

## Implementation Details

### `docs/metrics.md` Structure

```markdown
# Metrics Reference

This document defines all metrics used by sdk-scaffolder to evaluate
chunking strategies for legal document RAG.

## Structural Metrics

Structural metrics measure how well a chunking strategy preserves the
semantic structure of legal documents. Ground truth is established by
parsing each document with LexiChunk's LegalChunker.

### 1. Clause Fragmentation Rate (CFR)

**Definition:** The fraction of ground-truth clauses that are split
(fragmented) across multiple chunks.

**Formula:**

    CFR = |fragmented clauses| / |total clauses|

A clause is "fragmented" if no single chunk contains >= 80% of its
words (measured by word-level overlap).

**Range:** [0.0, 1.0]
**Ideal:** 0.0 (no fragmentation)
**Interpretation:**
- < 0.1: Excellent — nearly all clauses are intact
- 0.1-0.3: Good — minor fragmentation at clause boundaries
- 0.3-0.5: Fair — significant fragmentation affecting retrieval
- > 0.5: Poor — most clauses split, retrieval will return partial answers

### 2. Definition Preservation Rate (DPR)

**Definition:** The fraction of defined terms whose definition context
(the "means" clause) is accessible within at least one chunk.

**Formula:**

    DPR = |preserved terms| / |total defined terms|

A term is "preserved" if at least one chunk contains both the term and
a definition indicator ("means", "shall mean", "defined as").

**Range:** [0.0, 1.0]
**Ideal:** 1.0 (all definitions preserved)
**Interpretation:**
- > 0.9: Excellent — nearly all definitions available for retrieval
- 0.7-0.9: Good — most definitions available
- 0.5-0.7: Fair — many definitions lost to chunking boundaries
- < 0.5: Poor — definitions systematically broken

### 3. Cross-Reference Resolution Rate (CRRR)

**Definition:** The fraction of cross-references that can be resolved
from the chunks.

**Formula:**

    CRRR = |resolved references| / |total references|

A reference is "resolved" if the chunk containing the reference also
contains (or is adjacent to a chunk containing) the target section.

**Range:** [0.0, 1.0]
**Ideal:** 1.0

### 4. Hierarchy Depth Retained (HDR)

**Definition:** The ratio of maximum section numbering depth found in
chunks vs the original document.

**Formula:**

    HDR = max_depth_in_chunks / max_depth_in_document

**Range:** [0.0, 1.0]
**Ideal:** 1.0

### 5. Chunk Size Coefficient of Variation (CV)

**Definition:** Standard deviation of chunk sizes divided by mean chunk
size. Measures uniformity of chunk sizes.

**Formula:**

    CV = std(chunk_sizes) / mean(chunk_sizes)

**Range:** [0.0, inf)
**Ideal:** Context-dependent. Very low CV with fixed-size chunking is
expected. LexiChunk may have higher CV due to varying clause lengths,
which is acceptable.

## Retrieval Metrics

Retrieval metrics measure the quality of search results when using
chunked documents in a RAG pipeline. Queries are annotated with
ground-truth relevant sections and graded relevance.

### 6. Precision@k

**Formula:**

    P@k = |{relevant documents in top k}| / k

**Range:** [0.0, 1.0]
**Reported at:** k = 1, 3, 5, 10

### 7. Recall@k

**Formula:**

    R@k = |{relevant documents in top k}| / |{total relevant documents}|

**Range:** [0.0, 1.0]
**Reported at:** k = 1, 3, 5, 10

### 8. Mean Reciprocal Rank (MRR)

**Formula:**

    MRR = 1 / rank_of_first_relevant_result

**Range:** [0.0, 1.0]
**Interpretation:**
- MRR = 1.0: First result is always relevant
- MRR = 0.5: First relevant result is typically at rank 2

**Citation:** Voorhees, E.M. "The TREC-8 Question Answering Track Report."
TREC, 1999.

### 9. Normalized Discounted Cumulative Gain at 10 (NDCG@10)

**Definition:** Measures ranking quality with graded relevance.

**Graded relevance scale:**
- 3 (EXACT): Chunk contains the exact answer passage
- 2 (SAME_SECTION): Chunk is from the correct section
- 1 (RELATED): Chunk is topically related
- 0 (IRRELEVANT): Chunk is not relevant

**Formula:**

    DCG@k = sum_{i=1}^{k} (2^{rel_i} - 1) / log2(i + 1)
    IDCG@k = DCG@k for ideal ranking (sorted by relevance descending)
    NDCG@k = DCG@k / IDCG@k

**Range:** [0.0, 1.0]
**Ideal:** 1.0 (perfect ranking)

**Citation:** Jarvelin, K. and Kekalainen, J. "Cumulated Gain-Based
Evaluation of IR Techniques." ACM TOIS, 20(4):422-446, 2002.

### 10. Document Retrieval Mismatch Rate (DRM)

**Definition:** Fraction of top-k results from documents other than
the query's target document(s).

**Formula:**

    DRM = |{top-k chunks from non-target documents}| / k

**Range:** [0.0, 1.0]
**Ideal:** 0.0

## Statistical Testing

### Paired t-test

Compares LexiChunk vs each baseline using per-query metric values.

**Method:** scipy.stats.ttest_rel (two-sided paired t-test)
**Threshold:** alpha = 0.05
**Effect size:** Cohen's d = mean(differences) / std(differences)
- Small: d = 0.2
- Medium: d = 0.5
- Large: d = 0.8

**Citation:** Cohen, J. "Statistical Power Analysis for the Behavioral
Sciences." 2nd ed., Lawrence Erlbaum, 1988.
```

### Final Benchmark Run

Execute the complete benchmark and verify outputs:

```bash
# Clean previous results
rm -rf results/

# Run structural benchmark
make benchmark

# Run full benchmark with embeddings
make benchmark-embed

# Generate HTML report
make report

# Verify outputs exist
ls -la results/
# Expected: structural_benchmark.json, full_benchmark.json, report.html
```

### Sanity Checks

Verify these invariants hold for every (strategy, document, model) combination:

1. **Range checks:** All metrics in [0.0, 1.0] except chunk_size_cv
2. **LexiChunk dominance:** LexiChunk's clause_fragmentation_rate < every baseline's
3. **LexiChunk dominance:** LexiChunk's definition_preservation_rate > every baseline's
4. **NDCG consistency:** NDCG@10 >= MRR in most cases (graded > binary)
5. **Recall monotonicity:** R@1 <= R@3 <= R@5 <= R@10 for same (strategy, model)
6. **Precision trend:** P@1 >= P@10 in most cases
7. **Significance direction:** Where significant, LexiChunk mean > baseline mean
8. **DRM expectation:** LexiChunk should have lower DRM than baselines
9. **Contextual improvement:** LexiChunk Contextual NDCG@10 >= LexiChunk raw NDCG@10

Write a verification script or add assertions in a test:

```python
# tests/test_sanity.py
def test_metric_ranges(benchmark_result):
    for sm in benchmark_result.structural_metrics:
        assert 0.0 <= sm.clause_fragmentation_rate <= 1.0
        assert 0.0 <= sm.definition_preservation_rate <= 1.0
        assert 0.0 <= sm.cross_ref_resolution_rate <= 1.0
        assert 0.0 <= sm.hierarchy_depth_retained <= 1.0
        assert sm.chunk_size_cv >= 0.0

def test_recall_monotonicity(benchmark_result):
    for rm in benchmark_result.retrieval_metrics:
        assert rm.recall_at_1 <= rm.recall_at_3 + 0.001  # small epsilon
        assert rm.recall_at_3 <= rm.recall_at_5 + 0.001
        assert rm.recall_at_5 <= rm.recall_at_10 + 0.001
```

## Outputs
- `docs/metrics.md`
- `results/structural_benchmark.json` (refreshed)
- `results/full_benchmark.json` (refreshed)
- `results/report.html` (refreshed)
- `tests/test_sanity.py`

## Acceptance Criteria
1. `docs/metrics.md` contains definitions for all 10 metrics with formulas.
2. All metric formulas are correct and match the implementation.
3. Final benchmark run completes without errors.
4. All sanity checks pass.
5. `results/report.html` opens correctly in a browser with all data.
6. `pytest tests/test_sanity.py -v` -- all tests pass on real benchmark data.

## Handoff Notes
- **To Agent B:** The `docs/metrics.md` file is complete. Reference it from EXTENSIBILITY.md and README. The methodology section in the HTML report matches these definitions.
- **To Day 16:** All code and documentation for the metrics layer is complete. Day 16 focuses on test coverage to reach the 80% target.
- **Week 3 milestone:** The complete evaluation is done -- structural + retrieval + contextual + Voyage + significance + HTML report + metrics documentation. Week 4 is hardening, testing, and release prep.
