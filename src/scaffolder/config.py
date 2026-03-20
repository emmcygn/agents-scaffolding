"""Benchmark configuration with sensible defaults, YAML overrides, and env vars."""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml


class ConfigError(Exception):
    """Raised when configuration is invalid."""


VALID_STRATEGIES = frozenset(
    {
        "lexichunk",
        "lexichunk_contextual",
        "rcts",
        "sentence_split",
        "fixed_size",
    }
)

VALID_EMBEDDING_MODELS = frozenset(
    {
        "all-MiniLM-L6-v2",
        "bge-base-en-v1.5",
        "voyage-law-2",
    }
)

VALID_OUTPUT_FORMATS = frozenset({"cli", "json", "html"})


@dataclass
class BenchmarkConfig:
    """Central configuration for the scaffolder benchmark.

    Configuration precedence (highest to lowest):
    1. Environment variables (SCAFFOLDER_*)
    2. YAML config file
    3. Defaults defined here
    """

    # Chunking strategies to compare
    strategies: list[str] = field(
        default_factory=lambda: ["lexichunk", "rcts", "sentence_split", "fixed_size"]
    )

    # Embedding models to use
    embedding_models: list[str] = field(default_factory=lambda: ["all-MiniLM-L6-v2"])

    # Voyage AI toggle
    enable_voyage: bool = False
    voyage_model: str = "voyage-law-2"

    # Directory paths (relative to repo root or absolute)
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

    # Fixed-size chunking parameters
    fixed_chunk_size: int = 512
    fixed_chunk_overlap: int = 50

    # LangChain RCTS parameters
    rcts_chunk_size: int = 1000
    rcts_chunk_overlap: int = 200

    # Sentence splitting parameters
    sentence_min_chunk_size: int = 100

    def validate(self) -> None:
        """Validate all configuration values. Raises ConfigError on failure."""
        unknown = set(self.strategies) - VALID_STRATEGIES
        if unknown:
            raise ConfigError(f"Unknown strategies: {unknown}. Valid: {sorted(VALID_STRATEGIES)}")
        if not self.strategies:
            raise ConfigError("At least one strategy must be specified.")

        unknown_models = set(self.embedding_models) - VALID_EMBEDDING_MODELS
        if unknown_models:
            raise ConfigError(
                f"Unknown embedding models: {unknown_models}. "
                f"Valid: {sorted(VALID_EMBEDDING_MODELS)}"
            )

        if self.enable_voyage and not os.getenv("VOYAGE_API_KEY"):
            raise ConfigError(
                "enable_voyage is True but VOYAGE_API_KEY environment variable is not set. "
                "Set it or disable Voyage: enable_voyage: false"
            )

        if not self.k_values:
            raise ConfigError("k_values must not be empty.")
        if any(k < 1 for k in self.k_values):
            raise ConfigError("All k_values must be >= 1.")

        if self.top_k < 1:
            raise ConfigError("top_k must be >= 1.")

        if not 0 < self.significance_level < 1:
            raise ConfigError("significance_level must be between 0 and 1 exclusive.")

        unknown_formats = set(self.output_formats) - VALID_OUTPUT_FORMATS
        if unknown_formats:
            raise ConfigError(
                f"Unknown output formats: {unknown_formats}. Valid: {sorted(VALID_OUTPUT_FORMATS)}"
            )

        if self.fixed_chunk_size < 50:
            raise ConfigError("fixed_chunk_size must be >= 50.")
        if self.fixed_chunk_overlap >= self.fixed_chunk_size:
            raise ConfigError("fixed_chunk_overlap must be < fixed_chunk_size.")
        if self.rcts_chunk_size < 100:
            raise ConfigError("rcts_chunk_size must be >= 100.")
        if self.rcts_chunk_overlap >= self.rcts_chunk_size:
            raise ConfigError("rcts_chunk_overlap must be < rcts_chunk_size.")

    @classmethod
    def from_yaml(cls, path: str | Path) -> BenchmarkConfig:
        """Load config from a YAML file, merging with defaults.

        Only keys that exist as dataclass fields are accepted.
        Unknown keys raise ConfigError.
        """
        path = Path(path)
        if not path.exists():
            raise ConfigError(f"Config file not found: {path}")

        with open(path) as f:
            data: dict[str, Any] = yaml.safe_load(f) or {}

        valid_fields = set(cls.__dataclass_fields__.keys())
        unknown_keys = set(data.keys()) - valid_fields
        if unknown_keys:
            raise ConfigError(
                f"Unknown config keys: {unknown_keys}. Valid keys: {sorted(valid_fields)}"
            )

        config = cls(**{k: v for k, v in data.items() if k in valid_fields})
        config.validate()
        return config

    @classmethod
    def from_env(cls) -> BenchmarkConfig:
        """Create config with environment variable overrides.

        Environment variables use the prefix SCAFFOLDER_ and uppercase field names:
        - SCAFFOLDER_STRATEGIES=lexichunk,rcts
        - SCAFFOLDER_EMBEDDING_MODELS=all-MiniLM-L6-v2,bge-base-en-v1.5
        - SCAFFOLDER_ENABLE_VOYAGE=true
        - SCAFFOLDER_TOP_K=5
        - SCAFFOLDER_OUTPUT_DIR=/tmp/results
        - SCAFFOLDER_K_VALUES=1,3,5,10
        - SCAFFOLDER_OUTPUT_FORMATS=cli,json,html
        """
        config = cls()

        env_map: dict[str, str] = {
            "SCAFFOLDER_STRATEGIES": "strategies",
            "SCAFFOLDER_EMBEDDING_MODELS": "embedding_models",
            "SCAFFOLDER_ENABLE_VOYAGE": "enable_voyage",
            "SCAFFOLDER_FIXTURE_DIR": "fixture_dir",
            "SCAFFOLDER_QUERY_DIR": "query_dir",
            "SCAFFOLDER_OUTPUT_DIR": "output_dir",
            "SCAFFOLDER_TOP_K": "top_k",
            "SCAFFOLDER_K_VALUES": "k_values",
            "SCAFFOLDER_OUTPUT_FORMATS": "output_formats",
            "SCAFFOLDER_SIGNIFICANCE_LEVEL": "significance_level",
            "SCAFFOLDER_USE_CACHE": "use_cache",
            "SCAFFOLDER_CACHE_DIR": "cache_dir",
        }

        for env_key, field_name in env_map.items():
            value = os.getenv(env_key)
            if value is None:
                continue

            field_obj = cls.__dataclass_fields__[field_name]
            field_type = field_obj.type

            if field_type == "bool":
                setattr(config, field_name, value.lower() in ("true", "1", "yes"))
            elif field_type == "int":
                setattr(config, field_name, int(value))
            elif field_type == "float":
                setattr(config, field_name, float(value))
            elif field_type == "list[str]":
                setattr(config, field_name, [s.strip() for s in value.split(",")])
            elif field_type == "list[int]":
                setattr(config, field_name, [int(s.strip()) for s in value.split(",")])
            else:
                setattr(config, field_name, value)

        # Auto-detect Voyage
        if os.getenv("VOYAGE_API_KEY"):
            config.enable_voyage = True
            if config.voyage_model not in config.embedding_models:
                config.embedding_models.append(config.voyage_model)

        return config

    @classmethod
    def load(cls, config_path: str | Path | None = None) -> BenchmarkConfig:
        """Load config with full precedence chain.

        1. Start with defaults
        2. Override with YAML file (if provided or scaffolder.yaml exists)
        3. Override with environment variables
        """
        if config_path:
            config = cls.from_yaml(config_path)
        else:
            default_path = Path("scaffolder.yaml")
            config = cls.from_yaml(default_path) if default_path.exists() else cls()

        # Apply env overrides on top
        env_config = cls.from_env()
        for env_key in os.environ:
            if env_key.startswith("SCAFFOLDER_"):
                field_name_candidate = env_key[len("SCAFFOLDER_") :].lower()
                if field_name_candidate in cls.__dataclass_fields__:
                    setattr(config, field_name_candidate, getattr(env_config, field_name_candidate))

        config.validate()
        return config

    def resolve_paths(self, root: Path) -> None:
        """Resolve relative paths against the given root directory."""
        for attr in ("fixture_dir", "query_dir", "output_dir", "template_dir", "cache_dir"):
            value = getattr(self, attr)
            p = Path(value)
            if not p.is_absolute():
                setattr(self, attr, str(root / value))

    def to_dict(self) -> dict[str, Any]:
        """Serialize config to a dictionary for JSON/YAML export."""
        return asdict(self)
