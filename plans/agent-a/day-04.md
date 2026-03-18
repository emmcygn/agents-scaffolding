# Agent A — Day 04: Structural Metrics (Core Three)

## Mission
Implement the three core structural quality metrics -- clause fragmentation rate, definition preservation rate, and cross-reference resolution rate -- that measure how well each chunking strategy preserves the semantic structure of legal documents.

## Context
Day 3 delivered the `ChunkingPipeline` with four strategies, each producing `ChunkSet` instances. LexiChunk's wrapper extracts rich metadata (clause_type, defined_terms, cross_references, section_hierarchy) into `Chunk.metadata`. Baseline strategies have empty or minimal metadata. Today we build metrics that use LexiChunk's structural parser as ground truth to evaluate all strategies.

Agent B is working on query annotation YAML files today. No dependency on their work.

## Prerequisites
- `src/scaffolder/models.py` with `Chunk`, `ChunkSet`, `Document`, `StructuralMetrics`
- `src/scaffolder/chunking/strategies.py` with all four strategies working
- `lexichunk` installed (used for ground-truth structure parsing)
- `src/scaffolder/metrics/__init__.py` exists (stub from Day 1)

## Checklist
- [ ] Implement `GroundTruthStructure` dataclass and `get_ground_truth()` in `src/scaffolder/metrics/structural.py`
- [ ] Implement `clause_fragmentation_rate()` in `src/scaffolder/metrics/structural.py`
- [ ] Implement `definition_preservation_rate()` in `src/scaffolder/metrics/structural.py`
- [ ] Implement `cross_ref_resolution_rate()` in `src/scaffolder/metrics/structural.py`
- [ ] Implement helper regex fallbacks `_extract_defined_terms_regex()` and `_extract_cross_refs_regex()`
- [ ] Implement `compute_structural_metrics()` convenience function (with placeholders for Day 5 metrics)
- [ ] Write unit tests in `tests/test_structural_metrics.py`

## Implementation Details

### Ground Truth Extraction

All structural metrics compare a `ChunkSet` (from any strategy) against a ground-truth structural parse produced by LexiChunk. The ground truth is obtained by chunking the same document with LexiChunk and examining its metadata.

