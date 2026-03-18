"""Page 2: Retrieval demo — query against chunked documents."""

from __future__ import annotations

import streamlit as st


def render_page() -> None:
    """Render the retrieval demo page."""
    st.title("Retrieval Demo")
    st.markdown("Ask a legal question and compare retrieval results across chunking strategies.")

    # Query input
    query = st.text_input(
        "Legal question",
        placeholder="e.g., What are the termination provisions?",
    )

    # Settings row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.selectbox(
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
        st.slider("Top-k results", min_value=1, max_value=20, value=5)
    with col3:
        st.selectbox(
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
