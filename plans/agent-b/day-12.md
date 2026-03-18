# Agent B — Day 12: Metrics Summary Panel & Embedding Model Comparison

## Mission
Build the Metrics Dashboard page with headline comparison cards, embedding model comparison view (grouped bar chart and heatmap), and aggregate statistics — giving users an executive summary of how LexiChunk compares to baselines.

## Context
Days 7-11 built and polished the comparison and retrieval pages. The third page ("Metrics Dashboard") has been a stub since Day 5. Today we fill it with the aggregate view: headline metrics mirroring the success criteria from the proposal, and interactive Plotly charts comparing strategies across embedding models. This page is designed for stakeholders who want the bottom line, not the per-chunk details.

## Prerequisites
- `src/scaffolder/dashboard/app.py` routes to Metrics Dashboard (Day 5)
- `src/scaffolder/models.py` with `BenchmarkResult`, `StructuralResult`, `RetrievalResult`
- `src/scaffolder/reporting/json_export.py` with `load_json()` (Day 5)
- Plotly in `[dashboard]` extras

## Checklist
- [ ] Task 1 — Create `src/scaffolder/dashboard/page_metrics.py` with full layout
- [ ] Task 2 — Build headline metric cards (clause frag improvement, definition preservation, etc.)
- [ ] Task 3 — Build strategy comparison grouped bar chart
- [ ] Task 4 — Build embedding model comparison heatmap
- [ ] Task 5 — Add data source: load from results JSON or run live benchmark
- [ ] Task 6 — Wire into app.py navigation

## Implementation Details

### page_metrics.py — full implementation

```python
"""Page 3: Metrics Dashboard — aggregate results and comparisons."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st


def _load_results() -> dict[str, Any] | None:
    """Load benchmark results from file or session state."""
    # Check session state first
    if "benchmark_result" in st.session_state:
        return st.session_state["benchmark_result"]

    # Try loading from results directory
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
    from collections import defaultdict

    totals: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for r in structural_results:
        s = r["strategy"]
        totals[s]["clause_fragmentation_rate"].append(r["clause_fragmentation_rate"])
        totals[s]["definition_preservation_rate"].append(r["definition_preservation_rate"])
        totals[s]["cross_ref_resolution_rate"].append(r["cross_ref_resolution_rate"])
        totals[s]["hierarchy_depth_retained"].append(r["hierarchy_depth_retained"])

    averages: dict[str, dict[str, float]] = {}
    for strategy, metrics in totals.items():
        averages[strategy] = {
            k: sum(v) / len(v) for k, v in metrics.items()
        }

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

    avgs = _compute_strategy_averages(data["structural_results"])
    lexi = avgs.get("lexichunk", {})

    # Compare against the best baseline
    baselines = {k: v for k, v in avgs.items() if k != "lexichunk"}
    if not baselines:
        st.warning("No baseline strategies found in results.")
        return

    # For clause fragmentation (lower is better), find the best baseline
    best_baseline_frag = min(
        baselines.values(), key=lambda m: m.get("clause_fragmentation_rate", 1.0)
    )
    frag_improvement = (
        best_baseline_frag.get("clause_fragmentation_rate", 0)
        - lexi.get("clause_fragmentation_rate", 0)
    )

    # For definition preservation (higher is better)
    best_baseline_def = max(
        baselines.values(), key=lambda m: m.get("definition_preservation_rate", 0)
    )
    def_improvement = (
        lexi.get("definition_preservation_rate", 0)
        - best_baseline_def.get("definition_preservation_rate", 0)
    )

    # For cross-ref resolution (higher is better)
    best_baseline_xref = max(
        baselines.values(), key=lambda m: m.get("cross_ref_resolution_rate", 0)
    )
    xref_improvement = (
        lexi.get("cross_ref_resolution_rate", 0)
        - best_baseline_xref.get("cross_ref_resolution_rate", 0)
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

    # Retrieval headline if available
    if data.get("retrieval_results"):
        _render_retrieval_headlines(data)


def _render_retrieval_headlines(data: dict[str, Any]) -> None:
    """Render retrieval metric headlines."""
    from collections import defaultdict

    results = data["retrieval_results"]
    strategy_mrr: dict[str, list[float]] = defaultdict(list)
    strategy_ndcg: dict[str, list[float]] = defaultdict(list)
    strategy_drm: dict[str, list[bool]] = defaultdict(list)

    for r in results:
        strategy_mrr[r["strategy"]].append(r["mrr"])
        strategy_ndcg[r["strategy"]].append(r["ndcg_at_10"])
        strategy_drm[r["strategy"]].append(r["is_drm"])

    lexi_mrr = sum(strategy_mrr.get("lexichunk", [0])) / max(len(strategy_mrr.get("lexichunk", [1])), 1)
    lexi_ndcg = sum(strategy_ndcg.get("lexichunk", [0])) / max(len(strategy_ndcg.get("lexichunk", [1])), 1)
    lexi_drm = sum(strategy_drm.get("lexichunk", [False])) / max(len(strategy_drm.get("lexichunk", [True])), 1)

    st.markdown("")  # spacing
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("LexiChunk MRR", f"{lexi_mrr:.3f}")
    with col2:
        st.metric("LexiChunk NDCG@10", f"{lexi_ndcg:.3f}")
    with col3:
        st.metric("LexiChunk DRM Rate", f"{lexi_drm:.1%}",
                   help="Document Retrieval Mismatch — lower is better")


def _render_structural_comparison(data: dict[str, Any]) -> None:
    """Render structural metrics comparison as a grouped bar chart."""
    import plotly.graph_objects as go

    st.subheader("Structural Metrics by Strategy")

    avgs = _compute_strategy_averages(data["structural_results"])
    strategies = sorted(avgs.keys())

    metrics = [
        ("Clause Fragmentation", "clause_fragmentation_rate", True),   # invert for display
        ("Definition Preservation", "definition_preservation_rate", False),
        ("Cross-Ref Resolution", "cross_ref_resolution_rate", False),
    ]

    fig = go.Figure()
    colors = {
        "lexichunk": "#2196F3",
        "langchain_rcts": "#FF9800",
        "sentence_split": "#4CAF50",
        "fixed_512": "#9C27B0",
    }

    for strategy in strategies:
        values = []
        labels = []
        for label, key, invert in metrics:
            val = avgs[strategy].get(key, 0)
            if invert:
                val = 1 - val  # Show as "preservation" rather than "fragmentation"
            values.append(val)
            labels.append(label.replace("Clause Fragmentation", "Clause Preservation"))

        fig.add_trace(go.Bar(
            name=strategy,
            x=labels,
            y=values,
            marker_color=colors.get(strategy, "#757575"),
        ))

    fig.update_layout(
        barmode="group",
        yaxis=dict(range=[0, 1.05], title="Rate"),
        height=400,
        margin=dict(l=40, r=20, t=20, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    st.plotly_chart(fig, use_container_width=True)


def _render_retrieval_comparison(data: dict[str, Any]) -> None:
    """Render retrieval metrics comparison."""
    import plotly.graph_objects as go
    from collections import defaultdict

    st.subheader("Retrieval Metrics by Strategy")

    results = data["retrieval_results"]
    strategy_metrics: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for r in results:
        s = r["strategy"]
        strategy_metrics[s]["P@5"].append(r["precision_at_k"].get("5", r["precision_at_k"].get(5, 0)))
        strategy_metrics[s]["MRR"].append(r["mrr"])
        strategy_metrics[s]["NDCG@10"].append(r["ndcg_at_10"])

    strategies = sorted(strategy_metrics.keys())
    metric_names = ["P@5", "MRR", "NDCG@10"]

    colors = {
        "lexichunk": "#2196F3",
        "langchain_rcts": "#FF9800",
        "sentence_split": "#4CAF50",
        "fixed_512": "#9C27B0",
    }

    fig = go.Figure()
    for strategy in strategies:
        avgs = [
            sum(strategy_metrics[strategy][m]) / max(len(strategy_metrics[strategy][m]), 1)
            for m in metric_names
        ]
        fig.add_trace(go.Bar(
            name=strategy,
            x=metric_names,
            y=avgs,
            marker_color=colors.get(strategy, "#757575"),
        ))

    fig.update_layout(
        barmode="group",
        yaxis=dict(range=[0, 1.05], title="Score"),
        height=400,
        margin=dict(l=40, r=20, t=20, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    st.plotly_chart(fig, use_container_width=True)


def _render_model_comparison(data: dict[str, Any]) -> None:
    """Render embedding model comparison as a heatmap."""
    import plotly.graph_objects as go
    import numpy as np
    from collections import defaultdict

    st.subheader("Embedding Model Comparison")
    st.markdown("Heatmap showing NDCG@10 for each strategy x model combination.")

    results = data["retrieval_results"]

    # Build matrix: strategies x models
    models = sorted({r["model"] for r in results})
    strategies = sorted({r["strategy"] for r in results})

    matrix: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for r in results:
        matrix[r["strategy"]][r["model"]].append(r["ndcg_at_10"])

    z = []
    for strategy in strategies:
        row = []
        for model in models:
            vals = matrix[strategy][model]
            row.append(sum(vals) / max(len(vals), 1) if vals else 0)
        z.append(row)

    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=models,
        y=strategies,
        colorscale="Blues",
        text=[[f"{v:.3f}" for v in row] for row in z],
        texttemplate="%{text}",
        textfont={"size": 14},
        zmin=0,
        zmax=1,
        colorbar=dict(title="NDCG@10"),
    ))

    fig.update_layout(
        height=300,
        margin=dict(l=120, r=20, t=20, b=60),
        xaxis=dict(title="Embedding Model"),
        yaxis=dict(title="Strategy"),
    )

    st.plotly_chart(fig, use_container_width=True)
```

