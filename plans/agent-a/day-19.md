# Agent A — Day 19: Code Review Sweep + Reproducibility

## Mission
Perform a thorough code review sweep across all Agent A modules -- fix style issues, remove dead code, resolve all TODOs, verify all make targets, and pin random seeds for benchmark reproducibility.

## Context
Day 18 completed README content and pyproject.toml extras. All functionality is built, tested, and documented. Today is the final quality pass before the v1.0.0 release on Day 20. Every file Agent A owns must be clean, consistent, and production-ready.

Agent B is doing their own code review sweep today.

## Prerequisites
- All Agent A modules complete and tested (80%+ coverage)
- `make test`, `make lint`, `make benchmark`, `make benchmark-embed`, `make report` all working
- README content delivered to Agent B

## Checklist
- [ ] Run `ruff check src/scaffolder/ --fix` and resolve all issues
- [ ] Run `mypy src/scaffolder/ --strict` and resolve all errors
- [ ] Search for TODO, FIXME, HACK, XXX comments and resolve them
- [ ] Remove dead code (unused imports, unreachable branches, commented-out code)
- [ ] Verify consistent naming conventions across all modules
- [ ] Verify all docstrings are present and accurate
- [ ] Verify all `__init__.py` files have correct `__all__` exports
- [ ] Pin random seeds for reproducibility
- [ ] Verify `make test` passes
- [ ] Verify `make lint` passes
- [ ] Verify `make benchmark` produces consistent output
- [ ] Verify `make benchmark-embed` completes successfully
- [ ] Verify `make report` generates valid HTML
- [ ] Document known issues or limitations

## Implementation Details

### Linting Pass

```bash
# Fix auto-fixable issues
ruff check src/scaffolder/ --fix
ruff format src/scaffolder/

# Strict mypy
mypy src/scaffolder/ --strict --ignore-missing-imports

# Fix remaining issues manually
```

Common issues to look for:
- Missing type annotations on function parameters or return types
- `Any` types that should be more specific
- Missing `from __future__ import annotations` in files using `X | Y` syntax
- Unused imports
- Line length violations

### TODO/FIXME Resolution

```bash
# Find all TODOs
grep -rn "TODO\|FIXME\|HACK\|XXX" src/scaffolder/
```

For each TODO:
1. If it refers to a task that's done, remove it
2. If it refers to a post-v1 feature, convert to a GitHub issue (Day 20)
3. If it's a genuine bug or missing feature, fix it now

### Naming Convention Audit

Verify these conventions are consistent:
- **Classes:** PascalCase (e.g., `ChunkingPipeline`, `VectorIndex`)
- **Functions:** snake_case (e.g., `compute_structural_metrics`)
- **Constants:** UPPER_SNAKE_CASE (e.g., `_STRATEGY_REGISTRY`, `SIGNIFICANCE_METRICS`)
- **Private methods:** `_` prefix (e.g., `_load_document`, `_text_overlap_ratio`)
- **Module files:** snake_case (e.g., `structural.py`, `json_export.py`)
- **Test files:** `test_` prefix (e.g., `test_fixtures.py`)
- **Enum values:** UPPER_SNAKE_CASE (e.g., `StrategyName.LEXICHUNK`)

### Docstring Audit

Every public class and function must have a docstring. Check:

```python
# Every public function should have:
def function_name(arg: Type) -> ReturnType:
    """One-line summary.

    Longer description if needed.

    Args:
        arg: Description.

    Returns:
        Description.

    Raises:
        ErrorType: When.
    """
```

Files to audit:
- `src/scaffolder/models.py` — all dataclasses and protocols
- `src/scaffolder/fixtures/__init__.py` — FixtureManager and all methods
- `src/scaffolder/chunking/strategies.py` — all strategy classes
- `src/scaffolder/chunking/pipeline.py` — ChunkingPipeline
- `src/scaffolder/embedding/pipeline.py` — all classes
- `src/scaffolder/retrieval/index.py` — VectorIndex, IndexRegistry
- `src/scaffolder/retrieval/simulator.py` — QueryLoader, RetrievalSimulator
- `src/scaffolder/metrics/structural.py` — all metric functions
- `src/scaffolder/metrics/retrieval.py` — all metric functions
- `src/scaffolder/metrics/statistical.py` — all functions
- `src/scaffolder/reporting/cli.py` — all print functions
- `src/scaffolder/reporting/json_export.py` — export/load functions
- `src/scaffolder/reporting/html.py` — render function

