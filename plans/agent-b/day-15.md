# Agent B — Day 15: Screenshots, GIFs & EXTENSIBILITY.md Outline

## Mission
Capture polished screenshots and GIFs of the Streamlit dashboard for the README, and outline the EXTENSIBILITY.md document that will guide users in extending the scaffolder with custom fixtures, strategies, metrics, and queries.

## Context
Day 14 completed deployment preparation. The dashboard is feature-complete and deployable. Now we need visual assets for documentation. The README (Day 18, pair with Agent A) needs compelling images showing the dashboard in action. EXTENSIBILITY.md (completed Day 16) is a standalone design doc — today we outline it and write the first sections.

## Prerequisites
- Streamlit dashboard fully functional (Days 7-13)
- At least one benchmark run completed (results JSON exists)
- Screenshots directory: `docs/screenshots/`

## Checklist
- [ ] Task 1 — Create `docs/screenshots/` directory
- [ ] Task 2 — Capture screenshot: side-by-side chunk comparison
- [ ] Task 3 — Capture screenshot: retrieval query results with P@k chart
- [ ] Task 4 — Capture screenshot: metrics dashboard with headline cards
- [ ] Task 5 — Capture screenshot: filtered retrieval demo
- [ ] Task 6 — Create animated GIF showing the full workflow
- [ ] Task 7 — Outline EXTENSIBILITY.md with section headers and first 2 sections

## Implementation Details

### Screenshot capture process

Since this is an AI-agent workflow, screenshots must be captured programmatically or described for manual capture. Create a screenshot capture script:

```python
# scripts/capture_screenshots.py
"""Instructions for capturing dashboard screenshots.

Run the dashboard, then capture these views:
    streamlit run src/scaffolder/dashboard/app.py

Screenshot 1: chunk_comparison.png
    - Page: "Compare Chunks"
    - Document: uk_service_agreement
    - Baseline: langchain_rcts
    - Click "Run Chunking"
    - Capture: Full page showing side-by-side chunks with colour coding
    - Window width: 1400px

Screenshot 2: retrieval_results.png
    - Page: "Retrieval Demo"
    - Document: uk_service_agreement
    - Query: "What are the termination provisions?" (annotated query)
    - Click "Search"
    - Capture: Results with P@k bar chart + metrics table + strategy tabs
    - Window width: 1400px

Screenshot 3: metrics_dashboard.png
    - Page: "Metrics Dashboard"
    - Load results from file
    - Capture: Headline metrics + structural comparison bar chart
    - Window width: 1400px

Screenshot 4: filtered_retrieval.png
    - Page: "Retrieval Demo"
    - After running a search
    - Scroll to "Filtered Retrieval" section
    - Select "indemnification" clause type
    - Click "Find Clauses"
    - Capture: LexiChunk results on left, "Not possible" on right
    - Window width: 1400px

For GIF creation:
    - Use a screen recording tool to record the full workflow:
      1. Select fixture document
      2. Run chunk comparison
      3. Switch to retrieval page
      4. Run a query
      5. View metrics dashboard
    - Convert to GIF (e.g., using ffmpeg or gifski)
    - Target: 10-15 seconds, 800px wide, 15fps
    - Save as: docs/screenshots/demo.gif
"""
```

### Screenshot alt text and README references

Create a manifest file for screenshots:

```yaml
# docs/screenshots/manifest.yaml
screenshots:
  - filename: chunk_comparison.png
    alt: "Side-by-side comparison of LexiChunk vs LangChain RCTS chunks"
    caption: "LexiChunk preserves clause boundaries and adds metadata"
    readme_section: "visual-comparison"

  - filename: retrieval_results.png
    alt: "Retrieval results comparing P@k across chunking strategies"
    caption: "LexiChunk achieves higher precision across all k values"
    readme_section: "retrieval-evaluation"

  - filename: metrics_dashboard.png
    alt: "Metrics dashboard with headline comparison cards"
    caption: "Aggregate benchmark results at a glance"
    readme_section: "metrics-overview"

  - filename: filtered_retrieval.png
    alt: "Filtered retrieval demo showing clause-type filtering"
    caption: "Only LexiChunk enables filtered retrieval by clause type"
    readme_section: "filtered-retrieval"

  - filename: demo.gif
    alt: "Animated walkthrough of the scaffolder dashboard"
    caption: "Full workflow: chunk, embed, query, compare"
    readme_section: "hero"
```

