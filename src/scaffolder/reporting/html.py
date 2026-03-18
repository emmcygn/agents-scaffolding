"""HTML report generator using Jinja2 templates and Plotly charts."""

from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING, Any

import plotly.graph_objects as go
import plotly.io as pio
from jinja2 import Environment, FileSystemLoader

if TYPE_CHECKING:
    from scaffolder.models import BenchmarkResult, StructuralMetrics

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).parent / "templates"


def render_html_report(
    result: BenchmarkResult,
    output_path: Path,
) -> None:
    """Render a full HTML report from benchmark results.

    The output is a self-contained HTML file with:
    - Inline CSS (no external dependencies)
    - Inline Plotly charts (plotly.js loaded via CDN)
    - Structural metrics tables and charts
    - Retrieval metrics tables and charts
    - Significance results with colour-coded p-values
    - Methodology section

    Args:
        result: Complete BenchmarkResult from a benchmark run.
        output_path: Where to write the HTML file.
    """
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=True,
    )
    template = env.get_template("report.html.j2")

    context = _build_context(result)

    html = template.render(**context)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    logger.info("HTML report written to %s", output_path)


def _build_context(result: BenchmarkResult) -> dict[str, Any]:
    """Build the template context from benchmark results."""
    context: dict[str, Any] = {
        "timestamp": result.timestamp,
        "strategies": [s.value for s in result.strategies],
        "documents": result.documents,
        "structural_metrics": result.structural_metrics,
        "retrieval_metrics": result.retrieval_metrics,
        "significance_results": result.significance_results,
        "structural_chart_html": _structural_bar_chart(result),
        "structural_heatmap_html": _structural_heatmap(result),
        "has_retrieval": bool(result.retrieval_metrics),
        "has_significance": bool(result.significance_results),
        "retrieval_charts": {},
        "model_comparison_html": "",
        "drm_chart_html": "",
    }

    if result.retrieval_metrics:
        models = sorted({rm.embedding_model.value for rm in result.retrieval_metrics})
        for model in models:
            context["retrieval_charts"][model] = _retrieval_bar_chart(result, model)
        context["model_comparison_html"] = _model_comparison_chart(result)
        context["drm_chart_html"] = _drm_chart(result)

    return context


def _structural_bar_chart(result: BenchmarkResult) -> str:
    """Generate grouped bar chart comparing structural metrics across strategies."""
    if not result.structural_metrics:
        return ""

    by_strategy: dict[str, list[StructuralMetrics]] = defaultdict(list)
    for sm in result.structural_metrics:
        by_strategy[sm.strategy.value].append(sm)

    strategies = sorted(by_strategy.keys())

    metrics_config = [
        ("Clause Frag. (1-rate)", "clause_fragmentation_rate", True),
        ("Definition Preservation", "definition_preservation_rate", False),
        ("Cross-Ref Resolution", "cross_ref_resolution_rate", False),
        ("Hierarchy Depth", "hierarchy_depth_retained", False),
    ]

    fig = go.Figure()

    for label, attr, invert in metrics_config:
        values = []
        for strat in strategies:
            metrics = by_strategy[strat]
            avg = sum(getattr(m, attr) for m in metrics) / len(metrics)
            if invert:
                avg = 1.0 - avg
            values.append(avg)

        fig.add_trace(
            go.Bar(
                name=label,
                x=strategies,
                y=values,
                text=[f"{v:.3f}" for v in values],
                textposition="auto",
            )
        )

    fig.update_layout(
        title="Structural Quality Metrics by Strategy (higher = better)",
        barmode="group",
        yaxis_title="Score",
        yaxis_range=[0, 1.05],
        template="plotly_white",
        height=500,
    )

    return pio.to_html(fig, full_html=False, include_plotlyjs="cdn")


