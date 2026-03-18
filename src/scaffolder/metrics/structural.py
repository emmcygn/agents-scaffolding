"""Structural quality metrics for evaluating chunking strategies."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from scaffolder.models import ChunkSet, Document, StructuralMetrics

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class GroundTruthStructure:
    """Ground truth structural elements extracted via LexiChunk."""

    clauses: list[str]  # list of clause texts
    clause_boundaries: list[tuple[int, int]]  # (start_char, end_char) in original text
    defined_terms: set[str]  # all defined terms in the document
    cross_references: list[dict[str, str]]  # list of {text, target}
    max_hierarchy_depth: int  # deepest nesting level (e.g. 3 for "1.2.1")


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
        clauses.append(lc.content)
        # Approximate boundary from text position in original
        prefix = lc.content[:80] if len(lc.content) >= 80 else lc.content
        start = document.text.find(prefix)
        if start >= 0:
            clause_boundaries.append((start, start + len(lc.content)))

        if lc.defined_terms_used:
            all_defined_terms.update(lc.defined_terms_used)

        if lc.cross_references:
            for ref in lc.cross_references:
                all_cross_refs.append({
                    "text": str(ref.raw_text),
                    "target": str(ref.target_identifier),
                })

        if lc.hierarchy_path:
            # Count depth from hierarchy path (e.g. "1 > 1.2 > 1.2.1")
            depth = str(lc.hierarchy_path).count(">") + 1
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
    """Fallback: extract quoted defined terms via regex."""
    patterns = [
        r'"([A-Z][A-Za-z\s]{2,30})"',
        r"'([A-Z][A-Za-z\s]{2,30})'",
    ]
    terms: set[str] = set()
    for pattern in patterns:
        terms.update(re.findall(pattern, text))
    return terms


def _extract_cross_refs_regex(text: str) -> list[dict[str, str]]:
    """Fallback: extract cross-references via regex."""
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
    """Infer maximum section numbering depth from text."""
    max_depth = 0
    for match in re.finditer(r"^(\d+(?:\.\d+)*)\.", text, re.MULTILINE):
        depth = match.group(1).count(".") + 1
        max_depth = max(max_depth, depth)
    return max_depth


# -- Core Metrics -----------------------------------------------------------


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
                break
        if best_coverage < threshold:
            fragmented_count += 1

    return fragmented_count / len(non_trivial_clauses)


def _text_overlap_ratio(chunk_text: str, clause_text: str) -> float:
    """Calculate what fraction of clause_text words appear in chunk_text."""
    if clause_text in chunk_text:
        return 1.0

    clause_words = set(clause_text.lower().split())
    if not clause_words:
        return 0.0
    chunk_words = set(chunk_text.lower().split())
    return len(clause_words & chunk_words) / len(clause_words)


def definition_preservation_rate(chunk_set: ChunkSet, document: Document) -> float:
    """Calculate what fraction of defined terms have their definition in a chunk.

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

            has_definition = any(ind in chunk_lower for ind in definition_indicators)
            has_quoted = f'"{term_lower}"' in chunk_lower or f"'{term_lower}'" in chunk_lower
            has_metadata = bool(
                chunk.metadata.get("defined_terms") and term in chunk.metadata["defined_terms"]
            )

            if has_definition or has_quoted or has_metadata:
                preserved += 1
                break

    return preserved / len(valid_terms)


def cross_ref_resolution_rate(chunk_set: ChunkSet, document: Document) -> float:
    """Calculate what fraction of cross-references are resolvable from chunks.

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
                continue

            # Check 1: target section is in the same chunk
            if target_lower in chunk_lower:
                resolved += 1
                break

            # Check 2: metadata has resolved cross-refs
            if chunk.metadata.get("cross_references"):
                resolved += 1
                break

            # Check 3: target is in adjacent chunk (index +/- 1)
            found_adjacent = any(
                0 <= adj_i < len(chunks_list)
                and target_lower in chunks_list[adj_i].text.lower()
                for adj_i in (i - 1, i + 1)
            )
            if found_adjacent:
                resolved += 1
                break

    return resolved / len(valid_refs)


# -- Convenience Function ---------------------------------------------------


def compute_structural_metrics(chunk_set: ChunkSet, document: Document) -> StructuralMetrics:
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
        hierarchy_depth_retained=0.0,  # placeholder -- Day 5
        chunk_size_cv=0.0,  # placeholder -- Day 5
        chunk_count=chunk_set.count,
        avg_chunk_chars=chunk_set.avg_chunk_size,
    )
