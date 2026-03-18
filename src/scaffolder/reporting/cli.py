"""CLI output using rich tables."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.console import Console
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from scaffolder.models import BenchmarkResult, StructuralMetrics


def _best_worst(values: list[float], higher_is_better: bool) -> tuple[float, float]:
    """Return (best_value, worst_value) from a list of floats."""
    if not values:
        return 0.0, 0.0
    if higher_is_better:
        return max(values), min(values)
    return min(values), max(values)


def _color_value(value: float, best: float, worst: float, fmt: str = ".3f") -> Text:
    """Color a value green if best, red if worst, default otherwise."""
    text = f"{value:{fmt}}"
    if abs(value - best) < 1e-9:
        return Text(text, style="bold green")
    if abs(value - worst) < 1e-9:
        return Text(text, style="bold red")
    return Text(text)


def render_structural_table(
    results: list[StructuralMetrics],
    console: Console | None = None,
) -> None:
    """Render structural metrics as a colour-coded rich table.

    Green = best value per metric, Red = worst value per metric.
    """
    if console is None:
        console = Console()

    if not results:
        console.print("[yellow]No structural results to display.[/yellow]")
        return

    docs = sorted({r.document_id for r in results})

    for doc_id in docs:
        doc_results = [r for r in results if r.document_id == doc_id]
        if not doc_results:
            continue

        table = Table(
            title=f"Structural Metrics — {doc_id}",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Strategy", style="bold")
        table.add_column("Clause Frag.", justify="right")
        table.add_column("Def. Preserv.", justify="right")
        table.add_column("XRef Resol.", justify="right")
        table.add_column("Hierarchy", justify="right")
        table.add_column("Size CV", justify="right")
        table.add_column("Avg Chars", justify="right")
        table.add_column("Chunks", justify="right")

        frag_vals = [r.clause_fragmentation_rate for r in doc_results]
        def_vals = [r.definition_preservation_rate for r in doc_results]
        xref_vals = [r.cross_ref_resolution_rate for r in doc_results]
        hier_vals = [r.hierarchy_depth_retained for r in doc_results]

        frag_best, frag_worst = _best_worst(frag_vals, higher_is_better=False)
        def_best, def_worst = _best_worst(def_vals, higher_is_better=True)
        xref_best, xref_worst = _best_worst(xref_vals, higher_is_better=True)
        hier_best, hier_worst = _best_worst(hier_vals, higher_is_better=True)

        for r in doc_results:
            table.add_row(
                r.strategy.value,
                _color_value(r.clause_fragmentation_rate, frag_best, frag_worst),
                _color_value(r.definition_preservation_rate, def_best, def_worst),
                _color_value(r.cross_ref_resolution_rate, xref_best, xref_worst),
                _color_value(r.hierarchy_depth_retained, hier_best, hier_worst, ".2f"),
                f"{r.chunk_size_cv:.3f}",
                f"{r.avg_chunk_chars:.0f}",
                str(r.chunk_count),
            )

        console.print(table)
        console.print()


def render_summary_header(
    result: BenchmarkResult,
    console: Console | None = None,
) -> None:
    """Render a summary header with config and timestamp."""
    if console is None:
        console = Console()

    console.print()
    console.rule("[bold blue]Scaffolder Benchmark Results[/bold blue]")
    console.print(f"  Timestamp: {result.timestamp}")
    console.print(f"  Strategies: {', '.join(s.value for s in result.strategies)}")
    console.print(f"  Documents: {len(result.documents)}")
    if result.models:
        console.print(f"  Embedding models: {', '.join(m.value for m in result.models)}")
    console.rule()
    console.print()
