# Agent A — Day 08: RetrievalSimulator

## Mission
Build the RetrievalSimulator that loads annotated queries from YAML, embeds them, retrieves top-k chunks from each strategy's FAISS index, and matches results against ground-truth relevant sections to produce RetrievalResult objects.

## Context
Day 7 delivered the `VectorIndex` and `IndexRegistry`. Agent B has been building query annotation YAML files (starting Day 4). Today we consume those queries, run retrieval against every (strategy, model) index, and produce the raw `RetrievalResult` objects that Day 9's metrics will score.

## Prerequisites
- `src/scaffolder/retrieval/index.py` with `VectorIndex`, `IndexRegistry`
- `src/scaffolder/embedding/pipeline.py` with `EmbeddingPipeline`
- `src/scaffolder/models.py` with `AnnotatedQuery`, `RelevantSection`, `RelevanceGrade`, `RetrievalResult`, `RetrievalHit`
- `queries/` directory with YAML files (Agent B creates these)
- `pyyaml` installed

## Checklist
- [ ] Implement `QueryLoader` to parse YAML query files into `AnnotatedQuery` objects
- [ ] Implement `RetrievalSimulator` in `src/scaffolder/retrieval/simulator.py`
- [ ] Implement relevance matching logic (chunk text vs section snippet)
- [ ] Write tests in `tests/test_simulator.py`

## Implementation Details

### Query YAML Format

Agent B creates YAML files in `queries/`. Expected format (coordinate with Agent B):

```yaml
# queries/definition_queries.yaml
queries:
  - id: "def_001"
    text: "What is the definition of Service Provider?"
    document_ids: ["uk_service_agreement"]
    jurisdiction: "uk"
    category: "definition_lookup"
    relevant_sections:
      - document_id: "uk_service_agreement"
        section_id: "clause_1.1"
        text_snippet: "Service Provider means the party providing"
        grade: 3  # exact
      - document_id: "uk_service_agreement"
        section_id: "clause_2.1"
        text_snippet: "The Service Provider shall deliver"
        grade: 2  # same_section
```

### QueryLoader (`src/scaffolder/retrieval/simulator.py`)

```python
"""Retrieval simulation: query loading, execution, and relevance matching."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Sequence

import numpy as np
import yaml

from scaffolder.models import (
    AnnotatedQuery,
    Chunk,
    EmbeddingModelName,
    RelevanceGrade,
    RelevantSection,
    RetrievalHit,
    RetrievalResult,
    StrategyName,
    Jurisdiction,
)

logger = logging.getLogger(__name__)


class QueryLoader:
    """Loads annotated queries from YAML files in the queries/ directory."""

    def __init__(self, queries_dir: Path | None = None) -> None:
        self._queries_dir = queries_dir or Path("queries")

    def load_all(self) -> list[AnnotatedQuery]:
        """Load all queries from all YAML files in the queries directory.

        Returns:
            List of AnnotatedQuery, sorted by id.

        Raises:
            FileNotFoundError: If queries directory does not exist.
        """
        if not self._queries_dir.is_dir():
            raise FileNotFoundError(
                f"Queries directory not found: {self._queries_dir}"
            )

        all_queries: list[AnnotatedQuery] = []
        yaml_files = sorted(self._queries_dir.glob("*.yaml")) + sorted(
            self._queries_dir.glob("*.yml")
        )

        if not yaml_files:
            logger.warning("No YAML files found in %s", self._queries_dir)
            return []

        for path in yaml_files:
            queries = self._load_file(path)
            all_queries.extend(queries)
            logger.info("Loaded %d queries from %s", len(queries), path.name)

        return sorted(all_queries, key=lambda q: q.id)

    def _load_file(self, path: Path) -> list[AnnotatedQuery]:
        """Parse a single YAML file into AnnotatedQuery objects."""
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data or "queries" not in data:
            return []

        queries: list[AnnotatedQuery] = []
        for q in data["queries"]:
            sections = []
            for s in q.get("relevant_sections", []):
                sections.append(RelevantSection(
                    document_id=s["document_id"],
                    section_id=s["section_id"],
                    text_snippet=s["text_snippet"],
                    grade=RelevanceGrade(int(s["grade"])),
                ))

            queries.append(AnnotatedQuery(
                id=q["id"],
                text=q["text"],
                document_ids=q.get("document_ids", []),
                jurisdiction=Jurisdiction(q["jurisdiction"]),
                relevant_sections=tuple(sections),
                category=q.get("category", "general"),
            ))

        return queries
```

