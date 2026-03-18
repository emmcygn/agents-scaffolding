# Agent A — Day 13: HTML Report Template (Part 1)

## Mission
Build the Jinja2-based HTML report template with structural metrics comparison tables and inline Plotly charts, producing a self-contained HTML file that stakeholders can view without any server.

## Context
All metrics, benchmarks, and comparisons are complete (Days 1-12). The CLI and JSON outputs exist. Now we build the polished HTML report. This is split across Day 13 (structure + structural metrics + charts) and Day 14 (retrieval section + per-document breakdown + methodology).

Agent B is working on Streamlit components today. No dependency.

## Prerequisites
- `src/scaffolder/models.py` with `BenchmarkResult` containing all metric types
- `src/scaffolder/reporting/json_export.py` with serializable results
- `jinja2` installed
- `plotly` installed
- `src/scaffolder/reporting/templates/` directory exists

## Checklist
- [ ] Create Jinja2 template `src/scaffolder/reporting/templates/report.html.j2`
- [ ] Implement `render_html_report()` in `src/scaffolder/reporting/html.py`
- [ ] Build Plotly chart generators for structural metrics
- [ ] Strategy comparison bar charts (grouped by metric)
- [ ] Per-document heatmap
- [ ] Write tests for HTML rendering

## Implementation Details

### HTML Report Renderer (`src/scaffolder/reporting/html.py`)

```python
"""HTML report generator using Jinja2 templates and Plotly charts."""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

import plotly.graph_objects as go
import plotly.io as pio
from jinja2 import Environment, FileSystemLoader

from scaffolder.models import BenchmarkResult, StructuralMetrics, StrategyName

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).parent / "templates"


def render_html_report(
    result: BenchmarkResult,
    output_path: Path,
) -> None:
    """Render a full HTML report from benchmark results.

    The output is a self-contained HTML file with:
    - Inline CSS (no external dependencies)
    - Inline Plotly charts (plotly.js included via CDN)
    - Structural metrics tables and charts
    - Retrieval metrics (Day 14)
    - Methodology section (Day 14)

    Args:
        result: Complete BenchmarkResult from a benchmark run.
        output_path: Where to write the HTML file.
    """
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=True,
    )
    template = env.get_template("report.html.j2")

    # Prepare template context
    context = _build_context(result)

    html = template.render(**context)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    logger.info("HTML report written to %s", output_path)


def _build_context(result: BenchmarkResult) -> dict[str, Any]:
    """Build the template context from benchmark results."""
    return {
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
    }


def _structural_bar_chart(result: BenchmarkResult) -> str:
    """Generate grouped bar chart comparing structural metrics across strategies.

    X-axis: strategies
    Groups: fragmentation rate, def preservation, xref resolution, hierarchy depth
    """
    by_strategy: dict[str, list[StructuralMetrics]] = defaultdict(list)
    for sm in result.structural_metrics:
        by_strategy[sm.strategy.value].append(sm)

    strategies = sorted(by_strategy.keys())

    metrics_config = [
        ("Clause Fragmentation", "clause_fragmentation_rate", True),
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
            # For fragmentation (lower is better), show 1-value so all bars
            # point the same direction (higher = better)
            if invert:
                avg = 1.0 - avg
                label_mod = f"{label} (1-rate)"
            else:
                label_mod = label
            values.append(avg)

        fig.add_trace(go.Bar(
            name=label if not invert else f"{label} (1-rate)",
            x=strategies,
            y=values,
            text=[f"{v:.3f}" for v in values],
            textposition="auto",
        ))

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
    """Generate heatmap: strategies x documents, colored by composite score.

    Composite = avg(1-fragmentation, def_preservation, xref_resolution, hierarchy_depth)
    """
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

    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=documents,
        y=strategies,
        colorscale="RdYlGn",
        zmin=0,
        zmax=1,
        text=z,
        texttemplate="%{text:.3f}",
    ))

    fig.update_layout(
        title="Structural Quality Composite Score (strategy x document)",
        height=400,
        template="plotly_white",
    )

    return pio.to_html(fig, full_html=False, include_plotlyjs=False)
```

