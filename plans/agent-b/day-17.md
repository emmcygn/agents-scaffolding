# Agent B — Day 17: Streamlit Edge Cases & Robustness

## Mission
Harden the Streamlit dashboard against edge cases: bad file uploads, huge files, empty documents, documents with no legal structure, network errors for Voyage, and other failure scenarios that would degrade the user experience.

## Context
Days 7-13 built the dashboard for the happy path. Day 14 added basic graceful degradation for missing dependencies. Today we systematically test and handle every edge case that a real user might encounter. This is the defensive programming day — every input validation gap and error handling hole gets plugged.

## Prerequisites
- All Streamlit pages functional (Days 7-13)
- `src/scaffolder/dashboard/compat.py` (Day 14)
- `src/scaffolder/dashboard/components.py` with error helpers (Day 11)

## Checklist
- [ ] Task 1 — File upload validation: non-text files, encoding errors, file size limits
- [ ] Task 2 — Empty document handling: empty string, whitespace-only, very short text
- [ ] Task 3 — Non-legal document handling: graceful behavior when text has no legal structure
- [ ] Task 4 — Voyage network error handling: timeout, DNS failure, invalid response
- [ ] Task 5 — Large document handling: impose file size limit, truncation with warning
- [ ] Task 6 — Concurrent session state: handle multiple browser tabs
- [ ] Task 7 — Write `tests/test_dashboard_edge_cases.py`

## Implementation Details

### File upload validation

Update `page_compare.py` upload handler:

```python
# Constants
MAX_UPLOAD_SIZE_BYTES = 100 * 1024  # 100 KB
MAX_DOCUMENT_CHARS = 200_000  # 200K characters
MIN_DOCUMENT_CHARS = 50  # Minimum viable document

def _validate_upload(uploaded_file: Any) -> tuple[str | None, str | None]:
    """Validate an uploaded file.

    Returns:
        (content, None) on success, (None, error_message) on failure.
    """
    # Check file size
    file_size = uploaded_file.size
    if file_size > MAX_UPLOAD_SIZE_BYTES:
        return None, (
            f"File too large: {file_size / 1024:.0f} KB. "
            f"Maximum allowed: {MAX_UPLOAD_SIZE_BYTES / 1024:.0f} KB. "
            f"Large files slow down chunking and embedding significantly."
        )

    # Check file type (belt-and-suspenders — Streamlit already filters)
    if not uploaded_file.name.lower().endswith(".txt"):
        return None, (
            f"Unsupported file type: {uploaded_file.name}. "
            f"Please upload a .txt file."
        )

    # Try to decode
    raw_bytes = uploaded_file.getvalue()
    content: str | None = None

    # Try UTF-8 first, then common fallbacks
    for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            content = raw_bytes.decode(encoding)
            break
        except (UnicodeDecodeError, ValueError):
            continue

    if content is None:
        return None, (
            "Unable to decode file. Please ensure it is a UTF-8 or "
            "Latin-1 encoded text file."
        )

    # Check content length
    if len(content.strip()) < MIN_DOCUMENT_CHARS:
        return None, (
            f"Document too short ({len(content.strip())} characters). "
            f"Minimum: {MIN_DOCUMENT_CHARS} characters."
        )

    # Truncate with warning if very long
    if len(content) > MAX_DOCUMENT_CHARS:
        content = content[:MAX_DOCUMENT_CHARS]
        st.warning(
            f"Document truncated to {MAX_DOCUMENT_CHARS:,} characters "
            f"for performance. Original: {len(raw_bytes):,} bytes."
        )

    return content, None
```

Replace the upload handler in `render_page()`:

```python
elif doc_source == "Upload file":
    uploaded = st.file_uploader(
        "Upload a .txt legal document (max 100 KB)",
        type=["txt"],
        key="file_upload",
    )
    if uploaded is not None:
        content, error = _validate_upload(uploaded)
        if error:
            st.error(error)
        else:
            document = _create_document_from_upload(content, uploaded.name)
            st.success(f"Loaded: {uploaded.name} ({len(content):,} chars)")
```

### Empty and short document handling

Add to `page_compare.py`:

```python
def _validate_document(doc: Document) -> str | None:
    """Validate a document before chunking.

    Returns None if valid, error message if invalid.
    """
    text = doc.text.strip()

    if not text:
        return "Document is empty. Please provide a document with text content."

    if len(text) < MIN_DOCUMENT_CHARS:
        return (
            f"Document too short ({len(text)} characters). "
            f"Chunking requires at least {MIN_DOCUMENT_CHARS} characters."
        )

    # Check for binary content (null bytes)
    if "\x00" in text:
        return "Document appears to contain binary content. Please upload a text file."

    return None

# Before chunking:
if document is not None:
    validation_error = _validate_document(document)
    if validation_error:
        st.error(validation_error)
        return
```

### Non-legal document handling

When a document has no legal structure, LexiChunk may still work but with limited metadata. Handle this gracefully:

```python
# After chunking in _render_results:
def _check_legal_structure(lexi: ChunkSet) -> None:
    """Warn if the document appears to have no legal structure."""
    # Check if any chunk has meaningful clause types
    clause_types = [
        c.metadata.get("clause_type", "general")
        for c in lexi.chunks
    ]
    non_general = [ct for ct in clause_types if ct != "general"]

    if not non_general:
        st.warning(
            "This document does not appear to have recognized legal structure. "
            "LexiChunk works best with structured legal documents (contracts, "
            "regulations, terms of service). Clause type classification, hierarchy "
            "tracking, and cross-reference detection may not produce useful results."
        )
    elif len(non_general) < len(clause_types) * 0.2:
        st.info(
            f"Only {len(non_general)}/{len(clause_types)} chunks have recognized "
            f"clause types. The document may have limited legal structure."
        )
```

