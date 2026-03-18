"""Page 3: Metrics Dashboard — aggregate results and comparisons."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import streamlit as st


def _load_results() -> dict[str, Any] | None:
    """Load benchmark results from file or session state."""
    if "benchmark_result" in st.session_state:
        return st.session_state["benchmark_result"]

    results_dir = Path("results")
    if results_dir.exists():
        json_files = sorted(results_dir.glob("*.json"), reverse=True)
        if json_files:
            with open(json_files[0]) as f:
                data = json.load(f)
            st.session_state["benchmark_result"] = data
            return data

    return None


def _compute_strategy_averages(
    structural_results: list[dict[str, Any]],
) -> dict[str, dict[str, float]]:
    """Compute per-strategy averages across all documents."""
    totals: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

    for r in structural_results:
        s = r["strategy"]
        totals[s]["clause_fragmentation_rate"].append(r["clause_fragmentation_rate"])
        totals[s]["definition_preservation_rate"].append(r["definition_preservation_rate"])
        totals[s]["cross_ref_resolution_rate"].append(r["cross_ref_resolution_rate"])
        totals[s]["hierarchy_depth_retained"].append(r["hierarchy_depth_retained"])

    averages: dict[str, dict[str, float]] = {}
    for strategy, metrics in totals.items():
        averages[strategy] = {k: sum(v) / len(v) for k, v in metrics.items()}

    return averages


def render_page() -> None:
    """Render the metrics dashboard page."""
    st.title("Metrics Dashboard")
    st.markdown(
        "Aggregate benchmark results comparing LexiChunk against baselines. "
        "Load results from a previous benchmark run or upload a results JSON."
    )

    # --- Data Source ---
    col1, col2 = st.columns([3, 1])
    with col1:
        data_source = st.radio(
            "Data source",
            options=["Latest results file", "Upload JSON"],
            horizontal=True,
            key="metrics_source",
        )
    with col2:
        if st.button("Refresh", key="metrics_refresh"):
            st.session_state.pop("benchmark_result", None)
            st.rerun()

    result_data: dict[str, Any] | None = None

    if data_source == "Latest results file":
        result_data = _load_results()
        if result_data is None:
            st.warning(
                "No results found. Run a benchmark first: `make benchmark` "
                "or upload a results JSON file."
            )
            return
    else:
        uploaded = st.file_uploader("Upload results JSON", type=["json"])
        if uploaded:
            result_data = json.loads(uploaded.getvalue().decode("utf-8"))
            st.session_state["benchmark_result"] = result_data
        else:
            st.info("Upload a benchmark results JSON to view metrics.")
            return

    # --- Headline Metrics ---
    _render_headline_metrics(result_data)

    # --- Structural Comparison ---
    st.markdown("---")
    _render_structural_comparison(result_data)

    # --- Retrieval Comparison ---
    if result_data.get("retrieval_results"):
        st.markdown("---")
        _render_retrieval_comparison(result_data)

        # --- Embedding Model Comparison ---
        models = {r["model"] for r in result_data["retrieval_results"]}
        if len(models) > 1:
            st.markdown("---")
            _render_model_comparison(result_data)


def _render_headline_metrics(data: dict[str, Any]) -> None:
    """Render headline metric cards showing LexiChunk's improvements."""
    st.subheader("Headline Results")

    structural = data.get("structural_results", [])
    if not structural:
        st.warning("No structural results found.")
        return

    avgs = _compute_strategy_averages(structural)
    lexi = avgs.get("lexichunk", {})

    baselines = {k: v for k, v in avgs.items() if k != "lexichunk"}
    if not baselines:
        st.warning("No baseline strategies found in results.")
        return

    # Clause fragmentation (lower is better)
    best_baseline_frag = min(
        baselines.values(), key=lambda m: m.get("clause_fragmentation_rate", 1.0)
    )
    frag_improvement = best_baseline_frag.get("clause_fragmentation_rate", 0) - lexi.get(
        "clause_fragmentation_rate", 0
    )

    # Definition preservation (higher is better)
    best_baseline_def = max(
        baselines.values(), key=lambda m: m.get("definition_preservation_rate", 0)
    )
    def_improvement = lexi.get("definition_preservation_rate", 0) - best_baseline_def.get(
        "definition_preservation_rate", 0
    )

    # Cross-ref resolution (higher is better)
    best_baseline_xref = max(
        baselines.values(), key=lambda m: m.get("cross_ref_resolution_rate", 0)
    )
    xref_improvement = lexi.get("cross_ref_resolution_rate", 0) - best_baseline_xref.get(
        "cross_ref_resolution_rate", 0
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Clause Fragmentation",
            f"{lexi.get('clause_fragmentation_rate', 0):.1%}",
            delta=f"-{frag_improvement:.1%}" if frag_improvement > 0 else None,
            delta_color="normal",
            help="Lower is better. Shows how often clauses are split across chunks.",
        )
    with col2:
        st.metric(
            "Definition Preservation",
            f"{lexi.get('definition_preservation_rate', 0):.1%}",
            delta=f"+{def_improvement:.1%}" if def_improvement > 0 else None,
            help="Higher is better. Shows how well defined terms are preserved.",
        )
    with col3:
        st.metric(
            "Cross-Ref Resolution",
            f"{lexi.get('cross_ref_resolution_rate', 0):.1%}",
            delta=f"+{xref_improvement:.1%}" if xref_improvement > 0 else None,
            help="Higher is better. Shows how well cross-references are resolved.",
        )
    with col4:
        st.metric(
            "Hierarchy Depth",
            f"{lexi.get('hierarchy_depth_retained', 0):.1f}",
            help="Average hierarchy depth retained in chunks.",
        )

    if data.get("retrieval_results"):
        _render_retrieval_headlines(data)


