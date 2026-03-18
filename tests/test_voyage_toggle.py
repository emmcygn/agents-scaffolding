"""Tests for Voyage model availability toggle."""

from __future__ import annotations

from scaffolder.__main__ import _get_available_models
from scaffolder.models import EmbeddingModelName


def test_available_models_without_voyage(monkeypatch: object) -> None:
    monkeypatch.delenv("VOYAGE_API_KEY", raising=False)  # type: ignore[union-attr]
    models = _get_available_models()
    assert EmbeddingModelName.MINILM in models
    assert EmbeddingModelName.VOYAGE_LAW_2 not in models


def test_available_models_with_voyage(monkeypatch: object) -> None:
    monkeypatch.setenv("VOYAGE_API_KEY", "test-key")  # type: ignore[union-attr]
    models = _get_available_models()
    assert EmbeddingModelName.MINILM in models
    assert EmbeddingModelName.VOYAGE_LAW_2 in models
