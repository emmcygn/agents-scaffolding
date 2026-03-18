# Agent B — Day 19: Dependency Audit & CI Configuration

## Mission
Pin all dependency versions in `pyproject.toml`, verify license compatibility (all MIT/Apache/BSD), check for conflicts, and configure GitHub Actions CI to run lint + type-check + test on Python 3.10, 3.11, and 3.12.

## Context
Day 18 completed the README. The codebase is feature-complete and documented. Before tagging v1.0.0 (Day 20), we need to ensure reproducible builds (pinned deps), legal compliance (license audit), and automated quality gates (CI). This is the final quality assurance day.

## Prerequisites
- `pyproject.toml` with all dependencies (Day 1, refined throughout)
- All tests passing: `make ci` (lint + typecheck + test)
- Complete codebase in `src/scaffolder/`

## Checklist
- [ ] Task 1 — Audit and pin all dependency versions in `pyproject.toml`
- [ ] Task 2 — Check all dependency licenses (must be MIT, Apache-2.0, or BSD)
- [ ] Task 3 — Run `pip check` to verify no dependency conflicts
- [ ] Task 4 — Create `.github/workflows/ci.yml` for GitHub Actions
- [ ] Task 5 — Create `.github/workflows/dashboard.yml` for dashboard smoke test
- [ ] Task 6 — Generate `requirements.lock` for reproducible builds
- [ ] Task 7 — Final `make ci` run — all checks must pass

## Implementation Details

### Dependency version pinning

Update `pyproject.toml` with tighter version bounds. The strategy:
- Core deps: pin to `>=X.Y,<(X+1).0` (major version ceiling)
- Dev deps: pin to `>=X.Y,<(X+1).0`
- Avoid exact pins (`==`) in library metadata — that's too restrictive

```toml
dependencies = [
    "lexichunk>=0.1.0,<1.0",
    "langchain-text-splitters>=0.2.0,<1.0",
    "rich>=13.0,<14.0",
    "pyyaml>=6.0,<7.0",
    "numpy>=1.24,<2.0",
    "scipy>=1.10,<2.0",
    "jinja2>=3.1,<4.0",
]

[project.optional-dependencies]
embed = [
    "sentence-transformers>=2.2,<3.0",
    "faiss-cpu>=1.7,<2.0",
]
voyage = [
    "voyageai>=0.2,<1.0",
]
dashboard = [
    "streamlit>=1.30,<2.0",
    "plotly>=5.18,<6.0",
]
dev = [
    "ruff>=0.4,<1.0",
    "mypy>=1.10,<2.0",
    "pytest>=8.0,<9.0",
    "pytest-cov>=5.0,<6.0",
    "types-PyYAML>=6.0,<7.0",
]
```

### License audit

Check each dependency's license. All must be compatible with MIT:

| Package | License | Compatible? |
|---------|---------|-------------|
| lexichunk | MIT | Yes |
| langchain-text-splitters | MIT | Yes |
| rich | MIT | Yes |
| pyyaml | MIT | Yes |
| numpy | BSD-3-Clause | Yes |
| scipy | BSD-3-Clause | Yes |
| jinja2 | BSD-3-Clause | Yes |
| sentence-transformers | Apache-2.0 | Yes |
| faiss-cpu | MIT | Yes |
| voyageai | MIT | Yes |
| streamlit | Apache-2.0 | Yes |
| plotly | MIT | Yes |
| ruff | MIT | Yes |
| mypy | MIT | Yes |
| pytest | MIT | Yes |
| pytest-cov | MIT | Yes |

Verify programmatically:

```bash
pip install pip-licenses
pip-licenses --packages lexichunk langchain-text-splitters rich pyyaml numpy scipy jinja2 sentence-transformers faiss-cpu streamlit plotly ruff mypy pytest pytest-cov --format=table
```

All must show MIT, Apache-2.0, BSD-2-Clause, or BSD-3-Clause. If any dependency has a copyleft license (GPL, LGPL, AGPL), it must be removed or replaced.

