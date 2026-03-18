# Agent A — Day 16: Test Coverage Push to 80%

## Mission
Write comprehensive tests for all Agent A modules to reach the 80% code coverage target, covering fixtures, chunking, embedding, retrieval, metrics, and reporting with both unit tests and integration tests.

## Context
Days 1-15 built all the functionality. Tests exist for individual modules but coverage is likely 40-60%. Today we systematically identify coverage gaps and fill them. This is the start of Week 4 -- the hardening phase.

Agent B is working on dashboard tests and deployment config today.

## Prerequisites
- All source modules complete and functional
- `pytest` and `pytest-cov` installed
- Existing tests in `tests/` directory

## Checklist
- [ ] Run `pytest --cov=scaffolder --cov-report=term-missing` to identify coverage gaps
- [ ] Write missing tests for `src/scaffolder/fixtures/` (edge cases)
- [ ] Write missing tests for `src/scaffolder/chunking/` (each strategy, pipeline)
- [ ] Write missing tests for `src/scaffolder/metrics/structural.py` (edge cases)
- [ ] Write missing tests for `src/scaffolder/metrics/retrieval.py` (boundary conditions)
- [ ] Write missing tests for `src/scaffolder/metrics/statistical.py`
- [ ] Write missing tests for `src/scaffolder/embedding/pipeline.py` (cache, adapters)
- [ ] Write missing tests for `src/scaffolder/retrieval/` (index, simulator)
- [ ] Write missing tests for `src/scaffolder/reporting/` (cli, json, html)
- [ ] Write integration test: full pipeline end-to-end
- [ ] Verify 80% coverage target met

## Implementation Details

### Coverage Gap Analysis

Run this command first to see current state:
```bash
pytest --cov=scaffolder --cov-report=term-missing tests/
```

Expected gaps to fill:

### Fixtures Tests (`tests/test_fixtures.py` — extend)

Add these edge case tests:
```python
def test_empty_documents_dir(tmp_path):
    """Directory with no .txt files returns empty list."""
    manager = FixtureManager(documents_dir=tmp_path)
    docs = manager.load_all()
    assert docs == []

def test_unknown_file_in_dir(tmp_path):
    """A .txt file without metadata mapping raises ValueError."""
    (tmp_path / "unknown_document.txt").write_text("content")
    manager = FixtureManager(documents_dir=tmp_path)
    with pytest.raises(ValueError, match="No metadata mapping"):
        manager.load_all()

def test_reload_clears_previous(self):
    """Calling load_all() twice re-reads from disk."""
    manager = FixtureManager()
    docs1 = manager.load_all()
    docs2 = manager.load_all()
    assert len(docs1) == len(docs2)

def test_document_source_field():
    """Document.source matches the filename."""
    manager = FixtureManager()
    doc = manager.get_by_id("uk_service_agreement")
    assert doc.source == "uk_service_agreement.txt"
```

### Chunking Tests (`tests/test_chunking.py` — extend)

