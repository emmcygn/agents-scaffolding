# Agent A — Day 09: Retrieval Quality Metrics

## Mission
Implement all retrieval quality metrics -- precision@k, recall@k, MRR, NDCG@10, and DRM rate -- as pure functions that score RetrievalResults, completing the quantitative evaluation framework.

## Context
Day 8 delivered `RetrievalSimulator` which produces `RetrievalResult` objects containing retrieved chunks matched against ground-truth relevant sections. Today we write the scoring functions. These are all pure math -- no I/O, no models, no FAISS. Agent B is working on Streamlit dashboard scaffolding today.

## Prerequisites
- `src/scaffolder/models.py` with `RetrievalResult`, `RetrievalHit`, `RetrievalMetrics`, `RelevanceGrade`, `AnnotatedQuery`, `RelevantSection`
- `src/scaffolder/retrieval/simulator.py` with `RetrievalSimulator` and `get_relevance_grade()`
- `numpy` installed

## Checklist
- [ ] Implement `precision_at_k()` in `src/scaffolder/metrics/retrieval.py`
- [ ] Implement `recall_at_k()` in `src/scaffolder/metrics/retrieval.py`
- [ ] Implement `mrr()` (Mean Reciprocal Rank)
- [ ] Implement `ndcg_at_k()` (Normalized Discounted Cumulative Gain with graded relevance)
- [ ] Implement `drm_rate()` (Document Retrieval Mismatch)
- [ ] Implement `compute_retrieval_metrics()` convenience function
- [ ] Write exhaustive tests in `tests/test_retrieval_metrics.py`

## Implementation Details

### All metrics in `src/scaffolder/metrics/retrieval.py`

