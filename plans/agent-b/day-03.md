# Agent B — Day 03: Query Annotation Schema & First 8 Queries

## Mission
Design the query annotation YAML schema and write the first 8 annotated queries for `uk_service_agreement` and `us_msa`, targeting the 5 failure modes that differentiate LexiChunk from baselines.

## Context
Day 2 completed the config system. Agent A is delivering `ChunkingPipeline` and `FixtureManager` today — once those land, Agent B can start building Streamlit against them. Today is about preparing the retrieval evaluation ground truth: the query annotations that define what "correct retrieval" looks like for each test query. These YAML files live in `queries/` and are loaded by Agent A's `RetrievalSimulator` (arriving later) and by Agent B's Streamlit dashboard.

## Prerequisites
- `src/scaffolder/config.py` complete with `query_dir` pointing to `queries/`
- `src/scaffolder/fixtures/documents/` populated by Agent A with the 5 fixture texts (or at minimum `uk_service_agreement.txt` and `us_msa.txt`)
- Understanding of the 5 failure modes: clause fragmentation, orphaned cross-refs, lost definitions, destroyed hierarchy, cross-doc contamination

## Checklist
- [ ] Task 1 — Write `queries/schema.md` documenting the YAML annotation format
- [ ] Task 2 — Read `uk_service_agreement.txt` fixture and identify key sections
- [ ] Task 3 — Write `queries/uk_service_agreement.yaml` with 4 queries
- [ ] Task 4 — Read `us_msa.txt` fixture and identify key sections
- [ ] Task 5 — Write `queries/us_msa.yaml` with 4 queries
- [ ] Task 6 — Write `src/scaffolder/queries.py` — a loader that parses query YAML files into typed dataclasses

## Implementation Details

### Query Annotation Schema

The schema defines how to annotate queries with ground-truth relevance judgments. Each query targets a specific failure mode that general-purpose chunkers exhibit. Create `queries/schema.md`:

```markdown
# Query Annotation Schema

## File naming
Each fixture document gets a corresponding YAML file:
- `queries/uk_service_agreement.yaml`
- `queries/us_msa.yaml`
- `queries/uk_terms_conditions.yaml`
- `queries/us_terms_of_service.yaml`
- `queries/eu_gdpr_excerpt.yaml`

## YAML structure

```yaml
document_id: <string>  # Must match the fixture filename (without .txt)
queries:
  - id: <string>        # Unique query ID, format: {jurisdiction}_{doc_abbrev}_q{N}
    text: <string>       # The natural language query a user would ask
    failure_mode: <enum> # One of the 5 failure modes this query tests
    relevant_sections:
      - section_id: <string>    # Identifier for the relevant section
        relevance: <int>        # Graded relevance: 3=exact, 2=partial, 1=background
        description: <string>   # Human-readable description of what this section contains
    notes: <string>             # Explanation of what this query tests and why
```

## Failure modes
1. **clause_fragmentation** — A chunker splits a single clause across multiple chunks, losing context. Query should target a clause that needs to be read as a whole.
2. **orphaned_cross_refs** — A chunk references another section (e.g., "as defined in Section 3") but the chunker doesn't resolve or preserve the reference. Query should require understanding a cross-reference.
3. **lost_definitions** — A chunk uses a defined term (e.g., "Confidential Information") but the definition was in a different chunk and not propagated. Query should require the definition to answer correctly.
4. **destroyed_hierarchy** — A chunker loses the parent-child relationship between sections (e.g., sub-clause 3.1 separated from clause 3 heading). Query should need hierarchy context.
5. **cross_doc_contamination** — A query could match sections from multiple documents, but the correct answer is document-specific. Tests jurisdiction-aware retrieval.

## Graded relevance
- **3 (exact):** This section directly answers the query. The ideal chunk to retrieve.
- **2 (partial):** This section is closely related — same parent clause, related sub-clause, or provides necessary context.
- **1 (background):** This section provides background information that helps answer the query but isn't the primary answer.

## Section identification
Section IDs should match the structure of the document:
- Use `clause_N` for top-level numbered clauses
- Use `clause_N.M` for sub-clauses
- Use `schedule_N` for schedules/appendices
- Use `definition_TERM` for specific defined terms
- Use `preamble` for introductory paragraphs
- Use `recital_N` for recitals/whereas clauses
```

### First 4 queries: uk_service_agreement.yaml

Read the `uk_service_agreement.txt` fixture first. Look for:
- Numbered clauses with sub-clauses (hierarchy)
- Defined terms in quotes or bold
- Cross-references ("as set out in clause X", "subject to Section Y")
- Termination, liability, and indemnity clauses (commonly fragmented)