### Jinja2 Template (`src/scaffolder/reporting/templates/report.html.j2`)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LexiChunk Benchmark Report</title>
    <style>
        :root {
            --primary: #2563eb;
            --success: #16a34a;
            --warning: #d97706;
            --danger: #dc2626;
            --bg: #ffffff;
            --text: #1f2937;
            --border: #e5e7eb;
            --code-bg: #f3f4f6;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
            color: var(--text);
            line-height: 1.6;
        }
        h1 { color: var(--primary); border-bottom: 2px solid var(--primary); padding-bottom: 0.5rem; }
        h2 { color: var(--primary); margin-top: 2rem; }
        h3 { color: #4b5563; }
        table { border-collapse: collapse; width: 100%; margin: 1rem 0; }
        th { background: var(--primary); color: white; padding: 0.75rem; text-align: left; }
        td { padding: 0.75rem; border-bottom: 1px solid var(--border); }
        tr:hover { background: #f9fafb; }
        .metric-good { color: var(--success); font-weight: bold; }
        .metric-bad { color: var(--danger); font-weight: bold; }
        .metric-ok { color: var(--warning); }
        .summary-box {
            background: #eff6ff;
            border-left: 4px solid var(--primary);
            padding: 1rem 1.5rem;
            margin: 1rem 0;
            border-radius: 0 8px 8px 0;
        }
        .chart-container { margin: 2rem 0; }
        .timestamp { color: #6b7280; font-size: 0.875rem; }
        .badge {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: bold;
        }
        .badge-sig { background: #dcfce7; color: #166534; }
        .badge-nosig { background: #fee2e2; color: #991b1b; }
    </style>
</head>
<body>
    <h1>LexiChunk Benchmark Report</h1>
    <p class="timestamp">Generated: {{ timestamp }}</p>
    <p>Strategies: {{ strategies | join(', ') }} | Documents: {{ documents | length }}</p>

    <div class="summary-box">
        <strong>Summary:</strong> This report compares LexiChunk's legal document chunking
        against general-purpose alternatives across structural quality and retrieval metrics.
    </div>

    <h2>Structural Quality Metrics</h2>
    <div class="chart-container">
        {{ structural_chart_html | safe }}
    </div>

    <h3>Strategy x Document Heatmap</h3>
    <div class="chart-container">
        {{ structural_heatmap_html | safe }}
    </div>

    <h3>Detailed Structural Metrics</h3>
    <table>
        <thead>
            <tr>
                <th>Strategy</th>
                <th>Document</th>
                <th>Fragmentation</th>
                <th>Def Preservation</th>
                <th>XRef Resolution</th>
                <th>Hierarchy Depth</th>
                <th>Size CV</th>
                <th>Chunks</th>
            </tr>
        </thead>
        <tbody>
            {% for sm in structural_metrics %}
            <tr>
                <td>{{ sm.strategy.value }}</td>
                <td>{{ sm.document_id }}</td>
                <td class="{{ 'metric-good' if sm.clause_fragmentation_rate < 0.1 else ('metric-bad' if sm.clause_fragmentation_rate > 0.5 else 'metric-ok') }}">
                    {{ "%.3f" | format(sm.clause_fragmentation_rate) }}
                </td>
                <td class="{{ 'metric-good' if sm.definition_preservation_rate > 0.9 else ('metric-bad' if sm.definition_preservation_rate < 0.5 else 'metric-ok') }}">
                    {{ "%.3f" | format(sm.definition_preservation_rate) }}
                </td>
                <td class="{{ 'metric-good' if sm.cross_ref_resolution_rate > 0.9 else ('metric-bad' if sm.cross_ref_resolution_rate < 0.5 else 'metric-ok') }}">
                    {{ "%.3f" | format(sm.cross_ref_resolution_rate) }}
                </td>
                <td>{{ "%.3f" | format(sm.hierarchy_depth_retained) }}</td>
                <td>{{ "%.2f" | format(sm.chunk_size_cv) }}</td>
                <td>{{ sm.chunk_count }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    {% if has_retrieval %}
    <!-- Retrieval section added Day 14 -->
    <h2>Retrieval Quality Metrics</h2>
    <p><em>See Day 14 for retrieval metrics section.</em></p>
    {% endif %}

    {% if has_significance %}
    <!-- Significance section added Day 14 -->
    <h2>Statistical Significance</h2>
    <p><em>See Day 14 for significance section.</em></p>
    {% endif %}

    <footer style="margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--border); color: #6b7280; font-size: 0.875rem;">
        Generated by sdk-scaffolder | LexiChunk Evaluation Harness
    </footer>
</body>
</html>
```

### Tests

```python
# tests/test_html_report.py

# 1. render_html_report() produces a valid HTML file
# 2. Output contains "LexiChunk Benchmark Report" title
# 3. Output contains all strategy names
# 4. Output contains structural metrics table rows
# 5. Output contains Plotly chart divs
# 6. File is written to the specified path
# 7. Parent directories are created if missing

# Use a minimal BenchmarkResult with 2 strategies and 1 document
```

## Outputs
- `src/scaffolder/reporting/html.py`
- `src/scaffolder/reporting/templates/report.html.j2`
- `tests/test_html_report.py`

## Acceptance Criteria
1. `render_html_report(result, Path("results/report.html"))` produces a self-contained HTML file.
2. Opening the file in a browser shows: title, summary, structural bar chart, heatmap, detailed table.
3. Charts are interactive (Plotly hover, zoom).
4. `pytest tests/test_html_report.py -v` -- all tests pass.
5. `mypy src/scaffolder/reporting/html.py --strict` passes.
6. `ruff check src/scaffolder/reporting/` passes.

## Handoff Notes
- **To Day 14:** The template has placeholder sections for retrieval metrics, per-document breakdown, significance, and methodology. Day 14 fills these in.
- **To Agent B:** The HTML report is self-contained (no server needed). The Streamlit dashboard and HTML report serve different audiences: dashboard for interactive exploration, HTML for static sharing.
- **Template note:** Plotly.js is loaded from CDN (`include_plotlyjs="cdn"`). For the first chart, set `include_plotlyjs="cdn"`. For subsequent charts, use `include_plotlyjs=False` to avoid loading the library multiple times.
