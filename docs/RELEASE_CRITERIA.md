# Phase 9 release gates

**Alpha** (current target): locked Python 3.12 installation, deterministic synthetic provenance-to-G6 scenario, proof and falsification tests, signed semantic review and independent ledger checkpoint, direct-I/O insider attack rejection, required offline CI and openly recorded limitations.

**Beta** (not yet certified): tested external signing-service integration, protected policy/checkpoint access control, real human-review SOP, key rotation/revocation, reliable audit export, cross-platform reproducibility, curated validation corpus, TeX compilation in CI.

**Stable** (not yet certified): independent security assessment, disaster recovery including rollback/replay drills, complete key-custody processes, publication-specific manual semantic and reference audits, licensed third-party notice audit, supply-chain vulnerability response.

A green pytest pipeline is not a mathematical proof, a full PDF semantic verification, a causal-identification certificate, or a production security audit.

## RC1 review (2026-10-13)

**Status: ALPHA RELEASE CANDIDATE / NOT PRODUCTION CERTIFIED.** See `docs/RC1_DEPLOYMENT.md`.

Implemented code paths: Vault Transit remote Ed25519 signing request + separately privileged rotation request; external signed/expiring checkpoint retrieval with pinned root and minimum sequence; containerized read-only checkpoint endpoint; G6 external trust preflight with fail-closed CRITICAL status; single-host Compose network/capability/filesystem hardening and private-input ignore patterns. Test hooks use synthetic keys only.

**Mandatory release blockers for production:** no deployed enterprise Vault/KMS tenant and reviewed RBAC; no managed multi-host isolation; no hardened identity attestation and controlled issuer/reviewer separation-of-duties; no independent security penetration test; no operational key rotation/revocation/restore drill; no automatic SOC routing for CRITICAL events; no evidence of production TeX build reproducibility; no proven semantic correctness for real uploaded articles; no general solution to arbitrary HJB/optimization or automatic full causal identification. A green CI or Compose lint is neither deployment nor certification.
