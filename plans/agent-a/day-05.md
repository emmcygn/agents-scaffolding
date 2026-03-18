# Agent A — Day 05: Remaining Structural Metrics + CLI/JSON Output

## Mission
Complete the structural metrics suite (hierarchy depth retained, chunk size distribution) and wire all metrics into the CLI rich-table reporter and JSON exporter, so that `make benchmark` produces a full structural quality report end-to-end.

## Context
Day 4 delivered three core structural metrics (clause fragmentation, definition preservation, cross-ref resolution) with placeholder values for the remaining two. The `ChunkingPipeline` can run all four strategies on all five documents. Today we complete the metrics and build the output layer. This is the end of Week 1 -- the structural proof milestone.

Agent B is working on the Makefile `benchmark` target today. They will wire `make benchmark` to invoke our CLI entry point. Coordinate on the entry point name and arguments.

## Prerequisites
- `src/scaffolder/metrics/structural.py` with `compute_structural_metrics()`, `clause_fragmentation_rate()`, `definition_preservation_rate()`, `cross_ref_resolution_rate()`
- `src/scaffolder/chunking/pipeline.py` with working `ChunkingPipeline`
- `src/scaffolder/fixtures/__init__.py` with `FixtureManager`
- `src/scaffolder/models.py` with `StructuralMetrics`, `BenchmarkResult`
- `rich` installed, `json` stdlib

## Checklist
- [ ] Implement `hierarchy_depth_retained()` in `src/scaffolder/metrics/structural.py`
- [ ] Implement `chunk_size_cv()` in `src/scaffolder/metrics/structural.py`
- [ ] Update `compute_structural_metrics()` to use real implementations instead of placeholders
- [ ] Implement CLI reporter in `src/scaffolder/reporting/cli.py` using rich tables
- [ ] Implement JSON exporter in `src/scaffolder/reporting/json_export.py`
- [ ] Create CLI entry point in `src/scaffolder/__main__.py` or a `cli.py` at package root
- [ ] Wire `make benchmark` (coordinate with Agent B)
- [ ] Write tests for new metrics and reporters
- [ ] Run full end-to-end: `make benchmark` produces structural metrics for 4 strategies x 5 docs

## Implementation Details

### Hierarchy Depth Retained (`src/scaffolder/metrics/structural.py`)

```python
def hierarchy_depth_retained(chunk_set: ChunkSet, document: Document) -> float:
    """Calculate what fraction of the document's hierarchy depth is preserved in chunks.

    Examines section numbering patterns (1.2.3) in each chunk and compares
    the maximum depth found against the ground truth maximum depth.

    Returns:
        1.0 = full depth retained (best), 0.0 = flat (worst).
    """
    gt = get_ground_truth(document)
    if gt.max_hierarchy_depth <= 1:
        return 1.0  # flat document, nothing to lose

    max_chunk_depth = 0
    section_pattern = re.compile(r"(\d+(?:\.\d+)*)\.")

    for chunk in chunk_set.chunks:
        for match in section_pattern.finditer(chunk.text):
            depth = match.group(1).count(".") + 1
            max_chunk_depth = max(max_chunk_depth, depth)

        # Also check metadata for section_hierarchy
        hier = chunk.metadata.get("section_hierarchy")
        if isinstance(hier, (list, tuple)):
            max_chunk_depth = max(max_chunk_depth, len(hier))

    return min(max_chunk_depth / gt.max_hierarchy_depth, 1.0)
```

### Chunk Size Distribution (CV)

```python
def chunk_size_cv(chunk_set: ChunkSet) -> float:
    """Calculate the coefficient of variation of chunk sizes.

    CV = std_dev / mean. Lower is more uniform.
    A CV of 0 means all chunks are the same size.
    A CV > 1 means high variance relative to mean.

    Returns 0.0 if fewer than 2 chunks.
    """
    if len(chunk_set.chunks) < 2:
        return 0.0

    sizes = [c.char_count for c in chunk_set.chunks]
    mean = sum(sizes) / len(sizes)
    if mean == 0:
        return 0.0
    variance = sum((s - mean) ** 2 for s in sizes) / len(sizes)
    std_dev = variance ** 0.5
    return std_dev / mean
```

### Update `compute_structural_metrics()`

Replace the placeholder values:

```python
def compute_structural_metrics(
    chunk_set: ChunkSet, document: Document
) -> StructuralMetrics:
    """Compute all structural metrics for a ChunkSet against a Document."""
    return StructuralMetrics(
        strategy=chunk_set.strategy,
        document_id=chunk_set.document_id,
        clause_fragmentation_rate=clause_fragmentation_rate(chunk_set, document),
        definition_preservation_rate=definition_preservation_rate(chunk_set, document),
        cross_ref_resolution_rate=cross_ref_resolution_rate(chunk_set, document),
        hierarchy_depth_retained=hierarchy_depth_retained(chunk_set, document),
        chunk_size_cv=chunk_size_cv(chunk_set),
        chunk_count=chunk_set.count,
        avg_chunk_chars=chunk_set.avg_chunk_size,
    )
```