### GitHub Actions CI: .github/workflows/ci.yml

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Ruff check
        run: ruff check src/ tests/

      - name: Ruff format check
        run: ruff format --check src/ tests/

      - name: Mypy
        run: mypy src/scaffolder/

  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: pip install -e ".[dev,embed]"

      - name: Run tests
        run: pytest tests/ -v --cov=scaffolder --cov-report=term-missing --cov-fail-under=80

      - name: Upload coverage
        if: matrix.python-version == '3.12'
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: htmlcov/

  dependency-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install all dependencies
        run: pip install -e ".[all]"

      - name: Check for conflicts
        run: pip check

      - name: License check
        run: |
          pip install pip-licenses
          pip-licenses --fail-on="GNU General Public License v3 (GPLv3);GNU General Public License v2 (GPLv2);GNU Affero General Public License v3 (AGPLv3)"
```

### Dashboard smoke test: .github/workflows/dashboard.yml

```yaml
name: Dashboard Smoke Test

on:
  push:
    branches: [main]
    paths:
      - "src/scaffolder/dashboard/**"
      - "requirements-dashboard.txt"
  pull_request:
    branches: [main]
    paths:
      - "src/scaffolder/dashboard/**"

jobs:
  smoke-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dashboard dependencies
        run: pip install -r requirements-dashboard.txt && pip install -e .

      - name: Import check
        run: |
          python -c "from scaffolder.dashboard.app import main; print('Dashboard imports OK')"
          python -c "from scaffolder.dashboard.page_compare import render_page; print('Compare page OK')"
          python -c "from scaffolder.dashboard.page_retrieval import render_page; print('Retrieval page OK')"
          python -c "from scaffolder.dashboard.page_metrics import render_page; print('Metrics page OK')"

      - name: Streamlit check
        run: |
          timeout 10 streamlit run streamlit_app.py --server.headless true --server.port 8501 &
          sleep 5
          curl -f http://localhost:8501/_stcore/health || exit 1
          echo "Dashboard health check passed"
```

### Lock file generation

Generate a lock file for reproducible production installs:

```bash
pip install pip-tools
pip-compile pyproject.toml --all-extras -o requirements.lock
```

Add `requirements.lock` to the repo but note in README that it's for reference — the primary install method is `pip install -e ".[extras]"`.

### Final CI checklist

Run these commands and verify all pass:

```bash
# Lint
make lint

# Type check
make typecheck

# Tests
make test

# Dependency check
pip check

# Import smoke test
python -c "import scaffolder; print(scaffolder.__version__)"
python -c "from scaffolder.config import BenchmarkConfig; BenchmarkConfig().validate()"
python -c "from scaffolder.queries import load_queries; print(f'{len(load_queries(\"queries\"))} queries')"
python -c "from scaffolder.reporting.cli import render_benchmark"
python -c "from scaffolder.reporting.json_export import export_json"
python -c "from scaffolder.embedding.voyage import VoyageEmbedder"
```

## Outputs
- `pyproject.toml` (updated: pinned version ranges)
- `.github/workflows/ci.yml`
- `.github/workflows/dashboard.yml`
- `requirements.lock`

## Acceptance Criteria
1. `pip install -e ".[all]"` succeeds without dependency conflicts
2. `pip check` reports no broken dependencies
3. All dependency licenses are MIT, Apache-2.0, or BSD
4. `.github/workflows/ci.yml` is valid YAML (check with `yamllint` or GitHub)
5. `make ci` passes locally (lint + typecheck + test)
6. CI matrix covers Python 3.10, 3.11, 3.12
7. Dashboard smoke test imports all pages without error

## Handoff Notes
- **To Agent A:** CI is configured. After merging, push to GitHub and verify the Actions run. If your modules have import-time side effects (loading models, reading files), they may fail in CI where models aren't installed. Ensure lazy loading for heavy dependencies.
- **To Day 20:** Everything is ready for v1.0.0 tag. Day 20 is the final pairing day: verify everything works end-to-end, tag the release, and write post-v1 issues.
- **Decision:** We pin to major version ceilings (`<X+1.0`) rather than exact versions. This gives flexibility for patch updates while preventing breaking changes from major releases. The `requirements.lock` provides exact versions for anyone who needs reproducibility.