```yaml
document_id: uk_service_agreement
queries:
  - id: uk_sa_q1
    text: "What are the termination provisions and notice periods?"
    failure_mode: clause_fragmentation
    relevant_sections:
      - section_id: "clause_termination"
        relevance: 3
        description: "Main termination clause with notice period requirements"
      - section_id: "clause_termination_effects"
        relevance: 2
        description: "Effects of termination and surviving obligations"
      - section_id: "clause_termination_for_cause"
        relevance: 2
        description: "Termination for material breach provisions"
    notes: >
      Tests clause fragmentation. General-purpose chunkers often split the
      termination clause across multiple chunks, separating the notice period
      from the grounds for termination. LexiChunk should keep the entire
      termination clause tree intact.

  - id: uk_sa_q2
    text: "What happens to Confidential Information after termination?"
    failure_mode: lost_definitions
    relevant_sections:
      - section_id: "clause_confidentiality"
        relevance: 3
        description: "Confidentiality obligations and post-termination duties"
      - section_id: "definition_confidential_information"
        relevance: 2
        description: "Definition of Confidential Information"
      - section_id: "clause_termination_effects"
        relevance: 2
        description: "Surviving obligations after termination"
    notes: >
      Tests lost definitions. To answer this query, the retriever must surface
      both the confidentiality clause AND the definition of "Confidential
      Information." Baseline chunkers lose the definition linkage.

  - id: uk_sa_q3
    text: "What limitations apply to liability under this agreement?"
    failure_mode: orphaned_cross_refs
    relevant_sections:
      - section_id: "clause_limitation_liability"
        relevance: 3
        description: "Limitation of liability clause"
      - section_id: "clause_indemnification"
        relevance: 2
        description: "Indemnification obligations (often cross-referenced)"
      - section_id: "clause_exclusions"
        relevance: 1
        description: "Exclusions from limitation caps"
    notes: >
      Tests orphaned cross-references. Limitation of liability clauses
      typically reference other sections (e.g., "except as set out in clause X").
      Baseline chunkers drop these references.

  - id: uk_sa_q4
    text: "What are the obligations of the Service Provider under clause 2?"
    failure_mode: destroyed_hierarchy
    relevant_sections:
      - section_id: "clause_2"
        relevance: 3
        description: "Service provider obligations heading"
      - section_id: "clause_2.1"
        relevance: 3
        description: "Primary service delivery obligation"
      - section_id: "clause_2.2"
        relevance: 3
        description: "Quality and compliance obligation"
      - section_id: "clause_2.3"
        relevance: 2
        description: "Reporting obligations"
    notes: >
      Tests destroyed hierarchy. The query asks about a parent clause, so all
      sub-clauses are relevant. Baseline chunkers may separate 2.1, 2.2, and
      2.3 from the clause 2 heading, losing the hierarchical relationship.
```

Adjust `section_id` values based on actual fixture content. The IDs above are illustrative — read the fixture and map to real section identifiers.

### Next 4 queries: us_msa.yaml

```yaml
document_id: us_msa
queries:
  - id: us_msa_q1
    text: "What intellectual property rights does each party retain?"
    failure_mode: clause_fragmentation
    relevant_sections:
      - section_id: "clause_ip_ownership"
        relevance: 3
        description: "IP ownership and rights retention clause"
      - section_id: "clause_ip_license"
        relevance: 2
        description: "License grants related to IP"
      - section_id: "clause_work_product"
        relevance: 2
        description: "Work product ownership and assignment"
    notes: >
      Tests clause fragmentation. IP clauses in MSAs often span multiple
      sub-sections covering ownership, licensing, and work product. Fragmenting
      these gives an incomplete picture of IP rights.

  - id: us_msa_q2
    text: "How is a Force Majeure Event defined and what are its consequences?"
    failure_mode: lost_definitions
    relevant_sections:
      - section_id: "definition_force_majeure"
        relevance: 3
        description: "Definition of Force Majeure Event"
      - section_id: "clause_force_majeure"
        relevance: 3
        description: "Force majeure clause with notice and consequences"
    notes: >
      Tests lost definitions. The query requires both the definition of
      "Force Majeure Event" and the operative clause describing consequences.
      Baseline chunkers often place these in separate chunks without linkage.

  - id: us_msa_q3
    text: "What governing law applies and how are disputes resolved?"
    failure_mode: orphaned_cross_refs
    relevant_sections:
      - section_id: "clause_governing_law"
        relevance: 3
        description: "Governing law clause"
      - section_id: "clause_dispute_resolution"
        relevance: 3
        description: "Dispute resolution mechanism (arbitration/litigation)"
      - section_id: "clause_jurisdiction"
        relevance: 2
        description: "Jurisdiction and venue"
    notes: >
      Tests orphaned cross-references. Governing law and dispute resolution
      clauses frequently cross-reference each other. The dispute resolution
      clause may say "governed by the laws specified in Section X."

  - id: us_msa_q4
    text: "What are the payment terms under Schedule A?"
    failure_mode: destroyed_hierarchy
    relevant_sections:
      - section_id: "clause_fees"
        relevance: 3
        description: "Fees and payment terms in the main body"
      - section_id: "schedule_a"
        relevance: 3
        description: "Schedule A with pricing details"
      - section_id: "clause_invoicing"
        relevance: 2
        description: "Invoice and payment procedure"
    notes: >
      Tests destroyed hierarchy. Payment terms often span the main body
      clause plus a schedule. Baseline chunkers treat schedules as separate
      flat text, losing the relationship between the main clause and its
      schedule.
```

