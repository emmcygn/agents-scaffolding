# Agent A — Day 10: Statistical Significance + Full Retrieval Benchmark

## Mission
Add paired t-test statistical significance testing and wire the complete retrieval benchmark into CLI and JSON output, so that `make benchmark-embed` produces headline retrieval numbers with p-values proving LexiChunk's advantage is statistically significant.

## Context
Day 9 completed all retrieval metrics (P@k, R@k, MRR, NDCG@10, DRM). We have every piece of the pipeline: fixtures -> chunking -> embedding -> indexing -> retrieval -> scoring. Today we add the statistical testing layer and wire the full pipeline end-to-end. This is the end of Week 2 -- the retrieval proof milestone.

Agent B is working on Streamlit page scaffolding. Coordinate on the JSON output schema so the dashboard can consume it.

## Prerequisites
- `src/scaffolder/metrics/retrieval.py` with `compute_retrieval_metrics()`
- `src/scaffolder/retrieval/simulator.py` with `RetrievalSimulator`
- `src/scaffolder/retrieval/index.py` with `build_all_indices()`
- `src/scaffolder/embedding/pipeline.py` with `EmbeddingPipeline`
- `src/scaffolder/chunking/pipeline.py` with `ChunkingPipeline`
- `src/scaffolder/reporting/cli.py` with `print_structural_report()`
- `src/scaffolder/reporting/json_export.py` with `export_json()`
- `scipy` installed (`pip install scipy`)

## Checklist
- [ ] Implement `paired_t_test()` in `src/scaffolder/metrics/statistical.py`
- [ ] Implement `compute_all_significance()` convenience function
- [ ] Extend CLI reporter with retrieval metrics tables and significance results
- [ ] Extend `__main__.py` `benchmark-embed` command
- [ ] Wire `make benchmark-embed` (coordinate with Agent B)
- [ ] Run full eval: all queries x all strategies x 2 local models
- [ ] Verify JSON export includes all metrics
- [ ] Write tests for statistical module

## Implementation Details

### Statistical Significance (`src/scaffolder/metrics/statistical.py`)

