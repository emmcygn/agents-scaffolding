"""Page 2: Retrieval demo — query against chunked & embedded documents."""

from __future__ import annotations

from typing import Any

import streamlit as st

FIXTURE_OPTIONS = [
    "uk_service_agreement",
    "uk_terms_conditions",
    "us_msa",
    "us_terms_of_service",
    "eu_gdpr_excerpt",
]

MODEL_OPTIONS = ["all-MiniLM-L6-v2", "bge-base-en-v1.5"]


def _load_annotated_queries(document_id: str) -> list[dict[str, Any]]:
    """Load annotated queries for a specific document."""
    from scaffolder.queries import load_queries_for_document

    queries = load_queries_for_document("queries", document_id)
    return [{"id": q.id, "text": q.text, "failure_mode": q.failure_mode} for q in queries]


def _check_retrieval_available() -> bool:
    """Check if the retrieval pipeline is available."""
    try:
        from scaffolder.retrieval import simulator  # noqa: F401

        return True
    except (ImportError, AttributeError):
        return False


def render_page() -> None:
    """Render the retrieval demo page."""
    st.title("Retrieval Demo")
    st.markdown("Ask a legal question and compare retrieval results across chunking strategies.")

    if not _check_retrieval_available():
        st.warning(
            "The retrieval pipeline is not yet available. "
            "This page requires Agent A's RetrievalSimulator (Day 8). "
            "Install embedding dependencies with: `pip install -e '.[embeddings]'`"
        )
        _render_query_browser()
        return

    # --- Settings ---
    col1, col2, col3 = st.columns(3)

    with col1:
        doc_id = st.selectbox("Document", options=FIXTURE_OPTIONS, key="ret_doc")

    with col2:
        st.selectbox("Embedding Model", options=MODEL_OPTIONS, key="ret_model")

    with col3:
        st.slider("Top-k results", min_value=1, max_value=20, value=5, key="ret_k")

    # Strategies come from sidebar config (set in app.py)
    _ = st.session_state.get("config", {}).get("strategies", ["lexichunk", "langchain_rcts"])

    # --- Query Input ---
    st.subheader("Query")

    query_source = st.radio(
        "Query source",
        options=["Type your own", "Select annotated query"],
        horizontal=True,
        key="query_source",
    )

    query = ""

    if query_source == "Type your own":
        query = st.text_input(
            "Legal question",
            placeholder="e.g., What are the termination provisions?",
            key="ret_query_text",
        )
    else:
        annotated = _load_annotated_queries(doc_id)
        if annotated:
            options = [f"[{q['failure_mode']}] {q['text']}" for q in annotated]
            selected_idx = st.selectbox(
                "Select query",
                options=range(len(options)),
                format_func=lambda i: options[i],
                key="ret_annotated_query",
            )
            query = annotated[selected_idx]["text"]
            st.caption(
                f"Query ID: {annotated[selected_idx]['id']} | "
                f"Tests: {annotated[selected_idx]['failure_mode']}"
            )
        else:
            st.warning(f"No annotated queries found for {doc_id}")
            query = st.text_input("Type a query instead", key="ret_fallback_query")

    # --- Run Retrieval ---
    run_button = st.button(
        "Search",
        type="primary",
        disabled=not query.strip(),
        use_container_width=True,
    )

    if run_button and query.strip():
        st.info(
            "Retrieval pipeline integration pending Agent A's RetrievalSimulator. "
            "The query interface is ready — results will appear once the pipeline is connected."
        )

    # --- Placeholder Results ---
    st.markdown("---")
    st.subheader("Results")
    st.info("Results will appear here after retrieval pipeline is integrated.")

    # --- Filtered Retrieval Demo ---
    _render_filtered_retrieval(doc_id)


def _render_query_browser() -> None:
    """Render a query browser showing annotated queries without retrieval."""
    st.markdown("---")
    st.subheader("Annotated Query Browser")
    st.markdown("Browse the ground-truth queries while waiting for the retrieval pipeline.")

    doc_id = st.selectbox(
        "Document",
        options=FIXTURE_OPTIONS,
        key="browse_doc",
    )

    queries = _load_annotated_queries(doc_id)
    if not queries:
        st.info(f"No queries found for {doc_id}")
        return

    for q in queries:
        with st.expander(f"[{q['failure_mode']}] {q['text']}"):
            st.markdown(f"**ID:** {q['id']}")
            st.markdown(f"**Failure mode:** {q['failure_mode']}")
            st.markdown(f"**Query:** {q['text']}")


def _render_filtered_retrieval(doc_id: str) -> None:
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

    clause_types = [
        "definitions",
        "termination",
        "payment",
        "indemnification",
        "limitation_of_liability",
        "confidentiality",
        "intellectual_property",
        "data_protection",
        "governing_law",
        "dispute_resolution",
        "force_majeure",
        "warranties",
        "obligations",
        "notices",
    ]

    selected_type = st.selectbox(
        "Clause type to find",
        options=clause_types,
        key="filter_clause_type",
        help="Find all chunks classified as this clause type",
    )

    if st.button("Find Clauses", key="filter_search"):
        chunk_set_key = f"chunks_{doc_id}_lexichunk"
        chunk_set = st.session_state.get(chunk_set_key)

        if chunk_set is None:
            with st.spinner("Chunking with LexiChunk..."):
                try:
                    from scaffolder.chunking import get_strategy
                    from scaffolder.fixtures import FixtureManager

                    manager = FixtureManager()
                    document = manager.load(doc_id)
                    strategy = get_strategy("lexichunk")
                    chunk_set = strategy.chunk(document)
                    st.session_state[chunk_set_key] = chunk_set
                except Exception as e:
                    st.error(f"Failed to chunk document: {e}")
                    return

        matching = [c for c in chunk_set.chunks if c.metadata.get("clause_type") == selected_type]

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**LexiChunk: {len(matching)} matching chunks**")
            if matching:
                for i, chunk in enumerate(matching):
                    confidence = float(chunk.metadata.get("confidence", 0))
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

            baseline_key = f"chunks_{doc_id}_rcts"
            baseline_set = st.session_state.get(baseline_key)
            if baseline_set:
                keyword = selected_type.replace("_", " ")
                keyword_matches = [
                    c for c in baseline_set.chunks if keyword.lower() in c.text.lower()
                ]
                st.caption(
                    f"Naive keyword search for '{keyword}' in baseline chunks: "
                    f"{len(keyword_matches)} matches (likely imprecise)"
                )
