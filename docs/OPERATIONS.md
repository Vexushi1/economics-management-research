# Operations: reproducible offline research pipeline

Target CI: Ubuntu 24.04, CPython 3.12. Pin/verify install from `requirements/ci-py312-linux.lock` with `pip install --require-hashes --only-binary=:all:` then `pip install --no-deps --no-build-isolation -e .`. Run `python -m ruff check src tests` and `python -m pytest -q`. Offline tests are the default; online services and private documents are opt-in only.

## Approved publication flow

1. Load PDF under Phase 2 extraction constraints; store source anchors and SHA-256 outside shared repository.
2. Validate ModelSpec AST before any symbolic conversion; require legitimate Phase 4 checked equilibrium; handle mathematical non-supported states honestly.
3. Register proof obligations and obtain independent complete proof review; `SKETCH_ACCEPTED` never implies `PROVED`.
4. Obtain explicit signed PDF-to-ModelSpec semantic approval from an externally authorized scholarly reviewer. Keep the approval's review document and key under independently managed custody.
5. Deterministically assemble LaTeX from only permitted prose slots and immutable solver/proof macros.
6. Have external issuer sign the bounded evidence-ledger payload with Ed25519. Publish latest signed-envelope SHA-256 plus strictly increasing sequence in an external trusted checkpoint. Ledger writer and issuer should be separate principals.
7. For `audit_submission`, provide signed approval + ledger + `TrustPolicy` loaded from a protected source, **not** from the ledger directory. Release only after G6 returns `READY_FOR_SUBMISSION` with zero findings.

## Troubleshooting

- `SEMANTIC_BRIDGE_NOT_VERIFIED`: request independent paper-to-model review, do not auto-approve.
- `SEMANTIC_APPROVAL_INVALID`: signer, signature, UTC time, source/model scope or review evidence inconsistent; halt and seek fresh signed review.
- `TRUST_ANCHOR_MISSING`: no independent policy/checkpoint was supplied; fail closed.
- `CRITICAL_LEDGER_CORRUPTION`: signed ledger, pinned checkpoint or dependency digest disagrees. Quarantine and follow `docs/SECURITY.md` incident response.
- `UPSTREAM_STALE`: prior solver/proof snapshots no longer match; recompute affected downstream only, retaining original PDF source.

**Never** allow artifact writers to update both ledger and out-of-band trust checkpoint. A local folder containing both defeats insider detection. This first release has no automatic external signing, trusted timestamp server or hardware-backed key management. External operators must implement those policies.
