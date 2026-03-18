# Agent B — Day 04: Complete Query Annotations & Begin CLI Reporter

## Mission
Write the remaining 12-17 query annotations across all 5 fixtures (targeting 20-25 total) including cross-document contamination queries, then begin the CLI reporter with rich tables for structural metrics.

## Context
Day 3 produced 8 queries for `uk_service_agreement` and `us_msa`. Today completes the ground truth annotations for all 5 fixtures. Agent A is continuing work on the embedding pipeline. The CLI reporter is the first consumer of `BenchmarkResult` data — it produces the terminal output users see when running `scaffolder benchmark`.

## Prerequisites
- `queries/uk_service_agreement.yaml` and `queries/us_msa.yaml` exist (Day 3)
- `src/scaffolder/queries.py` exists with `load_queries()` function (Day 3)
- `src/scaffolder/models.py` exists with data contracts (Agent A, Day 1)
- Fixture files in `src/scaffolder/fixtures/documents/`: all 5 `.txt` files (Agent A)

## Checklist
- [ ] Task 1 — Write `queries/uk_terms_conditions.yaml` (4-5 queries)
- [ ] Task 2 — Write `queries/us_terms_of_service.yaml` (4-5 queries)
- [ ] Task 3 — Write `queries/eu_gdpr_excerpt.yaml` (4-5 queries)
- [ ] Task 4 — Add 2 cross-document contamination queries to existing files
- [ ] Task 5 — Begin `src/scaffolder/reporting/cli.py` — structural metrics table
- [ ] Task 6 — Write `tests/test_queries.py`

## Implementation Details

### queries/uk_terms_conditions.yaml

```yaml
document_id: uk_terms_conditions
queries:
  - id: uk_tc_q1
    text: "What are the consumer's rights to cancel or return products?"
    failure_mode: clause_fragmentation
    relevant_sections:
      - section_id: "clause_cancellation"
        relevance: 3
        description: "Cancellation rights and cooling-off period"
      - section_id: "clause_returns"
        relevance: 3
        description: "Returns policy and procedure"
      - section_id: "clause_refunds"
        relevance: 2
        description: "Refund conditions and timelines"
    notes: >
      Tests clause fragmentation. Consumer cancellation rights in UK T&Cs
      typically span cancellation, returns, and refund sub-clauses that
      must be read together for a complete understanding.

  - id: uk_tc_q2
    text: "How is personal data processed under this agreement?"
    failure_mode: orphaned_cross_refs
    relevant_sections:
      - section_id: "clause_data_protection"
        relevance: 3
        description: "Data protection and privacy clause"
      - section_id: "clause_privacy_policy_ref"
        relevance: 2
        description: "Reference to separate privacy policy"
    notes: >
      Tests orphaned cross-references. Data protection clauses in UK T&Cs
      frequently reference a separate privacy policy or GDPR compliance
      section. Baseline chunkers lose these references.

  - id: uk_tc_q3
    text: "What does 'Service' mean as defined in the terms?"
    failure_mode: lost_definitions
    relevant_sections:
      - section_id: "definition_service"
        relevance: 3
        description: "Definition of Service"
      - section_id: "clause_service_description"
        relevance: 2
        description: "Detailed service description"
    notes: >
      Tests lost definitions. Queries for defined terms should surface
      both the formal definition and the operative clauses that give
      the term practical meaning.

  - id: uk_tc_q4
    text: "Under what circumstances can the provider modify the terms?"
    failure_mode: destroyed_hierarchy
    relevant_sections:
      - section_id: "clause_amendments"
        relevance: 3
        description: "Amendment and variation clause"
      - section_id: "clause_amendments_notice"
        relevance: 3
        description: "Notice requirements for amendments"
      - section_id: "clause_amendments_acceptance"
        relevance: 2
        description: "Deemed acceptance of modified terms"
    notes: >
      Tests destroyed hierarchy. Amendment clauses have heading + multiple
      sub-clauses covering notice, acceptance, and effective date. Losing
      the parent heading makes sub-clauses meaningless.
```