```python
"""Statistical significance testing for benchmark comparisons."""

from __future__ import annotations

import logging
import math
from typing import Sequence

import numpy as np
from scipy import stats

from scaffolder.models import (
    RetrievalMetrics,
    SignificanceResult,
    StrategyName,
)

logger = logging.getLogger(__name__)

# Metrics to test significance for
SIGNIFICANCE_METRICS = [
    "precision_at_1",
    "precision_at_5",
    "precision_at_10",
    "recall_at_5",
    "recall_at_10",
    "mrr",
    "ndcg_at_10",
]


def paired_t_test(
    values_a: Sequence[float],
    values_b: Sequence[float],
    alpha: float = 0.05,
) -> tuple[float, float, bool, float]:
    """Perform a paired t-test comparing two sets of per-query metric values.

    Args:
        values_a: Metric values for strategy A (LexiChunk), one per query.
        values_b: Metric values for strategy B (baseline), one per query.
        alpha: Significance threshold (default 0.05).

    Returns:
        (t_statistic, p_value, is_significant, effect_size_cohens_d)

    Raises:
        ValueError: If arrays have different lengths or fewer than 2 values.
    """
    a = np.array(values_a, dtype=np.float64)
    b = np.array(values_b, dtype=np.float64)

    if len(a) != len(b):
        raise ValueError(f"Array lengths must match: {len(a)} vs {len(b)}")
    if len(a) < 2:
        raise ValueError(f"Need at least 2 paired observations, got {len(a)}")

    # Paired t-test
    t_stat, p_value = stats.ttest_rel(a, b)

    # Handle NaN (can happen with identical values)
    if math.isnan(t_stat):
        t_stat = 0.0
    if math.isnan(p_value):
        p_value = 1.0

    # Cohen's d for paired samples
    diff = a - b
    d_mean = np.mean(diff)
    d_std = np.std(diff, ddof=1)
    cohens_d = float(d_mean / d_std) if d_std > 0 else 0.0

    return float(t_stat), float(p_value), p_value < alpha, cohens_d


def compute_significance(
    lexichunk_metrics: Sequence[RetrievalMetrics],
    baseline_metrics: Sequence[RetrievalMetrics],
    baseline_strategy: StrategyName,
    alpha: float = 0.05,
) -> list[SignificanceResult]:
    """Compare LexiChunk vs one baseline across all significance metrics.

    Args:
        lexichunk_metrics: Per-query metrics for LexiChunk, sorted by query_id.
        baseline_metrics: Per-query metrics for the baseline, sorted by query_id.
        baseline_strategy: Name of the baseline strategy.
        alpha: Significance threshold.

    Returns:
        One SignificanceResult per metric in SIGNIFICANCE_METRICS.
    """
    # Ensure matching queries
    lc_by_query = {m.query_id: m for m in lexichunk_metrics}
    bl_by_query = {m.query_id: m for m in baseline_metrics}
    common_queries = sorted(set(lc_by_query.keys()) & set(bl_by_query.keys()))

    if len(common_queries) < 2:
        logger.warning(
            "Fewer than 2 common queries for %s vs %s, skipping significance.",
            StrategyName.LEXICHUNK.value, baseline_strategy.value,
        )
        return []

    results: list[SignificanceResult] = []

    for metric_name in SIGNIFICANCE_METRICS:
        values_a = [getattr(lc_by_query[q], metric_name) for q in common_queries]
        values_b = [getattr(bl_by_query[q], metric_name) for q in common_queries]

        mean_a = float(np.mean(values_a))
        mean_b = float(np.mean(values_b))

        # Calculate improvement percentage
        improvement_pct = (
            ((mean_a - mean_b) / mean_b * 100) if mean_b > 0 else 0.0
        )

        t_stat, p_value, significant, effect_size = paired_t_test(
            values_a, values_b, alpha=alpha
        )

        results.append(SignificanceResult(
            metric_name=metric_name,
            strategy_a=StrategyName.LEXICHUNK,
            strategy_b=baseline_strategy,
            mean_a=mean_a,
            mean_b=mean_b,
            improvement_pct=improvement_pct,
            t_statistic=t_stat,
            p_value=p_value,
            significant=significant,
            effect_size=effect_size,
            n_queries=len(common_queries),
        ))

    return results


def compute_all_significance(
    all_metrics: Sequence[RetrievalMetrics],
    alpha: float = 0.05,
) -> list[SignificanceResult]:
    """Compare LexiChunk vs every other strategy, per embedding model.

    Groups metrics by (strategy, model), then for each model, compares
    LexiChunk against each baseline.
    """
    from collections import defaultdict

    # Group by (strategy, model, query_id)
    by_strategy_model: dict[tuple[str, str], list[RetrievalMetrics]] = defaultdict(list)
    for m in all_metrics:
        key = (m.strategy.value, m.embedding_model.value)
        by_strategy_model[key].append(m)

    # Get unique models
    models = sorted({m.embedding_model.value for m in all_metrics})
    # Get baseline strategies (everything except LEXICHUNK)
    baselines = sorted({
        m.strategy for m in all_metrics
        if m.strategy != StrategyName.LEXICHUNK
        and m.strategy != StrategyName.LEXICHUNK_CONTEXTUAL
    })

    all_results: list[SignificanceResult] = []

    for model_name in models:
        lc_key = (StrategyName.LEXICHUNK.value, model_name)
        lc_metrics = by_strategy_model.get(lc_key, [])

        if not lc_metrics:
            continue

        for baseline in baselines:
            bl_key = (baseline.value, model_name)
            bl_metrics = by_strategy_model.get(bl_key, [])

            if not bl_metrics:
                continue

            results = compute_significance(
                lc_metrics, bl_metrics, baseline, alpha=alpha
            )
            all_results.extend(results)

    return all_results
```

### Extend CLI Reporter (`src/scaffolder/reporting/cli.py`)

