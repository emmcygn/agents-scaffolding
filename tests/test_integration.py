"""End-to-end integration tests for the full benchmark pipeline."""

from __future__ import annotations

from scaffolder.chunking import ChunkingPipeline, get_all_strategies
from scaffolder.fixtures import FixtureManager
from scaffolder.metrics.structural import compute_structural_metrics


class TestFullStructuralPipeline:
    def test_fixtures_to_metrics(self) -> None:
        """Full pipeline: fixtures -> chunking -> structural metrics."""
        fm = FixtureManager()
        docs = fm.load_all()
        assert len(docs) == 5

        strategies = get_all_strategies()
        pipeline = ChunkingPipeline(strategies)
        results = pipeline.run(docs)

        assert len(results) == 5  # 5 strategies

        for sr in results:
            assert len(sr.chunk_sets) == 5
            for cs in sr.chunk_sets:
                assert cs.count > 0
                doc = fm.get_by_id(cs.document_id)
                sm = compute_structural_metrics(cs, doc)
                assert 0.0 <= sm.clause_fragmentation_rate <= 1.0
                assert 0.0 <= sm.definition_preservation_rate <= 1.0
                assert 0.0 <= sm.cross_ref_resolution_rate <= 1.0
                assert 0.0 <= sm.hierarchy_depth_retained <= 1.0

    def test_all_strategies_produce_unique_chunk_ids(self) -> None:
        """No duplicate chunk IDs within a strategy run on a document."""
        fm = FixtureManager()
        docs = fm.load_all()
        strategies = get_all_strategies()

        for strategy in strategies:
            for doc in docs:
                cs = strategy.chunk(doc)
                ids = [c.id for c in cs.chunks]
                assert len(ids) == len(set(ids)), (
                    f"Duplicate IDs in {strategy.name.value} for {doc.id}"
                )

    def test_no_empty_chunks(self) -> None:
        """No strategy produces empty-text chunks on real documents."""
        fm = FixtureManager()
        docs = fm.load_all()
        strategies = get_all_strategies()

        for strategy in strategies:
            for doc in docs:
                cs = strategy.chunk(doc)
                for chunk in cs.chunks:
                    assert len(chunk.text.strip()) > 0, (
                        f"Empty chunk in {strategy.name.value} for {doc.id}"
                    )