```python
# Test each strategy with a realistic document (not just tiny test doc)
def test_lexichunk_on_real_fixture():
    """LexiChunk produces chunks with metadata on a real document."""
    fm = FixtureManager()
    doc = fm.get_by_id("uk_service_agreement")
    strategy = LexiChunkStrategy()
    cs = strategy.chunk(doc)
    assert cs.count > 0
    # At least some chunks should have metadata
    has_metadata = any(bool(c.metadata) for c in cs.chunks)
    assert has_metadata

def test_rcts_chunk_sizes():
    """RCTS chunks are approximately the configured size."""
    fm = FixtureManager()
    doc = fm.get_by_id("us_msa")
    strategy = RCTSStrategy(chunk_size=512)
    cs = strategy.chunk(doc)
    for chunk in cs.chunks[:-1]:  # last chunk may be smaller
        assert chunk.char_count <= 600  # allow some overflow

def test_fixed_size_exact():
    """Fixed-size chunks are exactly 512 chars (except last)."""
    fm = FixtureManager()
    doc = fm.get_by_id("us_msa")
    strategy = FixedSizeStrategy(chunk_size=512)
    cs = strategy.chunk(doc)
    for chunk in cs.chunks[:-1]:
        assert chunk.char_count == 512

def test_sentence_split_no_empty_chunks():
    """Sentence split never produces empty chunks."""
    fm = FixtureManager()
    for doc in fm.load_all():
        strategy = SentenceSplitStrategy()
        cs = strategy.chunk(doc)
        for chunk in cs.chunks:
            assert len(chunk.text.strip()) > 0

def test_pipeline_empty_strategies_raises():
    pipeline_cls = ChunkingPipeline
    with pytest.raises(ValueError, match="At least one"):
        pipeline_cls([])

def test_pipeline_run_single_not_found():
    strategies = [FixedSizeStrategy()]
    pipeline = ChunkingPipeline(strategies)
    with pytest.raises(ValueError, match="not found"):
        pipeline.run_single(StrategyName.LEXICHUNK, [])

def test_all_strategies_produce_unique_chunk_ids():
    """No duplicate chunk IDs across a strategy run."""
    fm = FixtureManager()
    docs = fm.load_all()
    for strategy_cls in [RCTSStrategy, SentenceSplitStrategy, FixedSizeStrategy]:
        strategy = strategy_cls()
        for doc in docs:
            cs = strategy.chunk(doc)
            ids = [c.id for c in cs.chunks]
            assert len(ids) == len(set(ids)), f"Duplicate IDs in {strategy.name.value}"
```

### Metrics Tests — Structural (`tests/test_structural_metrics.py` — extend)

```python
def test_fragmentation_whole_doc_is_one_chunk():
    """Single chunk containing entire doc = 0 fragmentation."""
    # Create a ChunkSet with one chunk = full document text
    ...
    assert clause_fragmentation_rate(cs, doc) == 0.0

def test_fragmentation_tiny_chunks():
    """Very small chunks should fragment most clauses."""
    # Create ChunkSet with 10-char chunks
    ...
    rate = clause_fragmentation_rate(cs, doc)
    assert rate > 0.5

def test_definition_preservation_no_terms():
    """Document with no defined terms returns 1.0."""
    doc = Document(id="bare", text="No definitions here.", ...)
    ...
    assert definition_preservation_rate(cs, doc) == 1.0

def test_cross_ref_no_refs():
    """Document with no cross-references returns 1.0."""
    ...
    assert cross_ref_resolution_rate(cs, doc) == 1.0

def test_hierarchy_flat_document():
    """Document with no section numbering returns 1.0."""
    ...
    assert hierarchy_depth_retained(cs, doc) == 1.0

def test_chunk_size_cv_uniform():
    """Identical chunk sizes gives CV = 0.0."""
    ...
    assert chunk_size_cv(cs) == 0.0

def test_chunk_size_cv_single_chunk():
    """Single chunk gives CV = 0.0."""
    ...
    assert chunk_size_cv(cs) == 0.0

def test_compute_structural_metrics_returns_all_fields():
    """compute_structural_metrics returns a complete StructuralMetrics."""
    ...
    sm = compute_structural_metrics(cs, doc)
    assert sm.strategy == cs.strategy
    assert sm.document_id == cs.document_id
    assert isinstance(sm.clause_fragmentation_rate, float)
```

### Metrics Tests — Retrieval (`tests/test_retrieval_metrics.py` — extend)

```python
def test_precision_at_k_zero():
    """P@k = 0 when no hits are relevant."""
    ...

def test_recall_no_relevant():
    """R@k = 1.0 when there are no relevant sections."""
    ...

def test_ndcg_perfect_ranking():
    """NDCG = 1.0 for ideal ranking order."""
    ...

def test_ndcg_with_worked_example():
    """Verify NDCG calculation matches hand-computed value."""
    # Grades: [3, 0, 2, 0, 1, 0, 0, 0, 0, 0]
    # Expected NDCG ~ 0.946
    ...
    assert abs(result - 0.946) < 0.01

def test_drm_all_correct_documents():
    """DRM = 0.0 when all hits are from target documents."""
    ...

def test_drm_all_wrong_documents():
    """DRM = 1.0 when all hits are from wrong documents."""
    ...

def test_compute_retrieval_metrics_complete():
    """compute_retrieval_metrics returns all fields."""
    ...
```

