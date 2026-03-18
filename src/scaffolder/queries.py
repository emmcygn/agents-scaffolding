"""Query annotation loader — reads YAML ground-truth files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

VALID_FAILURE_MODES = frozenset(
    {
        "clause_fragmentation",
        "orphaned_cross_refs",
        "lost_definitions",
        "destroyed_hierarchy",
        "cross_doc_contamination",
    }
)


@dataclass(frozen=True)
class RelevantSection:
    """A section identified as relevant to a query."""

    section_id: str
    relevance: int  # 3=exact, 2=partial, 1=background
    description: str


@dataclass(frozen=True)
class AnnotatedQuery:
    """A query with ground-truth relevance annotations."""

    id: str
    text: str
    document_id: str
    failure_mode: str
    relevant_sections: list[RelevantSection]
    notes: str = ""


def load_queries(query_dir: str | Path) -> list[AnnotatedQuery]:
    """Load all query annotation files from a directory.

    Args:
        query_dir: Path to directory containing YAML query files.

    Returns:
        List of all annotated queries across all fixture documents.

    Raises:
        ValueError: If a query file has invalid structure or unknown failure mode.
    """
    query_dir = Path(query_dir)
    queries: list[AnnotatedQuery] = []

    for yaml_path in sorted(query_dir.glob("*.yaml")):
        with open(yaml_path) as f:
            data: dict[str, Any] = yaml.safe_load(f) or {}

        document_id = data.get("document_id", yaml_path.stem)

        for q in data.get("queries", []):
            fm = q.get("failure_mode", "")
            if fm not in VALID_FAILURE_MODES:
                raise ValueError(
                    f"Query {q.get('id', '?')} has invalid failure_mode '{fm}'. "
                    f"Valid: {sorted(VALID_FAILURE_MODES)}"
                )

            sections = [
                RelevantSection(
                    section_id=s["section_id"],
                    relevance=s["relevance"],
                    description=s.get("description", ""),
                )
                for s in q.get("relevant_sections", [])
            ]

            queries.append(
                AnnotatedQuery(
                    id=q["id"],
                    text=q["text"],
                    document_id=document_id,
                    failure_mode=fm,
                    relevant_sections=sections,
                    notes=q.get("notes", ""),
                )
            )

    return queries


def load_queries_for_document(query_dir: str | Path, document_id: str) -> list[AnnotatedQuery]:
    """Load queries for a specific document."""
    all_queries = load_queries(query_dir)
    return [q for q in all_queries if q.document_id == document_id]
