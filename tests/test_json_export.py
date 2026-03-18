"""Tests for JSON export."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from scaffolder.models import BenchmarkResult, EmbeddingModelName, StrategyName

if TYPE_CHECKING:
    from pathlib import Path
from scaffolder.reporting.json_export import export_json, export_json_string, load_json


def _make_result() -> BenchmarkResult:
    """Create a minimal BenchmarkResult for testing."""
    return BenchmarkResult(
        timestamp="2026-03-18T12:00:00",
        strategies=[StrategyName.LEXICHUNK, StrategyName.RCTS],
        documents=["uk_service_agreement"],
        models=[EmbeddingModelName.MINILM],
        config={"strategies": ["lexichunk", "rcts"]},
    )


class TestExportJson:
    """Test JSON file export."""

    def test_export_creates_file(self, tmp_path: Path) -> None:
        result = _make_result()
        out = export_json(result, tmp_path / "test.json")
        assert out.exists()

    def test_export_valid_json(self, tmp_path: Path) -> None:
        result = _make_result()
        out = export_json(result, tmp_path / "test.json")
        data = json.loads(out.read_text())
        assert data["timestamp"] == "2026-03-18T12:00:00"

    def test_export_creates_parent_dirs(self, tmp_path: Path) -> None:
        result = _make_result()
        out = export_json(result, tmp_path / "nested" / "dir" / "test.json")
        assert out.exists()

    def test_export_strategies(self, tmp_path: Path) -> None:
        result = _make_result()
        out = export_json(result, tmp_path / "test.json")
        data = json.loads(out.read_text())
        assert data["strategies"] == ["lexichunk", "rcts"]


class TestExportJsonString:
    """Test JSON string export."""

    def test_returns_string(self) -> None:
        result = _make_result()
        s = export_json_string(result)
        assert isinstance(s, str)

    def test_valid_json_string(self) -> None:
        result = _make_result()
        s = export_json_string(result)
        data = json.loads(s)
        assert data["timestamp"] == "2026-03-18T12:00:00"


class TestLoadJson:
    """Test loading JSON results."""

    def test_roundtrip(self, tmp_path: Path) -> None:
        result = _make_result()
        out = export_json(result, tmp_path / "test.json")
        data = load_json(out)
        assert data["timestamp"] == "2026-03-18T12:00:00"
        assert data["documents"] == ["uk_service_agreement"]
