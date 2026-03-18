# Agent B — Day 01: Repo Init, Config System & Makefile (PAIR with Agent A)

## Mission
Establish the project skeleton — pyproject.toml, config system, Makefile, and shared data models — so both agents have a stable foundation to build on independently from Day 2 onward.

## Context
This is the first day. Nothing exists yet. Agent A and Agent B are pairing to bootstrap the repo. Agent A focuses on `src/scaffolder/__init__.py`, `models.py` (data contracts), and the fixture directory structure. Agent B focuses on `pyproject.toml` (dependencies, metadata, extras), `config.py` (BenchmarkConfig), the Makefile, and `.gitignore`. Both agents must agree on the data models before splitting up.

## Prerequisites
- Python 3.10+ installed
- git initialized in the repo root
- Agreement on repo structure (see project context)

## Checklist
- [ ] Task 1 — Create `pyproject.toml` with all dependencies, extras groups, and project metadata
- [ ] Task 2 — Create `src/scaffolder/__init__.py` with version and top-level imports
- [ ] Task 3 — Create `src/scaffolder/config.py` with `BenchmarkConfig` dataclass (stub — completed Day 2)
- [ ] Task 4 — Create `Makefile` with core targets
- [ ] Task 5 — Create `.gitignore`
- [ ] Task 6 — PAIR: Review Agent A's `models.py` and confirm data contracts
- [ ] Task 7 — Create empty `__init__.py` files for all subpackages

## Implementation Details

### pyproject.toml
Create at repo root. Use setuptools as build backend.

```toml
[build-system]
requires = ["setuptools>=68.0", "setuptools-scm>=8.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "scaffolder"
version = "0.1.0"
description = "Evaluation harness proving LexiChunk improves RAG retrieval quality over general-purpose chunkers"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.10"
authors = [
    {name = "SDK Scaffolder Team"}
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]

dependencies = [
    "lexichunk>=0.1.0",
    "langchain-text-splitters>=0.2.0",
    "rich>=13.0",
    "pyyaml>=6.0",
    "numpy>=1.24",
    "scipy>=1.10",
    "jinja2>=3.1",
]

[project.optional-dependencies]
embeddings = [
    "sentence-transformers>=2.2",
    "faiss-cpu>=1.7",
]
voyage = [
    "voyageai>=0.2",
]
dashboard = [
    "streamlit>=1.30",
    "plotly>=5.18",
]
dev = [
    "ruff>=0.4",
    "mypy>=1.10",
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "types-PyYAML>=6.0",
]
all = [
    "scaffolder[embeddings,voyage,dashboard,dev]",
]

[project.scripts]
scaffolder = "scaffolder.__main__:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.ruff]
target-version = "py310"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "A", "SIM", "TCH"]

[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[[tool.mypy.overrides]]
module = [
    "lexichunk.*",
    "langchain_text_splitters.*",
    "sentence_transformers.*",
    "faiss.*",
    "voyageai.*",
    "streamlit.*",
    "plotly.*",
]
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=scaffolder --cov-report=term-missing --cov-fail-under=80"

[tool.coverage.run]
source = ["src/scaffolder"]
omit = ["src/scaffolder/dashboard/*"]
```

Key decisions:
- **Extras groups** allow installing only what's needed: `pip install -e ".[dev]"` for development, `pip install -e ".[all]"` for everything.
- **Dashboard code excluded from coverage** since Streamlit components are hard to unit test; they'll be tested manually.
- **mypy strict mode** with ignores for third-party libraries that lack type stubs.
- The `build-backend` uses the standard setuptools legacy backend. If issues arise, switch to `"setuptools.build_meta"`.

### src/scaffolder/__init__.py

```python
"""Evaluation harness for LexiChunk RAG retrieval quality."""

__version__ = "0.1.0"
```

Keep it minimal. Top-level imports will be added as modules are built.

### src/scaffolder/config.py (stub)

```python
"""Benchmark configuration with sensible defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class BenchmarkConfig:
    """Central configuration for the scaffolder benchmark."""

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
    output_formats: list[str] = field(
        default_factory=lambda: ["cli", "json"]
    )

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
```

This is a working stub. Day 2 will add validation, environment variable overrides for all fields, and more sophisticated YAML merging.

### Makefile

```makefile
.PHONY: help install install-all lint typecheck test benchmark clean

PYTHON ?= python
SRC = src/scaffolder
TESTS = tests

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install package with dev dependencies
	$(PYTHON) -m pip install -e ".[dev]"

install-all:  ## Install package with all dependencies
	$(PYTHON) -m pip install -e ".[all]"

lint:  ## Run ruff linter
	$(PYTHON) -m ruff check $(SRC) $(TESTS)
	$(PYTHON) -m ruff format --check $(SRC) $(TESTS)

format:  ## Auto-format code with ruff
	$(PYTHON) -m ruff format $(SRC) $(TESTS)
	$(PYTHON) -m ruff check --fix $(SRC) $(TESTS)

typecheck:  ## Run mypy type checker
	$(PYTHON) -m mypy $(SRC)

test:  ## Run tests with coverage
	$(PYTHON) -m pytest

test-fast:  ## Run tests without coverage
	$(PYTHON) -m pytest --no-cov -x

benchmark:  ## Run the full benchmark suite
	$(PYTHON) -m scaffolder benchmark

benchmark-structural:  ## Run structural metrics only (no embedding)
	$(PYTHON) -m scaffolder benchmark --no-embed

dashboard:  ## Launch Streamlit dashboard
	$(PYTHON) -m streamlit run $(SRC)/dashboard/app.py

clean:  ## Remove build artifacts and caches
	rm -rf build/ dist/ *.egg-info .mypy_cache .pytest_cache .ruff_cache
	rm -rf .cache/embeddings
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

ci:  ## Run all CI checks (lint + typecheck + test)
	$(MAKE) lint
	$(MAKE) typecheck
	$(MAKE) test
```

