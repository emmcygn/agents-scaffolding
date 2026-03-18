# Agent B — Day 09: Streamlit Page 2 — Retrieval Demo

## Mission
Build the retrieval demo page where users enter a legal question, run retrieval against all strategies, and see ranked results with annotated correct chunks highlighted — the most compelling proof that LexiChunk improves retrieval quality.

## Context
Day 8 completed the chunk viewer component. Agent A has delivered `RetrievalSimulator` (which takes a query, chunked indexes, and returns ranked results) and `EmbeddingPipeline` (local embeddings). Today we build the retrieval page that ties everything together: chunk → embed → index → query → display ranked results with correctness annotations. This is the flagship demo of the scaffolder.

## Prerequisites
- `src/scaffolder/dashboard/page_retrieval.py` stub exists (Day 5)
- `src/scaffolder/dashboard/components.py` with chunk viewer (Day 8)
- `src/scaffolder/retrieval/simulator.py` with `RetrievalSimulator` (Agent A)
- `src/scaffolder/retrieval/index.py` with FAISS wrapper (Agent A)
- `src/scaffolder/embedding/pipeline.py` with `EmbeddingPipeline` (Agent A)
- `src/scaffolder/queries.py` with `load_queries()` (Day 3)
- `src/scaffolder/models.py` with `RetrievalResult` (Agent A, Day 1)

## Checklist
- [ ] Task 1 — Implement query input: free text or select from annotated queries
- [ ] Task 2 — Wire retrieval pipeline: chunk → embed → index → query
- [ ] Task 3 — Display per-strategy results with ranked chunks and scores
- [ ] Task 4 — Highlight annotated "correct" chunks in green
- [ ] Task 5 — Add Plotly bar chart comparing P@5 across strategies
- [ ] Task 6 — Cache embedding indexes in session state to avoid recomputation
- [ ] Task 7 — Show retrieval metrics (P@k, MRR, NDCG) per strategy

## Implementation Details

### Full page_retrieval.py implementation

