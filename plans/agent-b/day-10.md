# Agent B — Day 10: CLI Retrieval Metrics & Streamlit Embedding Model Toggle

## Mission
Extend the CLI reporter with retrieval metrics tables (P@k, R@k, MRR, NDCG, DRM rate) including statistical significance markers, and wire the Voyage embedding model toggle into the Streamlit dashboard.

## Context
Day 9 completed the Streamlit retrieval page. Agent A has delivered statistical testing (`metrics/statistical.py` with paired t-tests and bootstrap confidence intervals). Today we add the CLI retrieval output — this is what users see when running `scaffolder benchmark --embed`. We also complete the embedding model integration in the Streamlit dashboard by adding Voyage to the dropdown (conditionally, based on whether the API key is set).

## Prerequisites
- `src/scaffolder/reporting/cli.py` with structural tables (Day 4-5)
- `src/scaffolder/models.py` with `RetrievalResult`, `BenchmarkResult` (Agent A)
- `src/scaffolder/metrics/statistical.py` with t-test results (Agent A)
- `src/scaffolder/embedding/voyage.py` with `VoyageEmbedder` (Day 6)
- `src/scaffolder/dashboard/page_retrieval.py` (Day 9)

## Checklist
- [ ] Task 1 — Add `render_retrieval_table()` to CLI reporter
- [ ] Task 2 — Add significance markers (* p<0.05, ** p<0.01) to the retrieval table
- [ ] Task 3 — Add DRM rate summary row to the CLI output
- [ ] Task 4 — Update `render_benchmark()` to include retrieval section when results exist
- [ ] Task 5 — Add Voyage model to Streamlit embedding dropdown (conditional on VOYAGE_API_KEY)
- [ ] Task 6 — Write `tests/test_cli.py`

## Implementation Details

### CLI retrieval table: add to src/scaffolder/reporting/cli.py

```python
def render_retrieval_table(
    results: list[RetrievalResult],
    statistical_tests: dict[str, Any] | None = None,
    console: Console | None = None,
) -> None:
    """Render retrieval metrics as a colour-coded rich table.

    Shows per-strategy aggregate retrieval metrics (averaged across all queries).
    Adds significance markers when statistical tests are provided.

    Significance markers:
    - * p < 0.05 (significant)
    - ** p < 0.01 (highly significant)
    """
    if console is None:
        console = Console()

    if not results:
        console.print("[yellow]No retrieval results to display (run with --embed).[/yellow]")
        return

    # Group by model
    models = sorted({r.model for r in results})

    for model in models:
        model_results = [r for r in results if r.model == model]

        # Group by strategy and compute averages
        strategies = sorted({r.strategy for r in model_results})
        strategy_metrics: dict[str, dict[str, float]] = {}

        for strategy in strategies:
            strat_results = [r for r in model_results if r.strategy == strategy]
            n = len(strat_results)
            if n == 0:
                continue

            avg_p1 = sum(r.precision_at_k.get(1, 0.0) for r in strat_results) / n
            avg_p3 = sum(r.precision_at_k.get(3, 0.0) for r in strat_results) / n
            avg_p5 = sum(r.precision_at_k.get(5, 0.0) for r in strat_results) / n
            avg_p10 = sum(r.precision_at_k.get(10, 0.0) for r in strat_results) / n
            avg_mrr = sum(r.mrr for r in strat_results) / n
            avg_ndcg = sum(r.ndcg_at_10 for r in strat_results) / n
            drm_count = sum(1 for r in strat_results if r.is_drm)
            drm_rate = drm_count / n

            strategy_metrics[strategy] = {
                "P@1": avg_p1, "P@3": avg_p3, "P@5": avg_p5, "P@10": avg_p10,
                "MRR": avg_mrr, "NDCG@10": avg_ndcg, "DRM%": drm_rate,
                "n_queries": n,
            }

        # Build table
        table = Table(
            title=f"Retrieval Metrics — {model}",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Strategy", style="bold")
        table.add_column("P@1", justify="right")
        table.add_column("P@3", justify="right")
        table.add_column("P@5", justify="right")
        table.add_column("P@10", justify="right")
        table.add_column("MRR", justify="right")
        table.add_column("NDCG@10", justify="right")
        table.add_column("DRM%", justify="right")
        table.add_column("Queries", justify="right")

        # Compute best/worst for colour coding
        metric_keys = ["P@1", "P@3", "P@5", "P@10", "MRR", "NDCG@10"]
        best_worst: dict[str, tuple[float, float]] = {}
        for mk in metric_keys:
            vals = [m[mk] for m in strategy_metrics.values()]
            best_worst[mk] = _best_worst(vals, higher_is_better=True)

        # DRM is lower-is-better
        drm_vals = [m["DRM%"] for m in strategy_metrics.values()]
        best_worst["DRM%"] = _best_worst(drm_vals, higher_is_better=False)

        for strategy in strategies:
            m = strategy_metrics.get(strategy)
            if m is None:
                continue

            row: list[Text | str] = [strategy]
            for mk in metric_keys:
                value = m[mk]
                best, worst = best_worst[mk]
                text = _color_value(value, best, worst)

                # Add significance marker
                sig = _get_significance_marker(
                    strategy, mk, statistical_tests
                )
                if sig:
                    text.append(f" {sig}", style="bold yellow")

                row.append(text)

            # DRM rate (lower is better)
            drm_best, drm_worst = best_worst["DRM%"]
            drm_text = _color_value(m["DRM%"], drm_best, drm_worst)
            row.append(drm_text)

            row.append(str(int(m["n_queries"])))
            table.add_row(*row)

        console.print(table)
        console.print()


def _get_significance_marker(
    strategy: str,
    metric: str,
    statistical_tests: dict[str, Any] | None,
) -> str:
    """Get significance marker for a strategy/metric pair.

    Returns:
        "**" if p < 0.01, "*" if p < 0.05, "" otherwise.
    """
    if not statistical_tests:
        return ""

    # Statistical tests are structured as:
    # {f"{strategy_a}_vs_{strategy_b}": {"metric_name": {"p_value": float, ...}}}
    # We look for tests comparing this strategy against "lexichunk"
    if strategy == "lexichunk":
        return ""  # No significance marker for the reference strategy

    test_key = f"lexichunk_vs_{strategy}"
    alt_key = f"{strategy}_vs_lexichunk"

    test_data = statistical_tests.get(test_key) or statistical_tests.get(alt_key)
    if not test_data:
        return ""

    # Map CLI column names to statistical test metric names
    metric_map = {
        "P@1": "precision_at_1",
        "P@3": "precision_at_3",
        "P@5": "precision_at_5",
        "P@10": "precision_at_10",
        "MRR": "mrr",
        "NDCG@10": "ndcg_at_10",
    }

    stat_metric = metric_map.get(metric, "")
    metric_test = test_data.get(stat_metric, {})
    p_value = metric_test.get("p_value", 1.0)

    if p_value < 0.01:
        return "**"
    if p_value < 0.05:
        return "*"
    return ""
```