```python
"""Structural quality metrics for evaluating chunking strategies."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from scaffolder.models import Chunk, ChunkSet, Document, StructuralMetrics

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class GroundTruthStructure:
    """Ground truth structural elements extracted via LexiChunk."""
    clauses: list[str]                         # list of clause texts
    clause_boundaries: list[tuple[int, int]]   # (start_char, end_char) in original text
    defined_terms: set[str]                    # all defined terms in the document
    cross_references: list[dict[str, str]]     # list of {source, target, text}
    max_hierarchy_depth: int                   # deepest nesting level (e.g. 3 for "1.2.1")


# Cache ground truth per document to avoid re-parsing
_gt_cache: dict[str, GroundTruthStructure] = {}


def get_ground_truth(document: Document) -> GroundTruthStructure:
    """Parse a document with LexiChunk to extract ground truth structure.

    Results are cached by document.id so repeated calls are free.
    """
    if document.id in _gt_cache:
        return _gt_cache[document.id]

    from lexichunk import LegalChunker

    chunker = LegalChunker()
    legal_chunks = chunker.chunk(document.text, document_id=document.id)

    clauses: list[str] = []
    clause_boundaries: list[tuple[int, int]] = []
    all_defined_terms: set[str] = set()
    all_cross_refs: list[dict[str, str]] = []
    max_depth = 0

    for lc in legal_chunks:
        clauses.append(lc.text)
        # Approximate boundary from text position in original
        start = document.text.find(lc.text[:80]) if len(lc.text) >= 80 else document.text.find(lc.text)
        if start >= 0:
            clause_boundaries.append((start, start + len(lc.text)))

        if hasattr(lc, "defined_terms") and lc.defined_terms:
            all_defined_terms.update(lc.defined_terms)

        if hasattr(lc, "cross_references") and lc.cross_references:
            for ref in lc.cross_references:
                if isinstance(ref, dict):
                    all_cross_refs.append(ref)
                else:
                    all_cross_refs.append({"text": str(ref)})

        if hasattr(lc, "section_hierarchy") and lc.section_hierarchy:
            depth = (
                len(lc.section_hierarchy)
                if isinstance(lc.section_hierarchy, (list, tuple))
                else 1
            )
            max_depth = max(max_depth, depth)

    # Fallback: if LexiChunk doesn't extract defined terms, use regex
    if not all_defined_terms:
        all_defined_terms = _extract_defined_terms_regex(document.text)

    # Fallback: if no cross-refs found, use regex
    if not all_cross_refs:
        all_cross_refs = _extract_cross_refs_regex(document.text)

    # Fallback: infer hierarchy depth from section numbering
    if max_depth == 0:
        max_depth = _infer_hierarchy_depth(document.text)

    gt = GroundTruthStructure(
        clauses=clauses,
        clause_boundaries=clause_boundaries,
        defined_terms=all_defined_terms,
        cross_references=all_cross_refs,
        max_hierarchy_depth=max(max_depth, 1),
    )
    _gt_cache[document.id] = gt
    return gt


def _extract_defined_terms_regex(text: str) -> set[str]:
    """Fallback: extract quoted defined terms via regex.

    Looks for patterns like:
    - "Service Provider" (double-quoted capitalized terms)
    - 'Effective Date' (single-quoted capitalized terms)
    - "Term" means ... (definition pattern)
    """
    patterns = [
        r'"([A-Z][A-Za-z\s]{2,30})"',   # double-quoted capitalized
        r"'([A-Z][A-Za-z\s]{2,30})'",    # single-quoted capitalized
    ]
    terms: set[str] = set()
    for pattern in patterns:
        terms.update(re.findall(pattern, text))
    return terms


def _extract_cross_refs_regex(text: str) -> list[dict[str, str]]:
    """Fallback: extract cross-references via regex.

    Matches patterns like:
    - "as defined in Section 3.2"
    - "subject to Clause 7"
    - "pursuant to Article 5(1)"
    """
    patterns = [
        r"((?:as\s+(?:defined|set\s+(?:out|forth))\s+in\s+)((?:Section|Clause|Article)\s+[\d.()]+))",
        r"((?:subject\s+to\s+)((?:Section|Clause|Article)\s+[\d.()]+))",
        r"((?:pursuant\s+to\s+)((?:Section|Clause|Article)\s+[\d.()]+))",
        r"((?:in\s+accordance\s+with\s+)((?:Section|Clause|Article)\s+[\d.()]+))",
        r"((?:referred\s+to\s+in\s+)((?:Section|Clause|Article)\s+[\d.()]+))",
        r"((?:under\s+)((?:Section|Clause|Article)\s+[\d.()]+))",
    ]
    refs: list[dict[str, str]] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            refs.append({"text": match.group(1), "target": match.group(2)})
    return refs


def _infer_hierarchy_depth(text: str) -> int:
    """Infer maximum section numbering depth from text.

    e.g. "1.2.3" -> depth 3, "1.2" -> depth 2, "1." -> depth 1
    """
    max_depth = 0
    for match in re.finditer(r"^(\d+(?:\.\d+)*)\.", text, re.MULTILINE):
        depth = match.group(1).count(".") + 1
        max_depth = max(max_depth, depth)
    return max_depth
```

### Clause Fragmentation Rate

Measures how often a single logical clause gets split across multiple chunks. A fragmented clause means the retriever might return an incomplete clause.

