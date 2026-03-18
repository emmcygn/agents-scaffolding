"""Tests for CLI and JSON reporting modules."""

from __future__ import annotations

import io
import json
from typing import TYPE_CHECKING

from rich.console import Console

from scaffolder.models import (
    BenchmarkResult,
    EmbeddingModelName,
    RetrievalMetrics,
    SignificanceResult,
    StrategyName,
    StructuralMetrics,
)
from scaffolder.reporting.cli import (
    render_aggregate_summary,
    render_benchmark,
    render_structural_table,
    render_summary_header,
)
from scaffolder.reporting.json_export import (
    export_json,
    export_json_string,
    load_json,
)

if TYPE_CHECKING:
    from pathlib import Path


def _make_structural_result() -> BenchmarkResult:
    return BenchmarkResult(
        timestamp="2026-03-18T12:00:00",
        strategies=[StrategyName.LEXICHUNK, StrategyName.RCTS],
        documents=["doc1", "doc2"],
        structural_metrics=[
            StructuralMetrics(
                strategy=StrategyName.LEXICHUNK,
                document_id="doc1",
                clause_fragmentation_rate=0.05,
                definition_preservation_rate=0.95,
                cross_ref_resolution_rate=0.90,
                hierarchy_depth_retained=1.0,
                chunk_size_cv=0.3,
                chunk_count=10,
                avg_chunk_chars=400.0,
            ),
            StructuralMetrics(
                strategy=StrategyName.RCTS,
                document_id="doc1",
                clause_fragmentation_rate=0.45,
                definition_preservation_rate=0.60,
                cross_ref_resolution_rate=0.50,
                hierarchy_depth_retained=0.67,
                chunk_size_cv=0.1,
                chunk_count=15,
                avg_chunk_chars=350.0,
            ),
            StructuralMetrics(
                strategy=StrategyName.LEXICHUNK,
                document_id="doc2",
                clause_fragmentation_rate=0.08,
                definition_preservation_rate=0.92,
                cross_ref_resolution_rate=0.85,
                hierarchy_depth_retained=1.0,
                chunk_size_cv=0.25,
                chunk_count=8,
                avg_chunk_chars=450.0,
            ),
            StructuralMetrics(
                strategy=StrategyName.RCTS,
                document_id="doc2",
                clause_fragmentation_rate=0.50,
                definition_preservation_rate=0.55,
                cross_ref_resolution_rate=0.40,
                hierarchy_depth_retained=0.67,
                chunk_size_cv=0.12,
                chunk_count=12,
                avg_chunk_chars=380.0,
            ),
        ],
    )


class TestCLIRendering:
    def _console(self) -> Console:
        return Console(file=io.StringIO(), force_terminal=True, width=120)

    def test_render_structural_table_runs(self) -> None:
        console = self._console()
        result = _make_structural_result()
        render_structural_table(result.structural_metrics, console)
        output = console.file.getvalue()  # type: ignore[union-attr]
        assert "doc1" in output
        assert "doc2" in output

    def test_render_structural_table_empty(self) -> None:
        console = self._console()
        render_structural_table([], console)
        output = console.file.getvalue()  # type: ignore[union-attr]
        assert "No structural results" in output

    def test_render_summary_header(self) -> None:
        console = self._console()
        result = _make_structural_result()
        render_summary_header(result, console)
        output = console.file.getvalue()  # type: ignore[union-attr]
        assert "Benchmark Results" in output
        assert "lexichunk" in output

    def test_render_aggregate_summary(self) -> None:
        console = self._console()
        result = _make_structural_result()
        render_aggregate_summary(result, console)
        output = console.file.getvalue()  # type: ignore[union-attr]
        assert "Aggregate" in output

    def test_render_aggregate_summary_empty(self) -> None:
        console = self._console()
        result = BenchmarkResult(timestamp="now")
        render_aggregate_summary(result, console)
        output = console.file.getvalue()  # type: ignore[union-attr]
        # Should not crash, should produce empty output
        assert isinstance(output, str)

    def test_render_benchmark_full(self) -> None:
        console = self._console()
        result = _make_structural_result()
        render_benchmark(result, console)
        output = console.file.getvalue()  # type: ignore[union-attr]
        assert "Benchmark Results" in output
        assert "doc1" in output

    def test_render_benchmark_default_console(self) -> None:
        """render_benchmark works when called without a console."""
        result = _make_structural_result()
        # Just verify no exception; output goes to real stdout
        render_benchmark(result)

    def test_render_summary_header_with_models(self) -> None:
        console = self._console()
        result = _make_structural_result()
        result.models = [EmbeddingModelName.MINILM]
        render_summary_header(result, console)
        output = console.file.getvalue()  # type: ignore[union-attr]
        assert "all-MiniLM-L6-v2" in output


class TestJSONExport:
    def test_export_creates_file(self, tmp_path: Path) -> None:
        result = _make_structural_result()
        path = tmp_path / "test.json"
        export_json(result, path)
        assert path.exists()

    def test_export_creates_parent_dirs(self, tmp_path: Path) -> None:
        result = _make_structural_result()
        path = tmp_path / "deep" / "nested" / "result.json"
        export_json(result, path)
        assert path.exists()

    def test_export_roundtrip(self, tmp_path: Path) -> None:
        result = _make_structural_result()
        path = tmp_path / "test.json"
        export_json(result, path)
        loaded = load_json(path)
        assert loaded["timestamp"] == result.timestamp
        assert len(loaded["structural_metrics"]) == 4

    def test_export_json_string(self) -> None:
        result = _make_structural_result()
        s = export_json_string(result)
        data = json.loads(s)
        assert data["timestamp"] == "2026-03-18T12:00:00"

    def test_export_with_retrieval_metrics(self, tmp_path: Path) -> None:
        result = _make_structural_result()
        result.retrieval_metrics = [
            RetrievalMetrics(
                query_id="q1",
                strategy=StrategyName.LEXICHUNK,
                embedding_model=EmbeddingModelName.MINILM,
                precision_at_1=1.0,
                precision_at_3=0.67,
                precision_at_5=0.6,
                precision_at_10=0.4,
                recall_at_1=0.33,
                recall_at_3=0.67,
                recall_at_5=1.0,
                recall_at_10=1.0,
                mrr=1.0,
                ndcg_at_10=0.9,
                drm_hit=False,
            ),
        ]
        result.significance_results = [
            SignificanceResult(
                metric_name="ndcg_at_10",
                strategy_a=StrategyName.LEXICHUNK,
                strategy_b=StrategyName.RCTS,
                mean_a=0.9,
                mean_b=0.6,
                improvement_pct=50.0,
                t_statistic=3.5,
                p_value=0.01,
                significant=True,
                effect_size=1.2,
                n_queries=10,
            ),
        ]
        path = tmp_path / "full.json"
        export_json(result, path)
        loaded = load_json(path)
        assert len(loaded["retrieval_metrics"]) == 1
        assert len(loaded["significance_results"]) == 1
