# Economics & Management Research

Research-first, offline-capable Python scaffolding for economics and management research.

**Phase 2: offline PDF candidate extraction and provenance.** This release does **not** solve game-theoretic equilibria, verify theorems, parse untrusted formulas into executable expressions, infer economic findings automatically or invoke an LLM service. PDF metadata and mathematical expressions are unverified candidates.

## Research scope

Analytical games (Stackelberg/Nash/contract design), stochastic operations, empirical econometrics, theoretical/empirical hybrids and paper replication. These are planned research tracks, **not** implemented solvers.

## Setup

The targeted interpreter is **Python 3.12.x** (3.13 is excluded until tested). For a reproducible setup on Ubuntu 24.04 x86_64 / Python 3.12:

```bash
python -m pip install --require-hashes --only-binary=:all: -r requirements/ci-py312-linux.lock
python -m pip install --no-deps --no-build-isolation -e .
python -m ruff check src tests
python -m pytest -q
emr inspect
emr validate
emr plan --type analytical_game --description 'Compare two contracts'
```

`core-offline` depends only on `jsonschema` for offline state validation. The optional `math` extra pins SymPy and NumPy. The `dev` extra pins pytest and Ruff. Installing packages requires a package source (e.g. PyPI or a prepared wheelhouse); **runtime** research commands make no network calls. Exact application dependencies are pinned in `pyproject.toml`; production/research and CI installations use a separately maintained, hashed Python 3.12 CI dependency lock. Review `requirements/` for platform scope and exact hash constraints.

GitHub Actions validates the source on Python 3.12 for pull requests and pushes to `main` using a read-only token. GitHub Actions are not a substitute for independently verifying analytic proofs.

## Architecture

- `src/emr/core`: immutable request/plan contracts, registry, static routing and small local artifact store.
- `src/emr/solver`: **abstract-only** equilibrium solver with no formula parsing or dynamic execution.
- `skills/research-orchestrator/SKILL.md`: routing instructions, not executable code.
- `schemas/research-state.schema.json`: a provisional JSON Schema for state metadata.

All papers, PDFs and model equations are treated as untrusted data; do not feed equation text to Python `eval`, `exec`, unguarded SymPy parsers or shell commands.

## License and upstream material

Project-wide license for **new original code**: **MIT**, see [`LICENSE`](LICENSE). This repo currently contains no copied third-party Skill implementation. The existing audit documents record upstream licenses and the clean-room decision for `solving-model`. Do not assume repository visibility grants redistribution permission.

## Research integrity

Numerical consistency is not mathematical proof. Unsupported statements must be marked as such, and external references require source-level verification. See [`MODIFICATION_PLAN.md`](MODIFICATION_PLAN.md) and the audit documents in `docs/` and `third_party/`.

## Research-state snapshots

Use `emr.core.state.ResearchStateStore` for validated, immutable JSON snapshots. Each revision requires a new filename. `emr validate --state path/to/state.json` checks a snapshot. The `schemas/research-state.schema.json` file is mirrored as an installed package resource. In addition to schema checks, the implementation rejects duplicate artifact and workflow node identities, unknown artifact dependency endpoints, duplicate edges, self-dependencies and cyclic artifact dependency graphs. This is **metadata validation**, not a proof of economic propositions.

## Optional Phase 2 PDF and literature modules

The `pdf` extra (pypdf, pdfplumber, pdfminer.six) is opt-in. `emr paper scan /path/to/paper.pdf` emits a JSON **candidate** record with exact SHA-256, one-based pages, block-relative quote spans, sections/propositions/formula-like text and uncertain reading order. `emr paper matrix record1.json record2.json` combines offline records without inventing methods or findings. No PDF is uploaded and no network/API access occurs at runtime. Use an OS-level sandbox for adversarial PDFs: in-process page/byte limits are not a hard CPU/RAM bound.

The PDF dependency closure is resolved on a trusted Python 3.12 CI runner for review and must be committed with SHA-256 hashes before merge; final CI must consume the committed lock without regenerating it. This build profile is specific to Ubuntu 24.04 x86_64.

The three Skills `paper-reading`, `literature-review` and `research-novelty` are **instructions**, not a claim of automated semantic article understanding. OCR, semantic claim verification and mathematical formula execution are intentionally excluded from this stage.