### Query loader: src/scaffolder/queries.py

```python
"""Query annotation loader — reads YAML ground-truth files."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class RelevantSection:
    """A section identified as relevant to a query."""

    section_id: str
    relevance: int  # 3=exact, 2=partial, 1=background
    description: str


@dataclass(frozen=True)
class AnnotatedQuery:
    """A query with ground-truth relevance annotations."""

    id: str
    text: str
    document_id: str
    failure_mode: str
    relevant_sections: list[RelevantSection]
    notes: str = ""


VALID_FAILURE_MODES = frozenset({
    "clause_fragmentation",
    "orphaned_cross_refs",
    "lost_definitions",
    "destroyed_hierarchy",
    "cross_doc_contamination",
})


def load_queries(query_dir: str | Path) -> list[AnnotatedQuery]:
    """Load all query annotation files from a directory.

    Args:
        query_dir: Path to directory containing YAML query files.

    Returns:
        List of all annotated queries across all fixture documents.

    Raises:
        ValueError: If a query file has invalid structure or unknown failure mode.
    """
    query_dir = Path(query_dir)
    queries: list[AnnotatedQuery] = []

    for yaml_path in sorted(query_dir.glob("*.yaml")):
        if yaml_path.name == "schema.md":
            continue
        with open(yaml_path) as f:
            data: dict[str, Any] = yaml.safe_load(f) or {}

        document_id = data.get("document_id", yaml_path.stem)

        for q in data.get("queries", []):
            # Validate failure mode
            fm = q.get("failure_mode", "")
            if fm not in VALID_FAILURE_MODES:
                raise ValueError(
                    f"Query {q.get('id', '?')} has invalid failure_mode '{fm}'. "
                    f"Valid: {sorted(VALID_FAILURE_MODES)}"
                )

            sections = [
                RelevantSection(
                    section_id=s["section_id"],
                    relevance=s["relevance"],
                    description=s.get("description", ""),
                )
                for s in q.get("relevant_sections", [])
            ]

            queries.append(
                AnnotatedQuery(
                    id=q["id"],
                    text=q["text"],
                    document_id=document_id,
                    failure_mode=fm,
                    relevant_sections=sections,
                    notes=q.get("notes", ""),
                )
            )

    return queries


def load_queries_for_document(
    query_dir: str | Path, document_id: str
) -> list[AnnotatedQuery]:
    """Load queries for a specific document."""
    all_queries = load_queries(query_dir)
    return [q for q in all_queries if q.document_id == document_id]
```

## Outputs
- `queries/schema.md`
- `queries/uk_service_agreement.yaml` (4 queries)
- `queries/us_msa.yaml` (4 queries)
- `src/scaffolder/queries.py`

## Acceptance Criteria
1. `python -c "from scaffolder.queries import load_queries; qs = load_queries('queries'); print(f'{len(qs)} queries loaded')"` prints `8 queries loaded`
2. Each query has a valid `failure_mode` from the 5 defined modes
3. Each query has at least 2 `relevant_sections` with graded relevance
4. `make lint` and `make typecheck` pass on `queries.py`
5. The YAML files parse without errors: `python -c "import yaml; yaml.safe_load(open('queries/uk_service_agreement.yaml'))"`

## Handoff Notes
- **To Agent A:** The query annotations are in `queries/*.yaml`. Use `from scaffolder.queries import load_queries` to load them. Each `AnnotatedQuery` has `relevant_sections` with `section_id` and `relevance` (3=exact, 2=partial, 1=background). Your `RetrievalSimulator` will need to map `section_id` to actual chunk IDs after chunking — this mapping depends on how chunks align with document sections.
- **To Day 4:** Need 12-17 more queries across the remaining 3 fixtures. Also need at least 2 cross-document contamination queries that test jurisdiction-aware retrieval.
- **Decision:** Section IDs are human-assigned labels (not auto-generated). The mapping from section_id to chunk_id happens at retrieval evaluation time, based on text overlap between the annotated section and the generated chunks.
