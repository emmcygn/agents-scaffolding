# The lexchunk playbook: 4 weeks to a portfolio-defining open-source project

**A legal-document-aware chunking library can be the single most effective portfolio artifact for senior AI/legal tech roles — if built with the right signals in the right sequence.** The combination of a UK/Philippines law degree and an MSc in Computer Science is extraordinarily rare in the RAG tooling space; no other chunking library author can claim genuine legal expertise alongside systems-level engineering skill. This plan weaponizes that advantage across 160+ hours, producing not just a useful tool but a demonstrable proof of senior engineering judgment, domain mastery, and product thinking — the exact trifecta that founding-engineer hiring loops test for.

The strategy is front-loaded toward engineering credibility (Weeks 1–2) and back-loaded toward visibility (Weeks 3–4), because a polished repo with comprehensive tests and benchmarks converts interview attention into offers far more reliably than a viral but shallow project. Every week produces a shareable artifact: an installable package, a benchmark suite, an interactive demo, and a launch with social proof.

---

## What actually impresses hiring managers at AI startups

The 70% interview-credibility weighting demands understanding what technical evaluators genuinely scrutinize. Research across hiring manager perspectives, founding-engineer interview guides, and CTO blog posts reveals a consistent hierarchy of signals — and most candidates get it backwards.

**Documentation quality is the single strongest signal.** Well-documented projects are **65% more likely to receive interview callbacks**, and hiring managers treat README files as portfolio write-ups. But documentation alone isn't enough. For senior and founding engineer roles, evaluators run a mental checklist: Does this person understand trade-offs? Can they articulate *why*, not just *what*? Is there evidence of system design thinking? One founding-engineer hiring framework (HyperNest Labs) explicitly stages interviews around "tell me about a product you built from scratch" and "discuss the trade-offs you made." A GitHub project that preemptively answers these questions — through Architecture Decision Records, benchmark methodology documentation, and clear rationale in commit messages — converts a portfolio review into a passing interview stage.

The distinction between "impressive side project" and "another GitHub repo" comes down to **production thinking**: CI/CD with passing badges, semantic versioning with a CHANGELOG, custom exception classes instead of bare `Exception`, structured logging instead of `print()`, type hints throughout with a `py.typed` PEP 561 marker, and a published PyPI package with clean installation. These aren't technically difficult — they take perhaps 8 hours total — but they signal that the author operates at a professional level.

For legal tech roles specifically, the hybrid profile is the differentiator. Legal tech employers screen for "JD with Python proficiency" or "software engineer with legal domain expertise" — and finding both in one candidate is rare enough that the project itself becomes a conversation piece. **Quantified domain impact** seals it: "Improved retrieval precision on legal contracts by 23% over LangChain's default splitter" is the kind of claim that makes a CTO lean forward.

---

## The 160-hour execution plan, week by week

The time allocation across four weeks should roughly follow **55% core engineering (~88 hours), 15% documentation (~24 hours), 15% testing and benchmarking (~24 hours), 10% marketing and visibility (~16 hours), and 5% infrastructure (~8 hours)**. Each week has a clear theme and a demonstrable checkpoint artifact.

### Week 1: Foundation and core MVP (40+ hours)

The goal is a working `pip install lexchunk` with a core chunking engine that visibly outperforms naive splitting on a real contract. Every minute spent on infrastructure this week pays compound interest for the remaining three weeks.

**Days 1–2 (16 hours): Repository skeleton and CI/CD.** Set up the `src/lexchunk/` layout with `pyproject.toml` (using hatchling as build backend), MIT license, `.pre-commit-config.yaml` with ruff and mypy, and a GitHub Actions CI workflow that runs lint, type-check, and pytest across Python 3.10–3.13. Add issue templates, PR template, `.gitignore`, and a stub README. This infrastructure takes roughly 4–5 hours but immediately makes every subsequent commit look professional. Use `uv` for dependency management. Create the custom exception hierarchy (`LexChunkError`, `DocumentParseError`, `ChunkBoundaryError`) and the core data models with Pydantic.