Add these functions:

```python
def print_retrieval_report(
    result: BenchmarkResult,
    console: Console | None = None,
) -> None:
    """Print retrieval metrics comparison table.

    Groups by embedding model. Shows average P@5, R@10, MRR, NDCG@10
    per strategy.
    """
    if console is None:
        console = Console()

    from collections import defaultdict

    # Group by (strategy, model)
    by_sm: dict[tuple[str, str], list[RetrievalMetrics]] = defaultdict(list)
    for rm in result.retrieval_metrics:
        key = (rm.strategy.value, rm.embedding_model.value)
        by_sm[key].append(rm)

    models = sorted({rm.embedding_model.value for rm in result.retrieval_metrics})

    for model_name in models:
        table = Table(
            title=f"Retrieval Metrics -- {model_name}",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Strategy", style="bold")
        table.add_column("P@5", justify="right")
        table.add_column("P@10", justify="right")
        table.add_column("R@5", justify="right")
        table.add_column("R@10", justify="right")
        table.add_column("MRR", justify="right")
        table.add_column("NDCG@10", justify="right")
        table.add_column("DRM%", justify="right")

        strategies = sorted({
            rm.strategy.value for rm in result.retrieval_metrics
            if rm.embedding_model.value == model_name
        })

        for strat_name in strategies:
            key = (strat_name, model_name)
            metrics = by_sm[key]
            n = len(metrics)
            if n == 0:
                continue

            avg = lambda attr: sum(getattr(m, attr) for m in metrics) / n
            drm_pct = sum(1 for m in metrics if m.drm_hit) / n * 100

            table.add_row(
                strat_name,
                f"{avg('precision_at_5'):.3f}",
                f"{avg('precision_at_10'):.3f}",
                f"{avg('recall_at_5'):.3f}",
                f"{avg('recall_at_10'):.3f}",
                f"{avg('mrr'):.3f}",
                f"{avg('ndcg_at_10'):.3f}",
                f"{drm_pct:.1f}%",
            )

        console.print(table)
        console.print()


def print_significance_report(
    result: BenchmarkResult,
    console: Console | None = None,
) -> None:
    """Print significance test results table."""
    if console is None:
        console = Console()

    if not result.significance_results:
        console.print("[yellow]No significance results to report.[/yellow]")
        return

    table = Table(
        title="Statistical Significance (paired t-test, alpha=0.05)",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Metric")
    table.add_column("Baseline")
    table.add_column("LexiChunk", justify="right")
    table.add_column("Baseline", justify="right")
    table.add_column("Improvement", justify="right")
    table.add_column("p-value", justify="right")
    table.add_column("Significant?", justify="center")
    table.add_column("Cohen's d", justify="right")

    for sr in result.significance_results:
        sig_marker = "[green]YES[/green]" if sr.significant else "[red]NO[/red]"
        table.add_row(
            sr.metric_name,
            sr.strategy_b.value,
            f"{sr.mean_a:.3f}",
            f"{sr.mean_b:.3f}",
            f"+{sr.improvement_pct:.1f}%",
            f"{sr.p_value:.4f}",
            sig_marker,
            f"{sr.effect_size:.2f}",
        )

    console.print(table)
```

### Update `__main__.py` with `benchmark-embed` command

