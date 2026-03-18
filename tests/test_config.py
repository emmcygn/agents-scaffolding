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
        assert config.strategies == ["lexichunk", "langchain_rcts", "sentence_split", "fixed_512"]

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
        abs_path = str(Path("/absolute/path").resolve())
        config = BenchmarkConfig(output_dir=abs_path)
        root = Path("/home/user/project")
        config.resolve_paths(root)
        assert config.output_dir == abs_path


class TestBenchmarkConfigToDict:
    """Test serialization."""

    def test_to_dict_roundtrip(self) -> None:
        config = BenchmarkConfig()
        d = config.to_dict()
        assert isinstance(d, dict)
        assert d["strategies"] == config.strategies
        assert d["top_k"] == config.top_k