**Days 3–4 (16 hours): Core chunking engine.** Build the legal-structure-aware parser for contract-style documents. The key insight to encode: legal documents have a hierarchical structure (Parts → Articles → Sections → Subsections → Clauses) with cross-references ("as defined in Section 3.2(a)") and definitions sections that create implicit dependencies. The chunker should preserve clause boundaries, keep definitions grouped, maintain section hierarchy metadata, and handle nested structures. Implement a `LegalChunker` class with a `TextSplitter`-compatible interface for drop-in LangChain replacement. Start with UK/US contract conventions — numbered sections, lettered subsections, and standard boilerplate patterns. Write initial unit tests for each structural element.

**Days 4–5 (8 hours): First release and README.** Publish v0.1.0 to TestPyPI then PyPI. Create a demo script comparing lexchunk output against `RecursiveCharacterTextSplitter` on a CUAD contract. Record a terminal GIF (using `terminalizer` or `asciinema`) showing the comparison. Write the README with: tagline, badges (CI, PyPI version, Python versions, license), the GIF, `pip install lexchunk`, a 5-line quickstart, feature list, and "Why lexchunk?" section explaining the problem.

**Week 1 checkpoint artifact:** An installable PyPI package that chunks a legal contract while preserving clause boundaries, with a passing CI pipeline and a README with a demo GIF.

### Week 2: Engineering depth and benchmarks (40+ hours)

This is the most important week for interview credibility. The goal is to make the codebase unmistakably senior-grade and produce benchmark numbers that prove the library works.

**Days 1–2 (16 hours): Expand document support and edge cases.** Add chunking strategies for statutes (UK Acts from legislation.gov.uk), Terms & Conditions (using UNFAIR-ToS patterns), and NDAs (using ContractNLI patterns). Handle edge cases: nested definitions, cross-references that span sections, amendment clauses, schedules and annexes, and boilerplate sections. Add metadata preservation — each chunk should carry its section path, clause number, document type, and any cross-reference targets. Implement a LlamaIndex `NodeParser`-compatible interface alongside the LangChain one.

**Days 3–4 (16 hours): Benchmark suite.** This is where the $0 benchmarking methodology pays off. Download **LegalBench-RAG-mini** (776 query-answer pairs with character-level ground truth) and **CUAD** (510 commercial contracts). Implement the benchmark pipeline:

1. Chunk the LegalBench-RAG corpus using four strategies: fixed-size (256, 512, 1024 tokens), `RecursiveCharacterTextSplitter`, sentence-based splitting, and lexchunk
2. Embed all chunks using three free models: `all-MiniLM-L6-v2` (fast baseline), `bge-base-en-v1.5` (strong mid-tier), and `nomic-embed-text-v1.5` (long context)
3. Index in FAISS (flat L2)
4. Retrieve top-k for each query, compute character-level Precision@k and Recall@k per the LegalBench-RAG methodology
5. Also compute Token-IoU using Chroma's chunking evaluation framework
6. Run paired t-tests for statistical significance

All of this costs **$0** — deterministic metrics, local embedding models, local vector store. Save the $20 budget for Week 3's LLM-judge evaluation. Write the benchmark as a reproducible script in `benchmarks/` with clear CLI arguments.

**Day 5 (8 hours): Architecture documentation and release.** Write Architecture Decision Records for the 3–4 most important design choices (e.g., "Why clause-boundary preservation over semantic similarity," "Why metadata-first chunking," "Why drop-in LangChain compatibility"). These ADRs are interview gold — they demonstrate the trade-off reasoning that founding-engineer loops explicitly test for. Add comprehensive type hints, raise test coverage to **80%+** (enforced in CI via pytest-cov), add badges for coverage (Codecov), and tag v0.2.0 with a proper CHANGELOG entry.

**Week 2 checkpoint artifact:** A benchmark suite showing lexchunk outperforming baselines on LegalBench-RAG, 80%+ test coverage, and architecture decision records explaining key design choices.