```python
"""Retrieval quality metrics for evaluating chunking strategies.

All functions are pure: they take retrieval results and return floats.
No side effects, no I/O, no model calls.
"""

from __future__ import annotations

import math
import logging
from typing import Sequence

from scaffolder.models import (
    Chunk,
    RelevanceGrade,
    RelevantSection,
    RetrievalHit,
    RetrievalMetrics,
    RetrievalResult,
)

logger = logging.getLogger(__name__)


def precision_at_k(
    hits: Sequence[RetrievalHit],
    relevant_sections: Sequence[RelevantSection],
    k: int,
    *,
    relevance_checker=None,
) -> float:
    """Precision@k: fraction of top-k results that are relevant.

    P@k = |relevant in top-k| / k

    Args:
        hits: Retrieved chunks ordered by rank (1-indexed).
        relevant_sections: Ground-truth relevant sections.
        k: Cutoff rank.
        relevance_checker: Optional callable(chunk, sections) -> bool.
            If None, uses default _is_hit().

    Returns:
        Float in [0.0, 1.0].
    """
    if k <= 0:
        return 0.0

    checker = relevance_checker or _is_hit
    top_k = [h for h in hits if h.rank <= k]
    if not top_k:
        return 0.0

    relevant_count = sum(
        1 for h in top_k if checker(h.chunk, relevant_sections)
    )
    return relevant_count / k


def recall_at_k(
    hits: Sequence[RetrievalHit],
    relevant_sections: Sequence[RelevantSection],
    k: int,
    *,
    relevance_checker=None,
) -> float:
    """Recall@k: fraction of all relevant items found in top-k.

    R@k = |relevant in top-k| / |total relevant|

    Returns 1.0 if there are no relevant sections (vacuously true).
    """
    if not relevant_sections:
        return 1.0
    if k <= 0:
        return 0.0

    checker = relevance_checker or _is_hit
    top_k = [h for h in hits if h.rank <= k]

    relevant_count = sum(
        1 for h in top_k if checker(h.chunk, relevant_sections)
    )
    return relevant_count / len(relevant_sections)


def mrr(
    hits: Sequence[RetrievalHit],
    relevant_sections: Sequence[RelevantSection],
    *,
    relevance_checker=None,
) -> float:
    """Mean Reciprocal Rank: 1 / rank of first relevant result.

    Returns 0.0 if no relevant result is found.
    """
    checker = relevance_checker or _is_hit

    # hits should be sorted by rank, but ensure it
    sorted_hits = sorted(hits, key=lambda h: h.rank)

    for h in sorted_hits:
        if checker(h.chunk, relevant_sections):
            return 1.0 / h.rank

    return 0.0


def ndcg_at_k(
    hits: Sequence[RetrievalHit],
    relevant_sections: Sequence[RelevantSection],
    k: int,
    *,
    grade_fn=None,
) -> float:
    """Normalized Discounted Cumulative Gain at k.

    Uses graded relevance: EXACT=3, SAME_SECTION=2, RELATED=1, IRRELEVANT=0.

    NDCG@k = DCG@k / IDCG@k

    DCG@k = sum_{i=1}^{k} (2^rel_i - 1) / log2(i + 1)
    IDCG@k = DCG@k for the ideal ranking (sorted by grade descending)

    Args:
        hits: Retrieved chunks ordered by rank.
        relevant_sections: Ground-truth sections with grades.
        k: Cutoff rank.
        grade_fn: Optional callable(chunk, sections) -> RelevanceGrade.

    Returns:
        Float in [0.0, 1.0]. Returns 0.0 if IDCG is 0 (no relevant docs).
    """
    if k <= 0 or not relevant_sections:
        return 0.0

    grader = grade_fn or _get_grade

    # Get grades for top-k hits
    sorted_hits = sorted(hits, key=lambda h: h.rank)[:k]
    actual_grades = [
        grader(h.chunk, relevant_sections).value for h in sorted_hits
    ]

    # Pad with zeros if fewer than k hits
    while len(actual_grades) < k:
        actual_grades.append(0)

    # Ideal grades: all relevant sections' grades sorted descending, padded
    ideal_grades = sorted(
        [s.grade.value for s in relevant_sections],
        reverse=True,
    )[:k]
    while len(ideal_grades) < k:
        ideal_grades.append(0)

    dcg = _dcg(actual_grades)
    idcg = _dcg(ideal_grades)

    if idcg == 0.0:
        return 0.0

    return dcg / idcg


def _dcg(grades: list[int]) -> float:
    """Discounted Cumulative Gain."""
    return sum(
        (2 ** g - 1) / math.log2(i + 2)  # i+2 because i is 0-indexed, rank is 1-indexed
        for i, g in enumerate(grades)
    )


def drm_rate(
    hits: Sequence[RetrievalHit],
    query_document_ids: Sequence[str],
    k: int = 10,
) -> float:
    """Document Retrieval Mismatch rate.

    Measures how often retrieval pulls chunks from documents OTHER than
    the query's target documents. High DRM means the index is confusing
    documents.

    DRM = |top-k chunks from wrong documents| / k

    Returns:
        Float in [0.0, 1.0]. 0.0 = all from correct documents (best).
    """
    if k <= 0 or not query_document_ids:
        return 0.0

    top_k = [h for h in hits if h.rank <= k]
    if not top_k:
        return 0.0

    target_set = set(query_document_ids)
    mismatch_count = sum(
        1 for h in top_k if h.chunk.document_id not in target_set
    )

    return mismatch_count / k


# -- Internal helpers -------------------------------------------------------

def _is_hit(
    chunk: Chunk,
    relevant_sections: Sequence[RelevantSection],
) -> bool:
    """Check if a chunk matches any relevant section (binary relevance).

    Uses the same matching logic as RetrievalSimulator._is_relevant.
    Duplicated here to keep metrics module independent of retrieval module.
    """
    chunk_lower = chunk.text.lower()

    for section in relevant_sections:
        if section.document_id and chunk.document_id != section.document_id:
            continue

        snippet_lower = section.text_snippet.lower().strip()
        if not snippet_lower:
            continue

        # Substring match
        if snippet_lower in chunk_lower:
            return True

        # Section ID match
        if section.section_id:
            section_num = section.section_id.replace("clause_", "").replace("section_", "")
            if section_num in chunk.text:
                return True

        # Word overlap
        snippet_words = set(snippet_lower.split())
        chunk_words = set(chunk_lower.split())
        if snippet_words and len(snippet_words & chunk_words) / len(snippet_words) > 0.6:
            return True

    return False


def _get_grade(
    chunk: Chunk,
    relevant_sections: Sequence[RelevantSection],
) -> RelevanceGrade:
    """Get highest relevance grade for a chunk."""
    best = RelevanceGrade.IRRELEVANT
    chunk_lower = chunk.text.lower()

    for section in relevant_sections:
        if section.document_id and chunk.document_id != section.document_id:
            continue

        snippet_lower = section.text_snippet.lower().strip()
        if not snippet_lower:
            continue

        matched = False
        if snippet_lower in chunk_lower:
            matched = True
        elif section.section_id:
            section_num = section.section_id.replace("clause_", "").replace("section_", "")
            if section_num in chunk.text:
                matched = True
        else:
            snippet_words = set(snippet_lower.split())
            chunk_words = set(chunk_lower.split())
            if snippet_words and len(snippet_words & chunk_words) / len(snippet_words) > 0.6:
                matched = True

        if matched and section.grade.value > best.value:
            best = section.grade

    return best


# -- Convenience function ---------------------------------------------------

def compute_retrieval_metrics(result: RetrievalResult) -> RetrievalMetrics:
    """Compute all retrieval metrics for a single RetrievalResult.

    Returns a RetrievalMetrics dataclass with all P@k, R@k, MRR, NDCG, DRM values.
    """
    hits = list(result.hits)
    sections = list(result.query.relevant_sections)

    return RetrievalMetrics(
        query_id=result.query.id,
        strategy=result.strategy,
        embedding_model=result.embedding_model,
        precision_at_1=precision_at_k(hits, sections, k=1),
        precision_at_3=precision_at_k(hits, sections, k=3),
        precision_at_5=precision_at_k(hits, sections, k=5),
        precision_at_10=precision_at_k(hits, sections, k=10),
        recall_at_1=recall_at_k(hits, sections, k=1),
        recall_at_3=recall_at_k(hits, sections, k=3),
        recall_at_5=recall_at_k(hits, sections, k=5),
        recall_at_10=recall_at_k(hits, sections, k=10),
        mrr=mrr(hits, sections),
        ndcg_at_10=ndcg_at_k(hits, sections, k=10),
        drm_hit=drm_rate(hits, result.query.document_ids, k=10) > 0.0,
    )
```