### Voyage network error handling

Update `page_retrieval.py` to handle Voyage-specific errors:

```python
# In the retrieval error handler:
except Exception as e:
    error_str = str(e)

    if "VoyageEmbedderError" in type(e).__name__ or "voyage" in error_str.lower():
        if "authentication" in error_str.lower() or "401" in error_str:
            st.error(
                "Voyage API authentication failed. "
                "Please check your VOYAGE_API_KEY environment variable."
            )
        elif "rate" in error_str.lower() or "429" in error_str:
            st.error(
                "Voyage API rate limit exceeded. Please wait a moment "
                "and try again, or switch to a local embedding model."
            )
        elif "timeout" in error_str.lower() or "connection" in error_str.lower():
            st.error(
                "Network error connecting to Voyage API. "
                "Check your internet connection or switch to a local model."
            )
        else:
            st.error(f"Voyage API error: {e}")

        st.info("Switch to a local model (all-MiniLM-L6-v2) in the sidebar to continue.")
    elif "CUDA" in error_str or "out of memory" in error_str.lower():
        st.error(
            "GPU memory error. The embedding model may be too large. "
            "Try a smaller model (all-MiniLM-L6-v2) or ensure sufficient GPU memory."
        )
    else:
        st.error(f"Retrieval failed: {e}")
```

### Paste text validation

```python
elif doc_source == "Paste text":
    text = st.text_area(
        "Paste legal document text",
        height=200,
        placeholder="Paste your legal document text here...",
        key="paste_text",
        max_chars=MAX_DOCUMENT_CHARS,
    )
    if text.strip():
        if len(text.strip()) < MIN_DOCUMENT_CHARS:
            st.warning(
                f"Text too short ({len(text.strip())} chars). "
                f"Minimum: {MIN_DOCUMENT_CHARS} chars."
            )
        else:
            document = _create_document_from_text(text.strip())
            st.caption(f"Length: {len(text.strip()):,} chars")
```

### tests/test_dashboard_edge_cases.py

```python
"""Tests for dashboard edge case handling."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


class TestFileUploadValidation:
    """Test file upload validation logic."""

    def test_oversized_file_rejected(self) -> None:
        from scaffolder.dashboard.page_compare import _validate_upload

        mock_file = MagicMock()
        mock_file.size = 200 * 1024  # 200 KB
        mock_file.name = "big_file.txt"

        content, error = _validate_upload(mock_file)
        assert content is None
        assert "too large" in error

    def test_empty_file_rejected(self) -> None:
        from scaffolder.dashboard.page_compare import _validate_upload

        mock_file = MagicMock()
        mock_file.size = 10
        mock_file.name = "empty.txt"
        mock_file.getvalue.return_value = b"   "

        content, error = _validate_upload(mock_file)
        assert content is None
        assert "too short" in error

    def test_binary_content_rejected(self) -> None:
        from scaffolder.dashboard.page_compare import _validate_document
        from scaffolder.models import Document

        doc = Document(
            id="test",
            text="Hello\x00World",
            jurisdiction="unknown",
            document_type="unknown",
            source_path="<test>",
        )
        error = _validate_document(doc)
        assert error is not None
        assert "binary" in error

    def test_valid_file_accepted(self) -> None:
        from scaffolder.dashboard.page_compare import _validate_upload

        mock_file = MagicMock()
        mock_file.size = 5000
        mock_file.name = "contract.txt"
        mock_file.getvalue.return_value = (
            b"1. DEFINITIONS\n1.1 This agreement...\n" * 10
        )

        content, error = _validate_upload(mock_file)
        assert error is None
        assert content is not None


class TestDocumentValidation:
    """Test document content validation."""

    def test_empty_document(self) -> None:
        from scaffolder.dashboard.page_compare import _validate_document
        from scaffolder.models import Document

        doc = Document(
            id="test", text="", jurisdiction="unknown",
            document_type="unknown", source_path="<test>",
        )
        error = _validate_document(doc)
        assert error is not None
        assert "empty" in error

    def test_whitespace_only(self) -> None:
        from scaffolder.dashboard.page_compare import _validate_document
        from scaffolder.models import Document

        doc = Document(
            id="test", text="   \n\n\t  ",
            jurisdiction="unknown", document_type="unknown",
            source_path="<test>",
        )
        error = _validate_document(doc)
        assert error is not None
```

## Outputs
- `src/scaffolder/dashboard/page_compare.py` (updated: validation, edge cases)
- `src/scaffolder/dashboard/page_retrieval.py` (updated: Voyage error handling, edge cases)
- `tests/test_dashboard_edge_cases.py`

## Acceptance Criteria
1. Uploading a >100KB file shows a clear error message
2. Pasting empty text does not crash the app
3. Non-legal text (e.g., a recipe) shows a "no legal structure" warning
4. Voyage API errors show actionable messages with "switch to local model" hint
5. Binary file content is rejected with a helpful message
6. All tests in `test_dashboard_edge_cases.py` pass
7. `make lint` passes

## Handoff Notes
- **To Agent A:** No changes needed from your side. The dashboard now handles all the edge cases that could cause your pipeline to crash or behave unexpectedly.
- **To Day 18:** Dashboard is hardened. Day 18 is README writing (pair with Agent A). Agent B contributes: installation, dashboard usage, screenshots, deployment instructions.
- **Decision:** We set a 100KB file size limit. This is generous for legal text files (a typical contract is 20-50KB) but prevents someone from uploading a massive file that would crash the embedding pipeline. The limit can be raised in `.streamlit/config.toml` if needed.