### queries/us_terms_of_service.yaml

```yaml
document_id: us_terms_of_service
queries:
  - id: us_tos_q1
    text: "What is the arbitration process for disputes?"
    failure_mode: clause_fragmentation
    relevant_sections:
      - section_id: "clause_arbitration"
        relevance: 3
        description: "Mandatory arbitration clause"
      - section_id: "clause_arbitration_procedure"
        relevance: 3
        description: "Arbitration procedure and rules"
      - section_id: "clause_class_action_waiver"
        relevance: 2
        description: "Class action waiver"
      - section_id: "clause_opt_out"
        relevance: 1
        description: "Opt-out procedure for arbitration"
    notes: >
      Tests clause fragmentation. US ToS arbitration clauses are notoriously
      long and complex with multiple sub-sections. Fragmenting them loses
      critical opt-out and waiver information.

  - id: us_tos_q2
    text: "What content is prohibited under the acceptable use policy?"
    failure_mode: destroyed_hierarchy
    relevant_sections:
      - section_id: "clause_acceptable_use"
        relevance: 3
        description: "Acceptable use policy heading"
      - section_id: "clause_prohibited_content"
        relevance: 3
        description: "List of prohibited content types"
      - section_id: "clause_prohibited_conduct"
        relevance: 2
        description: "List of prohibited conduct"
    notes: >
      Tests destroyed hierarchy. Acceptable use policies often have a parent
      heading with two sub-lists (prohibited content and prohibited conduct).
      Baseline chunkers separate these from the heading.

  - id: us_tos_q3
    text: "How does the indemnification obligation work and what does it cover?"
    failure_mode: orphaned_cross_refs
    relevant_sections:
      - section_id: "clause_indemnification"
        relevance: 3
        description: "Indemnification obligation"
      - section_id: "clause_limitation_liability"
        relevance: 2
        description: "Limitation of liability (cross-referenced)"
      - section_id: "definition_losses"
        relevance: 1
        description: "Definition of covered losses"
    notes: >
      Tests orphaned cross-references. Indemnification clauses reference
      both the definition of losses and the limitation of liability section.
      Without resolving these references, the scope is unclear.

  - id: us_tos_q4
    text: "What rights does the user grant to the platform regarding their content?"
    failure_mode: lost_definitions
    relevant_sections:
      - section_id: "clause_user_content_license"
        relevance: 3
        description: "License grant for user content"
      - section_id: "definition_user_content"
        relevance: 2
        description: "Definition of User Content"
      - section_id: "clause_content_ownership"
        relevance: 2
        description: "Content ownership clause"
    notes: >
      Tests lost definitions. The license grant clause uses "User Content"
      which is defined elsewhere. Without the definition, the scope of
      the license is ambiguous.
```

### queries/eu_gdpr_excerpt.yaml