```python
"""Page 2: Retrieval demo — query against chunked & embedded documents."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import streamlit as st

if TYPE_CHECKING:
    from scaffolder.models import ChunkSet, RetrievalResult


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
    return [
        {"id": q.id, "text": q.text, "failure_mode": q.failure_mode}
        for q in queries
    ]


def _get_index_cache_key(doc_id: str, strategy: str, model: str) -> str:
    """Generate cache key for embedding index."""
    return f"index_{doc_id}_{strategy}_{model}"


def _ensure_index(
    doc_id: str, strategy: str, model: str
) -> Any:
    """Build or retrieve cached embedding index for a document + strategy + model.

    Returns the FAISS index wrapper from Agent A's retrieval module.
    """
    cache_key = _get_index_cache_key(doc_id, strategy, model)

    if cache_key in st.session_state:
        return st.session_state[cache_key]

    from scaffolder.fixtures import FixtureManager
    from scaffolder.chunking.pipeline import ChunkingPipeline
    from scaffolder.embedding.pipeline import EmbeddingPipeline
    from scaffolder.retrieval.index import FAISSIndex

    # Load document
    manager = FixtureManager()
    document = manager.load(doc_id)

    # Chunk
    pipeline = ChunkingPipeline()
    chunk_set = pipeline.chunk(document, strategy)

    # Embed
    embedder = EmbeddingPipeline(model_name=model)
    texts = [c.text for c in chunk_set.chunks]
    embeddings = embedder.embed(texts)

    # Index
    index = FAISSIndex(
        chunks=chunk_set.chunks,
        embeddings=embeddings,
        model_name=model,
    )

    st.session_state[cache_key] = index
    # Also cache the chunk set for display
    st.session_state[f"chunks_{doc_id}_{strategy}"] = chunk_set

    return index


def _run_retrieval(
    query: str,
    doc_id: str,
    strategies: list[str],
    model: str,
    k: int,
) -> dict[str, RetrievalResult]:
    """Run retrieval for a query against all strategies.

    Returns a dict mapping strategy name to RetrievalResult.
    """
    from scaffolder.retrieval.simulator import RetrievalSimulator

    results: dict[str, Any] = {}

    for strategy in strategies:
        index = _ensure_index(doc_id, strategy, model)
        simulator = RetrievalSimulator(index=index)
        result = simulator.query(query_text=query, k=k)
        results[strategy] = result

    return results


def render_page() -> None:
    """Render the retrieval demo page."""
    st.title("Retrieval Demo")
    st.markdown(
        "Ask a legal question and compare retrieval results across chunking strategies. "
        "See which strategy retrieves the most relevant chunks."
    )

    # --- Settings ---
    col1, col2, col3 = st.columns(3)

    with col1:
        doc_id = st.selectbox(
            "Document",
            options=FIXTURE_OPTIONS,
            key="ret_doc",
        )

    with col2:
        model = st.selectbox(
            "Embedding Model",
            options=MODEL_OPTIONS,
            key="ret_model",
        )

    with col3:
        k = st.slider(
            "Top-k results",
            min_value=1,
            max_value=20,
            value=5,
            key="ret_k",
        )

    # Strategy selection from sidebar (already set in app.py)
    strategies = st.session_state.get("config", {}).get(
        "strategies", ["lexichunk", "langchain_rcts"]
    )

    # --- Query Input ---
    st.subheader("Query")

    query_source = st.radio(
        "Query source",
        options=["Type your own", "Select annotated query"],
        horizontal=True,
        key="query_source",
    )

    query = ""
    annotated_query_id = None

    if query_source == "Type your own":
        query = st.text_input(
            "Legal question",
            placeholder="e.g., What are the termination provisions?",
            key="ret_query_text",
        )
    else:
        # Load annotated queries for selected document
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
            annotated_query_id = annotated[selected_idx]["id"]
            st.caption(
                f"Query ID: {annotated_query_id} | "
                f"Tests: {annotated[selected_idx]['failure_mode']}"
            )
        else:
            st.warning(f"No annotated queries found for {doc_id}")
            query = st.text_input(
                "Type a query instead",
                key="ret_fallback_query",
            )

    # --- Run Retrieval ---
    run_button = st.button(
        "Search",
        type="primary",
        disabled=not query.strip(),
        use_container_width=True,
    )

    if run_button and query.strip():
        with st.spinner("Building indexes and running retrieval..."):
            try:
                results = _run_retrieval(
                    query=query.strip(),
                    doc_id=doc_id,
                    strategies=strategies,
                    model=model,
                    k=k,
                )
                st.session_state["ret_results"] = results
                st.session_state["ret_last_query"] = query.strip()
            except Exception as e:
                st.error(f"Retrieval failed: {e}")
                return

    # --- Display Results ---
    results = st.session_state.get("ret_results")
    last_query = st.session_state.get("ret_last_query", "")

    if results and last_query:
        _render_retrieval_results(results, last_query, k)


def _render_retrieval_results(
    results: dict[str, RetrievalResult],
    query: str,
    k: int,
) -> None:
    """Render retrieval results with comparison chart and per-strategy details."""
    st.markdown("---")
    st.subheader("Results")
    st.markdown(f'**Query:** "{query}"')

    # --- Metrics comparison chart ---
    _render_metrics_chart(results, k)

    # --- Metrics table ---
    _render_metrics_table(results, k)

    # --- Per-strategy results in tabs ---
    strategy_names = list(results.keys())
    tabs = st.tabs(strategy_names)

    for tab, strategy in zip(tabs, strategy_names):
        with tab:
            result = results[strategy]
            _render_strategy_results(result, strategy)


def _render_metrics_chart(
    results: dict[str, RetrievalResult],
    k: int,
) -> None:
    """Render a Plotly grouped bar chart comparing P@k across strategies."""
    import plotly.graph_objects as go

    strategies = list(results.keys())
    k_display = min(k, 5)  # Show P@1, P@3, P@5 if available

    k_values = [kv for kv in [1, 3, 5, 10] if kv <= k]

    fig = go.Figure()

    colors = ["#2196F3", "#FF9800", "#4CAF50", "#9C27B0", "#F44336"]

    for i, strategy in enumerate(strategies):
        result = results[strategy]
        p_at_k_values = [
            result.precision_at_k.get(kv, 0.0) for kv in k_values
        ]
        fig.add_trace(go.Bar(
            name=strategy,
            x=[f"P@{kv}" for kv in k_values],
            y=p_at_k_values,
            marker_color=colors[i % len(colors)],
        ))

    fig.update_layout(
        title="Precision@k Comparison",
        xaxis_title="Metric",
        yaxis_title="Score",
        yaxis=dict(range=[0, 1.05]),
        barmode="group",
        height=350,
        margin=dict(l=40, r=20, t=50, b=40),
        legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99),
    )

    st.plotly_chart(fig, use_container_width=True)


def _render_metrics_table(
    results: dict[str, RetrievalResult],
    k: int,
) -> None:
    """Render a table of retrieval metrics per strategy."""
    import pandas as pd

    rows = []
    for strategy, result in results.items():
        row = {
            "Strategy": strategy,
            "MRR": f"{result.mrr:.3f}",
            "NDCG@10": f"{result.ndcg_at_10:.3f}",
            "DRM": "Yes" if result.is_drm else "No",
        }
        # Add P@k columns
        for kv in [1, 3, 5, 10]:
            if kv <= k:
                row[f"P@{kv}"] = f"{result.precision_at_k.get(kv, 0.0):.3f}"
        rows.append(row)

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


def _render_strategy_results(
    result: RetrievalResult,
    strategy: str,
) -> None:
    """Render the retrieved chunks for a single strategy."""
    from scaffolder.dashboard.components import render_chunk_card
    from scaffolder.models import Chunk

    st.markdown(f"**{strategy}** — {len(result.retrieved_chunk_ids)} results")

    # Get the actual chunk objects from session state
    # The chunks were cached when building the index
    relevant_ids = set(result.relevant_chunk_ids)

    for rank, (chunk_id, score) in enumerate(
        zip(result.retrieved_chunk_ids, result.scores)
    ):
        is_relevant = chunk_id in relevant_ids
        relevance_marker = " [RELEVANT]" if is_relevant else ""

        # Style relevant chunks with green border
        if is_relevant:
            st.markdown(
                f'<div style="border-left: 4px solid #4CAF50; padding-left: 8px; '
                f'margin-bottom: 4px;">'
                f'<strong>#{rank + 1}</strong> (score: {score:.4f})'
                f'<span style="color: #4CAF50; font-weight: bold;"> RELEVANT</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div style="border-left: 4px solid #ccc; padding-left: 8px; '
                f'margin-bottom: 4px;">'
                f'<strong>#{rank + 1}</strong> (score: {score:.4f})'
                f'</div>',
                unsafe_allow_html=True,
            )

        # Show chunk text in expander
        with st.expander(f"Chunk: {chunk_id}", expanded=rank < 3):
            # Try to get chunk text from cached chunk set
            chunk_set_key = f"chunks_{result.query_id.split('_')[0]}_{strategy}"
            chunk_set = st.session_state.get(chunk_set_key)
            if chunk_set:
                matching = [c for c in chunk_set.chunks if c.id == chunk_id]
                if matching:
                    st.text(matching[0].text[:1000])
                else:
                    st.caption(f"Chunk ID: {chunk_id}")
            else:
                st.caption(f"Chunk ID: {chunk_id}")
```

