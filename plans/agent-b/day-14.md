# Agent B — Day 14: Streamlit Deployment & Dependency Management

## Mission
Prepare the Streamlit dashboard for deployment on Streamlit Community Cloud or similar hosting, create a standalone requirements file, and ensure the app works gracefully without local embedding models installed.

## Context
Days 7-13 built a feature-complete Streamlit dashboard. Now it needs to work outside the developer's machine. The key challenges: (1) sentence-transformers and FAISS are large dependencies that may not be available on all hosts; (2) the app needs to degrade gracefully when optional features are unavailable; (3) deployment configuration must be documented.

## Prerequisites
- All dashboard pages functional (Days 7-13)
- `pyproject.toml` with extras groups (Day 1)
- `src/scaffolder/dashboard/app.py` as the entry point

## Checklist
- [ ] Task 1 — Create `requirements-dashboard.txt` with pinned versions for Streamlit Cloud
- [ ] Task 2 — Add graceful degradation for missing embedding dependencies
- [ ] Task 3 — Create `.streamlit/config.toml` with theme and server settings
- [ ] Task 4 — Create `Procfile` or `streamlit_app.py` for deployment entry point
- [ ] Task 5 — Test that dashboard works in "demo mode" (no embeddings, pre-loaded results)
- [ ] Task 6 — Document deployment steps in `docs/deployment.md`
- [ ] Task 7 — Add `STREAMLIT_DEPLOYMENT.md` with Streamlit Cloud-specific instructions

## Implementation Details

### requirements-dashboard.txt

Pinned versions for Streamlit Community Cloud deployment. This file should be at the repo root.

```
# Core dependencies for Streamlit dashboard
# Install with: pip install -r requirements-dashboard.txt

# Dashboard framework
streamlit>=1.30,<2.0
plotly>=5.18,<6.0

# LexiChunk SDK
lexichunk>=0.1.0

# Chunking baselines
langchain-text-splitters>=0.2.0,<1.0

# Reporting
rich>=13.0,<14.0
pyyaml>=6.0,<7.0
jinja2>=3.1,<4.0

# Numerical (needed for metrics display)
numpy>=1.24,<2.0

# Optional: Local embeddings (comment out for lightweight deployment)
# sentence-transformers>=2.2
# faiss-cpu>=1.7

# Optional: Voyage AI (requires API key)
# voyageai>=0.2
```

### Graceful degradation

Create `src/scaffolder/dashboard/compat.py`:

```python
"""Compatibility layer for optional dependencies in the dashboard."""

from __future__ import annotations

import importlib
from typing import Any


def check_embed_available() -> bool:
    """Check if embedding dependencies are installed."""
    try:
        importlib.import_module("sentence_transformers")
        importlib.import_module("faiss")
        return True
    except ImportError:
        return False


def check_voyage_available() -> bool:
    """Check if Voyage AI dependencies and API key are available."""
    import os
    try:
        importlib.import_module("voyageai")
        return bool(os.getenv("VOYAGE_API_KEY"))
    except ImportError:
        return False


# Feature flags derived from available dependencies
EMBED_AVAILABLE = check_embed_available()
VOYAGE_AVAILABLE = check_voyage_available()


def get_available_features() -> dict[str, bool]:
    """Return a dict of available features."""
    return {
        "embedding": EMBED_AVAILABLE,
        "voyage": VOYAGE_AVAILABLE,
        "chunking": True,  # Always available (lexichunk + langchain are core deps)
        "export": True,     # Always available
    }
```

Update pages to check feature availability:

```python
# In page_retrieval.py, at the top of render_page():
from scaffolder.dashboard.compat import EMBED_AVAILABLE

if not EMBED_AVAILABLE:
    st.warning(
        "Embedding dependencies not installed. Retrieval demo requires "
        "`sentence-transformers` and `faiss-cpu`. Install with: "
        "`pip install 'scaffolder[embed]'`"
    )
    st.info(
        "You can still view pre-computed results on the **Metrics Dashboard** page "
        "by uploading a results JSON file."
    )

    # Show demo with pre-loaded results if available
    _render_demo_mode()
    return
```

### .streamlit/config.toml

