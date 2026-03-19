"""Retrieval quality metrics for evaluating chunking strategies.

All functions are pure: they take retrieval results and return floats.
No side effects, no I/O, no model calls.
"""

from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING

from scaffolder.models import (
    RelevanceGrade,
    RetrievalMetrics,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from scaffolder.models import (
        Chunk,
        RelevantSection,
        RetrievalHit,
        RetrievalResult,
    )

logger = logging.getLogger(__name__)


def precision_at_k(
    hits: Sequence[RetrievalHit],
    relevant_sections: Sequence[RelevantSection],
    k: int,
) -> float:
    """Precision@k: fraction of top-k results that are relevant.

    P@k = |relevant in top-k| / k
    """
    if k <= 0:
        return 0.0

    top_k = [h for h in hits if h.rank <= k]
    if not top_k:
        return 0.0

    relevant_count = sum(1 for h in top_k if _is_hit(h.chunk, relevant_sections))
    return relevant_count / k


def recall_at_k(
    hits: Sequence[RetrievalHit],
    relevant_sections: Sequence[RelevantSection],
    k: int,
) -> float:
    """Recall@k: fraction of all relevant items found in top-k.

    Returns 1.0 if there are no relevant sections (vacuously true).
    """
    if not relevant_sections:
        return 1.0
    if k <= 0:
        return 0.0

    top_k = [h for h in hits if h.rank <= k]
    relevant_count = sum(1 for h in top_k if _is_hit(h.chunk, relevant_sections))
    return relevant_count / len(relevant_sections)


def mrr(
    hits: Sequence[RetrievalHit],
    relevant_sections: Sequence[RelevantSection],
) -> float:
    """Mean Reciprocal Rank: 1 / rank of first relevant result.

    Returns 0.0 if no relevant result is found.
    """
    sorted_hits = sorted(hits, key=lambda h: h.rank)

    for h in sorted_hits:
        if _is_hit(h.chunk, relevant_sections):
            return 1.0 / h.rank

    return 0.0


def ndcg_at_k(
    hits: Sequence[RetrievalHit],
    relevant_sections: Sequence[RelevantSection],
    k: int,
) -> float:
    """Normalized Discounted Cumulative Gain at k.

    Uses graded relevance: EXACT=3, SAME_SECTION=2, RELATED=1, IRRELEVANT=0.
    NDCG@k = DCG@k / IDCG@k
    """
    if k <= 0 or not relevant_sections:
        return 0.0

    sorted_hits = sorted(hits, key=lambda h: h.rank)[:k]
    actual_grades = [_get_grade(h.chunk, relevant_sections).value for h in sorted_hits]

    # Pad with zeros if fewer than k hits
    while len(actual_grades) < k:
        actual_grades.append(0)

    # Ideal grades: all relevant sections' grades sorted descending
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
    return float(
        sum(
            (2**g - 1) / math.log2(i + 2)  # i+2: 0-indexed i, rank 1-indexed
            for i, g in enumerate(grades)
        )
    )


def drm_rate(
    hits: Sequence[RetrievalHit],
    query_document_ids: Sequence[str],
    k: int = 10,
) -> float:
    """Document Retrieval Mismatch rate.

    Measures how often retrieval pulls chunks from wrong documents.
    DRM = |top-k chunks from wrong documents| / k
    """
    if k <= 0 or not query_document_ids:
        return 0.0

    top_k = [h for h in hits if h.rank <= k]
    if not top_k:
        return 0.0

    target_set = set(query_document_ids)
    mismatch_count = sum(1 for h in top_k if h.chunk.document_id not in target_set)
    return mismatch_count / k


# -- Internal helpers -------------------------------------------------------


def _is_hit(
    chunk: Chunk,
    relevant_sections: Sequence[RelevantSection],
) -> bool:
    """Check if a chunk matches any relevant section (binary relevance)."""
    chunk_lower = chunk.text.lower()

    for section in relevant_sections:
        if section.document_id and chunk.document_id != section.document_id:
            continue

        snippet_lower = section.text_snippet.lower().strip()

        # Substring match
        if snippet_lower and snippet_lower in chunk_lower:
            return True

        # Section ID match
        if section.section_id:
            section_num = (
                section.section_id.replace("clause_", "")
                .replace("section_", "")
                .replace("definition_", "")
            )
            if section_num in chunk.text:
                return True

        # Word overlap
        if snippet_lower:
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

        matched = False
        if snippet_lower and snippet_lower in chunk_lower:
            matched = True
        elif section.section_id:
            section_num = (
                section.section_id.replace("clause_", "")
                .replace("section_", "")
                .replace("definition_", "")
            )
            if section_num in chunk.text:
                matched = True
        elif snippet_lower:
            snippet_words = set(snippet_lower.split())
            chunk_words = set(chunk_lower.split())
            if snippet_words and len(snippet_words & chunk_words) / len(snippet_words) > 0.6:
                matched = True

        if matched and section.grade.value > best.value:
            best = section.grade

    return best


# -- Convenience function ---------------------------------------------------


def compute_retrieval_metrics(result: RetrievalResult) -> RetrievalMetrics:
    """Compute all retrieval metrics for a single RetrievalResult."""
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