### Update render_benchmark

```python
def render_benchmark(
    result: BenchmarkResult,
    console: Console | None = None,
) -> None:
    """Full CLI benchmark output."""
    if console is None:
        console = Console()

    render_summary_header(result, console)
    render_structural_table(result.structural_results, console)

    # Retrieval metrics (only if embedding was run)
    if result.retrieval_results:
        render_retrieval_table(
            result.retrieval_results,
            statistical_tests=result.statistical_tests,
            console=console,
        )

        # Significance legend
        if result.statistical_tests:
            console.print(
                "[dim]Significance: * p<0.05, ** p<0.01 "
                "(paired t-test, LexiChunk vs baseline)[/dim]"
            )
            console.print()

    render_aggregate_summary(result, console)
```

### Streamlit Voyage toggle

Update `src/scaffolder/dashboard/app.py` sidebar and `page_retrieval.py`:

In **app.py**, update the sidebar settings:

```python
# After the strategy multiselect, add:
import os

# Embedding model selection
available_models = ["all-MiniLM-L6-v2", "bge-base-en-v1.5"]
if os.getenv("VOYAGE_API_KEY"):
    available_models.append("voyage-law-2")

selected_model = st.sidebar.selectbox(
    "Embedding Model",
    options=available_models,
    key="global_model",
    help="Voyage requires VOYAGE_API_KEY environment variable",
)
st.session_state.config["embedding_model"] = selected_model

# Show Voyage status
if "voyage-law-2" in available_models:
    st.sidebar.success("Voyage API: Connected")
else:
    st.sidebar.caption(
        "Set VOYAGE_API_KEY to enable voyage-law-2"
    )
```

In **page_retrieval.py**, read the model from global config:

```python
# Replace the model selectbox with:
model = st.session_state.get("config", {}).get(
    "embedding_model", "all-MiniLM-L6-v2"
)
st.caption(f"Embedding model: **{model}** (change in sidebar)")
```

### tests/test_cli.py

