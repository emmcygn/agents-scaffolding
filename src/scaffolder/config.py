"""Benchmark configuration with sensible defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class BenchmarkConfig:
    """Central configuration for the scaffolder benchmark."""

    # Chunking strategies to compare
    strategies: list[str] = field(
        default_factory=lambda: ["lexichunk", "langchain_rcts", "sentence_split", "fixed_512"]
    )

    # Embedding models to use
    embedding_models: list[str] = field(default_factory=lambda: ["all-MiniLM-L6-v2"])

    # Voyage AI toggle
    enable_voyage: bool = False

    # Directory paths (relative to repo root)
    fixture_dir: str = "src/scaffolder/fixtures/documents"
    query_dir: str = "queries"
    output_dir: str = "results"
    template_dir: str = "src/scaffolder/reporting/templates"

    # Retrieval parameters
    k_values: list[int] = field(default_factory=lambda: [1, 3, 5, 10])
    top_k: int = 10

    # Statistical testing
    significance_level: float = 0.05

    # Embedding cache
    cache_dir: str = ".cache/embeddings"
    use_cache: bool = True

    # Output formats
    output_formats: list[str] = field(default_factory=lambda: ["cli", "json"])

    @classmethod
    def from_yaml(cls, path: str | Path) -> BenchmarkConfig:
        """Load config from a YAML file, merging with defaults."""
        with open(path) as f:
            data: dict[str, Any] = yaml.safe_load(f) or {}
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    @classmethod
    def from_env(cls) -> BenchmarkConfig:
        """Create config with environment variable overrides."""
        config = cls()
        if os.getenv("VOYAGE_API_KEY"):
            config.enable_voyage = True
            if "voyage-law-2" not in config.embedding_models:
                config.embedding_models.append("voyage-law-2")
        return config

    def resolve_paths(self, root: Path) -> None:
        """Resolve relative paths against the given root directory."""
        self.fixture_dir = str(root / self.fixture_dir)
        self.query_dir = str(root / self.query_dir)
        self.output_dir = str(root / self.output_dir)
        self.template_dir = str(root / self.template_dir)
        self.cache_dir = str(root / self.cache_dir)
