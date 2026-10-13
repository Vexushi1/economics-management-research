# RELEASE v0.1.0-alpha — Code Freeze Handoff

Release date: 2026-10-13  
Status: **Alpha source snapshot / NOT PRODUCTION CERTIFIED**  
Repository: `Vexushi1/economics-management-research`

## 1. Baseline snapshot and provenance

- **PR #11 squash-merge commit (reviewed implementation baseline):** `394465f9cdb0c120eac3b4807a64ac7e89feb96b`.
- **Release-document commit / tag target:** the commit that first adds this file to `main`; resolve its full SHA after this documentation-only change. Do **not** mistakenly tag the earlier merge SHA if the release artifact must contain these notes.
- **Requested tag:** `v0.1.0-alpha`. This Markdown file does **not** constitute creation of a Git tag, an annotated tag signature, or a GitHub Release.
- **Project metadata discrepancy:** `pyproject.toml` currently declares `version = "0.9.0"`; the release tag `v0.1.0-alpha` is a snapshot label, **not** a synchronized Python package version. Freeze prohibits silently changing code or package metadata to conceal this discrepancy.
- No new feature branches or business-logic PRs are authorized under this freeze. Changes require a separate, explicit release-management decision.

## 2. Locked dependency and toolchain scope

- Runtime target: **CPython 3.12.x** (`>=3.12,<3.13`), CI target Ubuntu 24.04 x86_64.
- Locked installation: `requirements/ci-py312-linux.lock` with exact versions and SHA-256 artifact hashes, installed using `pip install --require-hashes --only-binary=:all:`; local application installed `--no-deps --no-build-isolation`. This is a platform-scoped lock, not a universal reproducible image or supply-chain attestation.
- Core: `jsonschema==4.26.0`. Mathematics: `sympy==1.14.0`, `numpy==2.3.5`, `scipy==1.17.0`. PDF: `pypdf==6.20.0`, `pdfplumber==0.11.10`, `pdfminer.six==20260107`. Security: `cryptography==50.0.2`. Development: `pytest==9.0.2`, `ruff==0.13.2`.
- GitHub Actions is read-only with pinned checkout/setup-python action revisions, fixed-hash dependencies, lint, unit/integration tests, schema and wheel checks, and Compose **static** configuration validation. The PR #11 CI evidence is [run 38355730453](https://github.com/Vexushi1/economics-management-research/actions/runs/38355730453): **260 passed, 1 skipped**. The skip is TeX compilation on a runner without TeX. A green run does not certify a production deployment.
- Docker base image and final application image are required to be independently pinned by verified immutable digest at deployment time; no real image digest, image scan result, or reproducible container build attestation is supplied in this release.

## 3. Delivered assets by phase

| Phase | Implemented, bounded asset | Not established |
|---|---|---|
| 1 — Offline research foundation | Repository contract, state/registry/routing, reproducible offline CI | Autonomous science or validated findings |
| 2 — Paper provenance | Offline PDF extraction with source anchors, candidate records and literature matrix | OCR/semantic correctness; safe processing of every malicious PDF |
| 3 — Economic model design | Versioned ModelSpec JSON schema, inert whitelisted AST, game/information-sequence checks | Executable trust in extracted formula strings |
| 4 — Equilibrium engine | Checked bounded one-dimensional optimization, selected two-stage games, local numeric candidates, constrained contract guards | General nonlinear/multidimensional equilibrium, uniqueness or global proof in unsupported cases |
| 5 — Theorem verification | Proof obligations, explicit review states, counterexample re-evaluation, `\\unproven{}` protection | Fully automatic formal mathematical proofs or cryptographic reviewer identity |
| 6 — Stochastic/dynamic/replication | Exact finite-scenario information timing; deterministic linear-control necessary-condition preflight; fail-closed missing-input replication | Arbitrary HJB, SDE games, continuous stochastic optimization or reconstructed missing paper parameters |
| 7 — Cross-phase evidence/empirics | PDF→ModelSpec→solver→proof evidence fingerprints with `STALE`; DID/IV/panel identification preflight | Automatic causal identification or reliable semantic paper-to-model translation |
| 8 — Manuscripts & G6 | Deterministic LaTeX assembly; untrusted prose limited to three sections; macro/ledger/citation reconciliation; release blockers | Free-form mathematically safe LLM editing or automatic semantic claim support |
| 9 — Semantic trust/security | Explicit externally signed human approval, Ed25519 ledger/checkpoint checks, rollback and direct-file-tampering tests, content-addressed cache | Defense against compromise of signing keys, all trust roots, or execution host |
| RC1 deployment | Vault Transit signing/rotation request adapters, signed expiring checkpoint client, read-only service, G6 preflight, hardened single-host Compose reference | Real enterprise KMS tenant/RBAC, cross-host network isolation, mTLS and independent production security attestation |