### RetrievalSimulator

```python
class RetrievalSimulator:
    """Runs queries against FAISS indices and produces RetrievalResults.

    For each query, the simulator:
    1. Embeds the query text using the specified model.
    2. Searches the (strategy, model) index for top-k results.
    3. Matches retrieved chunks against annotated relevant sections.
    4. Produces a RetrievalResult with matched relevance info.

    Usage:
        sim = RetrievalSimulator(
            index_registry=registry,
            embedding_pipeline=emb_pipeline,
        )
        results = sim.run(queries, strategies, models, k=10)
    """

    def __init__(
        self,
        index_registry: IndexRegistry,
        embedding_pipeline: EmbeddingPipeline,
    ) -> None:
        from scaffolder.retrieval.index import IndexRegistry
        from scaffolder.embedding.pipeline import EmbeddingPipeline

        self._registry = index_registry
        self._embedding = embedding_pipeline

    def run(
        self,
        queries: Sequence[AnnotatedQuery],
        strategies: Sequence[StrategyName],
        models: Sequence[EmbeddingModelName],
        k: int = 10,
    ) -> list[RetrievalResult]:
        """Run all queries against all (strategy, model) indices.

        Returns:
            One RetrievalResult per (query, strategy, model) combination.
            Total results = len(queries) * len(strategies) * len(models).
        """
        results: list[RetrievalResult] = []

        for model in models:
            # Batch-embed all query texts at once for efficiency
            query_texts = [q.text for q in queries]
            query_embeddings = self._embedding.embed_texts(query_texts, model)

            for strategy in strategies:
                try:
                    index = self._registry.get(strategy, model)
                except KeyError:
                    logger.warning(
                        "No index for %s/%s, skipping.", strategy.value, model.value
                    )
                    continue

                for i, query in enumerate(queries):
                    query_vec = query_embeddings[i]
                    hits = index.search(query_vec, k=k)

                    # Count relevant retrieved
                    relevant_retrieved = sum(
                        1 for h in hits
                        if self._is_relevant(h.chunk, query.relevant_sections)
                    )

                    results.append(RetrievalResult(
                        query=query,
                        strategy=strategy,
                        embedding_model=model,
                        hits=tuple(hits),
                        relevant_retrieved=relevant_retrieved,
                        total_relevant=len(query.relevant_sections),
                    ))

        logger.info(
            "Simulation complete: %d results (%d queries x %d strategies x %d models)",
            len(results), len(queries), len(strategies), len(models),
        )
        return results

    def _is_relevant(
        self,
        chunk: Chunk,
        relevant_sections: tuple[RelevantSection, ...] | Sequence[RelevantSection],
    ) -> bool:
        """Check if a retrieved chunk matches any relevant section.

        Matching criteria (any of):
        1. Chunk text contains the section's text_snippet (first 200 chars).
        2. Chunk document_id matches AND section_id appears in chunk text.
        3. Word overlap between chunk and snippet exceeds 60%.
        """
        chunk_lower = chunk.text.lower()

        for section in relevant_sections:
            # Filter by document if section specifies one
            if section.document_id and chunk.document_id != section.document_id:
                continue

            snippet_lower = section.text_snippet.lower().strip()
            if not snippet_lower:
                continue

            # Check 1: substring match
            if snippet_lower in chunk_lower:
                return True

            # Check 2: section_id appears in chunk
            if section.section_id:
                # e.g. "clause_5.2" -> look for "5.2" in chunk
                section_num = section.section_id.replace("clause_", "").replace("section_", "")
                if section_num in chunk.text:
                    return True

            # Check 3: word overlap
            snippet_words = set(snippet_lower.split())
            chunk_words = set(chunk_lower.split())
            if snippet_words and len(snippet_words & chunk_words) / len(snippet_words) > 0.6:
                return True

        return False

    def get_relevance_grade(
        self,
        chunk: Chunk,
        relevant_sections: tuple[RelevantSection, ...] | Sequence[RelevantSection],
    ) -> RelevanceGrade:
        """Get the relevance grade for a chunk (used in NDCG).

        Returns the highest matching grade, or IRRELEVANT if no match.
        """
        best_grade = RelevanceGrade.IRRELEVANT
        chunk_lower = chunk.text.lower()

        for section in relevant_sections:
            if section.document_id and chunk.document_id != section.document_id:
                continue

            snippet_lower = section.text_snippet.lower().strip()
            if not snippet_lower:
                continue

            # Same matching logic as _is_relevant
            matched = False
            if snippet_lower in chunk_lower:
                matched = True
            elif section.section_id:
                section_num = section.section_id.replace("clause_", "").replace("section_", "")
                if section_num in chunk.text:
                    matched = True
            else:
                snippet_words = set(snippet_lower.split())
                chunk_words = set(chunk_lower.split())
                if snippet_words and len(snippet_words & chunk_words) / len(snippet_words) > 0.6:
                    matched = True

            if matched and section.grade.value > best_grade.value:
                best_grade = section.grade

        return best_grade
```

