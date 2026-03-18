# Agent A — Day 18: README Content + pyproject.toml Extras

## Mission
Write the technical content for README.md (quickstart, output examples, benchmark results with actual numbers, architecture overview) and configure pyproject.toml dependency extras ([local], [voyage], [dashboard], [all], [dev]).

## Context
Day 17 handled edge cases and performance. Agent B is PAIRING on README today -- Agent A provides the technical content and benchmark data, Agent B provides installation, screenshots, and formatting. Today also finalizes the pyproject.toml extras groups so users can install only what they need.

## Prerequisites
- `results/full_benchmark.json` with actual benchmark numbers
- All modules working and tested
- pyproject.toml exists (Agent B created on Day 1)

## Checklist
- [ ] Write README sections: Quickstart, Output Examples, Benchmark Results, Architecture
- [ ] Extract actual benchmark numbers from latest JSON results
- [ ] Create ASCII/table representation of CLI output for README
- [ ] Configure pyproject.toml extras: [local], [voyage], [dashboard], [all], [dev]
- [ ] Verify each extras group installs correctly
- [ ] PAIR with Agent B on final README assembly

## Implementation Details

### README Content for Agent A

Agent A writes these sections. Agent B integrates them into the final README.

#### Quickstart Section

```markdown
## Quickstart

```bash
# Install with local embedding models
pip install -e ".[local]"

# Run structural benchmark (no embeddings, fast)
make benchmark

# Run full benchmark with embeddings
make benchmark-embed

# Generate HTML report
make report
```

### Output

The CLI produces rich tables:

```
Structural Quality -- Average Across All Documents
┌───────────────────┬────────────┬──────────┬──────────┬──────────┐
│ Strategy          │ Avg Frag   │ Avg Def  │ Avg XRef │ Avg Hier │
├───────────────────┼────────────┼──────────┼──────────┼──────────┤
│ lexichunk         │ 0.045      │ 0.923    │ 0.871    │ 1.000    │
│ lexichunk_ctx     │ 0.045      │ 0.923    │ 0.871    │ 1.000    │
│ rcts              │ 0.412      │ 0.346    │ 0.203    │ 0.667    │
│ sentence_split    │ 0.523      │ 0.289    │ 0.156    │ 0.500    │
│ fixed_size        │ 0.634      │ 0.198    │ 0.102    │ 0.333    │
└───────────────────┴────────────┴──────────┴──────────┴──────────┘
```

> **Note:** Replace the numbers above with actual benchmark output. Run
> `make benchmark` and copy the table.
```

#### Benchmark Results Section

```markdown
## Benchmark Results

LexiChunk consistently outperforms general-purpose chunking strategies
across both structural quality and retrieval metrics.

### Structural Quality (averaged across 5 legal documents)

| Metric | LexiChunk | RCTS-512 | Sentence Split | Fixed-512 |
|--------|-----------|----------|----------------|-----------|
| Clause Fragmentation (lower=better) | **0.XXX** | 0.XXX | 0.XXX | 0.XXX |
| Definition Preservation | **0.XXX** | 0.XXX | 0.XXX | 0.XXX |
| Cross-Ref Resolution | **0.XXX** | 0.XXX | 0.XXX | 0.XXX |
| Hierarchy Depth | **0.XXX** | 0.XXX | 0.XXX | 0.XXX |

### Retrieval Quality (all-MiniLM-L6-v2, averaged across N queries)

| Metric | LexiChunk | LexiChunk+Context | RCTS-512 | Sentence | Fixed-512 |
|--------|-----------|-------------------|----------|----------|-----------|
| P@5 | **0.XXX** | 0.XXX | 0.XXX | 0.XXX | 0.XXX |
| R@10 | **0.XXX** | 0.XXX | 0.XXX | 0.XXX | 0.XXX |
| MRR | **0.XXX** | 0.XXX | 0.XXX | 0.XXX | 0.XXX |
| NDCG@10 | **0.XXX** | **0.XXX** | 0.XXX | 0.XXX | 0.XXX |

All improvements over baselines are statistically significant
(p < 0.05, paired t-test). See `docs/metrics.md` for methodology.
```

Fill in actual numbers from `results/full_benchmark.json`. Write a script or use Python to extract them:

```python
# Script to extract README numbers
import json

with open("results/full_benchmark.json") as f:
    data = json.load(f)

# Average structural metrics per strategy
from collections import defaultdict
by_strat = defaultdict(list)
for sm in data["structural_metrics"]:
    by_strat[sm["strategy"]].append(sm)

for strat, metrics in sorted(by_strat.items()):
    n = len(metrics)
    print(f"{strat}:")
    print(f"  CFR: {sum(m['clause_fragmentation_rate'] for m in metrics)/n:.3f}")
    print(f"  DPR: {sum(m['definition_preservation_rate'] for m in metrics)/n:.3f}")
    print(f"  CRRR: {sum(m['cross_ref_resolution_rate'] for m in metrics)/n:.3f}")
    print(f"  HDR: {sum(m['hierarchy_depth_retained'] for m in metrics)/n:.3f}")
```

#### Architecture Section

```markdown
## Architecture

```
┌─────────────┐    ┌─────────────────┐    ┌────────────────┐
│ Fixture     │───>│ Chunking        │───>│ Embedding      │
│ Manager     │    │ Pipeline        │    │ Pipeline       │
│ (5 docs)    │    │ (5 strategies)  │    │ (3 models)     │
└─────────────┘    └─────────────────┘    └───────┬────────┘
                                                   │
┌─────────────┐    ┌─────────────────┐    ┌───────┴────────┐
│ Reporters   │<───│ Metrics +       │<───│ FAISS Index +  │
│ (CLI/JSON/  │    │ Significance    │    │ Retrieval Sim  │
│  HTML)      │    │ Testing         │    │                │
└─────────────┘    └─────────────────┘    └────────────────┘
```

**Source layout:**
- `src/scaffolder/fixtures/` — Document loading and management
- `src/scaffolder/chunking/` — Strategy wrappers and pipeline
- `src/scaffolder/embedding/` — Model adapters and caching
- `src/scaffolder/retrieval/` — FAISS indexing and query simulation
- `src/scaffolder/metrics/` — Structural, retrieval, and statistical metrics
- `src/scaffolder/reporting/` — CLI (rich), JSON, HTML (Jinja2) output
- `src/scaffolder/dashboard/` — Streamlit interactive dashboard
```

### pyproject.toml Extras

Update pyproject.toml with dependency groups. Agent B owns this file, but Agent A provides the dependency specifications:

```toml
[project.optional-dependencies]
local = [
    "sentence-transformers>=2.2.0",
    "faiss-cpu>=1.7.4",
]
voyage = [
    "voyageai>=0.2.0",
]
dashboard = [
    "streamlit>=1.28.0",
    "plotly>=5.18.0",
]
all = [
    "sdk-scaffolder[local,voyage,dashboard]",
]
dev = [
    "sdk-scaffolder[all]",
    "ruff>=0.1.0",
    "mypy>=1.7.0",
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "types-PyYAML",
    "types-requests",
]
```

Core dependencies (always installed):
```toml
[project]
dependencies = [
    "lexichunk>=0.1.0",
    "langchain-text-splitters>=0.0.1",
    "rich>=13.0.0",
    "pyyaml>=6.0",
    "numpy>=1.24.0",
    "scipy>=1.10.0",
    "jinja2>=3.1.0",
]
```

### Verify Extras Installation

```bash
# Create fresh venv and test each extras group
python -m venv /tmp/test-local && source /tmp/test-local/bin/activate
pip install -e ".[local]"
python -c "from sentence_transformers import SentenceTransformer; print('OK')"
python -c "import faiss; print('OK')"
deactivate

python -m venv /tmp/test-minimal && source /tmp/test-minimal/bin/activate
pip install -e "."
python -c "from scaffolder.models import Document; print('OK')"
# Verify sentence-transformers is NOT installed
python -c "import sentence_transformers" 2>&1 | grep -q "No module"
deactivate

python -m venv /tmp/test-dev && source /tmp/test-dev/bin/activate
pip install -e ".[dev]"
make test
deactivate
```

## Outputs
- README content (sections for Agent B to integrate)
- `pyproject.toml` (updated extras -- coordinate with Agent B)
- Numbers extraction script

## Acceptance Criteria
1. README content includes actual benchmark numbers (not XXX placeholders).
2. `pip install -e ".[local]"` installs sentence-transformers and faiss-cpu.
3. `pip install -e ".[dev]"` installs everything including test dependencies.
4. `pip install -e "."` installs only core dependencies.
5. Architecture diagram accurately reflects the codebase.
6. PAIR session with Agent B produces agreement on final README structure.

## Handoff Notes
- **To Agent B (README PAIR):** Sections are ready: Quickstart, Output Examples, Benchmark Results, Architecture. Please integrate these with your sections (Installation, Screenshots, Configuration, Deployment). Use the actual numbers -- do not leave XXX placeholders.
- **To Day 19:** README and extras are complete. Day 19 is the code review sweep.
- **pyproject.toml note:** Agent B should merge the extras changes since they own this file. The dependency versions listed above are minimums.
