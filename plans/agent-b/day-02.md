# Agent B — Day 02: Config System Completion

## Mission
Complete the `BenchmarkConfig` system with validation, YAML override merging, environment variable support, and a sample config file so the benchmark can be configured without code changes.

## Context
Day 1 established the repo skeleton and a stub `config.py`. Agent A is building `FixtureManager` and `models.py` today. The config system must be finalized before Agent B writes query annotations (Day 3) and before Agent A wires up `ChunkingPipeline` (Day 3). The config must support all toggles needed by both agents.

## Prerequisites
- `src/scaffolder/config.py` exists (Day 1 stub)
- `pyproject.toml` exists with all dependencies
- `pip install -e ".[dev]"` has been run successfully

## Checklist
- [ ] Task 1 — Enhance `BenchmarkConfig` with validation logic
- [ ] Task 2 — Implement deep YAML merging for nested config overrides
- [ ] Task 3 — Add comprehensive environment variable overrides
- [ ] Task 4 — Create `scaffolder.yaml.example` at repo root
- [ ] Task 5 — Write `tests/test_config.py` with full coverage
- [ ] Task 6 — Add `ConfigError` exception class

## Implementation Details

### Enhanced BenchmarkConfig

Update `src/scaffolder/config.py` with the following:

```python
"""Benchmark configuration with sensible defaults, YAML overrides, and env vars."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


class ConfigError(Exception):
    """Raised when configuration is invalid."""


VALID_STRATEGIES = frozenset({
    "lexichunk",
    "langchain_rcts",
    "sentence_split",
    "fixed_512",
})

VALID_EMBEDDING_MODELS = frozenset({
    "all-MiniLM-L6-v2",
    "bge-base-en-v1.5",
    "voyage-law-2",
})

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
        default_factory=lambda: ["lexichunk", "langchain_rcts", "sentence_split", "fixed_512"]
    )

    # Embedding models to use
    embedding_models: list[str] = field(
        default_factory=lambda: ["all-MiniLM-L6-v2"]
    )

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
    output_formats: list[str] = field(
        default_factory=lambda: ["cli", "json"]
    )

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
        # Validate strategies
        unknown = set(self.strategies) - VALID_STRATEGIES
        if unknown:
            raise ConfigError(
                f"Unknown strategies: {unknown}. Valid: {sorted(VALID_STRATEGIES)}"
            )
        if not self.strategies:
            raise ConfigError("At least one strategy must be specified.")

        # Validate embedding models
        unknown_models = set(self.embedding_models) - VALID_EMBEDDING_MODELS
        if unknown_models:
            raise ConfigError(
                f"Unknown embedding models: {unknown_models}. "
                f"Valid: {sorted(VALID_EMBEDDING_MODELS)}"
            )

        # Validate Voyage config
        if self.enable_voyage and not os.getenv("VOYAGE_API_KEY"):
            raise ConfigError(
                "enable_voyage is True but VOYAGE_API_KEY environment variable is not set. "
                "Set it or disable Voyage: enable_voyage: false"
            )

        # Validate k_values
        if not self.k_values:
            raise ConfigError("k_values must not be empty.")
        if any(k < 1 for k in self.k_values):
            raise ConfigError("All k_values must be >= 1.")

        # Validate top_k
        if self.top_k < 1:
            raise ConfigError("top_k must be >= 1.")

        # Validate significance level
        if not 0 < self.significance_level < 1:
            raise ConfigError("significance_level must be between 0 and 1 exclusive.")

        # Validate output formats
        unknown_formats = set(self.output_formats) - VALID_OUTPUT_FORMATS
        if unknown_formats:
            raise ConfigError(
                f"Unknown output formats: {unknown_formats}. Valid: {sorted(VALID_OUTPUT_FORMATS)}"
            )

        # Validate chunk sizes
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

        # Check for unknown keys
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
        - SCAFFOLDER_STRATEGIES=lexichunk,langchain_rcts
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
        # Start with defaults
        if config_path:
            config = cls.from_yaml(config_path)
        else:
            # Check for scaffolder.yaml in current directory
            default_path = Path("scaffolder.yaml")
            if default_path.exists():
                config = cls.from_yaml(default_path)
            else:
                config = cls()

        # Apply env overrides on top
        env_config = cls.from_env()
        # Only override fields that were explicitly set via env vars
        for env_key in os.environ:
            if env_key.startswith("SCAFFOLDER_"):
                field_name_candidate = env_key[len("SCAFFOLDER_"):].lower()
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
        from dataclasses import asdict
        return asdict(self)
```

### scaffolder.yaml.example

Create at repo root:

```yaml
# Scaffolder Benchmark Configuration
# Copy to scaffolder.yaml and customize as needed.

# Chunking strategies to compare against LexiChunk
strategies:
  - lexichunk
  - langchain_rcts
  - sentence_split
  - fixed_512

# Embedding models for retrieval evaluation
# Local models (no API key needed):
#   - all-MiniLM-L6-v2 (fast, good baseline)
#   - bge-base-en-v1.5 (better quality, slower)
# Paid models (requires API key):
#   - voyage-law-2 (best for legal text, requires VOYAGE_API_KEY)
embedding_models:
  - all-MiniLM-L6-v2
  # - bge-base-en-v1.5
  # - voyage-law-2

# Voyage AI settings
# Set VOYAGE_API_KEY env var to enable automatically
enable_voyage: false

# Retrieval evaluation parameters
k_values: [1, 3, 5, 10]
top_k: 10

# Statistical significance threshold
significance_level: 0.05

# Output formats: cli, json, html
output_formats:
  - cli
  - json

# Directories (relative to repo root)
fixture_dir: src/scaffolder/fixtures/documents
query_dir: queries
output_dir: results

# Embedding cache (set use_cache: false to disable)
use_cache: true
cache_dir: .cache/embeddings

# Chunking parameters for baselines
fixed_chunk_size: 512
fixed_chunk_overlap: 50
rcts_chunk_size: 1000
rcts_chunk_overlap: 200
```

### tests/test_config.py

```python
"""Tests for BenchmarkConfig."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from scaffolder.config import BenchmarkConfig, ConfigError


class TestBenchmarkConfigDefaults:
    """Test default configuration values."""

    def test_default_strategies(self) -> None:
        config = BenchmarkConfig()
        assert config.strategies == [
            "lexichunk", "langchain_rcts", "sentence_split", "fixed_512"
        ]

    def test_default_embedding_models(self) -> None:
        config = BenchmarkConfig()
        assert config.embedding_models == ["all-MiniLM-L6-v2"]

    def test_default_k_values(self) -> None:
        config = BenchmarkConfig()
        assert config.k_values == [1, 3, 5, 10]

    def test_default_voyage_disabled(self) -> None:
        config = BenchmarkConfig()
        assert config.enable_voyage is False

    def test_default_output_formats(self) -> None:
        config = BenchmarkConfig()
        assert config.output_formats == ["cli", "json"]


class TestBenchmarkConfigValidation:
    """Test validation logic."""

    def test_valid_config_passes(self) -> None:
        config = BenchmarkConfig()
        config.validate()  # Should not raise

    def test_unknown_strategy_raises(self) -> None:
        config = BenchmarkConfig(strategies=["lexichunk", "unknown_strategy"])
        with pytest.raises(ConfigError, match="Unknown strategies"):
            config.validate()

    def test_empty_strategies_raises(self) -> None:
        config = BenchmarkConfig(strategies=[])
        with pytest.raises(ConfigError, match="At least one strategy"):
            config.validate()

    def test_unknown_embedding_model_raises(self) -> None:
        config = BenchmarkConfig(embedding_models=["nonexistent-model"])
        with pytest.raises(ConfigError, match="Unknown embedding models"):
            config.validate()

    def test_voyage_without_api_key_raises(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            config = BenchmarkConfig(enable_voyage=True)
            # Remove VOYAGE_API_KEY if present
            os.environ.pop("VOYAGE_API_KEY", None)
            with pytest.raises(ConfigError, match="VOYAGE_API_KEY"):
                config.validate()

    def test_voyage_with_api_key_passes(self) -> None:
        with patch.dict(os.environ, {"VOYAGE_API_KEY": "test-key"}):
            config = BenchmarkConfig(enable_voyage=True)
            config.validate()

    def test_negative_k_value_raises(self) -> None:
        config = BenchmarkConfig(k_values=[1, -1, 5])
        with pytest.raises(ConfigError, match="k_values must be >= 1"):
            config.validate()

    def test_empty_k_values_raises(self) -> None:
        config = BenchmarkConfig(k_values=[])
        with pytest.raises(ConfigError, match="k_values must not be empty"):
            config.validate()

    def test_bad_significance_level_raises(self) -> None:
        config = BenchmarkConfig(significance_level=0.0)
        with pytest.raises(ConfigError, match="significance_level"):
            config.validate()

    def test_overlap_exceeds_chunk_size_raises(self) -> None:
        config = BenchmarkConfig(fixed_chunk_size=100, fixed_chunk_overlap=200)
        with pytest.raises(ConfigError, match="fixed_chunk_overlap"):
            config.validate()

    def test_unknown_output_format_raises(self) -> None:
        config = BenchmarkConfig(output_formats=["cli", "pdf"])
        with pytest.raises(ConfigError, match="Unknown output formats"):
            config.validate()


class TestBenchmarkConfigYAML:
    """Test YAML loading."""

    def test_load_from_yaml(self, tmp_path: Path) -> None:
        yaml_content = {
            "strategies": ["lexichunk", "fixed_512"],
            "top_k": 5,
        }
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text(yaml.dump(yaml_content))

        config = BenchmarkConfig.from_yaml(config_file)
        assert config.strategies == ["lexichunk", "fixed_512"]
        assert config.top_k == 5
        # Defaults preserved for unspecified fields
        assert config.k_values == [1, 3, 5, 10]

    def test_missing_yaml_file_raises(self) -> None:
        with pytest.raises(ConfigError, match="Config file not found"):
            BenchmarkConfig.from_yaml("/nonexistent/path.yaml")

    def test_unknown_yaml_key_raises(self, tmp_path: Path) -> None:
        yaml_content = {"strategies": ["lexichunk"], "bogus_key": True}
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text(yaml.dump(yaml_content))

        with pytest.raises(ConfigError, match="Unknown config keys"):
            BenchmarkConfig.from_yaml(config_file)

    def test_empty_yaml_returns_defaults(self, tmp_path: Path) -> None:
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")

        config = BenchmarkConfig.from_yaml(config_file)
        assert config.strategies == BenchmarkConfig().strategies


class TestBenchmarkConfigEnv:
    """Test environment variable overrides."""

    def test_voyage_auto_detected(self) -> None:
        with patch.dict(os.environ, {"VOYAGE_API_KEY": "test-key"}, clear=False):
            config = BenchmarkConfig.from_env()
            assert config.enable_voyage is True
            assert "voyage-law-2" in config.embedding_models

    def test_strategies_from_env(self) -> None:
        with patch.dict(
            os.environ,
            {"SCAFFOLDER_STRATEGIES": "lexichunk,fixed_512"},
            clear=False,
        ):
            config = BenchmarkConfig.from_env()
            assert config.strategies == ["lexichunk", "fixed_512"]

    def test_top_k_from_env(self) -> None:
        with patch.dict(os.environ, {"SCAFFOLDER_TOP_K": "20"}, clear=False):
            config = BenchmarkConfig.from_env()
            assert config.top_k == 20


class TestBenchmarkConfigResolvePaths:
    """Test path resolution."""

    def test_relative_paths_resolved(self) -> None:
        config = BenchmarkConfig()
        root = Path("/home/user/project")
        config.resolve_paths(root)
        assert config.fixture_dir == str(root / "src/scaffolder/fixtures/documents")
        assert config.output_dir == str(root / "results")

    def test_absolute_paths_unchanged(self) -> None:
        config = BenchmarkConfig(output_dir="/absolute/path")
        root = Path("/home/user/project")
        config.resolve_paths(root)
        assert config.output_dir == "/absolute/path"


class TestBenchmarkConfigToDict:
    """Test serialization."""

    def test_to_dict_roundtrip(self) -> None:
        config = BenchmarkConfig()
        d = config.to_dict()
        assert isinstance(d, dict)
        assert d["strategies"] == config.strategies
        assert d["top_k"] == config.top_k
```