def _structural_heatmap(result: BenchmarkResult) -> str:
    """Generate heatmap: strategies x documents, coloured by composite score."""
    if not result.structural_metrics:
        return ""

    by_sd: dict[tuple[str, str], StructuralMetrics] = {}
    for sm in result.structural_metrics:
        by_sd[(sm.strategy.value, sm.document_id)] = sm

    strategies = sorted({sm.strategy.value for sm in result.structural_metrics})
    documents = sorted({sm.document_id for sm in result.structural_metrics})

    z: list[list[float]] = []
    for strat in strategies:
        row = []
        for doc in documents:
            sm = by_sd.get((strat, doc))
            if sm:
                composite = (
                    (1 - sm.clause_fragmentation_rate)
                    + sm.definition_preservation_rate
                    + sm.cross_ref_resolution_rate
                    + sm.hierarchy_depth_retained
                ) / 4.0
                row.append(round(composite, 3))
            else:
                row.append(0.0)
        z.append(row)

    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=documents,
            y=strategies,
            colorscale="RdYlGn",
            zmin=0,
            zmax=1,
            text=z,
            texttemplate="%{text:.3f}",
        )
    )

    fig.update_layout(
        title="Structural Quality Composite Score (strategy x document)",
        height=400,
        template="plotly_white",
    )

    return pio.to_html(fig, full_html=False, include_plotlyjs=False)


def _retrieval_bar_chart(result: BenchmarkResult, model_name: str) -> str:
    """Grouped bar chart: strategies x retrieval metrics for one model."""
    by_strategy: dict[str, list[Any]] = defaultdict(list)
    for rm in result.retrieval_metrics:
        if rm.embedding_model.value == model_name:
            by_strategy[rm.strategy.value].append(rm)

    strategies = sorted(by_strategy.keys())
    metrics = [
        ("P@5", "precision_at_5"),
        ("R@10", "recall_at_10"),
        ("MRR", "mrr"),
        ("NDCG@10", "ndcg_at_10"),
    ]

    fig = go.Figure()
    for label, attr in metrics:
        values = []
        for strat in strategies:
            items = by_strategy[strat]
            avg = sum(getattr(m, attr) for m in items) / len(items) if items else 0
            values.append(avg)
        fig.add_trace(
            go.Bar(
                name=label,
                x=strategies,
                y=values,
                text=[f"{v:.3f}" for v in values],
                textposition="auto",
            )
        )

    fig.update_layout(
        title=f"Retrieval Metrics by Strategy ({model_name})",
        barmode="group",
        yaxis_title="Score",
        yaxis_range=[0, 1.05],
        template="plotly_white",
        height=450,
    )
    return pio.to_html(fig, full_html=False, include_plotlyjs=False)


def _model_comparison_chart(result: BenchmarkResult) -> str:
    """Compare embedding models: for each strategy, show NDCG@10 across models."""
    by_sm: dict[tuple[str, str], list[Any]] = defaultdict(list)
    for rm in result.retrieval_metrics:
        key = (rm.strategy.value, rm.embedding_model.value)
        by_sm[key].append(rm)

    strategies = sorted({rm.strategy.value for rm in result.retrieval_metrics})
    models = sorted({rm.embedding_model.value for rm in result.retrieval_metrics})

    fig = go.Figure()
    for model in models:
        values = []
        for strat in strategies:
            items = by_sm.get((strat, model), [])
            avg = sum(m.ndcg_at_10 for m in items) / len(items) if items else 0
            values.append(avg)
        fig.add_trace(
            go.Bar(
                name=model,
                x=strategies,
                y=values,
                text=[f"{v:.3f}" for v in values],
                textposition="auto",
            )
        )

    fig.update_layout(
        title="NDCG@10 by Strategy and Embedding Model",
        barmode="group",
        yaxis_title="NDCG@10",
        yaxis_range=[0, 1.05],
        template="plotly_white",
        height=450,
    )
    return pio.to_html(fig, full_html=False, include_plotlyjs=False)


def _drm_chart(result: BenchmarkResult) -> str:
    """Bar chart showing Document Retrieval Mismatch rate per strategy."""
    by_strategy: dict[str, list[Any]] = defaultdict(list)
    for rm in result.retrieval_metrics:
        by_strategy[rm.strategy.value].append(rm)

    strategies = sorted(by_strategy.keys())
    drm_rates = []
    for strat in strategies:
        items = by_strategy[strat]
        rate = sum(1 for m in items if m.drm_hit) / len(items) * 100 if items else 0
        drm_rates.append(rate)

    fig = go.Figure(
        go.Bar(
            x=strategies,
            y=drm_rates,
            text=[f"{v:.1f}%" for v in drm_rates],
            textposition="auto",
            marker_color=["#16a34a" if v < 10 else "#dc2626" for v in drm_rates],
        )
    )
    fig.update_layout(
        title="Document Retrieval Mismatch Rate (lower = better)",
        yaxis_title="DRM Rate (%)",
        template="plotly_white",
        height=350,
    )
    return pio.to_html(fig, full_html=False, include_plotlyjs=False)