### `__all__` Audit

Every `__init__.py` should export its public API:

```python
# src/scaffolder/fixtures/__init__.py
__all__ = ["FixtureManager"]

# src/scaffolder/chunking/__init__.py
__all__ = [
    "ChunkingPipeline",
    "get_strategy",
    "get_all_strategies",
    "LexiChunkStrategy",
    "LexiChunkContextualStrategy",
    "RCTSStrategy",
    "SentenceSplitStrategy",
    "FixedSizeStrategy",
]

# src/scaffolder/embedding/__init__.py
__all__ = ["EmbeddingPipeline", "EmbeddingCache", "SentenceTransformerAdapter"]

# src/scaffolder/retrieval/__init__.py
__all__ = [
    "VectorIndex",
    "IndexRegistry",
    "build_all_indices",
    "QueryLoader",
    "RetrievalSimulator",
]

# src/scaffolder/metrics/__init__.py
__all__ = ["compute_structural_metrics", "compute_retrieval_metrics"]

# src/scaffolder/reporting/__init__.py
__all__ = [
    "print_structural_report",
    "print_retrieval_report",
    "print_significance_report",
    "export_json",
    "render_html_report",
]
```

### Random Seed Pinning

Pin seeds in all non-deterministic operations:

```python
# In __main__.py, at the start of each benchmark:
import numpy as np
import random

SEED = 42

def _pin_seeds(seed: int = SEED) -> None:
    """Pin random seeds for reproducible benchmark results."""
    random.seed(seed)
    np.random.seed(seed)
    # FAISS has no global seed, but flat index is deterministic anyway
```

Also set sentence-transformers to deterministic mode:
```python
# In SentenceTransformerAdapter.__init__:
import torch
torch.manual_seed(42)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(42)
```

### Version Pinning Documentation

Add to `results/` or a config comment:

```python
# Record versions used for reproducibility
def _record_environment(result: BenchmarkResult) -> None:
    """Record package versions in benchmark results."""
    import lexichunk
    import sentence_transformers
    import faiss

    result.config["environment"] = {
        "python_version": sys.version,
        "lexichunk_version": lexichunk.__version__,
        "sentence_transformers_version": sentence_transformers.__version__,
        "faiss_version": faiss.__version__,
        "numpy_version": np.__version__,
        "seed": SEED,
    }
```

### Verify All Make Targets

Run each target and verify:

```bash
make test          # All tests pass, 80%+ coverage
make lint          # Zero ruff + mypy errors
make benchmark     # Structural metrics for 4-5 strategies x 5 docs
make benchmark-embed  # Full retrieval benchmark, < 5 minutes
make report        # Generates results/report.html
```

Document the expected output for each target.

### Known Issues / Limitations

Document these in a comment block at the top of `__main__.py` or in a separate section:

1. Ground truth parsing uses LexiChunk itself -- circular dependency for evaluating LexiChunk
2. Relevance matching uses fuzzy heuristics (word overlap) -- not exact span matching
3. Sentence-split strategy's regex doesn't handle all sentence boundaries (e.g., abbreviations)
4. Fixed-size strategy cuts mid-word -- this is intentional as a worst-case baseline
5. DRM testing requires queries that target specific documents; generic queries are excluded
6. Voyage adapter has rate limits; large query sets may timeout

## Outputs
- All `src/scaffolder/` files (cleaned up)
- All `tests/` files (cleaned up)
- No new files -- this is a cleanup day

## Acceptance Criteria
1. `ruff check src/scaffolder/ tests/` -- zero errors.
2. `mypy src/scaffolder/ --strict --ignore-missing-imports` -- zero errors.
3. `grep -rn "TODO\|FIXME\|HACK\|XXX" src/scaffolder/` -- zero results (or all converted to issues).
4. `make test` passes with 80%+ coverage.
5. `make lint` passes clean.
6. `make benchmark` produces consistent output across two consecutive runs.
7. `make benchmark-embed` completes in < 5 minutes.
8. `make report` generates valid HTML.

## Handoff Notes
- **To Agent B:** All Agent A code is clean and reviewed. No TODO/FIXME remains. If you find issues in shared interfaces, raise them before Day 20.
- **To Day 20:** The codebase is release-ready. Day 20 is the final verification and v1.0.0 tag.
- **Known issues documented:** See the list above. These should become GitHub issues on Day 20.
