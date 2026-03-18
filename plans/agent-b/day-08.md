# Agent B — Day 08: Chunk Viewer Component with Clause-Type Colour Coding

## Mission
Build a rich chunk viewer component that colour-codes chunks by clause type, shows hierarchy breadcrumbs, highlights defined terms, and displays token counts — making the visual difference between LexiChunk and baselines immediately obvious.

## Context
Day 7 built the functional comparison page with basic `st.text()` chunk display. Today we replace that with a polished component that visually demonstrates LexiChunk's advantages: clause type classification, hierarchy tracking, defined term extraction, and cross-reference detection. This is the visual centrepiece of the dashboard — it makes the abstract metrics tangible.

## Prerequisites
- `src/scaffolder/dashboard/components.py` exists with stubs (Day 5)
- `src/scaffolder/dashboard/page_compare.py` functional (Day 7)
- LexiChunk's `Chunk.metadata` populated with: `clause_type`, `clause_confidence`, `hierarchy_path`, `defined_terms`, `cross_refs`, `hierarchy_depth` (Agent A's `ChunkingPipeline`)

## Checklist
- [ ] Task 1 — Define clause type colour palette (24+ clause types)
- [ ] Task 2 — Build `render_chunk_card()` with colour-coded header, hierarchy breadcrumb, and metadata badges
- [ ] Task 3 — Build `render_chunk_list()` with scroll container and summary stats
- [ ] Task 4 — Add defined term highlighting within chunk text using HTML/markdown
- [ ] Task 5 — Add cross-reference indicators
- [ ] Task 6 — Update `page_compare.py` to use the new components
- [ ] Task 7 — Add a chunk statistics comparison chart (bar chart: chunk sizes)

## Implementation Details

### Clause type colour palette

LexiChunk classifies chunks into 24+ clause types. Assign each a colour for visual distinction:

```python
# In components.py

CLAUSE_TYPE_COLORS: dict[str, str] = {
    # Core commercial
    "definitions": "#4CAF50",         # green
    "interpretation": "#66BB6A",      # light green
    "term": "#2196F3",                # blue
    "termination": "#F44336",         # red
    "payment": "#FF9800",             # orange
    "fees": "#FFA726",                # light orange

    # Obligations & liability
    "obligations": "#3F51B5",         # indigo
    "warranties": "#9C27B0",          # purple
    "indemnification": "#E91E63",     # pink
    "limitation_of_liability": "#D32F2F",  # dark red
    "exclusions": "#C62828",          # darker red

    # IP & confidentiality
    "intellectual_property": "#00BCD4", # cyan
    "confidentiality": "#009688",      # teal
    "data_protection": "#00897B",      # dark teal

    # Dispute & governance
    "governing_law": "#795548",       # brown
    "dispute_resolution": "#8D6E63",  # light brown
    "arbitration": "#A1887F",         # lighter brown
    "jurisdiction": "#6D4C41",        # dark brown
    "force_majeure": "#607D8B",       # blue grey

    # Administrative
    "notices": "#78909C",             # light blue grey
    "assignment": "#90A4AE",          # lighter blue grey
    "entire_agreement": "#B0BEC5",    # pale grey
    "amendments": "#546E7A",          # dark blue grey
    "severability": "#455A64",        # darker blue grey
    "waiver": "#37474F",             # darkest blue grey

    # Structure
    "preamble": "#8E24AA",           # dark purple
    "recitals": "#7B1FA2",           # deeper purple
    "schedules": "#5E35B1",          # deep indigo
    "general": "#757575",            # grey (fallback)
}

DEFAULT_CHUNK_COLOR = "#757575"  # grey for unclassified
```

### Enhanced render_chunk_card

