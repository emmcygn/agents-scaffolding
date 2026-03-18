"""Tests for structural quality metrics."""

from __future__ import annotations

from scaffolder.metrics.structural import (
    _gt_cache,
    clause_fragmentation_rate,
    compute_structural_metrics,
    cross_ref_resolution_rate,
    definition_preservation_rate,
    get_ground_truth,
)
from scaffolder.models import (
    Chunk,
    ChunkSet,
    Document,
    DocumentType,
    Jurisdiction,
    StrategyName,
)

STRUCTURED_DOC = Document(
    id="test_structural",
    text=(
        '1. Definitions.\n'
        '1.1 "Service Provider" means the party providing services.\n'
        '1.2 "Client" means the party receiving services.\n'
        "2. Obligations.\n"
        "2.1 The Service Provider shall deliver services as defined in Section 1.1.\n"
        "2.2 Subject to Clause 3, the Client shall pay fees.\n"
        "3. Payment Terms.\n"
        "3.1 Fees are due within 30 days.\n"
    ),
    jurisdiction=Jurisdiction.UK,
    document_type=DocumentType.SERVICE_AGREEMENT,
    source="test.txt",
)


def _make_chunk_set(
    texts: list[str],
    strategy: StrategyName = StrategyName.FIXED_SIZE,
    doc_id: str = "test_structural",
) -> ChunkSet:
    """Helper to create a ChunkSet from raw texts."""
    chunks = tuple(
        Chunk(
            id=f"{strategy.value}_{doc_id}_{i}",
            text=t,
            document_id=doc_id,
            strategy=strategy,
            index=i,
        )
        for i, t in enumerate(texts)
    )
    return ChunkSet(
        strategy=strategy,
        document_id=doc_id,
        chunks=chunks,
        elapsed_seconds=0.01,
    )


class TestClauseFragmentationRate:
    def test_perfect_single_chunk(self) -> None:
        """One chunk containing entire doc = no fragmentation."""
        cs = _make_chunk_set([STRUCTURED_DOC.text])
        rate = clause_fragmentation_rate(cs, STRUCTURED_DOC)
        assert rate == 0.0

    def test_fragmented_word_level(self) -> None:
        """Many tiny chunks = high fragmentation."""
        words = STRUCTURED_DOC.text.split()
        cs = _make_chunk_set(words)
        rate = clause_fragmentation_rate(cs, STRUCTURED_DOC)
        assert rate > 0.5

    def test_returns_float_in_range(self) -> None:
        cs = _make_chunk_set([STRUCTURED_DOC.text[:100], STRUCTURED_DOC.text[100:]])
        rate = clause_fragmentation_rate(cs, STRUCTURED_DOC)
        assert 0.0 <= rate <= 1.0


class TestDefinitionPreservationRate:
    def test_perfect_single_chunk(self) -> None:
        """One chunk with entire doc = all definitions preserved."""
        cs = _make_chunk_set([STRUCTURED_DOC.text])
        rate = definition_preservation_rate(cs, STRUCTURED_DOC)
        assert rate == 1.0

    def test_no_definitions_doc(self) -> None:
        """Doc with no defined terms = vacuously 1.0."""
        no_def_doc = Document(
            id="test_no_defs",
            text="This is plain text with no defined terms or legal language.",
            jurisdiction=Jurisdiction.UK,
            document_type=DocumentType.SERVICE_AGREEMENT,
            source="test.txt",
        )
        cs = _make_chunk_set(["This is plain text."], doc_id="test_no_defs")
        rate = definition_preservation_rate(cs, no_def_doc)
        assert rate == 1.0

    def test_returns_float_in_range(self) -> None:
        cs = _make_chunk_set([STRUCTURED_DOC.text[:50], STRUCTURED_DOC.text[50:]])
        rate = definition_preservation_rate(cs, STRUCTURED_DOC)
        assert 0.0 <= rate <= 1.0


class TestCrossRefResolutionRate:
    def test_perfect_single_chunk(self) -> None:
        """One chunk with entire doc = all cross-refs resolved."""
        cs = _make_chunk_set([STRUCTURED_DOC.text])
        rate = cross_ref_resolution_rate(cs, STRUCTURED_DOC)
        assert rate == 1.0

    def test_returns_float_in_range(self) -> None:
        cs = _make_chunk_set([STRUCTURED_DOC.text[:100], STRUCTURED_DOC.text[100:]])
        rate = cross_ref_resolution_rate(cs, STRUCTURED_DOC)
        assert 0.0 <= rate <= 1.0


class TestComputeStructuralMetrics:
    def test_returns_structural_metrics(self) -> None:
        cs = _make_chunk_set([STRUCTURED_DOC.text])
        metrics = compute_structural_metrics(cs, STRUCTURED_DOC)
        assert metrics.strategy == StrategyName.FIXED_SIZE
        assert metrics.document_id == "test_structural"
        assert metrics.chunk_count == 1
        assert 0.0 <= metrics.clause_fragmentation_rate <= 1.0
        assert 0.0 <= metrics.definition_preservation_rate <= 1.0
        assert 0.0 <= metrics.cross_ref_resolution_rate <= 1.0

    def test_placeholder_metrics_are_zero(self) -> None:
        cs = _make_chunk_set([STRUCTURED_DOC.text])
        metrics = compute_structural_metrics(cs, STRUCTURED_DOC)
        assert metrics.hierarchy_depth_retained == 0.0
        assert metrics.chunk_size_cv == 0.0


class TestGroundTruthCaching:
    def test_cache_returns_same_object(self) -> None:
        # Clear cache first
        _gt_cache.clear()
        gt1 = get_ground_truth(STRUCTURED_DOC)
        gt2 = get_ground_truth(STRUCTURED_DOC)
        assert gt1 is gt2

    def test_ground_truth_has_clauses(self) -> None:
        _gt_cache.clear()
        gt = get_ground_truth(STRUCTURED_DOC)
        assert len(gt.clauses) >= 1
        assert gt.max_hierarchy_depth >= 1