### Update `src/scaffolder/metrics/__init__.py`

```python
"""Structural and retrieval quality metrics."""

from scaffolder.metrics.structural import compute_structural_metrics
from scaffolder.metrics.retrieval import compute_retrieval_metrics

__all__ = ["compute_structural_metrics", "compute_retrieval_metrics"]
```

### Tests (`tests/test_retrieval_metrics.py`)

Exhaustive tests with known inputs and expected outputs:

```python
"""Tests for retrieval quality metrics."""

# Create synthetic test data:
# - 10 hits (rank 1-10), some relevant, some not
# - 3 relevant sections with grades 3, 2, 1

# Test cases for precision_at_k:
# 1. P@1 with relevant first hit = 1.0
# 2. P@1 with irrelevant first hit = 0.0
# 3. P@5 with 3 relevant in top 5 = 0.6
# 4. P@10 with 3 relevant in top 10 = 0.3
# 5. k=0 returns 0.0
# 6. Empty hits returns 0.0

# Test cases for recall_at_k:
# 7. R@10 with all 3 relevant found = 1.0
# 8. R@1 with 1 of 3 found = 0.333
# 9. No relevant sections = 1.0 (vacuously true)

# Test cases for MRR:
# 10. First hit is relevant -> MRR = 1.0
# 11. Second hit is relevant -> MRR = 0.5
# 12. No relevant hits -> MRR = 0.0

# Test cases for NDCG@10:
# 13. Perfect ranking (grade 3 first, 2 second, 1 third) -> NDCG close to 1.0
# 14. Reverse ranking (grade 1 first, 2 second, 3 third) -> NDCG < 1.0
# 15. No relevant hits -> NDCG = 0.0
# 16. No relevant sections -> NDCG = 0.0

# Test cases for DRM rate:
# 17. All hits from target doc -> DRM = 0.0
# 18. 3 of 10 from wrong doc -> DRM = 0.3
# 19. Empty document_ids -> DRM = 0.0

# Test compute_retrieval_metrics():
# 20. Returns a RetrievalMetrics with all fields populated
# 21. drm_hit is True when DRM > 0

# Helper to create test hits:
def _make_hit(rank: int, doc_id: str, text: str) -> RetrievalHit:
    chunk = Chunk(
        id=f"test_{rank}",
        text=text,
        document_id=doc_id,
        strategy=StrategyName.LEXICHUNK,
        index=rank - 1,
    )
    return RetrievalHit(chunk=chunk, score=1.0 / rank, rank=rank)
```

The NDCG test should verify the formula with a worked example:
- Grades: [3, 0, 2, 0, 1, 0, 0, 0, 0, 0]
- DCG = (2^3-1)/log2(2) + (2^0-1)/log2(3) + (2^2-1)/log2(4) + ... + (2^1-1)/log2(6)
- DCG = 7/1.0 + 0/1.585 + 3/2.0 + 0/2.322 + 1/2.585 = 7.0 + 0 + 1.5 + 0 + 0.387 = 8.887
- IDCG (ideal: [3, 2, 1, 0, ...]): 7/1.0 + 3/1.585 + 1/2.0 = 7.0 + 1.893 + 0.5 = 9.393
- NDCG = 8.887 / 9.393 = 0.946

## Outputs
- `src/scaffolder/metrics/retrieval.py`
- `src/scaffolder/metrics/__init__.py` (updated)
- `tests/test_retrieval_metrics.py`

## Acceptance Criteria
1. All metric functions return float in [0.0, 1.0].
2. NDCG worked example produces the expected value (within 0.01 tolerance).
3. `compute_retrieval_metrics()` returns a fully populated `RetrievalMetrics`.
4. `pytest tests/test_retrieval_metrics.py -v` -- all tests pass.
5. `mypy src/scaffolder/metrics/ --strict` passes.
6. `ruff check src/scaffolder/metrics/` passes.

## Handoff Notes
- **To Day 10:** Metrics are ready. Day 10 adds statistical significance testing and wires everything into the CLI/JSON output. The full pipeline will be: chunk -> embed -> index -> retrieve -> score -> test significance -> report.
- **To Agent B:** These are pure functions with no state. They can be called from the Streamlit dashboard directly.
- **Design note:** The relevance matching logic is duplicated between `retrieval.py` metrics and `simulator.py`. This is intentional -- the metrics module should be independent of the retrieval module. If matching logic changes, update both.
- **Design note:** `drm_hit` is a boolean (any mismatch in top-10) rather than the rate, to keep the `RetrievalMetrics` dataclass simple. The raw `drm_rate()` function is available for detailed analysis.