```python
def render_chunk_card(
    chunk: Chunk,
    index: int,
    show_metadata: bool = True,
    highlight_terms: bool = True,
) -> None:
    """Render a single chunk as a styled expandable card.

    Features:
    - Colour-coded left border by clause type
    - Hierarchy breadcrumb above the text
    - Defined terms shown as badges
    - Cross-reference indicators
    - Token count and char count in the header
    """
    clause_type = chunk.metadata.get("clause_type", "general")
    confidence = chunk.metadata.get("clause_confidence", 0.0)
    color = CLAUSE_TYPE_COLORS.get(clause_type, DEFAULT_CHUNK_COLOR)

    # Build header label
    char_count = len(chunk.text)
    token_estimate = char_count // 4  # Rough estimate
    header = f"Chunk {index + 1}"
    if clause_type and clause_type != "general":
        header += f" | {clause_type.replace('_', ' ').title()}"
    header += f" | ~{token_estimate} tokens"

    with st.expander(header, expanded=index < 3):
        # Colour bar + hierarchy breadcrumb
        hierarchy_path = chunk.metadata.get("hierarchy_path", "")
        if hierarchy_path:
            st.markdown(
                f'<div style="border-left: 4px solid {color}; padding-left: 8px; '
                f'color: #888; font-size: 0.85em; margin-bottom: 8px;">'
                f'{hierarchy_path}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div style="border-left: 4px solid {color}; padding-left: 8px; '
                f'height: 4px; margin-bottom: 8px;"></div>',
                unsafe_allow_html=True,
            )

        # Defined terms as badges
        defined_terms = chunk.metadata.get("defined_terms", [])
        if defined_terms and show_metadata:
            badges = " ".join(
                f'<span style="background: #E3F2FD; color: #1565C0; '
                f'padding: 2px 8px; border-radius: 12px; font-size: 0.8em; '
                f'margin-right: 4px;">{term}</span>'
                for term in defined_terms[:10]  # Cap at 10 to avoid overflow
            )
            st.markdown(badges, unsafe_allow_html=True)
            st.markdown("")  # Spacing

        # Cross-references
        cross_refs = chunk.metadata.get("cross_refs", [])
        if cross_refs and show_metadata:
            ref_text = ", ".join(str(ref) for ref in cross_refs[:5])
            st.markdown(
                f'<span style="color: #FF8F00; font-size: 0.85em;">'
                f'Cross-refs: {ref_text}</span>',
                unsafe_allow_html=True,
            )

        # Chunk text
        # If highlight_terms is True, bold the defined terms in the text
        display_text = chunk.text
        if highlight_terms and defined_terms:
            display_text = _highlight_terms(display_text, defined_terms)
            st.markdown(display_text, unsafe_allow_html=True)
        else:
            st.text(display_text)

        # Footer metadata
        if show_metadata and confidence > 0:
            st.caption(
                f"Clause confidence: {confidence:.0%} | "
                f"Characters: {char_count:,} | "
                f"Index: {chunk.index}"
            )


def _highlight_terms(text: str, terms: list[str]) -> str:
    """Highlight defined terms in text using HTML bold + colour.

    Uses case-insensitive replacement. Wraps terms in styled spans.
    Returns HTML-safe string for st.markdown(unsafe_allow_html=True).
    """
    import html
    import re

    # Escape HTML entities first
    escaped = html.escape(text)

    # Replace newlines with <br> for HTML display
    escaped = escaped.replace("\n", "<br>")

    # Highlight each term
    for term in terms:
        pattern = re.compile(re.escape(html.escape(term)), re.IGNORECASE)
        replacement = (
            f'<strong style="color: #1565C0; '
            f'background: #E3F2FD;">{html.escape(term)}</strong>'
        )
        escaped = pattern.sub(replacement, escaped)

    return f'<div style="font-family: monospace; white-space: pre-wrap; font-size: 0.9em;">{escaped}</div>'
```

### Enhanced render_chunk_list

```python
def render_chunk_list(
    chunk_set: ChunkSet,
    strategy_label: str = "",
    show_metadata: bool = True,
) -> None:
    """Render a full chunk list with summary stats and scrollable chunks.

    Args:
        chunk_set: The ChunkSet to render.
        strategy_label: Display name for the strategy.
        show_metadata: Whether to show clause types, terms, etc.
            Set to False for baseline strategies that don't have metadata.
    """
    # Summary stats row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Chunks", chunk_set.chunk_count)
    with col2:
        st.metric("Avg Size", f"{chunk_set.avg_chunk_size:.0f} tok")
    with col3:
        st.metric("Time", f"{chunk_set.duration_ms:.0f} ms")

    # Chunk list
    for i, chunk in enumerate(chunk_set.chunks):
        render_chunk_card(
            chunk,
            i,
            show_metadata=show_metadata,
            highlight_terms=show_metadata,
        )
```