```python
def run_retrieval_benchmark(args: argparse.Namespace) -> None:
    """Run full benchmark including embeddings and retrieval."""
    from scaffolder.embedding import EmbeddingPipeline
    from scaffolder.retrieval import build_all_indices, QueryLoader, RetrievalSimulator
    from scaffolder.metrics.retrieval import compute_retrieval_metrics
    from scaffolder.metrics.statistical import compute_all_significance
    from scaffolder.reporting.cli import (
        print_structural_report,
        print_retrieval_report,
        print_significance_report,
    )

    fm = FixtureManager()
    documents = fm.load_all()

    # Phase 1: Chunking
    strategies = get_all_strategies()
    pipeline = ChunkingPipeline(strategies)
    strategy_results = pipeline.run(documents)

    # Phase 2: Structural metrics
    result = BenchmarkResult(
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        strategies=[sr.strategy for sr in strategy_results],
        documents=[d.id for d in documents],
        models=[EmbeddingModelName.MINILM, EmbeddingModelName.BGE_BASE],
        strategy_results=strategy_results,
    )

    for sr in strategy_results:
        for cs in sr.chunk_sets:
            doc = fm.get_by_id(cs.document_id)
            sm = compute_structural_metrics(cs, doc)
            result.structural_metrics.append(sm)

    # Phase 3: Embedding + Indexing
    models = [EmbeddingModelName.MINILM, EmbeddingModelName.BGE_BASE]
    emb_pipeline = EmbeddingPipeline(models=models)
    registry = build_all_indices(strategy_results, emb_pipeline, models)

    # Phase 4: Retrieval simulation
    query_loader = QueryLoader()
    queries = query_loader.load_all()

    simulator = RetrievalSimulator(
        index_registry=registry,
        embedding_pipeline=emb_pipeline,
    )
    retrieval_results = simulator.run(
        queries=queries,
        strategies=[sr.strategy for sr in strategy_results],
        models=models,
        k=10,
    )

    # Phase 5: Retrieval metrics
    for rr in retrieval_results:
        rm = compute_retrieval_metrics(rr)
        result.retrieval_metrics.append(rm)

    # Phase 6: Statistical significance
    result.significance_results = compute_all_significance(result.retrieval_metrics)

    # Output
    print_structural_report(result)
    print_retrieval_report(result)
    print_significance_report(result)

    if args.json:
        json_path = args.output_dir / "full_benchmark.json"
        export_json(result, json_path)
        print(f"\nJSON exported to: {json_path}")
```

### Tests (`tests/test_statistical.py`)

```python
"""Tests for statistical significance testing."""

# 1. paired_t_test with known values: [0.8, 0.9, 0.7] vs [0.5, 0.6, 0.4] -> significant
# 2. paired_t_test with identical values -> not significant, p=1.0
# 3. paired_t_test with 1 value -> raises ValueError
# 4. paired_t_test with mismatched lengths -> raises ValueError
# 5. Cohen's d: large effect (d > 0.8) for clearly different distributions
# 6. Cohen's d: small effect (d < 0.2) for similar distributions
# 7. compute_significance produces one result per SIGNIFICANCE_METRICS
# 8. compute_all_significance groups by model correctly
```

## Outputs
- `src/scaffolder/metrics/statistical.py`
- `src/scaffolder/reporting/cli.py` (extended with retrieval + significance tables)
- `src/scaffolder/__main__.py` (extended with `benchmark-embed` command)
- `tests/test_statistical.py`

## Acceptance Criteria
1. `make benchmark-embed` runs the full pipeline end-to-end (chunk -> embed -> index -> retrieve -> score -> significance -> report).
2. CLI output shows: structural table, retrieval table per model, significance table.
3. JSON export at `results/full_benchmark.json` contains all sections.
4. At least some significance results show `significant: true` with `p < 0.05` for LexiChunk vs baselines.
5. `pytest tests/test_statistical.py -v` -- all tests pass.
6. `mypy src/scaffolder/metrics/statistical.py --strict` passes.

## Handoff Notes
- **To Agent B:** The JSON output at `results/full_benchmark.json` has this schema: `{ timestamp, strategies, documents, models, structural_metrics: [...], retrieval_metrics: [...], significance_results: [...], config: {} }`. The Streamlit dashboard can load this file directly.
- **To Day 11:** The local model benchmark is complete. Day 11 adds Voyage Law 2 evaluation using Agent B's adapter.
- **Week 2 milestone:** `make benchmark-embed` produces retrieval metrics with statistical significance. We should see LexiChunk outperforming baselines on MRR and NDCG@10 with p < 0.05.
- **Coordinate with Agent B:** The `make benchmark-embed` Makefile target should run: `python -m scaffolder benchmark-embed --json -v`