### CLI Reporter (`src/scaffolder/reporting/cli.py`)

Uses `rich` to produce colored terminal tables.

```python
"""CLI reporter using rich tables for terminal output."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from scaffolder.models import BenchmarkResult, StructuralMetrics, StrategyName


def print_structural_report(
    result: BenchmarkResult,
    console: Console | None = None,
) -> None:
    """Print structural metrics comparison table.

    Layout:
    ┌──────────────────────────────────────────────────────────────┐
    │  Structural Quality Metrics — {document_id}                  │
    ├──────────┬──────────┬──────────┬──────────┬──────────┬──────┤
    │ Strategy │ Frag Rate│ Def Pres │ XRef Res │ Hier Dep │  CV  │
    ├──────────┼──────────┼──────────┼──────────┼──────────┼──────┤
    │ lexichunk│    0.05  │    0.92  │    0.88  │    1.00  │ 0.31 │
    │ rcts     │    0.42  │    0.35  │    0.20  │    0.67  │ 0.15 │
    │ ...      │          │          │          │          │      │
    └──────────┴──────────┴──────────┴──────────┴──────────┴──────┘
    """
    if console is None:
        console = Console()

    # Group metrics by document
    by_doc: dict[str, list[StructuralMetrics]] = {}
    for sm in result.structural_metrics:
        by_doc.setdefault(sm.document_id, []).append(sm)

    for doc_id, metrics_list in sorted(by_doc.items()):
        table = Table(
            title=f"Structural Quality -- {doc_id}",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Strategy", style="bold")
        table.add_column("Frag Rate", justify="right")     # lower is better
        table.add_column("Def Pres", justify="right")      # higher is better
        table.add_column("XRef Res", justify="right")      # higher is better
        table.add_column("Hier Depth", justify="right")    # higher is better
        table.add_column("Size CV", justify="right")       # lower is better
        table.add_column("Chunks", justify="right")
        table.add_column("Avg Size", justify="right")

        # Sort: LexiChunk first, then alphabetical
        metrics_list.sort(key=lambda m: (
            0 if m.strategy == StrategyName.LEXICHUNK else 1,
            m.strategy.value,
        ))

        for sm in metrics_list:
            table.add_row(
                sm.strategy.value,
                _fmt_metric(sm.clause_fragmentation_rate, lower_better=True),
                _fmt_metric(sm.definition_preservation_rate, lower_better=False),
                _fmt_metric(sm.cross_ref_resolution_rate, lower_better=False),
                _fmt_metric(sm.hierarchy_depth_retained, lower_better=False),
                f"{sm.chunk_size_cv:.2f}",
                str(sm.chunk_count),
                f"{sm.avg_chunk_chars:.0f}",
            )

        console.print(table)
        console.print()

    # Summary table: average across all documents
    _print_summary_table(result, console)


def _fmt_metric(value: float, *, lower_better: bool) -> str:
    """Format a 0-1 metric with color hint."""
    text = f"{value:.3f}"
    if lower_better:
        if value <= 0.1:
            return f"[green]{text}[/green]"
        elif value >= 0.5:
            return f"[red]{text}[/red]"
    else:
        if value >= 0.9:
            return f"[green]{text}[/green]"
        elif value <= 0.5:
            return f"[red]{text}[/red]"
    return text


def _print_summary_table(result: BenchmarkResult, console: Console) -> None:
    """Print average metrics across all documents, per strategy."""
    from collections import defaultdict

    by_strategy: dict[str, list[StructuralMetrics]] = defaultdict(list)
    for sm in result.structural_metrics:
        by_strategy[sm.strategy.value].append(sm)

    table = Table(
        title="Structural Quality -- Average Across All Documents",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Strategy", style="bold")
    table.add_column("Avg Frag Rate", justify="right")
    table.add_column("Avg Def Pres", justify="right")
    table.add_column("Avg XRef Res", justify="right")
    table.add_column("Avg Hier Dep", justify="right")

    for strategy in sorted(by_strategy.keys()):
        metrics = by_strategy[strategy]
        n = len(metrics)
        table.add_row(
            strategy,
            f"{sum(m.clause_fragmentation_rate for m in metrics) / n:.3f}",
            f"{sum(m.definition_preservation_rate for m in metrics) / n:.3f}",
            f"{sum(m.cross_ref_resolution_rate for m in metrics) / n:.3f}",
            f"{sum(m.hierarchy_depth_retained for m in metrics) / n:.3f}",
        )

    console.print(table)
```

