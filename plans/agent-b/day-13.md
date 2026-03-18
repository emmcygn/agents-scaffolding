# Agent B — Day 13: Filtered Retrieval Demo & Export Functionality

## Mission
Build a filtered retrieval demo showcasing LexiChunk's unique clause_type metadata for targeted retrieval (something baselines cannot do), and add export functionality so users can download results JSON and HTML reports from the dashboard.

## Context
Day 12 completed the metrics dashboard. The filtered retrieval demo is a compelling differentiator: LexiChunk tags each chunk with a clause type (e.g., "indemnification", "termination"), enabling filtered retrieval that general-purpose chunkers cannot support. This is a powerful "only LexiChunk can do this" feature. The export functionality lets users take results offline.

## Prerequisites
- `src/scaffolder/dashboard/` with all three pages functional (Days 7-12)
- `src/scaffolder/reporting/json_export.py` (Day 5)
- `src/scaffolder/reporting/html.py` (Agent A)
- LexiChunk `Chunk.metadata["clause_type"]` populated (Agent A's pipeline)
- `src/scaffolder/dashboard/components.py` with chunk viewer (Day 8)

## Checklist
- [ ] Task 1 — Add filtered retrieval section to page_retrieval.py
- [ ] Task 2 — Implement clause-type filtering against FAISS results
- [ ] Task 3 — Show that baselines cannot perform filtered retrieval (no metadata)
- [ ] Task 4 — Add JSON download button to metrics dashboard
- [ ] Task 5 — Add HTML report generation and download
- [ ] Task 6 — Add export section to sidebar (available from any page)

## Implementation Details

### Filtered retrieval section in page_retrieval.py

Add a new section below the regular retrieval results:

```python
def _render_filtered_retrieval(doc_id: str, model: str) -> None:
    """Render the filtered retrieval demo.

    Shows that LexiChunk's clause_type metadata enables targeted retrieval
    that baselines cannot perform.
    """
    st.markdown("---")
    st.subheader("Filtered Retrieval (LexiChunk Exclusive)")
    st.markdown(
        "LexiChunk tags each chunk with a clause type, enabling **targeted retrieval** "
        "that general-purpose chunkers cannot support. Select a clause type to find "
        "all matching chunks across the document."
    )

    # Clause type selection
    clause_types = [
        "definitions", "termination", "payment", "indemnification",
        "limitation_of_liability", "confidentiality", "intellectual_property",
        "data_protection", "governing_law", "dispute_resolution",
        "force_majeure", "warranties", "obligations", "notices",
    ]

    selected_type = st.selectbox(
        "Clause type to find",
        options=clause_types,
        key="filter_clause_type",
        help="Find all chunks classified as this clause type",
    )

    if st.button("Find Clauses", key="filter_search"):
        # Get LexiChunk chunks from cache
        chunk_set_key = f"chunks_{doc_id}_lexichunk"
        chunk_set = st.session_state.get(chunk_set_key)

        if chunk_set is None:
            # Need to chunk first
            with st.spinner("Chunking with LexiChunk..."):
                from scaffolder.fixtures import FixtureManager
                from scaffolder.chunking.pipeline import ChunkingPipeline

                manager = FixtureManager()
                document = manager.load(doc_id)
                pipeline = ChunkingPipeline()
                chunk_set = pipeline.chunk(document, "lexichunk")
                st.session_state[chunk_set_key] = chunk_set

        # Filter chunks by clause type
        matching = [
            c for c in chunk_set.chunks
            if c.metadata.get("clause_type") == selected_type
        ]

        # Display results
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**LexiChunk: {len(matching)} matching chunks**")
            if matching:
                for i, chunk in enumerate(matching):
                    confidence = chunk.metadata.get("clause_confidence", 0)
                    with st.expander(
                        f"{selected_type} — Confidence: {confidence:.0%}",
                        expanded=i < 3,
                    ):
                        hierarchy = chunk.metadata.get("hierarchy_path", "")
                        if hierarchy:
                            st.caption(f"Path: {hierarchy}")
                        st.text(chunk.text[:800])
            else:
                st.info(f"No {selected_type} clauses found in this document.")

        with col2:
            st.markdown("**Baseline: Not possible**")
            st.warning(
                f"Baseline chunkers do not classify chunk types. "
                f"There is no way to filter for '{selected_type}' clauses "
                f"without LexiChunk's metadata. A keyword search for "
                f"'{selected_type.replace('_', ' ')}' would miss clauses "
                f"that don't contain the exact phrase."
            )

            # Show what keyword search would find (imprecise alternative)
            baseline_key = f"chunks_{doc_id}_langchain_rcts"
            baseline_set = st.session_state.get(baseline_key)
            if baseline_set:
                keyword = selected_type.replace("_", " ")
                keyword_matches = [
                    c for c in baseline_set.chunks
                    if keyword.lower() in c.text.lower()
                ]
                st.caption(
                    f"Naive keyword search for '{keyword}' in baseline chunks: "
                    f"{len(keyword_matches)} matches (likely imprecise)"
                )
```

### Add filtered retrieval to the page render flow

In `render_page()`, after the results section:

```python
# At the end of render_page(), add:
if st.session_state.get("ret_results"):
    _render_filtered_retrieval(doc_id, model)
```

### Export functionality: sidebar download buttons

Add to `components.py`:

```python
def render_export_section() -> None:
    """Render export buttons in the sidebar.

    Provides download buttons for JSON results and HTML report.
    Only active when benchmark results are available.
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Export**")

    result_data = st.session_state.get("benchmark_result")

    if result_data is None:
        st.sidebar.caption("Run a benchmark to enable exports.")
        return

    # JSON download
    import json
    json_str = json.dumps(result_data, indent=2)
    st.sidebar.download_button(
        label="Download JSON",
        data=json_str,
        file_name="scaffolder_results.json",
        mime="application/json",
        key="export_json",
    )

    # HTML report download
    try:
        html_str = _generate_html_report(result_data)
        st.sidebar.download_button(
            label="Download HTML Report",
            data=html_str,
            file_name="scaffolder_report.html",
            mime="text/html",
            key="export_html",
        )
    except Exception as e:
        st.sidebar.caption(f"HTML export unavailable: {e}")


def _generate_html_report(data: dict) -> str:
    """Generate HTML report from benchmark results.

    Uses Agent A's Jinja2 template if available, falls back to
    a minimal HTML report.
    """
    try:
        from scaffolder.reporting.html import render_html_report
        return render_html_report(data)
    except ImportError:
        # Fallback: generate minimal HTML
        import json
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Scaffolder Benchmark Report</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }}
        h1 {{ color: #1a237e; }}
        pre {{ background: #f5f5f5; padding: 1rem; border-radius: 4px; overflow-x: auto; }}
        .metric {{ display: inline-block; padding: 1rem; margin: 0.5rem; background: #e3f2fd; border-radius: 8px; }}
        .metric .value {{ font-size: 2rem; font-weight: bold; color: #1565c0; }}
        .metric .label {{ font-size: 0.9rem; color: #666; }}
    </style>
</head>
<body>
    <h1>LexiChunk Scaffolder Report</h1>
    <p>Generated from benchmark results</p>

    <h2>Raw Results</h2>
    <pre>{json.dumps(data, indent=2)}</pre>
</body>
</html>"""
```

### Wire export into app.py

In `app.py`, after the page routing:

```python
# After the page routing block:
from scaffolder.dashboard.components import render_export_section
render_export_section()
```

## Outputs
- `src/scaffolder/dashboard/page_retrieval.py` (updated: filtered retrieval section)
- `src/scaffolder/dashboard/components.py` (updated: export functions)
- `src/scaffolder/dashboard/app.py` (updated: export section in sidebar)

## Acceptance Criteria
1. Filtered retrieval: select "indemnification" clause type → see matching LexiChunk chunks on the left, "Not possible" warning on the right
2. Filtered retrieval shows clause confidence scores
3. JSON download button downloads valid JSON
4. HTML download button generates a viewable HTML file
5. Export buttons are disabled/hidden when no results are loaded
6. Keyword search comparison shows that naive matching is imprecise
7. `make lint` passes

## Handoff Notes
- **To Agent A:** The filtered retrieval demo depends on `Chunk.metadata["clause_type"]` being a string from the known set (see Day 8's colour palette). If LexiChunk returns different type names, update the `clause_types` list in the filtered retrieval section. Also, the HTML export tries to import `scaffolder.reporting.html.render_html_report(data: dict) -> str` — implement this when building the Jinja2 template.
- **To Day 14:** Dashboard is feature-complete. Day 14 focuses on deployment: testing on Streamlit Community Cloud, creating `requirements-dashboard.txt`, and ensuring graceful degradation without local models.
- **Decision:** The filtered retrieval demo is intentionally asymmetric — LexiChunk side shows results, baseline side shows a warning. This makes the value proposition visceral: "only LexiChunk can do this."
