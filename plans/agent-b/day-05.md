# Agent B — Day 05: JSON Export, CLI Polish & Streamlit Skeleton

## Mission
Complete the JSON export module, polish the CLI reporter with summary output, and build the Streamlit multi-page skeleton so dashboard development can proceed in parallel with Agent A's retrieval pipeline.

## Context
Day 4 completed query annotations (20+ queries across 5 fixtures) and began the CLI reporter with structural metric tables. Agent A has delivered `ChunkingPipeline` — it can chunk documents using all 4 strategies and return `ChunkSet` objects. Today we add JSON export (the machine-readable output format), polish the CLI, and create the Streamlit app skeleton. The Streamlit pages will be stubs with headers and layout, fleshed out on Days 7-9.

## Prerequisites
- `src/scaffolder/reporting/cli.py` exists with `render_structural_table()` (Day 4)
- `src/scaffolder/models.py` with all data contracts (Agent A, Day 1)
- `src/scaffolder/chunking/pipeline.py` with `ChunkingPipeline` (Agent A, Day 3)
- `pyproject.toml` has `streamlit` and `plotly` in `[dashboard]` extras

## Checklist
- [ ] Task 1 — Create `src/scaffolder/reporting/json_export.py`
- [ ] Task 2 — Polish CLI reporter: add `render_benchmark()` entry point that chains header + structural + summary
- [ ] Task 3 — Create `src/scaffolder/dashboard/app.py` — multi-page Streamlit app
- [ ] Task 4 — Create `src/scaffolder/dashboard/page_compare.py` — stub with layout
- [ ] Task 5 — Create `src/scaffolder/dashboard/page_retrieval.py` — stub with layout
- [ ] Task 6 — Create `src/scaffolder/dashboard/components.py` — shared component stubs
- [ ] Task 7 — Write `tests/test_json_export.py`

## Implementation Details

### JSON export: src/scaffolder/reporting/json_export.py

```python
"""JSON export for benchmark results."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from scaffolder.models import BenchmarkResult


def _serialize(obj: Any) -> Any:
    """Custom serializer for dataclass fields."""
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, set):
        return sorted(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def export_json(
    result: BenchmarkResult,
    output_path: str | Path,
    indent: int = 2,
) -> Path:
    """Export benchmark results to a JSON file.

    Args:
        result: The complete benchmark result to export.
        output_path: Path to write the JSON file. Parent dirs are created.
        indent: JSON indentation level.

    Returns:
        The Path where the file was written.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = asdict(result)

    with open(output_path, "w") as f:
        json.dump(data, f, indent=indent, default=_serialize)

    return output_path


def export_json_string(result: BenchmarkResult, indent: int = 2) -> str:
    """Export benchmark results as a JSON string.

    Useful for Streamlit download buttons and API responses.
    """
    data = asdict(result)
    return json.dumps(data, indent=indent, default=_serialize)


def load_json(path: str | Path) -> dict[str, Any]:
    """Load a previously exported benchmark result from JSON.

    Returns the raw dict — caller is responsible for reconstructing
    dataclass instances if needed.
    """
    with open(path) as f:
        return json.load(f)  # type: ignore[no-any-return]
```

### CLI reporter polish

Add to `src/scaffolder/reporting/cli.py`:

```python
def render_aggregate_summary(
    result: BenchmarkResult,
    console: Console | None = None,
) -> None:
    """Render aggregate summary comparing strategies across all documents."""
    if console is None:
        console = Console()

    summary = result.summary
    if not summary:
        return

    table = Table(
        title="Aggregate Summary (averaged across all documents)",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Strategy", style="bold")
    table.add_column("Avg Clause Frag.", justify="right")
    table.add_column("Avg Def. Preserv.", justify="right")
    table.add_column("Avg XRef Resol.", justify="right")
    table.add_column("Avg Hierarchy", justify="right")

    for strategy, metrics in sorted(summary.items()):
        if not isinstance(metrics, dict):
            continue
        table.add_row(
            strategy,
            f"{metrics.get('avg_clause_fragmentation_rate', 0):.3f}",
            f"{metrics.get('avg_definition_preservation_rate', 0):.3f}",
            f"{metrics.get('avg_cross_ref_resolution_rate', 0):.3f}",
            f"{metrics.get('avg_hierarchy_depth_retained', 0):.2f}",
        )

    console.print(table)
    console.print()


def render_benchmark(
    result: BenchmarkResult,
    console: Console | None = None,
) -> None:
    """Full CLI benchmark output: header + structural + summary.

    This is the main entry point for CLI rendering. Day 10 adds
    retrieval metrics rendering between structural and summary.
    """
    if console is None:
        console = Console()

    render_summary_header(result, console)
    render_structural_table(result.structural_results, console)
    render_aggregate_summary(result, console)

    # Output file paths
    if result.config.get("output_json"):
        console.print(
            f"[dim]JSON results written to: {result.config.get('output_dir', 'results')}/[/dim]"
        )
```