### .gitignore

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
dist/
build/
*.egg

# Virtual environments
.venv/
venv/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Type checking
.mypy_cache/

# Testing
.pytest_cache/
htmlcov/
.coverage
coverage.xml

# Ruff
.ruff_cache/

# Project-specific
results/
.cache/
*.faiss

# Environment variables
.env
.env.local

# OS
.DS_Store
Thumbs.db
```

### Empty __init__.py files
Create these files with minimal docstrings:

- `src/scaffolder/fixtures/__init__.py` — `"""Fixture loading and management."""`
- `src/scaffolder/chunking/__init__.py` — `"""Chunking strategy wrappers."""`
- `src/scaffolder/embedding/__init__.py` — `"""Embedding pipelines and adapters."""`
- `src/scaffolder/retrieval/__init__.py` — `"""Retrieval simulation and indexing."""`
- `src/scaffolder/metrics/__init__.py` — `"""Structural and retrieval metrics."""`
- `src/scaffolder/reporting/__init__.py` — `"""Output formatters: CLI, JSON, HTML."""`
- `src/scaffolder/dashboard/__init__.py` — `"""Streamlit dashboard."""`

Also create empty directories:
- `queries/` (with a `.gitkeep`)
- `tests/` (with `__init__.py` and `conftest.py`)
- `results/` (with `.gitkeep`)
- `docs/`
- `src/scaffolder/reporting/templates/` (empty, for Jinja2 templates)
- `src/scaffolder/fixtures/documents/` (Agent A will populate this)

### tests/conftest.py

```python
"""Shared pytest fixtures for scaffolder tests."""

from __future__ import annotations

import pytest

from scaffolder.config import BenchmarkConfig


@pytest.fixture
def default_config() -> BenchmarkConfig:
    """A default BenchmarkConfig for testing."""
    return BenchmarkConfig()


@pytest.fixture
def sample_legal_text() -> str:
    """A short legal text snippet for testing."""
    return (
        "1. DEFINITIONS\n"
        '1.1 "Agreement" means this Master Service Agreement.\n'
        '1.2 "Confidential Information" means any information disclosed '
        "by either party that is marked as confidential.\n\n"
        "2. TERM AND TERMINATION\n"
        "2.1 This Agreement shall commence on the Effective Date and "
        "continue for a period of twelve (12) months.\n"
        "2.2 Either party may terminate this Agreement by giving "
        "ninety (90) days written notice.\n"
        "2.3 Termination shall not affect the rights and obligations "
        "set forth in Sections 3 (Confidentiality) and 5 (Limitation of Liability).\n"
    )
```

## Outputs
- `pyproject.toml`
- `.gitignore`
- `Makefile`
- `src/scaffolder/__init__.py`
- `src/scaffolder/config.py`
- `src/scaffolder/fixtures/__init__.py`
- `src/scaffolder/chunking/__init__.py`
- `src/scaffolder/embedding/__init__.py`
- `src/scaffolder/retrieval/__init__.py`
- `src/scaffolder/metrics/__init__.py`
- `src/scaffolder/reporting/__init__.py`
- `src/scaffolder/dashboard/__init__.py`
- `src/scaffolder/reporting/templates/` (empty dir)
- `src/scaffolder/fixtures/documents/` (empty dir)
- `queries/.gitkeep`
- `tests/__init__.py`
- `tests/conftest.py`
- `results/.gitkeep`
- `docs/` (empty dir)

## Acceptance Criteria
1. `pip install -e ".[dev]"` succeeds without errors
2. `make lint` runs (may have warnings on empty files — that's fine)
3. `make test` runs (0 tests collected is acceptable on Day 1)
4. `python -c "from scaffolder.config import BenchmarkConfig; c = BenchmarkConfig(); print(c.strategies)"` prints `['lexichunk', 'langchain_rcts', 'sentence_split', 'fixed_512']`
5. All directories exist with `__init__.py` files
6. `make help` shows all targets with descriptions

## Handoff Notes
- **To Agent A:** The `BenchmarkConfig` dataclass is in `src/scaffolder/config.py`. Import it as `from scaffolder.config import BenchmarkConfig`. It has `strategies`, `embedding_models`, `k_values`, `fixture_dir`, `query_dir`, `output_dir` — use these in your pipelines. The extras groups mean Agent A should install with `pip install -e ".[embeddings,dev]"` to get sentence-transformers and faiss.
- **To Day 2:** Config system needs validation (strategy names must be in known set), full env var overrides, and a `scaffolder.yaml` example file. The `from_yaml` method needs to handle nested overrides (e.g., overriding just one strategy).
- **Decision:** We chose `dataclass` over Pydantic to keep dependencies minimal. If validation gets complex, revisit on Day 2.
