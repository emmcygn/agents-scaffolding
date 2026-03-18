"""Tests for retrieval quality metrics."""

from __future__ import annotations

from scaffolder.metrics.retrieval import (
    compute_retrieval_metrics,
    drm_rate,
    mrr,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)
from scaffolder.models import (
    AnnotatedQuery,
    Chunk,
    EmbeddingModelName,
    Jurisdiction,
    RelevanceGrade,
    RelevantSection,
    RetrievalHit,
    RetrievalResult,
    StrategyName,
)


def _make_hit(rank: int, doc_id: str, text: str) -> RetrievalHit:
    chunk = Chunk(
        id=f"test_{rank}",
        text=text,
        document_id=doc_id,
        strategy=StrategyName.LEXICHUNK,
        index=rank - 1,
    )
    return RetrievalHit(chunk=chunk, score=1.0 / rank, rank=rank)


# Relevant sections for testing
SECTIONS = (
    RelevantSection(
        document_id="doc1",
        section_id="clause_1",
        text_snippet="service provider definition",
        grade=RelevanceGrade.EXACT,
    ),
    RelevantSection(
        document_id="doc1",
        section_id="clause_2",
        text_snippet="client obligations",
        grade=RelevanceGrade.SAME_SECTION,
    ),
    RelevantSection(
        document_id="doc1",
        section_id="clause_3",
        text_snippet="payment terms",
        grade=RelevanceGrade.RELATED,
    ),
)

# Hits where rank 1 and 3 are relevant, rest are not
HITS = [
    _make_hit(1, "doc1", "This contains service provider definition here."),
    _make_hit(2, "doc1", "Unrelated content about weather."),
    _make_hit(3, "doc1", "This is about client obligations in detail."),
    _make_hit(4, "doc1", "More unrelated text."),
    _make_hit(5, "doc1", "payment terms and conditions apply."),
    _make_hit(6, "doc1", "Random filler text."),
    _make_hit(7, "doc1", "Another unrelated chunk."),
    _make_hit(8, "doc1", "Yet more content."),
    _make_hit(9, "doc1", "Filler content nine."),
    _make_hit(10, "doc1", "Last chunk ten."),
]


class TestPrecisionAtK:
    def test_p_at_1_relevant_first(self) -> None:
        assert precision_at_k(HITS, SECTIONS, k=1) == 1.0

    def test_p_at_1_irrelevant_first(self) -> None:
        # Shift hits so rank 1 is irrelevant
        hits = [_make_hit(1, "doc1", "unrelated")] + HITS[1:]
        assert precision_at_k(hits, SECTIONS, k=1) == 0.0

    def test_p_at_5(self) -> None:
        # Ranks 1, 3, 5 are relevant = 3/5 = 0.6
        assert precision_at_k(HITS, SECTIONS, k=5) == 0.6

    def test_p_at_10(self) -> None:
        # 3 relevant in 10 = 0.3
        assert precision_at_k(HITS, SECTIONS, k=10) == 0.3

    def test_k_zero_returns_zero(self) -> None:
        assert precision_at_k(HITS, SECTIONS, k=0) == 0.0

    def test_empty_hits(self) -> None:
        assert precision_at_k([], SECTIONS, k=5) == 0.0


class TestRecallAtK:
    def test_recall_at_10_all_found(self) -> None:
        assert recall_at_k(HITS, SECTIONS, k=10) == 1.0

    def test_recall_at_1(self) -> None:
        # 1 of 3 found at k=1
        result = recall_at_k(HITS, SECTIONS, k=1)
        assert abs(result - 1.0 / 3.0) < 0.01

    def test_no_relevant_sections(self) -> None:
        assert recall_at_k(HITS, [], k=10) == 1.0


class TestMRR:
    def test_first_hit_relevant(self) -> None:
        assert mrr(HITS, SECTIONS) == 1.0

    def test_second_hit_relevant(self) -> None:
        hits = [
            _make_hit(1, "doc1", "unrelated"),
            _make_hit(2, "doc1", "service provider definition here"),
        ]
        assert mrr(hits, SECTIONS) == 0.5

    def test_no_relevant_hits(self) -> None:
        hits = [_make_hit(1, "doc1", "unrelated")]
        assert mrr(hits, SECTIONS) == 0.0


class TestNDCG:
    def test_no_relevant_sections(self) -> None:
        assert ndcg_at_k(HITS, [], k=10) == 0.0

    def test_k_zero(self) -> None:
        assert ndcg_at_k(HITS, SECTIONS, k=0) == 0.0

    def test_perfect_ranking(self) -> None:
        # Hits with grades: 3, 2, 1 in order = perfect ranking
        hits = [
            _make_hit(1, "doc1", "service provider definition"),
            _make_hit(2, "doc1", "client obligations here"),
            _make_hit(3, "doc1", "payment terms apply"),
        ]
        ndcg = ndcg_at_k(hits, SECTIONS, k=3)
        assert ndcg > 0.99  # Should be 1.0 or very close

    def test_imperfect_ranking_less_than_1(self) -> None:
        # Reverse: grade 1 first, then 2, then 3
        hits = [
            _make_hit(1, "doc1", "payment terms apply"),
            _make_hit(2, "doc1", "client obligations here"),
            _make_hit(3, "doc1", "service provider definition"),
        ]
        ndcg = ndcg_at_k(hits, SECTIONS, k=3)
        assert 0.0 < ndcg < 1.0

    def test_no_relevant_hits(self) -> None:
        hits = [_make_hit(1, "doc1", "nothing relevant")]
        ndcg = ndcg_at_k(hits, SECTIONS, k=10)
        assert ndcg == 0.0


class TestDRMRate:
    def test_all_from_target_doc(self) -> None:
        assert drm_rate(HITS, ["doc1"], k=10) == 0.0

    def test_some_from_wrong_doc(self) -> None:
        hits = [
            _make_hit(1, "doc1", "correct doc"),
            _make_hit(2, "doc2", "wrong doc"),
            _make_hit(3, "doc2", "wrong doc"),
        ]
        # 2 of 3 from wrong doc at k=3
        result = drm_rate(hits, ["doc1"], k=3)
        assert abs(result - 2.0 / 3.0) < 0.01

    def test_empty_document_ids(self) -> None:
        assert drm_rate(HITS, [], k=10) == 0.0


class TestComputeRetrievalMetrics:
    def test_returns_metrics(self) -> None:
        query = AnnotatedQuery(
            id="q1",
            text="test query",
            document_ids=["doc1"],
            jurisdiction=Jurisdiction.UK,
            relevant_sections=SECTIONS,
            category="test",
        )
        result = RetrievalResult(
            query=query,
            strategy=StrategyName.LEXICHUNK,
            embedding_model=EmbeddingModelName.MINILM,
            hits=tuple(HITS),
            relevant_retrieved=3,
            total_relevant=3,
        )
        metrics = compute_retrieval_metrics(result)
        assert metrics.query_id == "q1"
        assert metrics.strategy == StrategyName.LEXICHUNK
        assert metrics.precision_at_1 == 1.0
        assert metrics.recall_at_10 == 1.0
        assert metrics.mrr == 1.0
        assert 0.0 <= metrics.ndcg_at_10 <= 1.0
        assert metrics.drm_hit is False
