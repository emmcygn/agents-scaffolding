# Agent A — Day 02: FixtureManager & Document Loading

## Mission
Build the FixtureManager that auto-discovers legal document fixtures, loads them with jurisdiction/type metadata, and provides them as `Document` dataclass instances for the rest of the pipeline.

## Context
Day 1 established the data models (`Document`, `Chunk`, `ChunkSet`, etc.) and the directory structure. Agent B completed `pyproject.toml`, `config.py`, `.gitignore`, and the Makefile skeleton. The `src/scaffolder/fixtures/documents/` directory exists but is empty. Today we populate it with the 5 fixture files from LexiChunk and build the manager.

Agent B is working on `config.py` (BenchmarkConfig, YAML loading) today. No dependencies on Agent B's work for this day.

## Prerequisites
- `src/scaffolder/models.py` exists with `Document`, `Jurisdiction`, `DocumentType` (from Day 1)
- `src/scaffolder/fixtures/` directory exists with `__init__.py`
- `src/scaffolder/fixtures/documents/` directory exists
- `lexichunk` installed (to copy fixture files from its test data)

## Checklist
- [ ] Copy 5 fixture documents into `src/scaffolder/fixtures/documents/`
- [ ] Create filename-to-metadata mapping
- [ ] Implement `FixtureManager` class in `src/scaffolder/fixtures/__init__.py`
- [ ] Write unit tests in `tests/test_fixtures.py`
- [ ] Verify all 5 documents load correctly

## Implementation Details

### Fixture Documents

Copy these 5 files from LexiChunk's test fixtures into `src/scaffolder/fixtures/documents/`:

1. `uk_service_agreement.txt` -- UK jurisdiction, service_agreement type
2. `uk_terms_conditions.txt` -- UK jurisdiction, terms_conditions type
3. `us_msa.txt` -- US jurisdiction, msa type
4. `us_terms_of_service.txt` -- US jurisdiction, terms_of_service type
5. `eu_gdpr_excerpt.txt` -- EU jurisdiction, gdpr_excerpt type

To locate LexiChunk's fixture files programmatically:
```python
import lexichunk
import os
lexichunk_dir = os.path.dirname(lexichunk.__file__)
# Check: {lexichunk_dir}/tests/fixtures/ or {lexichunk_dir}/fixtures/
# or use: pip show lexichunk to find the install path, then search for .txt files
```

If LexiChunk fixture files are not directly accessible, create representative legal document fixtures. Each should be 2,000-10,000 characters of realistic legal text with:
- Numbered clauses/sections (hierarchical: 1. -> 1.1 -> 1.1.1)
- Defined terms in quotes or caps (e.g., "Service Provider", "Effective Date")
- Cross-references (e.g., "as defined in Section 3.2", "subject to Clause 7")
- Jurisdiction-specific language (UK: "shall", US: "will", EU: references to GDPR articles)

### Filename-to-Metadata Mapping

```python
_FIXTURE_METADATA: dict[str, tuple[Jurisdiction, DocumentType]] = {
    "uk_service_agreement.txt": (Jurisdiction.UK, DocumentType.SERVICE_AGREEMENT),
    "uk_terms_conditions.txt": (Jurisdiction.UK, DocumentType.TERMS_CONDITIONS),
    "us_msa.txt": (Jurisdiction.US, DocumentType.MSA),
    "us_terms_of_service.txt": (Jurisdiction.US, DocumentType.TERMS_OF_SERVICE),
    "eu_gdpr_excerpt.txt": (Jurisdiction.EU, DocumentType.GDPR_EXCERPT),
}
```

### FixtureManager (`src/scaffolder/fixtures/__init__.py`)

