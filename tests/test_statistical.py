"""Tests for statistical significance testing."""

from __future__ import annotations

import pytest

from scaffolder.metrics.statistical import (
    SIGNIFICANCE_METRICS,
    compute_all_significance,
    compute_significance,
    paired_t_test,
)
from scaffolder.models import (
    EmbeddingModelName,
    RetrievalMetrics,
    StrategyName,
)


class TestPairedTTest:
    def test_significant_difference(self) -> None:
        a = [0.8, 0.9, 0.7, 0.85, 0.75]
        b = [0.5, 0.6, 0.4, 0.55, 0.45]
        t_stat, p_value, significant, cohens_d = paired_t_test(a, b)
        assert significant
        assert p_value < 0.05
        assert cohens_d > 0.8  # large effect

    def test_identical_values_not_significant(self) -> None:
        a = [0.5, 0.5, 0.5, 0.5, 0.5]
        b = [0.5, 0.5, 0.5, 0.5, 0.5]
        t_stat, p_value, significant, cohens_d = paired_t_test(a, b)
        assert not significant
        assert cohens_d == 0.0

    def test_single_value_raises(self) -> None:
        with pytest.raises(ValueError, match="at least 2"):
            paired_t_test([0.5], [0.5])

    def test_mismatched_lengths_raises(self) -> None:
        with pytest.raises(ValueError, match="lengths must match"):
            paired_t_test([0.5, 0.6], [0.5])


def _make_metrics(
    strategy: StrategyName,
    model: EmbeddingModelName,
    query_ids: list[str],
    p5_values: list[float],
) -> list[RetrievalMetrics]:
    """Create mock RetrievalMetrics with specified P@5 values."""
    return [
        RetrievalMetrics(
            query_id=qid,
            strategy=strategy,
            embedding_model=model,
            precision_at_1=v,
            precision_at_3=v,
            precision_at_5=v,
            precision_at_10=v * 0.8,
            recall_at_1=v * 0.5,
            recall_at_3=v * 0.7,
            recall_at_5=v * 0.9,
            recall_at_10=v,
            mrr=v,
            ndcg_at_10=v,
            drm_hit=False,
        )
        for qid, v in zip(query_ids, p5_values, strict=True)
    ]


class TestComputeSignificance:
    def test_produces_one_result_per_metric(self) -> None:
        queries = ["q1", "q2", "q3", "q4", "q5"]
        lc = _make_metrics(
            StrategyName.LEXICHUNK, EmbeddingModelName.MINILM, queries, [0.8, 0.9, 0.7, 0.85, 0.75]
        )
        bl = _make_metrics(
            StrategyName.RCTS, EmbeddingModelName.MINILM, queries, [0.5, 0.6, 0.4, 0.55, 0.45]
        )

        results = compute_significance(lc, bl, StrategyName.RCTS)
        assert len(results) == len(SIGNIFICANCE_METRICS)

    def test_too_few_queries_returns_empty(self) -> None:
        queries = ["q1"]
        lc = _make_metrics(StrategyName.LEXICHUNK, EmbeddingModelName.MINILM, queries, [0.8])
        bl = _make_metrics(StrategyName.RCTS, EmbeddingModelName.MINILM, queries, [0.5])

        results = compute_significance(lc, bl, StrategyName.RCTS)
        assert results == []


class TestComputeAllSignificance:
    def test_groups_by_model(self) -> None:
        queries = ["q1", "q2", "q3"]
        lc = _make_metrics(
            StrategyName.LEXICHUNK, EmbeddingModelName.MINILM, queries, [0.8, 0.9, 0.7]
        )
        rcts = _make_metrics(StrategyName.RCTS, EmbeddingModelName.MINILM, queries, [0.5, 0.6, 0.4])

        results = compute_all_significance(lc + rcts)
        assert len(results) == len(SIGNIFICANCE_METRICS)  # 1 baseline x 1 model x N metrics
