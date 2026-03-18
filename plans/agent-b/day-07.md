# Agent B — Day 07: Streamlit Page 1 — Side-by-Side Chunk Comparison

## Mission
Build the fully functional chunk comparison page in Streamlit, integrating Agent A's `ChunkingPipeline` to let users select a document and see LexiChunk vs. baseline chunks side by side with stats.

## Context
Day 5 created the Streamlit skeleton with stub pages. Agent A's `ChunkingPipeline` is available — it takes a `Document` object and a strategy name, and returns a `ChunkSet`. Today we wire it up to the comparison page with real chunking, side-by-side display, and summary statistics. The chunk viewer component (colour-coded by clause type) comes on Day 8.

## Prerequisites
- `src/scaffolder/dashboard/page_compare.py` stub exists (Day 5)
- `src/scaffolder/dashboard/app.py` with navigation (Day 5)
- `src/scaffolder/chunking/pipeline.py` with `ChunkingPipeline` class (Agent A, Day 3)
- `src/scaffolder/fixtures/__init__.py` with `FixtureManager` (Agent A, Day 2)
- `src/scaffolder/models.py` with `Document`, `Chunk`, `ChunkSet` (Agent A, Day 1)

## Checklist
- [ ] Task 1 — Implement document loading (fixture select, file upload, text paste) in page_compare.py
- [ ] Task 2 — Wire up `ChunkingPipeline` to chunk selected document with both strategies
- [ ] Task 3 — Display side-by-side results: chunk count, avg size, timing, chunk list
- [ ] Task 4 — Add session state caching to avoid re-chunking on page re-render
- [ ] Task 5 — Handle errors gracefully (chunking failures, missing fixtures)
- [ ] Task 6 — Add summary stats row at the top (metrics cards)

## Implementation Details

### Full page_compare.py implementation

```python
"""Page 1: Side-by-side chunk comparison."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import streamlit as st

if TYPE_CHECKING:
    from scaffolder.models import ChunkSet, Document


def _load_fixture(fixture_name: str) -> Document:
    """Load a fixture document by name."""
    from scaffolder.fixtures import FixtureManager

    manager = FixtureManager()
    return manager.load(fixture_name)


def _create_document_from_text(text: str, name: str = "pasted") -> Document:
    """Create a Document from raw text."""
    from scaffolder.models import Document

    return Document(
        id=name,
        text=text,
        jurisdiction="unknown",
        document_type="unknown",
        source_path="<pasted>",
    )


def _create_document_from_upload(content: str, filename: str) -> Document:
    """Create a Document from uploaded file content."""
    from scaffolder.models import Document

    # Try to infer jurisdiction from filename
    jurisdiction = "unknown"
    if "uk_" in filename.lower() or "uk-" in filename.lower():
        jurisdiction = "uk"
    elif "us_" in filename.lower() or "us-" in filename.lower():
        jurisdiction = "us"
    elif "eu_" in filename.lower() or "eu-" in filename.lower():
        jurisdiction = "eu"

    return Document(
        id=filename.replace(".txt", ""),
        text=content,
        jurisdiction=jurisdiction,
        document_type="uploaded",
        source_path=f"<upload:{filename}>",
    )


def _chunk_document(doc: Document, strategy: str) -> ChunkSet:
    """Chunk a document using the specified strategy."""
    from scaffolder.chunking.pipeline import ChunkingPipeline

    pipeline = ChunkingPipeline()
    return pipeline.chunk(doc, strategy)


def _get_cache_key(doc_id: str, strategy: str) -> str:
    """Generate a session state cache key for chunk results."""
    return f"chunks_{doc_id}_{strategy}"


def render_page() -> None:
    """Render the chunk comparison page."""
    st.title("Chunk Comparison")
    st.markdown(
        "Compare how **LexiChunk** and baseline chunkers split the same legal document. "
        "Select a document source and a baseline strategy, then click **Run Chunking**."
    )

    # --- Document Selection ---
    st.subheader("1. Select Document")
    doc_source = st.radio(
        "Document source",
        options=["Built-in fixture", "Upload file", "Paste text"],
        horizontal=True,
        key="doc_source",
    )

    document: Document | None = None

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
            key="fixture_select",
        )
        try:
            document = _load_fixture(fixture)
            with st.expander("Preview document", expanded=False):
                st.text(document.text[:2000] + ("..." if len(document.text) > 2000 else ""))
                st.caption(
                    f"Jurisdiction: {document.jurisdiction} | "
                    f"Type: {document.document_type} | "
                    f"Length: {len(document.text):,} chars"
                )
        except Exception as e:
            st.error(f"Failed to load fixture: {e}")

    elif doc_source == "Upload file":
        uploaded = st.file_uploader(
            "Upload a .txt legal document",
            type=["txt"],
            key="file_upload",
        )
        if uploaded is not None:
            content = uploaded.getvalue().decode("utf-8")
            document = _create_document_from_upload(content, uploaded.name)
            st.success(f"Loaded: {uploaded.name} ({len(content):,} chars)")

    elif doc_source == "Paste text":
        text = st.text_area(
            "Paste legal document text",
            height=200,
            placeholder="Paste your legal document text here...",
            key="paste_text",
        )
        if text.strip():
            document = _create_document_from_text(text.strip())
            st.caption(f"Length: {len(text):,} chars")

    # --- Strategy Selection ---
    st.subheader("2. Select Baseline")
    baseline = st.selectbox(
        "Baseline chunking strategy",
        options=["langchain_rcts", "sentence_split", "fixed_512"],
        key="baseline_select",
        help=(
            "langchain_rcts: LangChain RecursiveCharacterTextSplitter (1000/200)\n"
            "sentence_split: Split on sentence boundaries\n"
            "fixed_512: Fixed 512-token chunks with 50-token overlap"
        ),
    )

    # --- Run Chunking ---
    st.markdown("---")

    run_button = st.button(
        "Run Chunking",
        type="primary",
        disabled=document is None,
        use_container_width=True,
    )

    if document is None and run_button:
        st.warning("Please select or provide a document first.")
        return

    if run_button and document is not None:
        lexi_key = _get_cache_key(document.id, "lexichunk")
        base_key = _get_cache_key(document.id, baseline)

        with st.spinner("Chunking with LexiChunk..."):
            try:
                lexi_result = _chunk_document(document, "lexichunk")
                st.session_state[lexi_key] = lexi_result
            except Exception as e:
                st.error(f"LexiChunk chunking failed: {e}")
                return

        with st.spinner(f"Chunking with {baseline}..."):
            try:
                base_result = _chunk_document(document, baseline)
                st.session_state[base_key] = base_result
            except Exception as e:
                st.error(f"{baseline} chunking failed: {e}")
                return

        st.session_state["last_doc_id"] = document.id
        st.session_state["last_baseline"] = baseline

    # --- Display Results ---
    doc_id = st.session_state.get("last_doc_id")
    last_baseline = st.session_state.get("last_baseline", baseline)

    if doc_id:
        lexi_key = _get_cache_key(doc_id, "lexichunk")
        base_key = _get_cache_key(doc_id, last_baseline)

        lexi_result = st.session_state.get(lexi_key)
        base_result = st.session_state.get(base_key)

        if lexi_result and base_result:
            _render_results(lexi_result, base_result, last_baseline)


def _render_results(
    lexi: ChunkSet, baseline: ChunkSet, baseline_name: str
) -> None:
    """Render the comparison results."""
    # Summary metrics row
    st.subheader("3. Results")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        delta = baseline.chunk_count - lexi.chunk_count
        st.metric(
            "LexiChunk Chunks",
            lexi.chunk_count,
            delta=f"{-delta}" if delta != 0 else None,
            help="Fewer chunks often means less fragmentation",
        )
    with col2:
        st.metric(
            f"{baseline_name} Chunks",
            baseline.chunk_count,
        )
    with col3:
        st.metric(
            "LexiChunk Avg Size",
            f"{lexi.avg_chunk_size:.0f} tok",
        )
    with col4:
        st.metric(
            "LexiChunk Time",
            f"{lexi.duration_ms:.0f}ms",
        )

    st.markdown("---")

    # Side-by-side chunk display
    left, right = st.columns(2)

    with left:
        st.markdown(f"**LexiChunk** ({lexi.chunk_count} chunks)")
        for i, chunk in enumerate(lexi.chunks):
            with st.expander(
                f"Chunk {i + 1} — {len(chunk.text)} chars",
                expanded=i < 3,
            ):
                # Show metadata if available
                clause_type = chunk.metadata.get("clause_type", "")
                if clause_type:
                    st.caption(f"Clause: {clause_type}")

                hierarchy = chunk.metadata.get("hierarchy_path", "")
                if hierarchy:
                    st.caption(f"Path: {hierarchy}")

                terms = chunk.metadata.get("defined_terms", [])
                if terms:
                    st.caption(f"Defined terms: {', '.join(terms)}")

                st.text(chunk.text)

    with right:
        st.markdown(f"**{baseline_name}** ({baseline.chunk_count} chunks)")
        for i, chunk in enumerate(baseline.chunks):
            with st.expander(
                f"Chunk {i + 1} — {len(chunk.text)} chars",
                expanded=i < 3,
            ):
                st.text(chunk.text)
```