### Week 3: Demo, documentation site, and blog post (40+ hours)

The pivot from engineering to communication. The goal is to make lexchunk *discoverable* and *demonstrable* — anyone should be able to understand what it does in 30 seconds and try it in 60.

**Days 1–2 (16 hours): HuggingFace Space and notebooks.** Build a Gradio demo on HuggingFace Spaces: upload a legal document (text/PDF), visualize chunks with highlighted metadata, compare lexchunk output side-by-side against generic splitting, show token counts and boundary analysis. This serves as both a demo link for all social media posts and a discoverable artifact within HuggingFace's RAG/NLP ecosystem. Create two Jupyter notebooks in `examples/`: "Legal Document Chunking for RAG: Why Generic Splitters Fail" and "Using lexchunk with LangChain and ChromaDB."

**Days 2–3 (12 hours): Documentation site.** Set up MkDocs Material with mkdocstrings for auto-generated API reference. Sections: Getting Started, User Guide (with document-type-specific guides for contracts, statutes, and T&Cs), API Reference, Architecture, Benchmarks, and Contributing. Deploy to GitHub Pages. This hosted documentation site is what separates "production-grade" from "decent" in every evaluator's mental model.

**Days 3–4 (8 hours): LLM-judge evaluation ($10–15).** Now spend the budget. Sample 100 queries from LegalBench-RAG. For each chunking strategy, feed retrieved context + query to GPT-4o-mini via DeepEval or RAGAS. Evaluate faithfulness, answer relevancy, and contextual precision. This adds a qualitative dimension to the deterministic retrieval metrics and costs roughly **$10–15** at GPT-4o-mini's pricing ($0.15/1M input tokens). Keep $5–10 as buffer.

**Day 5 (4+ hours): Write the blog post.** Draft the technical blog post (detailed strategy below). Target **2,500–3,500 words**. This should be substantially complete by end of Week 3, with final polish in Week 4.

**Week 3 checkpoint artifact:** A live HuggingFace Space demo, hosted documentation site, and a drafted blog post with benchmark results and visualizations.

### Week 4: Launch, promote, and iterate (40+ hours)

**Day 1 — Launch day (Tuesday or Wednesday, 8 hours):**

- Publish the blog post on a personal blog (GitHub Pages or similar)
- Submit to Hacker News as: `Show HN: lexchunk – Legal-document-aware text chunking for RAG pipelines` (link to GitHub repo, not blog)
- Post the first-person comment with: who you are (lawyer + CS background), the problem, how it's different, and an invitation for feedback
- Post to r/LangChain with a code example showing drop-in replacement
- Launch Twitter/X thread summarizing key benchmark findings with the demo GIF
- **Respond to every comment within the first 4 hours** — this is non-negotiable for HN traction

**Days 2–3 (16 hours):** Post to r/LocalLLaMA (frame as "improved my local RAG accuracy on legal docs by X%"), r/Python (frame as library announcement with engineering quality emphasis), r/LegalTech (frame for lawyers building AI tools), and r/MachineLearning. Cross-post blog to HuggingFace blog and Dev.to with canonical URL. Post on LinkedIn targeting legal tech connections. Share in LangChain Discord, MLOps Community Slack. Incorporate quick feedback and bug fixes from early users.

**Days 4–5 (16 hours):** Tag **v1.0.0** with comprehensive CHANGELOG. Submit to awesome-rag, awesome-langchain, awesome-nlp awesome-lists. Pitch to legal tech newsletters (Artificial Lawyer, LawNext/Bob Ambrogi, The Docket). Create "good first issue" labels for future contributors. Address any filed issues. Write a follow-up Twitter thread addressing the most interesting questions received. If the benchmarks are rigorous enough, consider an arXiv preprint for additional academic credibility.

**Week 4 checkpoint artifact:** Public launch across 6+ platforms, v1.0.0 tagged, initial community feedback incorporated, newsletter pitches sent.

---

## The blog post that drives the entire visibility strategy

