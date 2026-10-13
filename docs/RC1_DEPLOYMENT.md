# RC1 deployment contract (not production certification)

## Non-negotiable boundaries

- This repository implements a **real Vault Transit Ed25519 adapter** (`emr.adapters.kms.VaultTransitSigner`) that POSTs raw, domain-separated bytes to `/v1/transit/sign/<key>` over TLS. The Vault token is passed by an injected operator credential provider and MUST run **only in the independent issuance context**. The G6 image / Compose services must receive **no signing token or private key**. The operator-only `rotate_vault_transit_key` performs the real rotation request using a separate privileged token. Rotation does not automatically change allowed issuer key or checkpoint root.
- The **independent** checkpoint issuer signs a small `policy` JSON with `EMR:CHECKPOINT:V1\0 + canonical_json(policy)` using a root key never stored on G6 or checkpoint service. The signed policy contains public keys, `sequence`, expiration, latest signed-ledger digest. The checkpoint HTTP service returns that signed envelope read-only. G6 pins the root **public** key via externally provisioned read-only file and independently requires a minimum sequence; TLS should be used across hosts. Expiry requires a trusted clock.
- `emr.services.g6_application.audit_with_protected_checkpoint` fetches and verifies the external policy before calling the existing full Phase 8 `audit_submission`; on error it returns `BLOCKED` with `CRITICAL_LEDGER_CORRUPTION`. The HTTP process `emr.services.g6_service` exposes a read-only **trust health** endpoint only, not a public manuscript submission or signing endpoint. Publication still requires the full library G6 audit and authenticated job orchestration.
- `.dockerignore` excludes user PDFs and private key formats. Independently scan the build context and result; ignore patterns alone are not an exfiltration control.

## Single-host test topology

`docker-compose.yml` intentionally has two containers and an `internal: true` checkpoint link. Only G6 exposes `127.0.0.1:8081`; checkpoint has no published ports, runs read-only, drops capabilities, uses no-new-privileges and mounts only a signed *public* JSON snapshot. Both run as UID 65532 and use separately bounded resources. It is a **single-kernel logical separation test**, not physical isolation. A compromised Docker host can break both containers.

Image building requires a **reviewed base image pinned by digest**; the Dockerfile deliberately has no default `PYTHON_BASE_IMAGE`:

```shell
docker build --build-arg PYTHON_BASE_IMAGE='python:3.12-slim@sha256:<verified-real-digest>' -t 'registry.example/emr:rc1' .
```

Scan and push the image, then use the registry's **immutable digest** in `EMR_RC1_IMAGE`. Do not paste a placeholder digest literally. Independently provision, through separate operator access: `EMR_TRUST_ROOT_FILE` (base64 raw 32-byte Ed25519 *public* key), `EMR_SIGNED_POLICY_FILE` (signed policy envelope), `EMR_MIN_SEQUENCE` (minimum committed sequence), `EMR_RC1_IMAGE` (immutable reviewed image digest). These are all public trust artifacts except the integrity-critical file permissions. No signer credentials are needed in Docker Compose.

```
docker compose config -q
docker compose up -d
docker compose exec g6 python -c 'from emr.services.g6_service import load_protected_policy; print(load_protected_policy().expected_sequence)'
```

**Production separation:** deploy the checkpoint issuer/trust service to a *different machine/account/network/security domain* managed by a different team; configure G6 with `https://trust.example/v1/trust-policy` and a pinned public root key; set `EMR_INTERNAL_HTTP_FOR_DEV=0`. Restrict access with firewall/mTLS, authenticated issuer operations and append-only checkpoint storage. Neither Docker `internal` nor Compose itself guarantees that. This release is an **Alpha RC reference scaffold**, not proof that any external KMS deployment, multi-host segmentation, disaster recovery, or network access policy has been tested.

## Key operations and incident handling

1. A trusted reviewer independently checks the original PDF/ModelSpec mapping and signs the semantic approval with an **issued** key outside G6. A separate ledger issuer signs the ledger payload; a separate checkpoint authority signs policy with latest digest and sequence.
2. Rotation is **two-phase**: sign/rotate through separately privileged Vault operator role; install new reviewer/issuer public key(s) by independently signing a new checkpoint at a higher sequence; distribute new protected minimum sequence to G6; restart checkpoint snapshot server. Never accept an old sequence to recover availability.
3. If Vault is down, the signed policy expired, a signature fails, or the current digest differs, G6 is `BLOCKED`, emits `CRITICAL_LEDGER_CORRUPTION` and must not publish. Archive forensic artifacts; do not self-heal from the untrusted ledger.
4. RBAC, actual Vault permissions and sign-only credentials, organization identity assurance, external key lifecycle, independent attestation, cross-host end-to-end networking, and operational disaster-recovery exercises require real infrastructure and **remain unverified**.