All scientific statements must remain bounded to the stated capabilities. PDF/LLM-derived text is never implicitly executable mathematics; a located PDF quote does not by itself certify that the ModelSpec represents the paper.

## 4. Production warnings — mandatory handoff

1. **NOT PRODUCTION CERTIFIED.** The Compose reference isolates processes within one Docker host/kernel. It is **not physical isolation**. The checkpoint issuer/root must be provisioned in a separately controlled failure and security domain for production.
2. **No private keys on G6 is an architecture constraint, not a verified deployment fact.** Vault Transit adapters use external requests. Actual Vault tenant, token scopes, dual control, revocation, rotation and key custody have **not** been deployed or independently exercised; a privileged host attacker or compromised signing authority can defeat the proposed boundary.
3. **G6 defaults to BLOCKED.** A semantically verified paper→ModelSpec mapping requires real independent human review and a scoped signed approval. Synthetic signatures/test assertions are not real scholarly attestations.
4. **Trust checkpoint freshness and identity.** Deployment must independently pin the root public key, minimum sequence and trusted clock. Stale, missing, corrupted, unsigned or inaccessible checkpoints must block publishing; do not self-heal from the writable local ledger.
5. **No complete end-to-end production runtime test.** CI validates Compose syntax and offline Python behavior, not running multi-host hardened containers, mTLS, cloud identity, trusted persistent checkpoint store, monitoring, scaling, backup, or disaster recovery.
6. **No automated SOC paging.** `CRITICAL_LEDGER_CORRUPTION` is a structured local block; operators must integrate alert delivery and immutable incident retention.
7. **Third-party PDF and manuscript rights.** Do not commit or externally send private/copyrighted PDFs, unpublished drafts, human subject data or API keys. Avoid assuming license notices or the current dependency lock constitute an audited SBOM.
8. **Research capability is limited.** Unresolved equilibria, nonconvex globality, incomplete assumptions, unsupported HJB/causal identification, missing replication parameters, and unreviewed citations may remain blocked. No model result is made true by a green test suite.
9. **Build and version limitations.** TeX compilation was skipped in CI; Docker image digests are deployment placeholders; the Git tag requested here differs from `pyproject.toml` version `0.9.0`. These are release observations, not silently resolved defects.

## 5. Independent handoff / acceptance conditions

**Security auditors:** examine KMS issuer/reviewer separation, authorized human review artifacts, certificate/root provisioning, checkpoint replay defenses, data provenance, insider attack limitations, dependency advisories and source licenses; independently attempt tampering and rollback.

**Infrastructure operations:** deploy separate KMS/checkpoint trust domain and actual G6 host; configure least-privilege TLS/mTLS/RBAC, immutable image digests, trusted time, monotonic checkpoint storage, logs/alerts, key rotation and restore drills; record immutable deployment evidence.

**Release manager:** verify this exact frozen commit and hash-locked CI, create and inspect the release tag externally, archive checksums and notes, then transfer operational ownership. No claim of security certification follows solely from issuing a tag.

## 6. Freeze rule

Effective at the release handoff, the repository enters **Alpha Code Freeze**: no new feature branches, no new business-logic changes, no unreviewed generated scientific claims. Security emergency changes, if ever authorized, require a documented exception and a new reviewable release process. Tagging and this documentation-only note must not be represented as runtime code modifications.
