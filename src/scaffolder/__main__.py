"""CLI entry point: python -m scaffolder benchmark."""

from __future__ import annotations

import argparse
import datetime
import logging
import sys
from pathlib import Path

from scaffolder.chunking import ChunkingPipeline, get_all_strategies
from scaffolder.fixtures import FixtureManager
from scaffolder.metrics.structural import compute_structural_metrics
from scaffolder.models import BenchmarkResult
from scaffolder.reporting.cli import render_benchmark
from scaffolder.reporting.json_export import export_json


def main() -> None:
    """Parse CLI arguments and dispatch to the appropriate command."""
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
        "--no-embed",
        action="store_true",
        help="Skip embedding evaluation (structural only)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
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
        timestamp=datetime.datetime.now(datetime.UTC).isoformat(),
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

    # Print CLI report (force_terminal avoids encoding issues on Windows)
    from rich.console import Console

    console = Console(force_terminal=True)
    render_benchmark(result, console=console)

    # Export JSON if requested
    if args.json:
        json_path = args.output_dir / "structural_benchmark.json"
        export_json(result, json_path)
        print(f"\nJSON exported to: {json_path}")


if __name__ == "__main__":
    main()
