# Agent B — Day 11: Streamlit Polish — Spinners, Errors & Session State

## Mission
Polish the Streamlit dashboard with loading spinners, error handling, responsive layout, and optimised session state management to create a production-quality user experience.

## Context
Days 7-9 built functional Streamlit pages. They work, but the UX has rough edges: no loading feedback during long operations, basic error messages, no session state cleanup when inputs change, and layout that may not work well on different screen sizes. Today is a dedicated polish day to make the dashboard feel professional.

## Prerequisites
- `src/scaffolder/dashboard/app.py` with navigation (Day 5)
- `src/scaffolder/dashboard/page_compare.py` functional (Day 7-8)
- `src/scaffolder/dashboard/page_retrieval.py` functional (Day 9)
- `src/scaffolder/dashboard/components.py` with chunk viewer (Day 8)

## Checklist
- [ ] Task 1 — Add progress bars for multi-step operations (chunk → embed → index)
- [ ] Task 2 — Improve error messages with actionable guidance
- [ ] Task 3 — Add session state invalidation when inputs change
- [ ] Task 4 — Add responsive layout adjustments
- [ ] Task 5 — Add a "Clear cache" button in sidebar
- [ ] Task 6 — Add timing information to operations
- [ ] Task 7 — Add Streamlit toast notifications for completed operations

## Implementation Details

### Progress bars for multi-step operations

Replace simple `st.spinner()` with `st.progress()` for multi-step operations in `page_retrieval.py`:

```python
def _run_retrieval_with_progress(
    query: str,
    doc_id: str,
    strategies: list[str],
    model: str,
    k: int,
) -> dict[str, RetrievalResult]:
    """Run retrieval with progress bar feedback."""
    results: dict[str, Any] = {}
    total_steps = len(strategies)
    progress_bar = st.progress(0, text="Preparing...")

    for i, strategy in enumerate(strategies):
        progress_text = f"Processing {strategy} ({i + 1}/{total_steps})..."
        progress_bar.progress((i) / total_steps, text=progress_text)

        # Check if index exists in cache
        cache_key = _get_index_cache_key(doc_id, strategy, model)
        if cache_key not in st.session_state:
            progress_bar.progress(
                (i + 0.3) / total_steps,
                text=f"{strategy}: Chunking document..."
            )
            # Chunking happens inside _ensure_index

            progress_bar.progress(
                (i + 0.6) / total_steps,
                text=f"{strategy}: Building embedding index..."
            )

        index = _ensure_index(doc_id, strategy, model)

        progress_bar.progress(
            (i + 0.9) / total_steps,
            text=f"{strategy}: Running retrieval..."
        )

        from scaffolder.retrieval.simulator import RetrievalSimulator
        simulator = RetrievalSimulator(index=index)
        result = simulator.query(query_text=query, k=k)
        results[strategy] = result

    progress_bar.progress(1.0, text="Complete!")
    return results
```

### Improved error messages

Create a helper in `components.py`:

```python
def render_error(
    title: str,
    detail: str,
    suggestion: str = "",
) -> None:
    """Render a structured error message with optional suggestion.

    Provides more context than bare st.error() for common failure modes.
    """
    st.error(f"**{title}**")
    st.markdown(f"> {detail}")
    if suggestion:
        st.info(f"**Suggestion:** {suggestion}")


def render_dependency_error(package: str, extra: str) -> None:
    """Render a helpful error for missing optional dependencies."""
    render_error(
        title=f"Missing dependency: {package}",
        detail=f"The `{package}` package is required for this feature but not installed.",
        suggestion=f'Install with: `pip install "scaffolder[{extra}]"`',
    )


def render_api_key_error(service: str, env_var: str, url: str) -> None:
    """Render a helpful error for missing API keys."""
    render_error(
        title=f"{service} API key not found",
        detail=f"The environment variable `{env_var}` is not set.",
        suggestion=f"Get a key at {url} and set `export {env_var}=your-key`",
    )
```

Use these in page_retrieval.py:

```python
# In the retrieval error handler:
except ImportError as e:
    if "sentence_transformers" in str(e):
        render_dependency_error("sentence-transformers", "embed")
    elif "faiss" in str(e):
        render_dependency_error("faiss-cpu", "embed")
    elif "voyageai" in str(e):
        render_dependency_error("voyageai", "voyage")
    else:
        st.error(f"Import error: {e}")
except Exception as e:
    error_str = str(e).lower()
    if "voyage_api_key" in error_str:
        render_api_key_error("Voyage AI", "VOYAGE_API_KEY", "https://dash.voyageai.com/")
    else:
        st.error(f"Retrieval failed: {e}")
```

