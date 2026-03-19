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
            "Retrieval requires embedding dependencies. Install with: `pip install -e '.[local]'`"
        )
        _render_query_browser()
        return

    # --- Settings ---
    col1, col2, col3 = st.columns(3)

    with col1:
        doc_id = st.selectbox("Document", options=FIXTURE_OPTIONS, key="ret_doc")

    with col2:
        # Use global model setting from sidebar if available
        global_model = st.session_state.get("config", {}).get("embedding_model", "all-MiniLM-L6-v2")
        model_default = MODEL_OPTIONS.index(global_model) if global_model in MODEL_OPTIONS else 0
        st.selectbox("Embedding Model", options=MODEL_OPTIONS, index=model_default, key="ret_model")

    with col3:
        st.slider("Top-k results", min_value=1, max_value=20, value=5, key="ret_k")

    # Strategies come from sidebar config (set in app.py)
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
        model = st.session_state.get("ret_model", MODEL_OPTIONS[0])
        _run_retrieval(doc_id, query, strategies, model)

    # --- Results ---
    st.markdown("---")
    st.subheader("Results")
    if "ret_results" not in st.session_state:
        st.info("Click 'Search' to run retrieval and see results.")
    elif not run_button:
        _display_retrieval_results(st.session_state["ret_results"])

    # --- Filtered Retrieval Demo ---
    _render_filtered_retrieval(doc_id)


def _run_retrieval(
    doc_id: str,
    query_text: str,
    strategies: list[str],
    model_name: str,
) -> None:
    """Run retrieval for a query across selected strategies and display results."""
    k = st.session_state.get("ret_k", 5)

    with st.spinner("Running retrieval pipeline..."):
        try:
            from scaffolder.chunking import get_strategy
            from scaffolder.embedding.pipeline import EmbeddingPipeline
            from scaffolder.fixtures import FixtureManager
            from scaffolder.models import EmbeddingModelName, StrategyName
            from scaffolder.retrieval.index import VectorIndex

            manager = FixtureManager()
            document = manager.get_by_id(doc_id)

            # Map string model name to enum
            model_enum = EmbeddingModelName(model_name)
            embed_pipeline = EmbeddingPipeline()

            results_by_strategy: dict[str, list[dict[str, Any]]] = {}

            for strat_name in strategies:
                # Get or cache chunk set
                chunk_key = f"chunks_{doc_id}_{strat_name}"
                chunk_set = st.session_state.get(chunk_key)
                if chunk_set is None:
                    strategy = get_strategy(StrategyName(strat_name))
                    chunk_set = strategy.chunk(document)
                    st.session_state[chunk_key] = chunk_set

                chunks = list(chunk_set.chunks)
                if not chunks:
                    continue

                # Get or cache index
                index_key = f"index_{doc_id}_{strat_name}_{model_name}"
                index = st.session_state.get(index_key)
                if index is None:
                    chunk_texts = [c.text for c in chunks]
                    embeddings = embed_pipeline.embed_texts(chunk_texts, model_enum)
                    index = VectorIndex(dimension=embeddings.shape[1])
                    index.add(chunks, embeddings)
                    st.session_state[index_key] = index

                # Embed query and search
                query_emb = embed_pipeline.embed_texts([query_text], model_enum)
                hits = index.search(query_emb[0], k=k)

                results_by_strategy[strat_name] = [
                    {
                        "rank": h.rank,
                        "score": h.score,
                        "text": h.chunk.text[:500],
                        "chunk_id": h.chunk.id,
                        "clause_type": h.chunk.metadata.get("clause_type", ""),
                    }
                    for h in hits
                ]

            st.session_state["ret_results"] = results_by_strategy

        except Exception as e:
            st.error(f"Retrieval failed: {e}")
            return

    # Display results
    _display_retrieval_results(results_by_strategy)


def _display_retrieval_results(results_by_strategy: dict[str, list[dict[str, Any]]]) -> None:
    """Display retrieval results side by side."""
    if not results_by_strategy:
        st.warning("No results returned.")
        return

    strategy_names = list(results_by_strategy.keys())
    cols = st.columns(len(strategy_names))

    for col, strat_name in zip(cols, strategy_names, strict=True):
        with col:
            st.markdown(f"**{strat_name}**")
            hits = results_by_strategy[strat_name]
            if not hits:
                st.caption("No results")
                continue

            for hit in hits:
                clause_label = f" ({hit['clause_type']})" if hit["clause_type"] else ""
                with st.expander(
                    f"#{hit['rank']} — score: {hit['score']:.3f}{clause_label}",
                    expanded=hit["rank"] <= 3,
                ):
                    st.text(hit["text"])


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
                    from scaffolder.models import StrategyName

                    manager = FixtureManager()
                    document = manager.get_by_id(doc_id)
                    strategy = get_strategy(StrategyName("lexichunk"))
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