```yaml
document_id: eu_gdpr_excerpt
queries:
  - id: eu_gdpr_q1
    text: "What are the lawful bases for processing personal data?"
    failure_mode: clause_fragmentation
    relevant_sections:
      - section_id: "article_6"
        relevance: 3
        description: "Article 6 — Lawfulness of processing"
      - section_id: "article_6_1"
        relevance: 3
        description: "Six lawful bases enumerated"
      - section_id: "recital_40"
        relevance: 1
        description: "Recital explaining lawful bases"
    notes: >
      Tests clause fragmentation. Article 6 lists six lawful bases — splitting
      them across chunks means a retrieval query gets an incomplete list.

  - id: eu_gdpr_q2
    text: "What rights does a data subject have regarding their personal data?"
    failure_mode: destroyed_hierarchy
    relevant_sections:
      - section_id: "chapter_3_heading"
        relevance: 2
        description: "Chapter 3 heading — Rights of the data subject"
      - section_id: "article_15"
        relevance: 3
        description: "Right of access"
      - section_id: "article_16"
        relevance: 3
        description: "Right to rectification"
      - section_id: "article_17"
        relevance: 3
        description: "Right to erasure"
      - section_id: "article_20"
        relevance: 2
        description: "Right to data portability"
    notes: >
      Tests destroyed hierarchy. GDPR data subject rights span multiple
      articles under a single chapter. The chapter heading provides crucial
      context that baseline chunkers discard.

  - id: eu_gdpr_q3
    text: "What does 'personal data' mean under the GDPR?"
    failure_mode: lost_definitions
    relevant_sections:
      - section_id: "article_4_1"
        relevance: 3
        description: "Definition of personal data"
      - section_id: "recital_26"
        relevance: 2
        description: "Recital elaborating on personal data definition"
      - section_id: "article_9"
        relevance: 1
        description: "Special categories of personal data"
    notes: >
      Tests lost definitions. The GDPR defines 'personal data' in Article 4(1)
      and elaborates in Recital 26. Special categories in Article 9 extend
      the concept. All three must be retrievable for a complete answer.

  - id: eu_gdpr_q4
    text: "What are the requirements for obtaining valid consent?"
    failure_mode: orphaned_cross_refs
    relevant_sections:
      - section_id: "article_7"
        relevance: 3
        description: "Conditions for consent"
      - section_id: "article_4_11"
        relevance: 3
        description: "Definition of consent"
      - section_id: "recital_32"
        relevance: 2
        description: "Recital on consent requirements"
      - section_id: "article_8"
        relevance: 1
        description: "Consent for children"
    notes: >
      Tests orphaned cross-references. Article 7 on consent conditions
      cross-references the definition in Article 4(11). Without the
      definition, the conditions lack a foundation.
```

### Cross-document contamination queries

Add to `queries/uk_service_agreement.yaml`:

```yaml
  - id: uk_sa_q5
    text: "What are the limitation of liability provisions?"
    failure_mode: cross_doc_contamination
    relevant_sections:
      - section_id: "clause_limitation_liability"
        relevance: 3
        description: "UK service agreement limitation of liability"
    notes: >
      Tests cross-document contamination. Both UK and US documents have
      limitation of liability clauses. The retriever must prefer the UK
      service agreement clause when this query is asked in the context
      of the UK document. A jurisdiction-unaware chunker may surface
      the US clause.
```

Add to `queries/us_msa.yaml`:

```yaml
  - id: us_msa_q5
    text: "What data protection obligations does the service provider have?"
    failure_mode: cross_doc_contamination
    relevant_sections:
      - section_id: "clause_data_protection"
        relevance: 3
        description: "US MSA data protection provisions"
    notes: >
      Tests cross-document contamination. Both UK/EU and US documents
      address data protection, but under different legal frameworks
      (GDPR vs US state privacy laws). The retriever should surface
      the US-specific clause for this US document query.
```

### CLI reporter: src/scaffolder/reporting/cli.py