```python
"""Fixture loading and document management."""

from __future__ import annotations

import logging
from pathlib import Path

from scaffolder.models import Document, DocumentType, Jurisdiction

logger = logging.getLogger(__name__)

_DOCUMENTS_DIR = Path(__file__).parent / "documents"

_FIXTURE_METADATA: dict[str, tuple[Jurisdiction, DocumentType]] = {
    "uk_service_agreement.txt": (Jurisdiction.UK, DocumentType.SERVICE_AGREEMENT),
    "uk_terms_conditions.txt": (Jurisdiction.UK, DocumentType.TERMS_CONDITIONS),
    "us_msa.txt": (Jurisdiction.US, DocumentType.MSA),
    "us_terms_of_service.txt": (Jurisdiction.US, DocumentType.TERMS_OF_SERVICE),
    "eu_gdpr_excerpt.txt": (Jurisdiction.EU, DocumentType.GDPR_EXCERPT),
}


class FixtureManager:
    """Discovers and loads legal document fixtures from the documents/ directory.

    Usage:
        fm = FixtureManager()
        docs = fm.load_all()           # returns list[Document], sorted by id
        doc = fm.get_by_id("us_msa")   # returns single Document
        uk = fm.get_by_jurisdiction(Jurisdiction.UK)  # returns list[Document]
    """

    def __init__(self, documents_dir: Path | None = None) -> None:
        self._documents_dir = documents_dir or _DOCUMENTS_DIR
        self._documents: dict[str, Document] = {}
        self._loaded = False

    def load_all(self) -> list[Document]:
        """Discover and load all .txt files in the documents directory.

        Returns:
            List of Document instances, sorted by id.

        Raises:
            FileNotFoundError: If documents directory does not exist.
            ValueError: If a .txt file has no metadata mapping.
        """
        if not self._documents_dir.is_dir():
            raise FileNotFoundError(
                f"Documents directory not found: {self._documents_dir}"
            )

        self._documents.clear()
        txt_files = sorted(self._documents_dir.glob("*.txt"))

        if not txt_files:
            logger.warning("No .txt files found in %s", self._documents_dir)
            return []

        for path in txt_files:
            doc = self._load_document(path)
            self._documents[doc.id] = doc
            logger.info(
                "Loaded %s (%s, %s) -- %d chars, %d lines",
                doc.id,
                doc.jurisdiction.value,
                doc.document_type.value,
                doc.char_count,
                doc.line_count,
            )

        self._loaded = True
        return self.get_all()

    def get_all(self) -> list[Document]:
        """Return all loaded documents, sorted by id."""
        if not self._loaded:
            self.load_all()
        return sorted(self._documents.values(), key=lambda d: d.id)

    def get_by_id(self, document_id: str) -> Document:
        """Return a specific document by id.

        Raises:
            KeyError: If document_id is not found.
        """
        if not self._loaded:
            self.load_all()
        if document_id not in self._documents:
            raise KeyError(
                f"Document '{document_id}' not found. "
                f"Available: {sorted(self._documents.keys())}"
            )
        return self._documents[document_id]

    def get_by_jurisdiction(self, jurisdiction: Jurisdiction) -> list[Document]:
        """Return all documents for a given jurisdiction."""
        if not self._loaded:
            self.load_all()
        return [
            d for d in self._documents.values()
            if d.jurisdiction == jurisdiction
        ]

    @property
    def document_ids(self) -> list[str]:
        """Return sorted list of all document ids."""
        if not self._loaded:
            self.load_all()
        return sorted(self._documents.keys())

    def _load_document(self, path: Path) -> Document:
        """Load a single document from a file path."""
        filename = path.name
        if filename not in _FIXTURE_METADATA:
            raise ValueError(
                f"No metadata mapping for '{filename}'. "
                f"Add it to _FIXTURE_METADATA in fixtures/__init__.py."
            )

        jurisdiction, document_type = _FIXTURE_METADATA[filename]
        text = path.read_text(encoding="utf-8")

        doc_id = path.stem  # e.g., "uk_service_agreement"

        return Document(
            id=doc_id,
            text=text,
            jurisdiction=jurisdiction,
            document_type=document_type,
            source=filename,
        )
```

### Tests (`tests/test_fixtures.py`)