### Wire into app.py

Update the routing in `app.py`:

```python
elif page == "Metrics Dashboard":
    from scaffolder.dashboard.page_metrics import render_page
    render_page()
```

## Outputs
- `src/scaffolder/dashboard/page_metrics.py` (new file, complete)
- `src/scaffolder/dashboard/app.py` (updated routing)

## Acceptance Criteria
1. Navigate to "Metrics Dashboard" in Streamlit
2. Headline metrics show with delta improvements (LexiChunk vs best baseline)
3. Structural comparison grouped bar chart renders with all strategies
4. Retrieval comparison chart renders when retrieval results exist
5. Heatmap renders when multiple embedding models are in the results
6. Upload JSON works as an alternative data source
7. "Refresh" button reloads data from disk
8. `make lint` passes

## Handoff Notes
- **To Agent A:** The metrics dashboard reads from `results/*.json` files produced by your benchmark runner. The JSON structure should match `dataclasses.asdict(BenchmarkResult)`. Specifically, it needs `structural_results` (list of dicts with `strategy`, `document_id`, and all metric fields) and optionally `retrieval_results` (list of dicts with `strategy`, `model`, `mrr`, `ndcg_at_10`, `precision_at_k`, `is_drm`).
- **To Day 13:** The metrics dashboard is complete. Day 13 adds the filtered retrieval demo (using LexiChunk's clause_type metadata) and export functionality (download JSON/HTML from dashboard).
- **Decision:** We show "Clause Preservation" (1 - fragmentation_rate) in the bar chart instead of "Clause Fragmentation" so that all bars go in the same direction (higher = better). This is more intuitive for stakeholders.