### Streamlit app skeleton: src/scaffolder/dashboard/app.py

```python
"""Streamlit multi-page dashboard for scaffolder results."""

from __future__ import annotations

import streamlit as st


def main() -> None:
    """Configure and launch the Streamlit dashboard."""
    st.set_page_config(
        page_title="LexiChunk Scaffolder",
        page_icon="(scale-icon)",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Sidebar navigation
    st.sidebar.title("LexiChunk Scaffolder")
    st.sidebar.markdown("---")

    page = st.sidebar.radio(
        "Navigate",
        options=["Compare Chunks", "Retrieval Demo", "Metrics Dashboard"],
        index=0,
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "**Settings**",
    )

    # Global settings in sidebar
    if "config" not in st.session_state:
        st.session_state.config = {
            "strategies": ["lexichunk", "langchain_rcts", "sentence_split", "fixed_512"],
            "embedding_model": "all-MiniLM-L6-v2",
        }

    # Strategy multi-select
    selected_strategies = st.sidebar.multiselect(
        "Strategies",
        options=["lexichunk", "langchain_rcts", "sentence_split", "fixed_512"],
        default=["lexichunk", "langchain_rcts"],
    )
    st.session_state.config["strategies"] = selected_strategies

    # Route to pages
    if page == "Compare Chunks":
        from scaffolder.dashboard.page_compare import render_page
        render_page()
    elif page == "Retrieval Demo":
        from scaffolder.dashboard.page_retrieval import render_page
        render_page()
    elif page == "Metrics Dashboard":
        # Stub for Day 12
        st.title("Metrics Dashboard")
        st.info("Coming soon — metrics summary panels and comparison charts.")


if __name__ == "__main__":
    main()
```

### Page stubs

**src/scaffolder/dashboard/page_compare.py:**

```python
"""Page 1: Side-by-side chunk comparison."""

from __future__ import annotations

import streamlit as st


def render_page() -> None:
    """Render the chunk comparison page."""
    st.title("Chunk Comparison")
    st.markdown(
        "Compare how LexiChunk and baseline chunkers split the same legal document."
    )

    # Document selection
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Document")
        doc_source = st.radio(
            "Source",
            options=["Built-in fixture", "Upload file", "Paste text"],
            horizontal=True,
        )

        if doc_source == "Built-in fixture":
            fixture = st.selectbox(
                "Select fixture",
                options=[
                    "uk_service_agreement",
                    "uk_terms_conditions",
                    "us_msa",
                    "us_terms_of_service",
                    "eu_gdpr_excerpt",
                ],
            )
            st.info(f"Selected: {fixture}")

        elif doc_source == "Upload file":
            uploaded = st.file_uploader(
                "Upload a .txt file", type=["txt"]
            )
            if uploaded:
                st.success(f"Uploaded: {uploaded.name}")

        elif doc_source == "Paste text":
            text = st.text_area(
                "Paste legal text",
                height=200,
                placeholder="Paste your legal document text here...",
            )

    with col2:
        st.subheader("Compare Against")
        baseline = st.selectbox(
            "Baseline strategy",
            options=["langchain_rcts", "sentence_split", "fixed_512"],
        )

    # Placeholder for chunk display (Day 7)
    st.markdown("---")
    st.subheader("Results")

    left, right = st.columns(2)
    with left:
        st.markdown("**LexiChunk**")
        st.info("Run chunking to see results (implemented Day 7)")
    with right:
        st.markdown(f"**{baseline}**")
        st.info("Run chunking to see results (implemented Day 7)")

    # Chunking button
    if st.button("Run Chunking", type="primary"):
        st.warning("Chunking pipeline integration coming Day 7")
```

**src/scaffolder/dashboard/page_retrieval.py:**