### Chunk size distribution chart

```python
def render_chunk_size_chart(
    lexi_chunks: ChunkSet,
    baseline_chunks: ChunkSet,
    baseline_name: str,
) -> None:
    """Render a Plotly bar chart comparing chunk size distributions.

    Uses overlapping histograms to show how chunk sizes differ
    between LexiChunk and the baseline.
    """
    import plotly.graph_objects as go

    lexi_sizes = [len(c.text) for c in lexi_chunks.chunks]
    base_sizes = [len(c.text) for c in baseline_chunks.chunks]

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=lexi_sizes,
        name="LexiChunk",
        marker_color="#2196F3",
        opacity=0.7,
        nbinsx=20,
    ))
    fig.add_trace(go.Histogram(
        x=base_sizes,
        name=baseline_name,
        marker_color="#FF9800",
        opacity=0.7,
        nbinsx=20,
    ))

    fig.update_layout(
        title="Chunk Size Distribution (characters)",
        xaxis_title="Chunk size (chars)",
        yaxis_title="Count",
        barmode="overlay",
        height=300,
        margin=dict(l=40, r=20, t=40, b=40),
        legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99),
    )

    st.plotly_chart(fig, use_container_width=True)
```

### Update page_compare.py

Update `_render_results` in `page_compare.py` to use the new components:

```python
def _render_results(
    lexi: ChunkSet, baseline: ChunkSet, baseline_name: str
) -> None:
    """Render the comparison results using enhanced components."""
    from scaffolder.dashboard.components import (
        render_chunk_list,
        render_chunk_size_chart,
    )

    st.subheader("3. Results")

    # Summary metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        delta = baseline.chunk_count - lexi.chunk_count
        st.metric("LexiChunk Chunks", lexi.chunk_count,
                   delta=f"{-delta}" if delta else None)
    with col2:
        st.metric(f"{baseline_name} Chunks", baseline.chunk_count)
    with col3:
        st.metric("LexiChunk Avg Size", f"{lexi.avg_chunk_size:.0f} tok")
    with col4:
        st.metric("LexiChunk Time", f"{lexi.duration_ms:.0f} ms")

    # Chunk size distribution
    render_chunk_size_chart(lexi, baseline, baseline_name)

    st.markdown("---")

    # Side-by-side chunk display
    left, right = st.columns(2)

    with left:
        render_chunk_list(lexi, strategy_label="LexiChunk", show_metadata=True)

    with right:
        render_chunk_list(
            baseline,
            strategy_label=baseline_name,
            show_metadata=False,  # Baselines don't have rich metadata
        )
```

## Outputs
- `src/scaffolder/dashboard/components.py` (complete rewrite with all component functions)
- `src/scaffolder/dashboard/page_compare.py` (updated `_render_results`)

## Acceptance Criteria
1. `streamlit run src/scaffolder/dashboard/app.py` → "Compare Chunks" → select fixture → "Run Chunking"
2. LexiChunk chunks show: colour-coded borders by clause type, hierarchy breadcrumbs, defined term badges
3. Baseline chunks show: plain text without metadata (since baselines don't produce metadata)
4. Chunk size distribution histogram displays with overlapping bars
5. Summary metrics row shows chunk count, avg size, timing for both strategies
6. Defined terms in chunk text are highlighted in blue
7. `make lint` passes

## Handoff Notes
- **To Agent A:** The chunk viewer expects `Chunk.metadata` to contain: `clause_type` (str), `clause_confidence` (float, 0-1), `hierarchy_path` (str, e.g., "1 > 1.1 > 1.1.2"), `defined_terms` (list[str]), `cross_refs` (list[str]). For baseline strategies, these should be empty/absent — the component handles the empty case gracefully.
- **To Day 9:** The comparison page is complete. Day 9 builds page_retrieval.py using Agent A's `RetrievalSimulator`. The components from today (`render_chunk_card`) will also be used on the retrieval page to show retrieved chunks.
- **Decision:** We use `unsafe_allow_html=True` for the colour-coded display. This is safe because all user text goes through `html.escape()` before rendering. The `_highlight_terms` function is careful to escape first, then add HTML styling.
