---
name: semantic-review
summary: Independent human attestation of paper-to-ModelSpec interpretation and signed evidence-ledger checkpoints.
---

# Semantic bridge human audit (Phase 9)

1. Open the legally accessible original PDF outside the model code. Verify the **exact** SHA-256, page, block, text span, not only the DOI. Manually check players, timing, objective functions, domains and material caveats against the mapped ModelSpec.
2. Preserve an independently retrievable review document; calculate its SHA-256. Record reviewer identifier, UTC timestamp, explicit `APPROVE` action, source anchor and ModelSpec fingerprint. Do **not** preapprove based on LLM confidence or PDF extraction success.
3. Obtain Ed25519 signature in a **separate authorized human-signing environment** over `EMR:SEMANTIC:V1\0` + canonical UTF-8 JSON payload. The application is only a verifier; it does not hold private keys.
4. Have an independent ledger issuer validate current evidence (including proof status and citations), sign `EMR:LEDGER:V1\0` + canonical ledger payload, and publish the approved signed-envelope digest and monotonic sequence to a checkpoint **outside the ledger-writable directory**.
5. Configure G6 using the protected reviewer public-key allowlist, protected ledger public key and latest checkpoint; supply the original signed approval and ledger. Never use a trust policy loaded from the same writable ledger folder.
6. If G6 emits `CRITICAL_LEDGER_CORRUPTION`, quarantine the manuscript and ledger, preserve security logs, verify trusted checkpoint/key integrity out of band, and require an explicit new issuance. Do not automatically repair by rehashing the poisoned file.

**Threat boundaries:** An attacker who controls the signing private key, trusted application code, protected public-key policy or out-of-band checkpoint can defeat this model. For adversarial administrators or machine compromise, use separate hardware/remote signing and audit services, immutable external storage, access separation and independent incident response. A signature authenticates an approved *review declaration*, not the mathematical or semantic truth of its claims.
