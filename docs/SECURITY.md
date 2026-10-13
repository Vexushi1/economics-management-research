# Security model and incident response

## G6 release boundary

All draft content is untrusted, including the `.tex` file, accompanying JSON ledger, self-hashes and suggested `PROVED` status. G6 independently rebuilds its manuscript against source PDF, ModelSpec, solver and proof ledger, then validates detached human semantic approval and signed evidence ledger. Missing authentic inputs fail closed.

The **protected trust policy must reside outside the attacker-writable artifact tree**: Ed25519 reviewer public keys, ledger issuer public key, latest approved ledger sequence and signed-envelope SHA-256 checkpoint. Issuer/reviewer private keys must **never** be installed in CI, included in a Git commit, loaded by G6 or stored alongside the ledger. The publisher signs after independent external review; G6 only verifies. A release-ready status is conditional on these explicit organizational trust assumptions.

An adversary who can rewrite a JSON ledger and update its internal hash **cannot** forge the detached Ed25519 signatures or change the independently pinned checkpoint. Direct filesystem writes trigger `CRITICAL_LEDGER_CORRUPTION` and block G6. A replay of an old authentically signed ledger is detected by the independently pinned sequence/hash. Simply chaining or rehashing local records gives **no** protection against full write access.

### Limits

- Signatures establish attribution to a key and immutable payload, **not** that a person fully understood the paper. Human identities and signing approvals must be established by organizational key issuance and independent records.
- This does not survive a compromised signing private key, corrupt protected checkpoint, malicious modified code/runtime or attacker with full machine administrator and signing-service privileges. There is no general self-defending file when the attacker controls both file and all roots of trust.
- Signed reviewer approvals bind exactly one source-anchor, PDF fingerprint and ModelSpec version; changing source, parameters, proof status, citations or draft requires a new ledger and published external checkpoint.
- The G6 trust interface accepts injected `TrustPolicy`. Callers MUST retrieve it through a trusted deployment channel, never JSON on an untrusted working directory.
- Semantic review evidence must be independently retained. The included keys and synthetic signatures in tests are **not** production credentials.
- CRITICAL findings are local structured reports; there is no automatic remote SOC paging in this release. Operations teams must route the error code to alert infrastructure.

### Response to CRITICAL_LEDGER_CORRUPTION

1. Stop submission and freeze outputs; do not regenerate a trusted hash from the compromised source.
2. Archive the poisoned ledger and original file bytes in a forensics store with read-only access.
3. Fetch the checkpoint and keys over their protected channel, verify signatures and sequence.
4. Quarantine potentially compromised reviewer/issuer credentials, rotate as appropriate.
5. Restart from independently reverified source documents; issue a *new* review and ledger checkpoint.

No PDF, unpublished manuscript, personal data or authentication token should be copied into the public repository, issue discussions or logs.