```toml
[theme]
primaryColor = "#2196F3"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F5F5F5"
textColor = "#212121"
font = "sans serif"

[server]
headless = true
enableCORS = false
enableXsrfProtection = true
maxUploadSize = 10  # MB

[browser]
gatherUsageStats = false
```

### Deployment entry point

Create `streamlit_app.py` at repo root (Streamlit Cloud looks for this):

```python
"""Entry point for Streamlit Cloud deployment."""

import sys
from pathlib import Path

# Add src to path so scaffolder package is importable
src_path = str(Path(__file__).parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from scaffolder.dashboard.app import main

main()
```

### Demo mode for page_retrieval.py

```python
def _render_demo_mode() -> None:
    """Render retrieval page in demo mode with pre-loaded results."""
    st.subheader("Demo Mode")
    st.markdown(
        "Upload a benchmark results JSON to explore retrieval results "
        "without running live embeddings."
    )

    uploaded = st.file_uploader(
        "Upload results JSON",
        type=["json"],
        key="demo_results_upload",
    )

    if uploaded:
        import json
        data = json.loads(uploaded.getvalue().decode("utf-8"))

        if "retrieval_results" in data and data["retrieval_results"]:
            st.success(f"Loaded {len(data['retrieval_results'])} retrieval results")
            st.session_state["benchmark_result"] = data

            # Show summary
            strategies = {r["strategy"] for r in data["retrieval_results"]}
            models = {r["model"] for r in data["retrieval_results"]}
            st.markdown(
                f"**Strategies:** {', '.join(sorted(strategies))}  \n"
                f"**Models:** {', '.join(sorted(models))}  \n"
                f"**Queries:** {len(data['retrieval_results']) // max(len(strategies), 1)}"
            )

            st.info("Navigate to **Metrics Dashboard** to explore these results.")
        else:
            st.warning("The uploaded JSON does not contain retrieval results.")
```

### docs/deployment.md

Create a deployment guide:

```markdown
# Deployment Guide

## Streamlit Community Cloud

1. Push the repo to GitHub
2. Go to share.streamlit.io
3. Connect your GitHub repository
4. Set the main file to `streamlit_app.py`
5. Set Python version to 3.10+
6. Deploy

### Environment Variables
Set in Streamlit Cloud's "Advanced settings":
- `VOYAGE_API_KEY` (optional) — enables Voyage AI embeddings

### Limitations
- Streamlit Cloud has limited memory (~1GB)
- sentence-transformers models are large (~500MB each)
- For lightweight deployment, use `requirements-dashboard.txt` without embedding deps
- Pre-compute results locally and upload JSON to the dashboard

## Local Deployment

```bash
pip install -e ".[all]"
streamlit run src/scaffolder/dashboard/app.py
```

## Docker (optional)

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install -e ".[dashboard]"
EXPOSE 8501
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501"]
```
```

## Outputs
- `requirements-dashboard.txt`
- `src/scaffolder/dashboard/compat.py` (new)
- `.streamlit/config.toml`
- `streamlit_app.py`
- `docs/deployment.md`
- Updated: `page_retrieval.py` (graceful degradation)

## Acceptance Criteria
1. `pip install -r requirements-dashboard.txt` installs without errors (no sentence-transformers)
2. `streamlit run streamlit_app.py` works from repo root
3. Without sentence-transformers installed: Retrieval page shows helpful warning, Compare page still works for chunking, Metrics page works with uploaded JSON
4. `.streamlit/config.toml` applies the blue theme
5. Upload of results JSON works on the demo mode page
6. `make lint` passes on all new files

## Handoff Notes
- **To Agent A:** The dashboard can now run without your `EmbeddingPipeline` dependencies installed. When embeddings are missing, it shows a demo mode. Your `ChunkingPipeline` is still a core dependency — it should work without sentence-transformers.
- **To Day 15:** Deployment is ready. Day 15 focuses on screenshots/GIFs for the README and starting EXTENSIBILITY.md.
- **Decision:** We use `requirements-dashboard.txt` rather than having Streamlit Cloud read `pyproject.toml` because Cloud doesn't support extras groups well. The requirements file has embedding deps commented out for lightweight deployment.