### EXTENSIBILITY.md outline and first sections

Create `EXTENSIBILITY.md` at repo root:

```markdown
# Extensibility Guide

This document explains how to extend the scaffolder evaluation harness with
custom fixtures, chunking strategies, embedding models, metrics, and query sets.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Adding Test Fixtures](#adding-test-fixtures)
3. [Adding Chunking Strategies](#adding-chunking-strategies)
4. [Adding Embedding Models](#adding-embedding-models)
5. [Adding Metrics](#adding-metrics)
6. [Adding Query Sets](#adding-query-sets)
7. [Adding Output Formats](#adding-output-formats)
8. [Configuration Reference](#configuration-reference)

---

## Architecture Overview

The scaffolder follows a pipeline architecture:

```
Fixtures → Chunking → Embedding → Indexing → Retrieval → Metrics → Reporting
```

Each stage is modular and extensible:

| Stage | Module | Extension Point |
|-------|--------|-----------------|
| Fixtures | `scaffolder.fixtures` | `FixtureManager.register()` |
| Chunking | `scaffolder.chunking` | `ChunkingPipeline.register_strategy()` |
| Embedding | `scaffolder.embedding` | `Embedder` protocol |
| Retrieval | `scaffolder.retrieval` | `FAISSIndex` (or custom index) |
| Metrics | `scaffolder.metrics` | Metric functions |
| Reporting | `scaffolder.reporting` | Output format modules |

**Key design principle:** Each extension point uses Python protocols or simple
registration patterns. No base classes to inherit from — just implement the
expected interface.

---

## Adding Test Fixtures

### Step 1: Prepare the document

Save your legal document as a `.txt` file in `src/scaffolder/fixtures/documents/`:

```
src/scaffolder/fixtures/documents/my_nda.txt
```

Naming convention: `{jurisdiction}_{document_type}.txt`
- Examples: `uk_service_agreement.txt`, `us_msa.txt`, `eu_gdpr_excerpt.txt`

### Step 2: Register the fixture

The `FixtureManager` auto-discovers `.txt` files in the fixtures directory.
No code changes needed for basic fixtures.

For custom metadata, add an entry to the fixture registry:

```python
# In your setup or conftest:
from scaffolder.fixtures import FixtureManager

manager = FixtureManager()
manager.register(
    document_id="my_nda",
    jurisdiction="us",
    document_type="nda",
    path="src/scaffolder/fixtures/documents/my_nda.txt",
)
```

### Step 3: Add query annotations

Create `queries/my_nda.yaml`:

```yaml
document_id: my_nda
queries:
  - id: my_nda_q1
    text: "What information is covered by the NDA?"
    failure_mode: lost_definitions
    relevant_sections:
      - section_id: "definition_confidential_information"
        relevance: 3
        description: "Definition of confidential information"
      - section_id: "clause_exclusions"
        relevance: 2
        description: "Exclusions from confidential information"
    notes: "Tests whether the chunker preserves the definition link"
```

See `queries/schema.md` for the full YAML schema reference.

### Step 4: Run the benchmark

```bash
scaffolder benchmark  # Will automatically include the new fixture
```

---

[Sections 3-8 to be completed on Day 16]
```

## Outputs
- `docs/screenshots/` directory (created)
- `scripts/capture_screenshots.py` (screenshot capture instructions)
- `docs/screenshots/manifest.yaml` (screenshot metadata)
- `EXTENSIBILITY.md` (outline + sections 1-2)

## Acceptance Criteria
1. `docs/screenshots/` directory exists
2. `scripts/capture_screenshots.py` contains clear instructions for all 4 screenshots + GIF
3. `EXTENSIBILITY.md` has complete table of contents and sections 1-2 written
4. Section 2 (Adding Test Fixtures) has a complete working example
5. Architecture overview table accurately maps stages to modules
6. `make lint` passes (no Python files need linting — only markdown)

## Handoff Notes
- **To Agent A:** Screenshots need to be captured after a benchmark run produces results. If your pipeline isn't producing results yet, we can capture screenshots with mock data loaded via JSON upload.
- **To Day 16:** EXTENSIBILITY.md sections 3-8 need to be written. Each section needs: (1) step-by-step instructions, (2) code examples, (3) registration patterns, (4) testing guidance.
- **Decision:** Screenshots are described rather than auto-captured, because Streamlit doesn't have a built-in screenshot API. The script serves as a checklist for manual capture (or could be automated with Playwright/Selenium later).
