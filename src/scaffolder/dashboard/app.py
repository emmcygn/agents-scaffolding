"""Streamlit multi-page dashboard for scaffolder results."""

from __future__ import annotations

from typing import Any

import streamlit as st


def _invalidate_on_change(key: str, new_value: Any) -> bool:
    """Track a value and return True if it changed, clearing relevant caches."""
    prev_key = f"_prev_{key}"
    prev = st.session_state.get(prev_key)

    if prev != new_value:
        st.session_state[prev_key] = new_value
        if key == "global_model":
            keys_to_clear = [k for k in list(st.session_state) if k.startswith("index_")]
            for k in keys_to_clear:
                del st.session_state[k]
            return True
        if key == "strategies":
            keys_to_clear = [
                k for k in list(st.session_state) if k.startswith("index_") or k.startswith("ret_")
            ]
            for k in keys_to_clear:
                del st.session_state[k]
            return True
    return False


def main() -> None:
    """Configure and launch the Streamlit dashboard."""
    st.set_page_config(
        page_title="LexiChunk Scaffolder",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom CSS for polish
    st.markdown(
        """
    <style>
        @media (max-width: 768px) {
            .block-container { padding-left: 1rem; padding-right: 1rem; }
        }
        .streamlit-expanderHeader { font-size: 0.95em; }
        [data-testid="stMetricValue"] { font-size: 1.5rem; }
        .stDataFrame { font-size: 0.9em; }
    </style>
    """,
        unsafe_allow_html=True,
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
    _invalidate_on_change("strategies", tuple(selected_strategies))

    # Cache management section
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Cache**")

    index_count = sum(1 for k in st.session_state if k.startswith("index_"))
    chunk_count = sum(1 for k in st.session_state if k.startswith("chunks_"))
    st.sidebar.caption(f"Cached: {index_count} indexes, {chunk_count} chunk sets")

    if st.sidebar.button("Clear All Caches", type="secondary"):
        keys_to_clear = [
            k for k in list(st.session_state) if k.startswith(("index_", "chunks_", "ret_"))
        ]
        for k in keys_to_clear:
            del st.session_state[k]
        st.sidebar.success("Cache cleared!")
        st.rerun()

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
