# Engineering changelog

## 0.9.0 — Phase 9 candidate (PR #10)

- Adds Ed25519 human semantic-bridge approval verification and signed ledger with out-of-band checkpoint/sequence requirements.
- G6 rejects missing/forged semantic reviews and physically modified self-hashed JSON ledgers with `CRITICAL_LEDGER_CORRUPTION`.
- Adds a content-addressed dependency-aware in-memory cache with explicit `STALE` outcomes and no executable serialization.
- Adds offline security and replay tests, operations, security response instructions and alpha/beta/stable criteria.
- No automatically certified source-to-model equivalence, no automatic remote human-signing workflow, and no claim of resilience against an administrator who compromises both the application and trust root.

## RC1 candidate (PR #11, not merged)

- Added runtime Vault Transit signer/explicit operator rotation interface; no issuer private key on G6.
- Added signed root-pinned checkpoint client, read-only checkpoint HTTP service and fail-closed G6 trust adapter.
- Added Docker/Compose single-host network/capability isolation scaffolding, private-input ignore patterns and adversarial tests.
- Explicitly retained Alpha RC status and multi-host/production validation limitations.
