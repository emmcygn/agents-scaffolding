# Agent A — Day 14: HTML Report (Part 2) — Retrieval + Methodology

## Mission
Complete the HTML report with retrieval metrics section, per-document breakdown tables, embedding model comparison charts, significance results, and a methodology section citing research sources, then wire `make report` to generate it.

## Context
Day 13 built the HTML report skeleton with structural metrics tables and Plotly charts. Today we add the remaining sections: retrieval metrics, statistical significance with color-coded p-values, per-document breakdowns, and a methodology section. After today, `make report` produces the complete evaluation document.

Agent B is working on Streamlit dashboard polish today.

## Prerequisites
- `src/scaffolder/reporting/html.py` with `render_html_report()` from Day 13
- `src/scaffolder/reporting/templates/report.html.j2` from Day 13
- Full benchmark results with both structural and retrieval metrics
- `plotly` installed

## Checklist
- [ ] Add retrieval metrics Plotly charts (strategy comparison per model)
- [ ] Add retrieval metrics detailed table to template
- [ ] Add embedding model comparison chart (same strategy across models)
- [ ] Add significance results table with color-coded p-values
- [ ] Add per-document breakdown section
- [ ] Add methodology section with metric definitions and citations
- [ ] Wire `make report` in `__main__.py`
- [ ] Run `make report` with real benchmark data
- [ ] Update tests

## Implementation Details

### Retrieval Charts (`src/scaffolder/reporting/html.py`)

Add these chart generators:

```python
def _retrieval_bar_chart(result: BenchmarkResult, model_name: str) -> str:
    """Grouped bar chart: strategies x retrieval metrics for one model.

    Shows P@5, R@10, MRR, NDCG@10 per strategy.
    """
    by_strategy: dict[str, list] = defaultdict(list)
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
        fig.add_trace(go.Bar(
            name=label, x=strategies, y=values,
            text=[f"{v:.3f}" for v in values], textposition="auto",
        ))

    fig.update_layout(
        title=f"Retrieval Metrics by Strategy ({model_name})",
        barmode="group", yaxis_title="Score", yaxis_range=[0, 1.05],
        template="plotly_white", height=450,
    )
    return pio.to_html(fig, full_html=False, include_plotlyjs=False)


def _model_comparison_chart(result: BenchmarkResult) -> str:
    """Compare embedding models: for each strategy, show NDCG@10 across models.

    Helps answer: does the embedding model choice matter more or less than
    the chunking strategy?
    """
    by_sm: dict[tuple[str, str], list] = defaultdict(list)
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
        fig.add_trace(go.Bar(
            name=model, x=strategies, y=values,
            text=[f"{v:.3f}" for v in values], textposition="auto",
        ))

    fig.update_layout(
        title="NDCG@10 by Strategy and Embedding Model",
        barmode="group", yaxis_title="NDCG@10", yaxis_range=[0, 1.05],
        template="plotly_white", height=450,
    )
    return pio.to_html(fig, full_html=False, include_plotlyjs=False)


def _drm_chart(result: BenchmarkResult) -> str:
    """Bar chart showing Document Retrieval Mismatch rate per strategy."""
    by_strategy: dict[str, list] = defaultdict(list)
    for rm in result.retrieval_metrics:
        by_strategy[rm.strategy.value].append(rm)

    strategies = sorted(by_strategy.keys())
    drm_rates = []
    for strat in strategies:
        items = by_strategy[strat]
        rate = sum(1 for m in items if m.drm_hit) / len(items) * 100 if items else 0
        drm_rates.append(rate)

    fig = go.Figure(go.Bar(
        x=strategies, y=drm_rates,
        text=[f"{v:.1f}%" for v in drm_rates], textposition="auto",
        marker_color=["#16a34a" if v < 10 else "#dc2626" for v in drm_rates],
    ))
    fig.update_layout(
        title="Document Retrieval Mismatch Rate (lower = better)",
        yaxis_title="DRM Rate (%)", template="plotly_white", height=350,
    )
    return pio.to_html(fig, full_html=False, include_plotlyjs=False)
```

### Update `_build_context()` to include new charts