```python
"""Page 2: Retrieval demo — query against chunked documents."""

from __future__ import annotations

import streamlit as st


def render_page() -> None:
    """Render the retrieval demo page."""
    st.title("Retrieval Demo")
    st.markdown(
        "Ask a legal question and compare retrieval results across chunking strategies."
    )

    # Query input
    query = st.text_input(
        "Legal question",
        placeholder="e.g., What are the termination provisions?",
    )

    # Settings row
    col1, col2, col3 = st.columns(3)
    with col1:
        doc_filter = st.selectbox(
            "Document",
            options=[
                "All documents",
                "uk_service_agreement",
                "uk_terms_conditions",
                "us_msa",
                "us_terms_of_service",
                "eu_gdpr_excerpt",
            ],
        )
    with col2:
        k = st.slider("Top-k results", min_value=1, max_value=20, value=5)
    with col3:
        model = st.selectbox(
            "Embedding model",
            options=["all-MiniLM-L6-v2", "bge-base-en-v1.5"],
        )

    # Search button
    if st.button("Search", type="primary"):
        if not query:
            st.warning("Please enter a query.")
        else:
            st.info("Retrieval pipeline integration coming Day 9")

    # Placeholder results
    st.markdown("---")
    st.subheader("Results")
    st.info("Results will appear here after retrieval is implemented (Day 9)")
```

**src/scaffolder/dashboard/components.py:**

```python
"""Shared Streamlit components for the dashboard."""

from __future__ import annotations

from typing import TYPE_CHECKING

import streamlit as st

if TYPE_CHECKING:
    from scaffolder.models import Chunk, ChunkSet


def render_chunk_card(chunk: Chunk, index: int) -> None:
    """Render a single chunk as an expandable card.

    Shows chunk text, metadata, and styling based on clause type.
    Full implementation on Day 8.
    """
    with st.expander(f"Chunk {index + 1}", expanded=index < 3):
        st.text(chunk.text[:500] + ("..." if len(chunk.text) > 500 else ""))
        if chunk.metadata:
            st.json(chunk.metadata)


def render_chunk_list(chunk_set: ChunkSet) -> None:
    """Render a list of chunks with summary stats.

    Full implementation on Day 8.
    """
    st.metric("Chunks", chunk_set.chunk_count)
    st.metric("Avg size (tokens)", f"{chunk_set.avg_chunk_size:.0f}")
    st.metric("Time (ms)", f"{chunk_set.duration_ms:.1f}")

    for i, chunk in enumerate(chunk_set.chunks):
        render_chunk_card(chunk, i)


def render_metric_card(
    label: str,
    value: float,
    delta: float | None = None,
    fmt: str = ".3f",
) -> None:
    """Render a metric card with optional delta.

    Full implementation on Day 12.
    """
    formatted = f"{value:{fmt}}"
    if delta is not None:
        st.metric(label, formatted, delta=f"{delta:+{fmt}}")
    else:
        st.metric(label, formatted)
```

## Outputs
- `src/scaffolder/reporting/json_export.py`
- `src/scaffolder/reporting/cli.py` (updated with `render_benchmark`, `render_aggregate_summary`)
- `src/scaffolder/dashboard/app.py`
- `src/scaffolder/dashboard/page_compare.py`
- `src/scaffolder/dashboard/page_retrieval.py`
- `src/scaffolder/dashboard/components.py`
- `tests/test_json_export.py`

## Acceptance Criteria
1. `python -c "from scaffolder.reporting.json_export import export_json, export_json_string"` imports without error
2. `python -c "from scaffolder.reporting.cli import render_benchmark"` imports without error
3. `streamlit run src/scaffolder/dashboard/app.py` launches without errors (pages show stub content)
4. Sidebar navigation works — switching between "Compare Chunks", "Retrieval Demo", "Metrics Dashboard"
5. `make lint` and `make typecheck` pass on all new files
6. `tests/test_json_export.py` passes — tests serialization and deserialization

## Handoff Notes
- **To Agent A:** The JSON export module is at `scaffolder.reporting.json_export`. Use `export_json(result, "results/benchmark.json")` to write results. The `export_json_string` function is for Streamlit downloads.
- **To Day 6:** Voyage adapter is next. The Streamlit dashboard skeleton is ready — pages are stubs. Day 7 will flesh out page_compare.py with actual ChunkingPipeline integration.
- **Decision:** Streamlit uses `st.sidebar.radio` for page navigation instead of the native multi-page feature — this gives us more control over shared state and sidebar settings.