The blog post is the single highest-leverage marketing artifact. Research on viral technical posts from 2024–2025 reveals a clear pattern: the most-shared RAG/chunking posts combine **a surprising finding, real benchmark data, and immediately usable code**. The NVIDIA chunking benchmark post became the field's standard reference because it published reproducible numbers. The HuggingFace "Why Best Practices Failed Us" post went viral because its contrarian finding — naive chunking outperformed context-aware (70.5% vs 63.8%) — challenged assumptions.

**Recommended title:** "Why Your RAG Pipeline Fails on Legal Documents (and How to Fix It)" — this is pain-point-first, domain-specific, and implies a solution.

**Structure the post in 8 sections across 2,500–3,500 words:**

1. **Hook** (2–3 sentences): Lead with the most surprising benchmark finding. If lexchunk shows a dramatic improvement, lead with the number. If certain "best practices" underperform, lead with the contrarian insight.
2. **The problem** (300 words): Why legal documents break standard chunking — cross-references get orphaned, definitions get separated from their clauses, section hierarchies are destroyed. Use a visual showing a naive chunk that splits a clause mid-sentence.
3. **Why it matters** (200 words): Legal tech AI adoption jumped from 19% to 79% in 2024. RAG pipelines are the backbone, but chunking quality is the bottleneck.
4. **The approach** (500 words): How lexchunk works, with an architecture diagram (use Excalidraw). Include the 5-line quickstart code snippet.
5. **Benchmarks** (500 words): The benchmark comparison table showing lexchunk vs. baselines on LegalBench-RAG metrics across multiple embedding models. This table will be the most-shared element.
6. **Deep dive into legal document structure** (400 words): This is where the law degree pays off. Explain definitions sections, cross-reference patterns, and clause nesting from genuine expertise — not googled facts.
7. **What I learned** (300 words): Surprises, trade-offs, what didn't work. Honest "lessons learned" content consistently outperforms pure announcements.
8. **Try it** (100 words): `pip install lexchunk`, GitHub link, HuggingFace demo link.

**Publish on a personal blog first** (full SEO ownership), then cross-post to HuggingFace blog and Dev.to with canonical URLs. HN and developer communities demonstrably prefer personal blogs over platform posts. Include **at minimum**: one architecture diagram, one benchmark table, one before/after chunking comparison visual, and three code snippets.

---

## Benchmarking that costs almost nothing but looks rigorous

The benchmarking strategy is built on **LegalBench-RAG**, the first benchmark specifically designed for evaluating retrieval in legal RAG pipelines. It provides 6,858 query-answer pairs (776 in the mini version) with **character-level ground truth annotations** — meaning evaluation is completely deterministic with no LLM judge required and zero API cost.

**The free benchmarking stack:**

- **Datasets:** LegalBench-RAG-mini (776 queries, from CUAD + ContractNLI + MAUD + PrivacyQA), plus CUAD contracts directly (510 documents, CC BY 4.0) and UNFAIR-ToS (50 Terms of Service with sentence-level annotations)
- **Embedding models** (all free, local): `all-MiniLM-L6-v2` (22M params, fast baseline), `bge-base-en-v1.5` (110M, strong retrieval), `nomic-embed-text-v1.5` (137M, 8192-token context ideal for legal documents)
- **Vector store:** FAISS with flat L2 index — deterministic, fast, standard for academic benchmarks
- **Metrics:** Character-level Precision@k and Recall@k (per LegalBench-RAG), plus Token-IoU from Chroma's chunking evaluation framework, nDCG@k, and MRR
- **Statistical testing:** Paired t-tests across queries for significance

Using three embedding models is critical — it demonstrates results generalize rather than being model-specific. The combination of an established benchmark (LegalBench-RAG is published on arXiv), deterministic metrics, multiple embedding models, and statistical significance testing makes this publishable-quality evaluation.

**Spend the $20 on a qualitative layer.** Reserve $10–15 for GPT-4o-mini LLM-judge evaluations on a 100-query subset via DeepEval, measuring faithfulness and answer relevancy. This adds a dimension beyond retrieval metrics and costs roughly $10–15 at current pricing. Keep $5 as buffer. Alternatively, run Llama 3.1 8B locally via Ollama as a free (but less reliable) judge.