```python
"""CLI output using rich tables."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.console import Console
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from scaffolder.models import BenchmarkResult, StructuralResult


def _best_worst(
    values: list[float], higher_is_better: bool
) -> tuple[float, float]:
    """Return (best_value, worst_value) from a list of floats."""
    if not values:
        return 0.0, 0.0
    if higher_is_better:
        return max(values), min(values)
    return min(values), max(values)


def _color_value(
    value: float, best: float, worst: float, fmt: str = ".3f"
) -> Text:
    """Color a value green if best, red if worst, default otherwise."""
    text = f"{value:{fmt}}"
    if abs(value - best) < 1e-9:
        return Text(text, style="bold green")
    if abs(value - worst) < 1e-9:
        return Text(text, style="bold red")
    return Text(text)


def render_structural_table(
    results: list[StructuralResult],
    console: Console | None = None,
) -> None:
    """Render structural metrics as a colour-coded rich table.

    Green = best value per metric, Red = worst value per metric.
    """
    if console is None:
        console = Console()

    if not results:
        console.print("[yellow]No structural results to display.[/yellow]")
        return

    # Group by document
    docs = sorted({r.document_id for r in results})

    for doc_id in docs:
        doc_results = [r for r in results if r.document_id == doc_id]
        if not doc_results:
            continue

        table = Table(
            title=f"Structural Metrics — {doc_id}",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Strategy", style="bold")
        table.add_column("Clause Frag.", justify="right")
        table.add_column("Def. Preserv.", justify="right")
        table.add_column("XRef Resol.", justify="right")
        table.add_column("Hierarchy Depth", justify="right")
        table.add_column("Avg Size (tok)", justify="right")
        table.add_column("Chunks", justify="right")

        # Compute best/worst for colour coding
        frag_vals = [r.clause_fragmentation_rate for r in doc_results]
        def_vals = [r.definition_preservation_rate for r in doc_results]
        xref_vals = [r.cross_ref_resolution_rate for r in doc_results]
        hier_vals = [r.hierarchy_depth_retained for r in doc_results]

        frag_best, frag_worst = _best_worst(frag_vals, higher_is_better=False)
        def_best, def_worst = _best_worst(def_vals, higher_is_better=True)
        xref_best, xref_worst = _best_worst(xref_vals, higher_is_better=True)
        hier_best, hier_worst = _best_worst(hier_vals, higher_is_better=True)

        for r in doc_results:
            stats = r.chunk_size_stats
            avg_size = f"{stats.get('mean', 0):.0f}"
            chunk_count = str(stats.get('count', 0)) if 'count' in stats else "—"

            table.add_row(
                r.strategy,
                _color_value(r.clause_fragmentation_rate, frag_best, frag_worst),
                _color_value(r.definition_preservation_rate, def_best, def_worst),
                _color_value(r.cross_ref_resolution_rate, xref_best, xref_worst),
                _color_value(r.hierarchy_depth_retained, hier_best, hier_worst, ".2f"),
                avg_size,
                chunk_count,
            )

        console.print(table)
        console.print()


def render_summary_header(
    result: BenchmarkResult,
    console: Console | None = None,
) -> None:
    """Render a summary header with config and timestamp."""
    if console is None:
        console = Console()

    console.print()
    console.rule("[bold blue]Scaffolder Benchmark Results[/bold blue]")
    console.print(f"  Timestamp: {result.timestamp}")
    console.print(f"  Strategies: {', '.join(result.config.get('strategies', []))}")
    console.print(f"  Documents: {len({r.document_id for r in result.structural_results})}")
    if result.retrieval_results:
        models = {r.model for r in result.retrieval_results}
        console.print(f"  Embedding models: {', '.join(sorted(models))}")
    console.rule()
    console.print()
```

## Outputs
- `queries/uk_terms_conditions.yaml` (4 queries)
- `queries/us_terms_of_service.yaml` (4 queries)
- `queries/eu_gdpr_excerpt.yaml` (4 queries)
- Updated `queries/uk_service_agreement.yaml` (+1 cross-doc query)
- Updated `queries/us_msa.yaml` (+1 cross-doc query)
- `src/scaffolder/reporting/cli.py` (structural metrics table)
- `tests/test_queries.py`

## Acceptance Criteria
1. `python -c "from scaffolder.queries import load_queries; qs = load_queries('queries'); print(f'{len(qs)} queries loaded')"` prints `20` or more
2. At least 2 queries have `failure_mode: cross_doc_contamination`
3. Every failure mode is represented by at least 3 queries
4. `from scaffolder.reporting.cli import render_structural_table` imports without error
5. `make lint` passes on all new files
6. `tests/test_queries.py` passes — tests that all YAML files parse, all failure modes are valid, all queries have at least 2 relevant sections

## Handoff Notes
- **To Agent A:** All 5 query annotation files are now complete. The `section_id` values are human labels — your `RetrievalSimulator` needs a mapping strategy to convert them to chunk IDs. Recommended approach: for each annotated section, find chunks whose text overlaps with the section text, using the section description as a hint.
- **To Day 5:** The CLI reporter has structural metrics. Day 5 adds JSON export and the Streamlit skeleton. The retrieval metrics CLI table comes on Day 10 (after Agent A delivers `RetrievalSimulator`).
- **Decision:** We target 20-25 total queries. More can be added later — the YAML schema is extensible. The `load_queries` function is the stable API.