def _render_retrieval_headlines(data: dict[str, Any]) -> None:
    """Render retrieval metric headlines."""
    results = data["retrieval_results"]
    strategy_mrr: dict[str, list[float]] = defaultdict(list)
    strategy_ndcg: dict[str, list[float]] = defaultdict(list)
    strategy_drm: dict[str, list[bool]] = defaultdict(list)

    for r in results:
        strategy_mrr[r["strategy"]].append(r["mrr"])
        strategy_ndcg[r["strategy"]].append(r["ndcg_at_10"])
        strategy_drm[r["strategy"]].append(r.get("drm_hit", False))

    lc_mrr_vals = strategy_mrr.get("lexichunk", [])
    lc_ndcg_vals = strategy_ndcg.get("lexichunk", [])
    lc_drm_vals = strategy_drm.get("lexichunk", [])

    lexi_mrr = sum(lc_mrr_vals) / max(len(lc_mrr_vals), 1)
    lexi_ndcg = sum(lc_ndcg_vals) / max(len(lc_ndcg_vals), 1)
    lexi_drm = sum(lc_drm_vals) / max(len(lc_drm_vals), 1)

    st.markdown("")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("LexiChunk MRR", f"{lexi_mrr:.3f}")
    with col2:
        st.metric("LexiChunk NDCG@10", f"{lexi_ndcg:.3f}")
    with col3:
        st.metric(
            "LexiChunk DRM Rate",
            f"{lexi_drm:.1%}",
            help="Document Retrieval Mismatch — lower is better",
        )