Additionally, compute a **structural quality metric unique to lexchunk**: the percentage of chunks that break mid-clause, mid-sentence, or mid-section. This metric directly measures the library's core value proposition and is trivially free to compute.

---

## The seven datasets worth using and how to use them

Not all legal datasets serve the same purpose. For a contract chunking library, prioritize datasets with **clause-level or span-level annotations** that can serve as ground truth for boundary evaluation.

**Tier 1 — Essential (use in primary benchmarks):**

**CUAD** (Contract Understanding Atticus Dataset) provides 510 real commercial contracts from SEC EDGAR filings with **13,000+ expert annotations** across 41 clause categories. Available on HuggingFace (`theatticusproject/cuad`) under CC BY 4.0. The annotated clause spans are directly useful for testing whether lexchunk preserves clause boundaries — each annotation is effectively a "correct chunk boundary" marker.

**LegalBench-RAG** provides 6,858 query-answer pairs with character-level span annotations derived from CUAD, ContractNLI, MAUD, and PrivacyQA. The mini version (776 pairs) enables rapid iteration. This is the primary retrieval evaluation benchmark — free, deterministic, and published.

**Tier 2 — High value (use for domain coverage):**

**ContractNLI** contains 607 annotated NDAs with evidence span annotations marking which text supports each hypothesis. Directly useful for NDA-specific chunking evaluation. **UNFAIR-ToS** provides 50 Terms of Service documents with sentence-level annotations across 8 unfair clause categories — directly relevant since lexchunk targets T&Cs. **LEDGAR** offers ~100,000 contract provisions from 60,540 contracts, each labeled with its topic — effectively a dataset of "correctly chunked" provisions for boundary comparison.

**Tier 3 — Supplementary (use for UK coverage and stress testing):**

**legislation.gov.uk** provides all UK legislation from 1267 to present with a free API and bulk XML downloads — ideal for testing statute-aware chunking. **Pile of Law** (256GB) provides massive scale for stress testing. EDGAR filings provide unlimited additional raw contracts via the SEC's free API.

---

## What to build and what to skip

Given the 70% interview-credibility weighting, ruthless prioritization is essential. Build things that demonstrate senior engineering judgment; skip things that add scope without adding signal.

**Build (high credibility-per-hour):**
- Contract-aware, statute-aware, and T&C-aware chunking strategies with metadata preservation
- Drop-in LangChain `TextSplitter` and LlamaIndex `NodeParser` interfaces
- Cross-reference detection and linking (the killer feature no other chunker has)
- Comprehensive pytest suite at 80%+ coverage with property-based testing via Hypothesis
- Reproducible benchmark suite against LegalBench-RAG
- Architecture Decision Records for 3–4 key design choices
- Full CI/CD with matrix testing, type checking (mypy strict), and automated PyPI publishing
- MkDocs Material documentation site with auto-generated API reference
- HuggingFace Space demo

**Skip (low credibility-per-hour):**
- PDF parsing — recommend users use Docling, PyMuPDF, or Unstructured upstream; document parsing is a solved problem and building it adds scope without demonstrating chunking expertise
- OCR for scanned documents — out of scope, low signal
- Multi-language support — UK/US English is sufficient for the target market
- Custom web UI beyond the Gradio demo — the demo proves the concept; a full web app adds weeks of work for marginal credibility
- Fine-tuned embedding models — reference existing models, don't train new ones
- Streaming/async interfaces — nice-to-have for v2, not essential for launch
- Docker support — a `pip install` is sufficient for a library

---

## The production-grade checklist that separates senior from junior

Experienced Python developers and hiring managers evaluate libraries against an implicit checklist. Hit every item in the "must have" tier and most of the "should have" tier to signal unambiguously senior work.

