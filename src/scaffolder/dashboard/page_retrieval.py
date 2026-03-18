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
