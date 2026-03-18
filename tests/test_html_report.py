"""Tests for HTML report generation."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from scaffolder.models import (
    BenchmarkResult,
    EmbeddingModelName,
    RetrievalMetrics,
    SignificanceResult,
    StrategyName,
    StructuralMetrics,
)
from scaffolder.reporting.html import render_html_report


def _minimal_result() -> BenchmarkResult:
    """Create a minimal BenchmarkResult for testing."""
    return BenchmarkResult(
        timestamp="2026-03-18T00:00:00",
        strategies=[StrategyName.LEXICHUNK, StrategyName.RCTS],
        documents=["doc_a", "doc_b"],
        structural_metrics=[
            StructuralMetrics(
                strategy=StrategyName.LEXICHUNK,
                document_id="doc_a",
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
                document_id="doc_a",
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
                document_id="doc_b",
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
                document_id="doc_b",
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


def _result_with_retrieval() -> BenchmarkResult:
    """Create a BenchmarkResult that includes retrieval and significance data."""
    result = _minimal_result()
    result.models = [EmbeddingModelName.MINILM]
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
        RetrievalMetrics(
            query_id="q1",
            strategy=StrategyName.RCTS,
            embedding_model=EmbeddingModelName.MINILM,
            precision_at_1=0.0,
            precision_at_3=0.33,
            precision_at_5=0.4,
            precision_at_10=0.3,
            recall_at_1=0.0,
            recall_at_3=0.33,
            recall_at_5=0.67,
            recall_at_10=1.0,
            mrr=0.5,
            ndcg_at_10=0.6,
            drm_hit=True,
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
    return result


class TestRenderHtmlReport:
    def test_produces_html_file(self, tmp_path: Path) -> None:
        path = tmp_path / "report.html"
        render_html_report(_minimal_result(), path)
        assert path.exists()
        assert path.stat().st_size > 0

    def test_contains_title(self, tmp_path: Path) -> None:
        path = tmp_path / "report.html"
        render_html_report(_minimal_result(), path)
        html = path.read_text(encoding="utf-8")
        assert "LexiChunk Benchmark Report" in html

    def test_contains_strategy_names(self, tmp_path: Path) -> None:
        path = tmp_path / "report.html"
        render_html_report(_minimal_result(), path)
        html = path.read_text(encoding="utf-8")
        assert "lexichunk" in html
        assert "rcts" in html

    def test_contains_structural_table_rows(self, tmp_path: Path) -> None:
        path = tmp_path / "report.html"
        render_html_report(_minimal_result(), path)
        html = path.read_text(encoding="utf-8")
        assert "doc_a" in html
        assert "doc_b" in html
        assert "0.050" in html  # fragmentation

    def test_contains_plotly_chart(self, tmp_path: Path) -> None:
        path = tmp_path / "report.html"
        render_html_report(_minimal_result(), path)
        html = path.read_text(encoding="utf-8")
        assert "plotly" in html.lower()

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        path = tmp_path / "deep" / "nested" / "report.html"
        render_html_report(_minimal_result(), path)
        assert path.exists()

    def test_contains_timestamp(self, tmp_path: Path) -> None:
        path = tmp_path / "report.html"
        render_html_report(_minimal_result(), path)
        html = path.read_text(encoding="utf-8")
        assert "2026-03-18" in html

    def test_methodology_section(self, tmp_path: Path) -> None:
        path = tmp_path / "report.html"
        render_html_report(_minimal_result(), path)
        html = path.read_text(encoding="utf-8")
        assert "Methodology" in html
        assert "Clause Fragmentation Rate" in html
        assert "NDCG" in html


class TestRenderWithRetrieval:
    def test_retrieval_section_present(self, tmp_path: Path) -> None:
        path = tmp_path / "report.html"
        render_html_report(_result_with_retrieval(), path)
        html = path.read_text(encoding="utf-8")
        assert "Retrieval Quality Metrics" in html

    def test_significance_section_present(self, tmp_path: Path) -> None:
        path = tmp_path / "report.html"
        render_html_report(_result_with_retrieval(), path)
        html = path.read_text(encoding="utf-8")
        assert "Statistical Significance" in html
        assert "badge-sig" in html

    def test_drm_chart_present(self, tmp_path: Path) -> None:
        path = tmp_path / "report.html"
        render_html_report(_result_with_retrieval(), path)
        html = path.read_text(encoding="utf-8")
        assert "Document Retrieval Mismatch" in html


class TestRenderWithoutRetrieval:
    def test_no_retrieval_section(self, tmp_path: Path) -> None:
        path = tmp_path / "report.html"
        render_html_report(_minimal_result(), path)
        html = path.read_text(encoding="utf-8")
        assert "Retrieval Quality Metrics" not in html

    def test_no_significance_section(self, tmp_path: Path) -> None:
        path = tmp_path / "report.html"
        render_html_report(_minimal_result(), path)
        html = path.read_text(encoding="utf-8")
        assert "Statistical Significance" not in html