```python
def clause_fragmentation_rate(chunk_set: ChunkSet, document: Document) -> float:
    """Calculate what fraction of ground-truth clauses are fragmented across chunks.

    A clause is 'fragmented' if no single chunk contains at least 80% of the
    clause text (measured by word overlap ratio).

    Returns:
        0.0 = no fragmentation (best), 1.0 = all fragmented (worst).
    """
    gt = get_ground_truth(document)
    if not gt.clauses:
        return 0.0

    threshold = 0.80
    non_trivial_clauses = [c for c in gt.clauses if len(c.strip()) >= 20]
    if not non_trivial_clauses:
        return 0.0

    fragmented_count = 0
    for clause_text in non_trivial_clauses:
        best_coverage = 0.0
        for chunk in chunk_set.chunks:
            overlap = _text_overlap_ratio(chunk.text, clause_text)
            best_coverage = max(best_coverage, overlap)
            if best_coverage >= threshold:
                break  # early exit
        if best_coverage < threshold:
            fragmented_count += 1

    return fragmented_count / len(non_trivial_clauses)


def _text_overlap_ratio(chunk_text: str, clause_text: str) -> float:
    """Calculate what fraction of clause_text words appear in chunk_text.

    Returns 1.0 if clause_text is a substring of chunk_text.
    Otherwise returns word-level Jaccard overlap (clause words in chunk / clause words).
    """
    if clause_text in chunk_text:
        return 1.0

    clause_words = set(clause_text.lower().split())
    if not clause_words:
        return 0.0
    chunk_words = set(chunk_text.lower().split())
    return len(clause_words & chunk_words) / len(clause_words)
```

### Definition Preservation Rate

Measures whether defined terms remain accessible within the chunks that reference them.

```python
def definition_preservation_rate(chunk_set: ChunkSet, document: Document) -> float:
    """Calculate what fraction of defined terms have their definition in a chunk.

    A defined term is 'preserved' if at least one chunk contains both the term
    AND its definition context (a "means" clause, or the term appears in
    chunk.metadata.defined_terms).

    Returns:
        1.0 = all preserved (best), 0.0 = none preserved (worst).
    """
    gt = get_ground_truth(document)
    valid_terms = [t for t in gt.defined_terms if len(t.strip()) >= 2]
    if not valid_terms:
        return 1.0  # no terms to preserve = vacuously true

    preserved = 0
    definition_indicators = ("means", "shall mean", "defined as", "refers to")

    for term in valid_terms:
        term_lower = term.lower().strip()

        for chunk in chunk_set.chunks:
            chunk_lower = chunk.text.lower()
            if term_lower not in chunk_lower:
                continue

            # Check 1: chunk contains the definition context
            has_definition = any(
                ind in chunk_lower for ind in definition_indicators
            )
            # Check 2: term appears in the quoted form
            has_quoted = (
                f'"{term_lower}"' in chunk_lower
                or f"'{term_lower}'" in chunk_lower
            )
            # Check 3: metadata reports defined_terms
            has_metadata = (
                chunk.metadata.get("defined_terms")
                and term in chunk.metadata["defined_terms"]
            )

            if has_definition or has_quoted or has_metadata:
                preserved += 1
                break

    return preserved / len(valid_terms)
```

### Cross-Reference Resolution Rate

Measures whether cross-references and their targets land in the same or adjacent chunks.

```python
def cross_ref_resolution_rate(chunk_set: ChunkSet, document: Document) -> float:
    """Calculate what fraction of cross-references are resolvable from chunks.

    A cross-reference is 'resolved' if the chunk containing it also contains
    (or is adjacent to a chunk containing) the target section identifier.
    LexiChunk chunks with cross_references metadata are always counted as resolved.

    Returns:
        1.0 = all resolved (best), 0.0 = none resolved (worst).
    """
    gt = get_ground_truth(document)
    valid_refs = [r for r in gt.cross_references if r.get("text") and r.get("target")]
    if not valid_refs:
        return 1.0  # no refs = vacuously true

    chunks_list = list(chunk_set.chunks)
    resolved = 0

    for ref in valid_refs:
        ref_text_lower = ref["text"].lower()
        target_lower = ref["target"].lower()

        for i, chunk in enumerate(chunks_list):
            chunk_lower = chunk.text.lower()
            if ref_text_lower not in chunk_lower:
                continue  # this chunk doesn't contain the reference

            # Check 1: target section is in the same chunk
            if target_lower in chunk_lower:
                resolved += 1
                break

            # Check 2: metadata has resolved cross-refs
            if chunk.metadata.get("cross_references"):
                resolved += 1
                break

            # Check 3: target is in adjacent chunk (index +/- 1)
            found_adjacent = False
            for adj_i in (i - 1, i + 1):
                if 0 <= adj_i < len(chunks_list):
                    if target_lower in chunks_list[adj_i].text.lower():
                        found_adjacent = True
                        break
            if found_adjacent:
                resolved += 1
                break

    return resolved / len(valid_refs)
```