### Key Streamlit patterns used

1. **Session state caching**: Results are stored in `st.session_state` with keys like `chunks_uk_service_agreement_lexichunk`. This persists across re-renders so switching pages and coming back preserves results.

2. **Conditional rendering**: The results section only renders when `last_doc_id` is in session state, preventing empty UI on first load.

3. **Spinner feedback**: `st.spinner()` wraps chunking operations to show progress.

4. **Metric cards**: `st.metric()` with delta shows the difference between strategies at a glance.

5. **Two-column layout**: `st.columns(2)` for the side-by-side chunk display.

### Error handling patterns

- Fixture loading failure: `st.error()` with the exception message
- Chunking failure: `st.error()` with strategy name + exception, early return
- No document selected: Button disabled via `disabled=document is None`
- Empty text paste: Ignored (no document created)
- Upload decode error: Caught by `getvalue().decode("utf-8")` — add try/except around it

## Outputs
- `src/scaffolder/dashboard/page_compare.py` (complete implementation)

## Acceptance Criteria
1. `streamlit run src/scaffolder/dashboard/app.py` → Navigate to "Compare Chunks"
2. Select "uk_service_agreement" fixture → Click "Run Chunking"
3. See side-by-side chunk display: LexiChunk on left, baseline on right
4. Summary metrics show chunk count, avg size, timing
5. Switching pages and returning preserves the chunking results
6. Uploading a .txt file works and produces chunking results
7. `make lint` passes on the updated file

## Handoff Notes
- **To Agent A:** The page uses `ChunkingPipeline().chunk(document, strategy)` — make sure this returns a `ChunkSet` with all fields populated including `duration_ms` and `avg_chunk_size`. The `Chunk.metadata` dict should include `clause_type`, `hierarchy_path`, and `defined_terms` keys when the strategy is "lexichunk".
- **To Day 8:** The chunk display is basic `st.text()` in expanders. Day 8 adds colour-coded chunk viewer with clause type badges, hierarchy breadcrumbs, and defined term highlights.
- **Decision:** We cache chunk results in session state (not `@st.cache_data`) because the results depend on the document content, not just the fixture name. For uploaded/pasted text, `@st.cache_data` would need a content hash, which is more complex.