### Package init update (`src/scaffolder/retrieval/__init__.py`)

```python
"""FAISS indexing and retrieval simulation."""

from scaffolder.retrieval.index import (
    VectorIndex,
    IndexKey,
    IndexRegistry,
    build_all_indices,
)
from scaffolder.retrieval.simulator import (
    QueryLoader,
    RetrievalSimulator,
)

__all__ = [
    "VectorIndex",
    "IndexKey",
    "IndexRegistry",
    "build_all_indices",
    "QueryLoader",
    "RetrievalSimulator",
]
```

### Tests (`tests/test_simulator.py`)

```python
"""Tests for RetrievalSimulator and QueryLoader."""

# QueryLoader tests:
# 1. Loads queries from a temp YAML file with known content
# 2. Parses relevant_sections with correct grades
# 3. Empty directory returns empty list
# 4. Missing directory raises FileNotFoundError
# 5. Queries are sorted by id

# RetrievalSimulator tests (with mock index and embeddings):
# 1. run() returns correct number of results (queries x strategies x models)
# 2. _is_relevant() correctly matches substring snippets
# 3. _is_relevant() correctly matches section_id patterns
# 4. _is_relevant() rejects non-matching chunks
# 5. _is_relevant() respects document_id filtering
# 6. get_relevance_grade() returns highest matching grade
# 7. get_relevance_grade() returns IRRELEVANT for non-matching chunks

# Use tmp_path fixture for YAML files:
def test_query_loader(tmp_path):
    yaml_content = """
queries:
  - id: "test_001"
    text: "What is the definition?"
    document_ids: ["test_doc"]
    jurisdiction: "uk"
    category: "definition_lookup"
    relevant_sections:
      - document_id: "test_doc"
        section_id: "clause_1"
        text_snippet: "means the party"
        grade: 3
"""
    (tmp_path / "test.yaml").write_text(yaml_content)
    loader = QueryLoader(queries_dir=tmp_path)
    queries = loader.load_all()
    assert len(queries) == 1
    assert queries[0].relevant_sections[0].grade == RelevanceGrade.EXACT
```

## Outputs
- `src/scaffolder/retrieval/simulator.py`
- `src/scaffolder/retrieval/__init__.py` (updated)
- `tests/test_simulator.py`

## Acceptance Criteria
1. `QueryLoader` correctly parses YAML files from `queries/`.
2. `RetrievalSimulator.run()` produces one `RetrievalResult` per (query, strategy, model).
3. Relevance matching correctly identifies matching chunks.
4. `pytest tests/test_simulator.py -v` -- all tests pass.
5. `mypy src/scaffolder/retrieval/ --strict` passes.
6. `ruff check src/scaffolder/retrieval/` passes.

## Handoff Notes
- **To Agent B:** The `QueryLoader` expects YAML files in `queries/` with the schema shown above. Each query needs: `id`, `text`, `document_ids`, `jurisdiction`, `category`, `relevant_sections` (with `document_id`, `section_id`, `text_snippet`, `grade`). Grade values: 3=exact, 2=same_section, 1=related.
- **To Day 9:** `RetrievalSimulator.run()` returns `list[RetrievalResult]`. Day 9's retrieval metrics functions will compute P@k, R@k, MRR, NDCG from these results. The `get_relevance_grade()` method is needed for graded relevance in NDCG.
- **Design note:** Relevance matching uses three criteria (substring, section_id, word overlap). This is intentionally fuzzy because chunk boundaries vary across strategies, so an exact string match would miss valid hits where the chunk contains the relevant text but with slightly different boundaries.
