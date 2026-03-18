# Bootstrap Checklist

Run this ONCE before Day 1 begins. Both agents should verify these conditions are met.

## Pre-flight

```bash
# Verify Python
python --version  # Must be 3.10+

# Verify git
git status  # Must be in sdk-scaffolder repo

# Verify LexiChunk is accessible
pip install lexichunk
python -c "from lexichunk import LegalChunker; print('LexiChunk OK')"

# Verify LangChain text splitters
pip install langchain-text-splitters
python -c "from langchain_text_splitters import RecursiveCharacterTextSplitter; print('LangChain OK')"
```

## Fixture Documents

The 5 test fixtures must be copied from the LexiChunk repo into this repo. Agent A does this on Day 2, but if you want to pre-stage them:

```bash
pip install lexichunk
python -c "
import importlib.resources
import lexichunk
# Find the test fixtures path
import subprocess
result = subprocess.run(['pip', 'show', 'lexichunk'], capture_output=True, text=True)
for line in result.stdout.splitlines():
    if line.startswith('Location:'):
        print(line)
"
```

The fixtures are typically at: `<site-packages>/lexichunk/../tests/fixtures/` or can be fetched from:
https://github.com/emmcygn/lexichunk/tree/master/tests/fixtures

Files needed:
- `uk_service_agreement.txt`
- `uk_terms_conditions.txt`
- `us_msa.txt`
- `us_terms_of_service.txt`
- `eu_gdpr_excerpt.txt`

Place them in: `src/scaffolder/fixtures/documents/`

## What Day 1 Creates

After Day 1 completes, the repo should have:
- `pyproject.toml` — with all dependency groups
- `Makefile` — with make targets
- `src/scaffolder/models.py` — shared data contracts
- `src/scaffolder/config.py` — BenchmarkConfig
- `src/scaffolder/__init__.py` — package init
- `.gitignore` — results/, .cache/, __pycache__/, etc.
- CI skeleton (ruff + mypy + pytest should be runnable)

Until Day 1 is complete, `make lint` and `make test` will fail. That's expected.
