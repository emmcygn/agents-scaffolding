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