### Session state management pattern

The retrieval page caches three things in session state:

1. **Embedding indexes**: `st.session_state[f"index_{doc}_{strategy}_{model}"]` — the FAISS index. This is the expensive computation (chunking + embedding + indexing). Cached per document/strategy/model triple.

2. **Chunk sets**: `st.session_state[f"chunks_{doc}_{strategy}"]` — the ChunkSet from chunking. Used to display chunk text in results.

3. **Query results**: `st.session_state["ret_results"]` — the last query's results. Updated on each search.

When the user changes the embedding model, indexes need to be rebuilt. When they change the document, everything needs to be rebuilt. The `_ensure_index` function handles this with a cache-or-compute pattern.

## Outputs
- `src/scaffolder/dashboard/page_retrieval.py` (complete implementation)

## Acceptance Criteria
1. `streamlit run src/scaffolder/dashboard/app.py` → "Retrieval Demo"
2. Select document → select annotated query → click "Search"
3. See P@k bar chart comparing strategies
4. See metrics table with MRR, NDCG@10, P@k per strategy
5. See per-strategy tabs with ranked chunks
6. Relevant chunks highlighted with green border and "RELEVANT" label
7. Switching embedding model triggers index rebuild on next search
8. `make lint` passes

## Handoff Notes
- **To Agent A:** The retrieval page uses `RetrievalSimulator.query(query_text, k)` → expects `RetrievalResult` with all fields populated: `retrieved_chunk_ids`, `relevant_chunk_ids`, `scores`, `precision_at_k`, `recall_at_k`, `mrr`, `ndcg_at_10`, `is_drm`. The `FAISSIndex` constructor should accept `chunks`, `embeddings`, `model_name`.
- **To Day 10:** Need to extend the CLI reporter with retrieval metrics tables and add the Voyage model to the Streamlit model dropdown. The retrieval page is functional but the Voyage toggle needs wiring.
- **Decision:** We build indexes lazily per-strategy rather than all-at-once. This means first search is slow but subsequent searches (changing query only) are fast. The UX tradeoff is acceptable for a demo tool.