### Reporting Tests (`tests/test_reporting.py`)

```python
def test_cli_structural_report(capsys):
    """print_structural_report outputs a rich table."""
    ...
    print_structural_report(result, Console(file=io.StringIO()))
    # Verify no exceptions

def test_json_export_roundtrip(tmp_path):
    """Export then load produces equivalent data."""
    path = tmp_path / "test.json"
    export_json(result, path)
    loaded = load_json(path)
    assert loaded["timestamp"] == result.timestamp

def test_json_export_creates_parent_dirs(tmp_path):
    """JSON export creates parent directories."""
    path = tmp_path / "deep" / "nested" / "result.json"
    export_json(result, path)
    assert path.exists()

def test_html_report_contains_strategies(tmp_path):
    """HTML report mentions all strategy names."""
    path = tmp_path / "report.html"
    render_html_report(result, path)
    html = path.read_text()
    for s in result.strategies:
        assert s.value in html
```

### Integration Test (`tests/test_integration.py`)

```python
"""End-to-end integration test for the full benchmark pipeline."""

import pytest

@pytest.mark.slow
def test_full_structural_pipeline():
    """Full pipeline: fixtures -> chunking -> structural metrics."""
    from scaffolder.fixtures import FixtureManager
    from scaffolder.chunking import get_all_strategies, ChunkingPipeline
    from scaffolder.metrics.structural import compute_structural_metrics

    fm = FixtureManager()
    docs = fm.load_all()
    assert len(docs) == 5

    strategies = get_all_strategies()
    pipeline = ChunkingPipeline(strategies)
    results = pipeline.run(docs)

    assert len(results) >= 4  # 4 or 5 strategies

    for sr in results:
        assert len(sr.chunk_sets) == 5
        for cs in sr.chunk_sets:
            assert cs.count > 0
            doc = fm.get_by_id(cs.document_id)
            sm = compute_structural_metrics(cs, doc)
            assert 0.0 <= sm.clause_fragmentation_rate <= 1.0
            assert 0.0 <= sm.definition_preservation_rate <= 1.0
```

### Coverage Verification

After writing all tests, run:
```bash
pytest --cov=scaffolder --cov-report=term-missing --cov-fail-under=80 tests/
```

If coverage is below 80%, identify the remaining uncovered lines from the `term-missing` report and add targeted tests.

## Outputs
- `tests/test_fixtures.py` (extended)
- `tests/test_chunking.py` (extended)
- `tests/test_structural_metrics.py` (extended)
- `tests/test_retrieval_metrics.py` (extended)
- `tests/test_statistical.py` (extended)
- `tests/test_embedding.py` (extended)
- `tests/test_retrieval_index.py` (extended)
- `tests/test_simulator.py` (extended)
- `tests/test_reporting.py` (extended or new)
- `tests/test_integration.py` (new)

## Acceptance Criteria
1. `pytest --cov=scaffolder --cov-fail-under=80 tests/` passes.
2. All tests pass: `pytest tests/ -v` -- zero failures.
3. `pytest tests/ -m "not slow"` passes quickly (< 30s).
4. Integration test runs the full structural pipeline end-to-end.
5. No test depends on network access (except `@pytest.mark.slow` embedding tests).

## Handoff Notes
- **To Agent B:** Tests that need network (Voyage API, model downloads) are marked `@pytest.mark.slow`. Skip them in CI with `pytest -m "not slow"`.
- **To Day 17:** Coverage is at 80%+. Day 17 handles edge cases and performance optimization.
- **Test fixtures note:** Tests should use `tmp_path` for file operations and small synthetic documents for speed. Only integration tests should load real fixtures.
