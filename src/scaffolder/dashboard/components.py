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
    st.metric("Chunks", chunk_set.count)
    st.metric("Avg size (chars)", f"{chunk_set.avg_chunk_size:.0f}")
    st.metric("Time (s)", f"{chunk_set.elapsed_seconds:.3f}")

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