## Outputs
- `src/scaffolder/config.py` (enhanced)
- `scaffolder.yaml.example`
- `tests/test_config.py`

## Acceptance Criteria
1. `make test` passes with all `test_config.py` tests green
2. `python -c "from scaffolder.config import BenchmarkConfig; c = BenchmarkConfig(); c.validate(); print('OK')"` prints `OK`
3. Copying `scaffolder.yaml.example` to `scaffolder.yaml` and loading it works: `python -c "from scaffolder.config import BenchmarkConfig; c = BenchmarkConfig.from_yaml('scaffolder.yaml'); c.validate(); print(c.strategies)"`
4. `make lint` and `make typecheck` pass on `config.py`
5. Environment variable overrides work: `SCAFFOLDER_TOP_K=20 python -c "from scaffolder.config import BenchmarkConfig; c = BenchmarkConfig.from_env(); print(c.top_k)"` prints `20`

## Handoff Notes
- **To Agent A:** The config system is complete. Use `BenchmarkConfig.load()` to get a config with full precedence (defaults -> YAML -> env vars). Key fields for your pipelines: `config.strategies`, `config.embedding_models`, `config.k_values`, `config.top_k`, `config.fixture_dir`, `config.cache_dir`, `config.use_cache`. Chunking parameters: `config.fixed_chunk_size`, `config.fixed_chunk_overlap`, `config.rcts_chunk_size`, `config.rcts_chunk_overlap`.
- **To Day 3:** The `query_dir` config field points to `queries/` — Day 3 will populate this with YAML annotation files. The `from_yaml` method validates unknown keys, so the query YAML files use a different schema (not BenchmarkConfig).
- **Decision:** We went with `dataclass` + manual validation rather than Pydantic. The `validate()` method is called explicitly in `from_yaml()` and `load()` but NOT in `__init__()` to allow constructing partial configs in tests.