```python
"""Tests for CLI reporter."""

from __future__ import annotations

from io import StringIO
from unittest.mock import MagicMock

import pytest
from rich.console import Console

from scaffolder.reporting.cli import (
    render_benchmark,
    render_retrieval_table,
    render_structural_table,
)


def _make_structural_result(**kwargs: object) -> MagicMock:
    """Create a mock StructuralResult."""
    defaults = {
        "strategy": "lexichunk",
        "document_id": "test_doc",
        "clause_fragmentation_rate": 0.1,
        "definition_preservation_rate": 0.9,
        "cross_ref_resolution_rate": 0.85,
        "hierarchy_depth_retained": 2.5,
        "chunk_size_stats": {"mean": 350, "count": 12},
    }
    defaults.update(kwargs)
    mock = MagicMock()
    for k, v in defaults.items():
        setattr(mock, k, v)
    return mock


def _make_retrieval_result(**kwargs: object) -> MagicMock:
    """Create a mock RetrievalResult."""
    defaults = {
        "query_id": "q1",
        "query_text": "test query",
        "strategy": "lexichunk",
        "model": "all-MiniLM-L6-v2",
        "retrieved_chunk_ids": ["c1", "c2"],
        "relevant_chunk_ids": ["c1"],
        "scores": [0.9, 0.7],
        "precision_at_k": {1: 1.0, 3: 0.67, 5: 0.4, 10: 0.2},
        "recall_at_k": {1: 0.5, 3: 0.75, 5: 1.0, 10: 1.0},
        "mrr": 1.0,
        "ndcg_at_10": 0.85,
        "is_drm": False,
    }
    defaults.update(kwargs)
    mock = MagicMock()
    for k, v in defaults.items():
        setattr(mock, k, v)
    # Make .get() work for dict fields
    mock.precision_at_k = defaults["precision_at_k"]
    mock.recall_at_k = defaults["recall_at_k"]
    return mock


class TestRenderStructuralTable:
    def test_renders_without_error(self) -> None:
        console = Console(file=StringIO())
        results = [
            _make_structural_result(strategy="lexichunk"),
            _make_structural_result(
                strategy="fixed_512",
                clause_fragmentation_rate=0.45,
                definition_preservation_rate=0.3,
            ),
        ]
        render_structural_table(results, console=console)

    def test_empty_results(self) -> None:
        console = Console(file=StringIO())
        render_structural_table([], console=console)


class TestRenderRetrievalTable:
    def test_renders_without_error(self) -> None:
        console = Console(file=StringIO())
        results = [
            _make_retrieval_result(strategy="lexichunk"),
            _make_retrieval_result(strategy="fixed_512", mrr=0.5, ndcg_at_10=0.4),
        ]
        render_retrieval_table(results, console=console)

    def test_with_significance_markers(self) -> None:
        console = Console(file=StringIO())
        results = [
            _make_retrieval_result(strategy="lexichunk"),
            _make_retrieval_result(strategy="fixed_512"),
        ]
        stats = {
            "lexichunk_vs_fixed_512": {
                "mrr": {"p_value": 0.003},
                "ndcg_at_10": {"p_value": 0.04},
            }
        }
        render_retrieval_table(results, statistical_tests=stats, console=console)

    def test_empty_results(self) -> None:
        console = Console(file=StringIO())
        render_retrieval_table([], console=console)
```

## Outputs
- `src/scaffolder/reporting/cli.py` (updated with retrieval tables + significance markers)
- `src/scaffolder/dashboard/app.py` (updated with Voyage toggle in sidebar)
- `src/scaffolder/dashboard/page_retrieval.py` (updated to use global model setting)
- `tests/test_cli.py`

## Acceptance Criteria
1. `python -c "from scaffolder.reporting.cli import render_retrieval_table"` imports without error
2. CLI output shows colour-coded retrieval metrics with green=best, red=worst per column
3. Significance markers (* and **) appear when statistical tests are provided
4. Streamlit sidebar shows "voyage-law-2" option when `VOYAGE_API_KEY` is set
5. Streamlit sidebar shows "Set VOYAGE_API_KEY to enable..." when key is absent
6. All tests in `tests/test_cli.py` pass
7. `make lint` and `make typecheck` pass

## Handoff Notes
- **To Agent A:** The CLI reporter now renders both structural and retrieval results. The `render_benchmark(result)` function is the single entry point — it handles everything. Your `__main__.py` should call this after running the benchmark pipeline. Statistical tests should be structured as `{"lexichunk_vs_STRATEGY": {"metric_name": {"p_value": float}}}`.
- **To Day 11:** Streamlit pages are functional. Day 11 focuses on polish: loading spinners, error messages, responsive layout, and session state management to prevent unnecessary recomputation.
- **Decision:** Significance markers only compare baselines against LexiChunk (the reference). We don't show markers between baselines because the primary claim is "LexiChunk > baselines", not "baseline A > baseline B".