```python
def _build_context(result: BenchmarkResult) -> dict[str, Any]:
    context = {
        # ... existing fields from Day 13 ...
        # Retrieval charts (one per model)
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
```

### Update Jinja2 Template — Retrieval Section

Add after the structural section in `report.html.j2`:

```html
{% if has_retrieval %}
<h2>Retrieval Quality Metrics</h2>

{% for model, chart_html in retrieval_charts.items() %}
<h3>{{ model }}</h3>
<div class="chart-container">
    {{ chart_html | safe }}
</div>
{% endfor %}

<h3>Embedding Model Comparison</h3>
<div class="chart-container">
    {{ model_comparison_html | safe }}
</div>

<h3>Document Retrieval Mismatch</h3>
<div class="chart-container">
    {{ drm_chart_html | safe }}
</div>

<h3>Per-Document Retrieval Breakdown</h3>
<!-- Group retrieval metrics by document, showing each strategy's average -->
<table>
    <thead>
        <tr>
            <th>Document</th>
            <th>Strategy</th>
            <th>Model</th>
            <th>P@5</th>
            <th>R@10</th>
            <th>MRR</th>
            <th>NDCG@10</th>
        </tr>
    </thead>
    <tbody>
        {% for rm in retrieval_metrics %}
        <tr>
            <td>{{ rm.query_id.split('_')[0] if '_' in rm.query_id else rm.query_id }}</td>
            <td>{{ rm.strategy.value }}</td>
            <td>{{ rm.embedding_model.value }}</td>
            <td>{{ "%.3f" | format(rm.precision_at_5) }}</td>
            <td>{{ "%.3f" | format(rm.recall_at_10) }}</td>
            <td>{{ "%.3f" | format(rm.mrr) }}</td>
            <td class="{{ 'metric-good' if rm.ndcg_at_10 > 0.8 else ('metric-bad' if rm.ndcg_at_10 < 0.4 else '') }}">
                {{ "%.3f" | format(rm.ndcg_at_10) }}
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>
{% endif %}

{% if has_significance %}
<h2>Statistical Significance</h2>
<div class="summary-box">
    Paired t-tests compare LexiChunk against each baseline. Results with p &lt; 0.05
    are marked as statistically significant.
</div>
<table>
    <thead>
        <tr>
            <th>Metric</th>
            <th>Baseline</th>
            <th>LexiChunk Mean</th>
            <th>Baseline Mean</th>
            <th>Improvement</th>
            <th>p-value</th>
            <th>Significant?</th>
            <th>Effect Size (d)</th>
        </tr>
    </thead>
    <tbody>
        {% for sr in significance_results %}
        <tr>
            <td>{{ sr.metric_name }}</td>
            <td>{{ sr.strategy_b.value }}</td>
            <td>{{ "%.3f" | format(sr.mean_a) }}</td>
            <td>{{ "%.3f" | format(sr.mean_b) }}</td>
            <td>+{{ "%.1f" | format(sr.improvement_pct) }}%</td>
            <td>{{ "%.4f" | format(sr.p_value) }}</td>
            <td><span class="badge {{ 'badge-sig' if sr.significant else 'badge-nosig' }}">
                {{ "YES" if sr.significant else "NO" }}
            </span></td>
            <td>{{ "%.2f" | format(sr.effect_size) }}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>
{% endif %}

<h2>Methodology</h2>
<h3>Metrics Definitions</h3>
<dl>
    <dt><strong>Clause Fragmentation Rate</strong></dt>
    <dd>Fraction of logical clauses (per LexiChunk parser) that are split across
    multiple chunks. 0.0 = no fragmentation (best). Threshold: 80% word overlap.</dd>

    <dt><strong>Definition Preservation Rate</strong></dt>
    <dd>Fraction of defined terms whose definition context appears in at least
    one chunk. 1.0 = all preserved (best).</dd>

    <dt><strong>Cross-Reference Resolution Rate</strong></dt>
    <dd>Fraction of cross-references (e.g., "as defined in Section 3.2") where
    both the reference and its target appear in the same or adjacent chunks. 1.0 = all resolved.</dd>

    <dt><strong>Hierarchy Depth Retained</strong></dt>
    <dd>Ratio of maximum section numbering depth in chunks vs the original document.
    1.0 = full depth preserved.</dd>

    <dt><strong>Precision@k</strong></dt>
    <dd>Fraction of top-k retrieved chunks that are relevant. P@k = |relevant in top-k| / k.</dd>

    <dt><strong>Recall@k</strong></dt>
    <dd>Fraction of all relevant chunks found in top-k. R@k = |relevant in top-k| / |total relevant|.</dd>

    <dt><strong>MRR (Mean Reciprocal Rank)</strong></dt>
    <dd>1 / rank of the first relevant result, averaged across queries.</dd>

    <dt><strong>NDCG@10 (Normalized Discounted Cumulative Gain)</strong></dt>
    <dd>Information retrieval metric using graded relevance (3=exact, 2=same section, 1=related).
    Rewards placing highly relevant results at the top. Formula: DCG@k / IDCG@k.</dd>

    <dt><strong>DRM Rate (Document Retrieval Mismatch)</strong></dt>
    <dd>Fraction of top-k results from documents other than the query's target.
    Measures cross-document confusion in multi-document indices.</dd>
</dl>

<h3>Statistical Testing</h3>
<p>Paired t-tests (scipy.stats.ttest_rel) compare per-query metric values between
LexiChunk and each baseline. Significance threshold: alpha = 0.05. Effect size
reported as Cohen's d (small: 0.2, medium: 0.5, large: 0.8).</p>

<h3>References</h3>
<ul>
    <li>Anthropic. "Contextual Retrieval." 2024.</li>
    <li>Manning, Raghavan, Schutze. "Introduction to Information Retrieval." Cambridge UP.</li>
    <li>Jarvelin, Kekalainen. "Cumulated Gain-Based Evaluation of IR Techniques." ACM TOIS, 2002.</li>
</ul>
```