### Convenience Function

```python
def compute_structural_metrics(
    chunk_set: ChunkSet, document: Document
) -> StructuralMetrics:
    """Compute all structural metrics for a ChunkSet against a Document.

    NOTE: hierarchy_depth_retained and chunk_size_cv return placeholder
    values (0.0) today. Day 5 will implement them.
    """
    return StructuralMetrics(
        strategy=chunk_set.strategy,
        document_id=chunk_set.document_id,
        clause_fragmentation_rate=clause_fragmentation_rate(chunk_set, document),
        definition_preservation_rate=definition_preservation_rate(chunk_set, document),
        cross_ref_resolution_rate=cross_ref_resolution_rate(chunk_set, document),
        hierarchy_depth_retained=0.0,    # placeholder -- Day 5
        chunk_size_cv=0.0,               # placeholder -- Day 5
        chunk_count=chunk_set.count,
        avg_chunk_chars=chunk_set.avg_chunk_size,
    )
```

### Tests (`tests/test_structural_metrics.py`)

Test with synthetic documents where the expected metric values are known:

```python
"""Tests for structural quality metrics."""

import pytest
from scaffolder.models import Document, Chunk, ChunkSet, Jurisdiction, DocumentType, StrategyName

# Document with known structure
STRUCTURED_DOC = Document(
    id="test_structured",
    text='''1. Definitions.
1.1 "Service Provider" means the party providing services.
1.2 "Client" means the party receiving services.
2. Obligations.
2.1 The Service Provider shall deliver services as defined in Section 1.1.
2.2 Subject to Clause 3, the Client shall pay fees.
3. Payment Terms.
3.1 Fees are due within 30 days.''',
    jurisdiction=Jurisdiction.UK,
    document_type=DocumentType.SERVICE_AGREEMENT,
    source="test.txt",
)
```

Test cases:
1. **Perfect chunker** (one chunk = whole doc): fragmentation=0.0, definition_preservation=1.0, cross_ref_resolution=1.0
2. **Terrible chunker** (every word is a chunk): fragmentation~1.0, definition_preservation~0.0
3. **Metric range**: all return float in [0.0, 1.0]
4. **compute_structural_metrics()**: returns `StructuralMetrics` with correct strategy and document_id
5. **Empty document**: returns 0.0 for fragmentation (no clauses = no fragmentation)
6. **Document with no defined terms**: definition_preservation returns 1.0 (vacuously true)
7. **Ground truth caching**: calling `get_ground_truth` twice returns same object

## Outputs
- `src/scaffolder/metrics/structural.py`
- `tests/test_structural_metrics.py`

## Acceptance Criteria
1. `pytest tests/test_structural_metrics.py -v` -- all tests pass.
2. Each metric function returns a float in [0.0, 1.0].
3. `compute_structural_metrics()` returns a complete `StructuralMetrics` instance.
4. `mypy src/scaffolder/metrics/structural.py --strict` passes.
5. `ruff check src/scaffolder/metrics/` passes.

## Handoff Notes
- **To Day 5:** `hierarchy_depth_retained` and `chunk_size_cv` are still placeholder values (0.0). Day 5 will implement them and wire everything into CLI output.
- **To Agent B:** No dependency. These metrics are pure functions -- they don't need config.
- **Design note:** Ground truth results are cached in `_gt_cache` by document ID. This matters because each document is parsed once even if evaluated against 4+ strategies. The cache should be cleared between benchmark runs if documents change (unlikely in practice).
- **Design note:** The `_text_overlap_ratio` function uses word-level overlap, not character-level. This is more robust against minor whitespace differences between LexiChunk output and raw text.
