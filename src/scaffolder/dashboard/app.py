"""Streamlit multi-page dashboard for scaffolder results."""

from __future__ import annotations

import streamlit as st


def main() -> None:
    """Configure and launch the Streamlit dashboard."""
    st.set_page_config(
        page_title="LexiChunk Scaffolder",
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
    st.sidebar.markdown("**Settings**")

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
        st.title("Metrics Dashboard")
        st.info("Coming soon — metrics summary panels and comparison charts.")


if __name__ == "__main__":
    main()