### Session state invalidation

When inputs change (document, strategy, model), stale cached results should be invalidated:

```python
# In app.py, add a cache invalidation helper:

def _invalidate_on_change(key: str, new_value: Any) -> bool:
    """Track a value and return True if it changed.

    Clears relevant session state when a change is detected.
    """
    prev_key = f"_prev_{key}"
    prev = st.session_state.get(prev_key)

    if prev != new_value:
        st.session_state[prev_key] = new_value
        # Clear index caches when model changes
        if key == "global_model":
            keys_to_clear = [
                k for k in st.session_state
                if k.startswith("index_")
            ]
            for k in keys_to_clear:
                del st.session_state[k]
            return True
        # Clear all results when strategies change
        if key == "strategies":
            keys_to_clear = [
                k for k in st.session_state
                if k.startswith("index_") or k.startswith("ret_")
            ]
            for k in keys_to_clear:
                del st.session_state[k]
            return True
    return False


# Call after sidebar selections:
_invalidate_on_change("global_model", selected_model)
_invalidate_on_change("strategies", tuple(selected_strategies))
```

### Responsive layout

Add CSS adjustments for different screen sizes in `app.py`:

```python
# Add at the top of main(), after set_page_config:
st.markdown("""
<style>
    /* Reduce padding on mobile */
    @media (max-width: 768px) {
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }

    /* Improve expander styling */
    .streamlit-expanderHeader {
        font-size: 0.95em;
    }

    /* Metric cards styling */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
    }

    /* Compact tables */
    .stDataFrame {
        font-size: 0.9em;
    }
</style>
""", unsafe_allow_html=True)
```

### Clear cache button

Add to the sidebar in `app.py`:

```python
st.sidebar.markdown("---")
st.sidebar.markdown("**Cache**")

# Show cache stats
index_count = sum(1 for k in st.session_state if k.startswith("index_"))
chunk_count = sum(1 for k in st.session_state if k.startswith("chunks_"))
st.sidebar.caption(
    f"Cached: {index_count} indexes, {chunk_count} chunk sets"
)

if st.sidebar.button("Clear All Caches", type="secondary"):
    keys_to_clear = [
        k for k in st.session_state
        if k.startswith(("index_", "chunks_", "ret_"))
    ]
    for k in keys_to_clear:
        del st.session_state[k]
    st.sidebar.success("Cache cleared!")
    st.rerun()
```

### Timing information

Add timing to operations in `page_compare.py`:

```python
import time

# Wrap chunking:
start = time.perf_counter()
lexi_result = _chunk_document(document, "lexichunk")
lexi_time = time.perf_counter() - start

start = time.perf_counter()
base_result = _chunk_document(document, baseline)
base_time = time.perf_counter() - start

st.toast(
    f"Chunking complete in {lexi_time + base_time:.1f}s",
    icon="checkmark",
)
```

### Toast notifications

```python
# After successful retrieval in page_retrieval.py:
total_time = time.perf_counter() - start_time
st.toast(
    f"Retrieved results for {len(strategies)} strategies in {total_time:.1f}s",
    icon="magnifying-glass",
)
```

## Outputs
- `src/scaffolder/dashboard/app.py` (updated: CSS, cache management, invalidation)
- `src/scaffolder/dashboard/page_compare.py` (updated: timing, toasts)
- `src/scaffolder/dashboard/page_retrieval.py` (updated: progress bars, error handling)
- `src/scaffolder/dashboard/components.py` (updated: error helper functions)

## Acceptance Criteria
1. Progress bar appears during retrieval with per-strategy step names
2. Missing `sentence-transformers` shows a helpful install command, not a raw traceback
3. Changing embedding model in sidebar clears cached indexes
4. "Clear All Caches" button works and shows confirmation
5. Toast notification appears after chunking/retrieval completes
6. Dashboard works on a 1280px wide browser window without horizontal scrolling
7. `make lint` passes on all updated files

## Handoff Notes
- **To Agent A:** No changes needed from your side. The dashboard now handles import errors gracefully for optional dependencies.
- **To Day 12:** The dashboard is polished and functional. Day 12 adds the metrics summary panel (third page) with headline numbers and comparison charts — the "executive summary" view.
- **Decision:** We use `st.session_state` key prefixes (`index_`, `chunks_`, `ret_`) for cache management. This convention makes it easy to selectively clear caches. All code that creates cache entries must use these prefixes.