**Must have** (non-negotiable for credibility): `src/` layout with `pyproject.toml`, comprehensive type hints with `py.typed` marker, ruff for linting/formatting, mypy in strict mode, pytest with 80%+ coverage enforced in CI, GitHub Actions CI running across Python 3.10–3.13, published on PyPI with semantic versioning, comprehensive README with badges and quickstart, CHANGELOG.md following Keep a Changelog format, custom exception classes, Pydantic models for configuration, structured logging, and pre-commit hooks.

**Should have** (strong professional signal): CONTRIBUTING.md with development setup, CODE_OF_CONDUCT.md, issue and PR templates, hosted MkDocs Material documentation, examples directory with runnable notebooks, integration tests, Dependabot for dependency updates, Architecture Decision Records, and a `Makefile` or `justfile` with common commands (`make test`, `make lint`, `make docs`, `make benchmark`).

**Nice to have** (elite tier, do if time permits): Property-based testing with Hypothesis, GitHub Releases with auto-generated notes, versioned documentation, and a SECURITY.md with vulnerability reporting instructions.

---

## Visibility without a budget: platform-by-platform tactics

The 10% GitHub-stars weighting and 20% adoption weighting mean visibility matters — but only after the engineering foundation is solid. The highest-ROI channels for a niche developer tool, in order:

**Hacker News Show HN is the single highest-impact channel.** One successful Show HN can drive 11,000+ unique visitors in 3 days. Title it exactly: `Show HN: lexchunk – Legal-document-aware text chunking for RAG pipelines`. Link to the GitHub repo, not the blog post. Post Tuesday or Wednesday at **9–11 AM Eastern**. Write a first comment explaining: your background (lawyer + CS — this is HN catnip), the problem, what's different, and an invitation for feedback. **Respond to every single comment for the entire day.** HN's algorithm rewards engagement.

**Reddit requires staggered, community-specific framing.** Post to r/LangChain first (frame as drop-in `TextSplitter` replacement with benchmark comparison), then r/LocalLLaMA the next day (frame as "improved my local RAG accuracy by X%"), then r/Python (library announcement emphasizing engineering quality), then r/LegalTech (frame for lawyers building AI). Always include a terminal GIF or screenshot — image posts get dramatically more engagement. Space posts 1–2 days apart to avoid appearing spammy.

**Twitter/X #buildinpublic from Week 1.** Start sharing progress during development: architecture decisions, surprising benchmark findings, and WIP screenshots. This creates a narrative arc so the launch post has context. Tag @LangChainAI and relevant legal tech accounts. A thread summarizing key findings with the demo GIF is the launch-day format.

**HuggingFace Spaces provides passive discoverability.** The Gradio demo lives within HuggingFace's ecosystem and appears in searches for RAG, chunking, and legal NLP tools. Tag the Space with relevant topics.

**Legal tech newsletters for niche reach.** Pitch to Artificial Lawyer, LawNext (Bob Ambrogi), and The Docket after launch, once you have social proof from HN/Reddit engagement. Frame it as: "Open-source tool from a lawyer-engineer for building AI-powered contract analysis."

## Conclusion

The lexchunk project succeeds or fails on sequencing. **Weeks 1–2 build the engineering foundation that survives technical scrutiny in interviews** — the CI pipeline, test coverage, type safety, architecture documentation, and benchmark methodology. Weeks 3–4 make that foundation visible and accessible through a demo, blog post, and coordinated multi-platform launch. The law degree is not a background detail; it is the core differentiator that makes every architectural decision, every edge case handled, and every benchmark result more credible than what any pure-software-engineer competitor could produce. Lead with it in the blog post, the HN comment, and every interview conversation.

The most important single insight from this research: **hiring managers at AI startups evaluate portfolio projects primarily on whether they demonstrate product thinking and trade-off reasoning, not just technical execution.** The Architecture Decision Records, the "Why lexchunk?" section in the README, and the "What I Learned" section in the blog post are not optional extras — they are the primary interview artifacts. Build lexchunk as if you're explaining every decision to a future co-founder, because that is exactly what the founding-engineer interview loop tests.