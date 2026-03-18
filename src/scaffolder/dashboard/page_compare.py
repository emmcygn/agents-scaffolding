"""Page 1: Side-by-side chunk comparison."""

from __future__ import annotations

import streamlit as st


def render_page() -> None:
    """Render the chunk comparison page."""
    st.title("Chunk Comparison")
    st.markdown("Compare how LexiChunk and baseline chunkers split the same legal document.")

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
            uploaded = st.file_uploader("Upload a .txt file", type=["txt"])
            if uploaded:
                st.success(f"Uploaded: {uploaded.name}")

        elif doc_source == "Paste text":
            st.text_area(
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