### Wire `make report` in `__main__.py`

Update the `report` command to:
1. Load results from the most recent JSON export, or
2. Run a fresh benchmark if no results exist.

```python
def run_report(args: argparse.Namespace) -> None:
    """Generate HTML report from existing benchmark results."""
    from scaffolder.reporting.html import render_html_report
    from scaffolder.reporting.json_export import load_json

    # Try to load existing results
    json_path = args.output_dir / "full_benchmark.json"
    if not json_path.exists():
        json_path = args.output_dir / "structural_benchmark.json"

    if json_path.exists():
        logger.info("Loading results from %s", json_path)
        data = load_json(json_path)
        result = _reconstruct_benchmark_result(data)
    else:
        logger.info("No existing results found, running fresh benchmark.")
        # Run benchmark first
        result = _run_full_benchmark()

    output_path = args.output_dir / "report.html"
    render_html_report(result, output_path)
    print(f"HTML report generated: {output_path}")
```

Coordinate with Agent B: `make report` should run `python -m scaffolder report --json -v`.

## Outputs
- `src/scaffolder/reporting/html.py` (extended with retrieval charts)
- `src/scaffolder/reporting/templates/report.html.j2` (complete template)
- `src/scaffolder/__main__.py` (added `report` command)
- `tests/test_html_report.py` (extended)

## Acceptance Criteria
1. `make report` generates `results/report.html`.
2. Opening the HTML file shows all sections: structural, retrieval, significance, methodology.
3. All Plotly charts are interactive (hover, zoom).
4. Significance badges show green YES / red NO correctly.
5. Methodology section has complete metric definitions.
6. `pytest tests/test_html_report.py -v` -- all tests pass.
7. `mypy src/scaffolder/reporting/ --strict` passes.

## Handoff Notes
- **To Agent B:** `make report` is now wired. It generates `results/report.html`. Add this target to the Makefile if not already present.
- **To Day 15:** The report is complete. Day 15 writes `docs/metrics.md` with formal definitions and runs a final sanity check on all numbers.
- **Template extensibility:** The Jinja2 template can be customized by replacing `report.html.j2`. The context dict passed to the template is the API contract between the renderer and the template.