```python
"""Tests for FixtureManager."""

import pytest
from pathlib import Path

from scaffolder.fixtures import FixtureManager
from scaffolder.models import Document, Jurisdiction, DocumentType


class TestFixtureManager:
    """Tests for fixture loading and discovery."""

    def test_load_all_returns_five_documents(self) -> None:
        manager = FixtureManager()
        docs = manager.load_all()
        assert len(docs) == 5

    def test_all_documents_have_non_empty_text(self) -> None:
        manager = FixtureManager()
        for doc in manager.load_all():
            assert len(doc.text) > 0
            assert doc.char_count > 0

    def test_all_documents_have_line_count(self) -> None:
        manager = FixtureManager()
        for doc in manager.load_all():
            assert doc.line_count >= 1

    def test_document_ids_match_filenames(self) -> None:
        manager = FixtureManager()
        manager.load_all()
        expected_ids = {
            "uk_service_agreement",
            "uk_terms_conditions",
            "us_msa",
            "us_terms_of_service",
            "eu_gdpr_excerpt",
        }
        assert set(manager.document_ids) == expected_ids

    def test_get_by_id(self) -> None:
        manager = FixtureManager()
        doc = manager.get_by_id("uk_service_agreement")
        assert doc.jurisdiction == Jurisdiction.UK
        assert doc.document_type == DocumentType.SERVICE_AGREEMENT

    def test_get_by_id_not_found_raises(self) -> None:
        manager = FixtureManager()
        with pytest.raises(KeyError, match="nonexistent"):
            manager.get_by_id("nonexistent")

    def test_get_by_jurisdiction(self) -> None:
        manager = FixtureManager()
        uk_docs = manager.get_by_jurisdiction(Jurisdiction.UK)
        assert len(uk_docs) == 2
        for doc in uk_docs:
            assert doc.jurisdiction == Jurisdiction.UK

    def test_get_by_jurisdiction_us(self) -> None:
        manager = FixtureManager()
        us_docs = manager.get_by_jurisdiction(Jurisdiction.US)
        assert len(us_docs) == 2

    def test_get_by_jurisdiction_eu(self) -> None:
        manager = FixtureManager()
        eu_docs = manager.get_by_jurisdiction(Jurisdiction.EU)
        assert len(eu_docs) == 1

    def test_lazy_loading(self) -> None:
        manager = FixtureManager()
        assert not manager._loaded
        docs = manager.get_all()
        assert manager._loaded
        assert len(docs) == 5

    def test_missing_directory_raises(self) -> None:
        manager = FixtureManager(documents_dir=Path("/nonexistent/path"))
        with pytest.raises(FileNotFoundError):
            manager.load_all()

    def test_document_is_frozen(self) -> None:
        manager = FixtureManager()
        doc = manager.get_by_id("us_msa")
        with pytest.raises(AttributeError):
            doc.text = "modified"  # type: ignore[misc]

    def test_char_count_matches_text_length(self) -> None:
        manager = FixtureManager()
        for doc in manager.load_all():
            assert doc.char_count == len(doc.text)
```

## Outputs
- `src/scaffolder/fixtures/__init__.py` (FixtureManager implementation)
- `src/scaffolder/fixtures/documents/uk_service_agreement.txt`
- `src/scaffolder/fixtures/documents/uk_terms_conditions.txt`
- `src/scaffolder/fixtures/documents/us_msa.txt`
- `src/scaffolder/fixtures/documents/us_terms_of_service.txt`
- `src/scaffolder/fixtures/documents/eu_gdpr_excerpt.txt`
- `tests/test_fixtures.py`

## Acceptance Criteria
1. `python -c "from scaffolder.fixtures import FixtureManager; fm = FixtureManager(); docs = fm.load_all(); print(len(docs))"` prints `5`.
2. Each document has `char_count > 100`.
3. `pytest tests/test_fixtures.py -v` -- all tests pass.
4. `mypy src/scaffolder/fixtures/__init__.py --strict` passes.
5. `ruff check src/scaffolder/fixtures/` passes.

## Handoff Notes
- **To Day 3:** `FixtureManager().load_all()` returns `list[Document]`. The `ChunkingPipeline` will iterate over these and pass each `Document` to every `ChunkingStrategy`.
- **To Agent B:** Fixture documents are now in `src/scaffolder/fixtures/documents/`. If you need to reference them from config or queries, the document IDs are the filenames without `.txt` extension (e.g., `uk_service_agreement`).
- The `FixtureManager` supports custom `documents_dir` for testing with mock fixtures.
- Documents are frozen dataclasses -- they cannot be mutated after creation. `char_count` and `line_count` are computed in `__post_init__`.