def _render_structural_comparison(data: dict[str, Any]) -> None:
    """Render structural metrics comparison as a grouped bar chart."""
    import plotly.graph_objects as go

    st.subheader("Structural Metrics by Strategy")

    structural = data.get("structural_results", [])
    if not structural:
        st.info("No structural results available.")
        return

    avgs = _compute_strategy_averages(structural)
    strategies = sorted(avgs.keys())

    metrics = [
        ("Clause Preservation", "clause_fragmentation_rate", True),
        ("Definition Preservation", "definition_preservation_rate", False),
        ("Cross-Ref Resolution", "cross_ref_resolution_rate", False),
    ]

    colors = {
        "lexichunk": "#2196F3",
        "rcts": "#FF9800",
        "sentence_split": "#4CAF50",
        "fixed_size": "#9C27B0",
        "lexichunk_contextual": "#03A9F4",
    }

    fig = go.Figure()
    for strategy in strategies:
        values = []
        labels = []
        for label, key, invert in metrics:
            val = avgs[strategy].get(key, 0)
            if invert:
                val = 1 - val
            values.append(val)
            labels.append(label)

        fig.add_trace(
            go.Bar(
                name=strategy,
                x=labels,
                y=values,
                marker_color=colors.get(strategy, "#757575"),
            )
        )

    fig.update_layout(
        barmode="group",
        yaxis={"range": [0, 1.05], "title": "Rate"},
        height=400,
        margin={"l": 40, "r": 20, "t": 20, "b": 40},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
    )

    st.plotly_chart(fig, use_container_width=True)


def _render_retrieval_comparison(data: dict[str, Any]) -> None:
    """Render retrieval metrics comparison."""
    import plotly.graph_objects as go

    st.subheader("Retrieval Metrics by Strategy")

    results = data["retrieval_results"]
    strategy_metrics: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

    for r in results:
        s = r["strategy"]
        p_at_k = r.get("precision_at_k", r.get("precision_at_5", 0))
        if isinstance(p_at_k, dict):
            strategy_metrics[s]["P@5"].append(p_at_k.get("5", p_at_k.get(5, 0)))
        else:
            strategy_metrics[s]["P@5"].append(r.get("precision_at_5", 0))
        strategy_metrics[s]["MRR"].append(r["mrr"])
        strategy_metrics[s]["NDCG@10"].append(r["ndcg_at_10"])

    strategies = sorted(strategy_metrics.keys())
    metric_names = ["P@5", "MRR", "NDCG@10"]

    colors = {
        "lexichunk": "#2196F3",
        "rcts": "#FF9800",
        "sentence_split": "#4CAF50",
        "fixed_size": "#9C27B0",
        "lexichunk_contextual": "#03A9F4",
    }

    fig = go.Figure()
    for strategy in strategies:
        avgs = [
            sum(strategy_metrics[strategy][m]) / max(len(strategy_metrics[strategy][m]), 1)
            for m in metric_names
        ]
        fig.add_trace(
            go.Bar(
                name=strategy,
                x=metric_names,
                y=avgs,
                marker_color=colors.get(strategy, "#757575"),
            )
        )

    fig.update_layout(
        barmode="group",
        yaxis={"range": [0, 1.05], "title": "Score"},
        height=400,
        margin={"l": 40, "r": 20, "t": 20, "b": 40},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
    )

    st.plotly_chart(fig, use_container_width=True)


def _render_model_comparison(data: dict[str, Any]) -> None:
    """Render embedding model comparison as a heatmap."""
    import plotly.graph_objects as go

    st.subheader("Embedding Model Comparison")
    st.markdown("Heatmap showing NDCG@10 for each strategy x model combination.")

    results = data["retrieval_results"]

    models = sorted({r["model"] for r in results})
    strategies = sorted({r["strategy"] for r in results})

    matrix: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for r in results:
        matrix[r["strategy"]][r["model"]].append(r["ndcg_at_10"])

    z = []
    for strategy in strategies:
        row = []
        for model in models:
            vals = matrix[strategy][model]
            row.append(sum(vals) / max(len(vals), 1) if vals else 0)
        z.append(row)

    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=models,
            y=strategies,
            colorscale="Blues",
            text=[[f"{v:.3f}" for v in row] for row in z],
            texttemplate="%{text}",
            textfont={"size": 14},
            zmin=0,
            zmax=1,
            colorbar={"title": "NDCG@10"},
        )
    )

    fig.update_layout(
        height=300,
        margin={"l": 120, "r": 20, "t": 20, "b": 60},
        xaxis={"title": "Embedding Model"},
        yaxis={"title": "Strategy"},
    )

    st.plotly_chart(fig, use_container_width=True)