### JSON Exporter (`src/scaffolder/reporting/json_export.py`)

```python
"""JSON export for benchmark results."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from scaffolder.models import BenchmarkResult


def _serialize(obj: Any) -> Any:
    """Custom serializer for enum values and other non-JSON types."""
    if hasattr(obj, "value"):
        return obj.value
    if isinstance(obj, set):
        return sorted(obj)
    raise TypeError(f"Cannot serialize {type(obj)}")


def export_json(result: BenchmarkResult, path: Path) -> None:
    """Export BenchmarkResult to a JSON file.

    The output file is human-readable (indented) and includes all
    structural metrics, retrieval metrics, and significance results.
    """
    data = asdict(result)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=_serialize)


def load_json(path: Path) -> dict:
    """Load a previously exported JSON result."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)
```

### CLI Entry Point (`src/scaffolder/__main__.py`)

```python
"""CLI entry point: python -m scaffolder benchmark"""

from __future__ import annotations

import argparse
import datetime
import logging
import sys
from pathlib import Path

from scaffolder.fixtures import FixtureManager
from scaffolder.chunking import get_all_strategies, ChunkingPipeline
from scaffolder.metrics.structural import compute_structural_metrics
from scaffolder.reporting.cli import print_structural_report
from scaffolder.reporting.json_export import export_json
from scaffolder.models import BenchmarkResult


def main() -> None:
    parser = argparse.ArgumentParser(description="sdk-scaffolder benchmark")
    parser.add_argument(
        "command",
        choices=["benchmark", "benchmark-embed", "report"],
        help="Command to run",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results"),
        help="Directory for output files",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Export results to JSON",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(name)s %(levelname)s: %(message)s",
    )

    if args.command == "benchmark":
        run_structural_benchmark(args)
    elif args.command == "benchmark-embed":
        print("Embedding benchmark not yet implemented (Day 10).")
        sys.exit(1)
    elif args.command == "report":
        print("HTML report not yet implemented (Day 14).")
        sys.exit(1)


def run_structural_benchmark(args: argparse.Namespace) -> None:
    """Run structural-only benchmark (no embeddings)."""
    fm = FixtureManager()
    documents = fm.load_all()

    strategies = get_all_strategies()
    pipeline = ChunkingPipeline(strategies)
    strategy_results = pipeline.run(documents)

    result = BenchmarkResult(
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        strategies=[sr.strategy for sr in strategy_results],
        documents=[d.id for d in documents],
        strategy_results=strategy_results,
    )

    # Compute structural metrics for each (strategy, document) pair
    for sr in strategy_results:
        for cs in sr.chunk_sets:
            doc = fm.get_by_id(cs.document_id)
            sm = compute_structural_metrics(cs, doc)
            result.structural_metrics.append(sm)

    # Print CLI report
    print_structural_report(result)

    # Export JSON if requested
    if args.json:
        json_path = args.output_dir / "structural_benchmark.json"
        export_json(result, json_path)
        print(f"\nJSON exported to: {json_path}")


if __name__ == "__main__":
    main()
```

### Coordinate with Agent B on Makefile

The `make benchmark` target should run:
```makefile
benchmark:
	python -m scaffolder benchmark --json -v
```

## Outputs
- `src/scaffolder/metrics/structural.py` (updated with hierarchy_depth_retained, chunk_size_cv)
- `src/scaffolder/reporting/cli.py`
- `src/scaffolder/reporting/json_export.py`
- `src/scaffolder/__main__.py`
- `tests/test_reporting.py` (tests for CLI and JSON export)

## Acceptance Criteria
1. `make benchmark` runs end-to-end and prints a rich table with structural metrics for all 4 strategies x 5 documents.
2. `make benchmark` with `--json` flag produces `results/structural_benchmark.json`.
3. All 5 structural metrics are non-placeholder (real computed values).
4. `pytest tests/ -v` -- all existing + new tests pass.
5. `mypy src/scaffolder/metrics/ src/scaffolder/reporting/ --strict` passes.
6. `ruff check src/scaffolder/` passes.

## Handoff Notes
- **To Agent B:** The CLI entry point is `python -m scaffolder benchmark`. Wire `make benchmark` to call this. The `--json` flag exports to `results/`. The `benchmark-embed` command is stubbed for Day 10.
- **To Day 6:** The structural benchmark is complete. Day 6 starts the embedding pipeline. The `BenchmarkResult` object now has `structural_metrics` populated. Day 10 will add `retrieval_metrics` and `significance_results`.
- **Week 1 milestone:** `make benchmark` produces structural quality metrics proving LexiChunk outperforms baselines on clause fragmentation, definition preservation, and cross-reference resolution.
