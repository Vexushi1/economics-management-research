# Engineering changelog

## 0.9.0 — Phase 9 candidate (PR #10)

- Adds Ed25519 human semantic-bridge approval verification and signed ledger with out-of-band checkpoint/sequence requirements.
- G6 rejects missing/forged semantic reviews and physically modified self-hashed JSON ledgers with `CRITICAL_LEDGER_CORRUPTION`.
- Adds a content-addressed dependency-aware in-memory cache with explicit `STALE` outcomes and no executable serialization.
- Adds offline security and replay tests, operations, security response instructions and alpha/beta/stable criteria.
- No automatically certified source-to-model equivalence, no automatic remote human-signing workflow, and no claim of resilience against an administrator who compromises both the application and trust root.
