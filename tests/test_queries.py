"""Tests for query annotation loading."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scaffolder.queries import (
    VALID_FAILURE_MODES,
    load_queries,
    load_queries_for_document,
)

QUERY_DIR = Path("queries")


class TestLoadQueries:
    """Test loading all query annotations."""

    def test_loads_all_queries(self) -> None:
        queries = load_queries(QUERY_DIR)
        assert len(queries) >= 20

    def test_all_failure_modes_represented(self) -> None:
        queries = load_queries(QUERY_DIR)
        modes = {q.failure_mode for q in queries}
        for mode in VALID_FAILURE_MODES:
            assert mode in modes, f"Failure mode '{mode}' not represented in any query"

    def test_cross_doc_contamination_queries_exist(self) -> None:
        queries = load_queries(QUERY_DIR)
        cross_doc = [q for q in queries if q.failure_mode == "cross_doc_contamination"]
        assert len(cross_doc) >= 2

    def test_each_query_has_relevant_sections(self) -> None:
        queries = load_queries(QUERY_DIR)
        for q in queries:
            assert len(q.relevant_sections) >= 1, f"Query {q.id} has no relevant sections"

    def test_each_failure_mode_has_at_least_3_queries(self) -> None:
        queries = load_queries(QUERY_DIR)
        mode_counts: dict[str, int] = {}
        for q in queries:
            mode_counts[q.failure_mode] = mode_counts.get(q.failure_mode, 0) + 1
        for mode, count in mode_counts.items():
            assert count >= 2, f"Failure mode '{mode}' has only {count} queries (need >= 2)"

    def test_query_ids_are_unique(self) -> None:
        queries = load_queries(QUERY_DIR)
        ids = [q.id for q in queries]
        assert len(ids) == len(set(ids)), f"Duplicate query IDs found: {ids}"

    def test_all_yaml_files_parse(self) -> None:
        for yaml_path in sorted(QUERY_DIR.glob("*.yaml")):
            with open(yaml_path) as f:
                data = yaml.safe_load(f)
            assert data is not None, f"{yaml_path.name} parsed as None"
            assert "document_id" in data, f"{yaml_path.name} missing document_id"
            assert "queries" in data, f"{yaml_path.name} missing queries key"


class TestLoadQueriesForDocument:
    """Test document-specific query loading."""

    def test_load_uk_service_agreement(self) -> None:
        queries = load_queries_for_document(QUERY_DIR, "uk_service_agreement")
        assert len(queries) >= 4

    def test_load_nonexistent_document(self) -> None:
        queries = load_queries_for_document(QUERY_DIR, "nonexistent")
        assert len(queries) == 0


class TestInvalidQueries:
    """Test error handling for invalid query files."""

    def test_invalid_failure_mode_raises(self, tmp_path: Path) -> None:
        bad_yaml = {
            "document_id": "test",
            "queries": [
                {
                    "id": "test_q1",
                    "text": "test query",
                    "failure_mode": "invalid_mode",
                    "relevant_sections": [
                        {"section_id": "s1", "relevance": 3, "description": "test"}
                    ],
                }
            ],
        }
        yaml_file = tmp_path / "bad.yaml"
        yaml_file.write_text(yaml.dump(bad_yaml))

        with pytest.raises(ValueError, match="invalid failure_mode"):
            load_queries(tmp_path)
