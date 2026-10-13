"""Out-of-band Ed25519 trust anchors for semantic approvals and evidence ledgers.

Threat model: an attacker may freely rewrite artifact JSON, hashes and local
ledger files but MUST NOT control the signing keys or the protected trust policy.
Hashes, circular hashes and local file permissions alone cannot defeat an
attacker who can rewrite every file; a remotely pinned checkpoint is required.

No private keys are loaded, retained, generated or stored by this verifier.
Signatures are produced by a separately authorized human/issuer process.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from types import MappingProxyType
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

_MAX_BYTES = 65536
_HASH = re.compile(r"[a-f0-9]{64}\Z")
_KEY = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}\Z")
_ALLOWED_LEDGER = frozenset({
    "sequence", "previous_digest", "pdf_sha256", "model_sha256",
    "parameter_sha256", "result_sha256", "proof_sha256", "approval_digest",
    "draft_sha256", "core_sha256", "citations_sha256", "proposition_id",
    "proof_version", "schema_version",
})
_APPROVAL = frozenset({
    "version", "action", "reviewer_id", "signer_key_id", "approved_at",
    "pdf_sha256", "source_anchor", "model_sha256", "review_refs",
    "review_digest", "semantic_scope",
})


class SecurityBoundaryError(ValueError):
    """An untrusted record crossed a signature, scope or freshness boundary."""


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            raise SecurityBoundaryError("duplicate JSON object key")
        output[key] = value
    return output


def canonical_json(value: Mapping[str, Any]) -> bytes:
    """Canonical UTF-8 without implicit NaN or coercion of arbitrary objects."""
    if not isinstance(value, Mapping):
        raise SecurityBoundaryError("expected a mapping")
    try:
        result = json.dumps(value, sort_keys=True, ensure_ascii=False,
                            separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, RecursionError, OverflowError) as exc:
        raise SecurityBoundaryError("invalid canonical record") from exc
    if len(result) > _MAX_BYTES:
        raise SecurityBoundaryError("security record exceeds size limit")
    return result


def digest(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def parse_json_record(raw: bytes) -> dict[str, Any]:
    """Reject duplicate fields, NaN, non-UTF8, oversized and non-object JSON."""
    if not isinstance(raw, bytes) or len(raw) > _MAX_BYTES:
        raise SecurityBoundaryError("invalid ledger file size/type")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_no_duplicate_keys,
                           parse_constant=lambda _: (_ for _ in ()).throw(
                               SecurityBoundaryError("nonfinite JSON number")))
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise SecurityBoundaryError("invalid ledger JSON") from exc
    if not isinstance(value, dict):
        raise SecurityBoundaryError("ledger must be a JSON object")
    return value


def _hash(value: Any, name: str) -> None:
    if not isinstance(value, str) or not _HASH.fullmatch(value):
        raise SecurityBoundaryError(f"invalid {name} SHA256")


def _id(value: Any, name: str) -> None:
    if not isinstance(value, str) or not _KEY.fullmatch(value):
        raise SecurityBoundaryError(f"invalid {name}")


def _signature(signature: Any) -> bytes:
    if not isinstance(signature, str) or not re.fullmatch(r"[a-f0-9]{128}", signature):
        raise SecurityBoundaryError("malformed Ed25519 signature")
    return bytes.fromhex(signature)


def _timestamp(value: Any) -> None:
    if not isinstance(value, str) or len(value) > 40:
        raise SecurityBoundaryError("invalid approval timestamp")
    try:
        date = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SecurityBoundaryError("invalid approval timestamp") from exc
    if date.tzinfo is None or date.utcoffset() != UTC.utcoffset(date):
        raise SecurityBoundaryError("approval must use UTC time")


@dataclass(frozen=True, slots=True)
class TrustPolicy:
    """External trust config, NEVER loaded from the attacker-writable ledger path.

    In real deployment pin this policy in protected remote configuration or a
    separate trusted signing service, and bind to trusted code/environment.
    """

    reviewers: Mapping[str, bytes]
    ledger_key_id: str
    ledger_public_key: bytes
    expected_sequence: int
    expected_envelope_digest: str

    def __post_init__(self) -> None:
        if not isinstance(self.reviewers, Mapping) or not self.reviewers:
            raise SecurityBoundaryError("explicit reviewer allowlist required")
        refs = dict(self.reviewers)
        for key, pub in refs.items():
            _id(key, "reviewer key id")
            if not isinstance(pub, bytes) or len(pub) != 32:
                raise SecurityBoundaryError("invalid reviewer public key")
        _id(self.ledger_key_id, "ledger key id")
        if not isinstance(self.ledger_public_key, bytes) or len(self.ledger_public_key) != 32:
            raise SecurityBoundaryError("invalid issuer public key")
        if type(self.expected_sequence) is not int or self.expected_sequence < 1:
            raise SecurityBoundaryError("missing protected checkpoint sequence")
        _hash(self.expected_envelope_digest, "protected checkpoint")
        object.__setattr__(self, "reviewers", MappingProxyType(refs))


def _verify(public_key: bytes, record: Mapping[str, Any], signature: Any, *, domain: bytes) -> None:
    try:
        Ed25519PublicKey.from_public_bytes(public_key).verify(
            _signature(signature), domain + canonical_json(record))
    except (InvalidSignature, ValueError) as exc:
        raise SecurityBoundaryError("signature does not match protected trust root") from exc


def verify_semantic_approval(approval: Mapping[str, Any], policy: TrustPolicy, *,
                             pdf_sha256: str, source_anchor: str,
                             model_sha256: str) -> str:
    """Only a signed human approval may elevate the PDF-to-ModelSpec bridge."""
    if not isinstance(policy, TrustPolicy) or not isinstance(approval, Mapping):
        raise SecurityBoundaryError("signed human approval and protected policy required")
    if set(approval) != {"payload", "signature"}:
        raise SecurityBoundaryError("unexpected approval envelope")
    payload = approval["payload"]
    if not isinstance(payload, Mapping) or set(payload) != _APPROVAL:
        raise SecurityBoundaryError("unexpected semantic approval fields")
    if payload["version"] != "1" or payload["action"] != "APPROVE":
        raise SecurityBoundaryError("semantic approval must be affirmative and versioned")
    if (payload["pdf_sha256"] != pdf_sha256 or
        payload["source_anchor"] != source_anchor or
        payload["model_sha256"] != model_sha256):
        raise SecurityBoundaryError("semantic approval scope does not match source/model")
    _id(payload["reviewer_id"], "human reviewer")
    _id(payload["signer_key_id"], "signer key")
    _timestamp(payload["approved_at"])
    _hash(payload["review_digest"], "review artifact")
    if payload["semantic_scope"] != "PDF_TO_MODELSPEC_MAPPING":
        raise SecurityBoundaryError("wrong approval scope")
    refs = payload["review_refs"]
    if (not isinstance(refs, list) or not 1 <= len(refs) <= 20 or
        any(not isinstance(r, str) or not 1 <= len(r) <= 256 for r in refs)):
        raise SecurityBoundaryError("human reviewer evidence references required")
    key = policy.reviewers.get(payload["signer_key_id"])
    if key is None:
        raise SecurityBoundaryError("signer not on protected allowlist")
    _verify(key, payload, approval["signature"], domain=b"EMR:SEMANTIC:V1\0")
    return "SEMANTIC_BRIDGE_VERIFIED"


def verify_signed_ledger(envelope: Mapping[str, Any], policy: TrustPolicy,
                         expected: Mapping[str, Any]) -> None:
    """Check signature, freshness checkpoint and CURRENT canonical data bindings.

    A SHA field recalculated by an intruder is useless without the protected
    Ed25519 issuer key and an independently protected expected head digest.
    """
    if not isinstance(policy, TrustPolicy) or not isinstance(envelope, Mapping):
        raise SecurityBoundaryError("ledger envelope and protected policy required")
    if set(envelope) != {"payload", "signature", "key_id", "self_sha256"}:
        raise SecurityBoundaryError("invalid signed ledger envelope")
    payload = envelope["payload"]
    if not isinstance(payload, Mapping) or set(payload) != _ALLOWED_LEDGER:
        raise SecurityBoundaryError("invalid signed ledger payload")
    for key in ("pdf_sha256", "model_sha256", "parameter_sha256", "result_sha256",
                "proof_sha256", "approval_digest", "draft_sha256", "core_sha256",
                "citations_sha256", "previous_digest"):
        _hash(payload[key], key)
    _id(payload["proposition_id"], "proposition identifier")
    if payload["schema_version"] != "1" or type(payload["proof_version"]) is not int or payload["proof_version"] < 1:
        raise SecurityBoundaryError("invalid ledger schema/proof version")
    if type(payload["sequence"]) is not int or payload["sequence"] != policy.expected_sequence:
        raise SecurityBoundaryError("ledger sequence rollback/fork detected")
    if envelope["key_id"] != policy.ledger_key_id:
        raise SecurityBoundaryError("ledger signing authority changed")
    if digest(payload) != envelope["self_sha256"]:
        raise SecurityBoundaryError("ledger self-digest mismatch")
    if digest(envelope) != policy.expected_envelope_digest:
        raise SecurityBoundaryError("signed ledger differs from out-of-band checkpoint")
    _verify(policy.ledger_public_key, payload, envelope["signature"], domain=b"EMR:LEDGER:V1\0")
    if dict(payload) != dict(expected):
        raise SecurityBoundaryError("ledger dependencies no longer match CURRENT source")


def prepare_ledger_payload(*, seal: Any, draft_sha256: str, core_sha256: str,
                           citations_sha256: str, approval_digest: str,
                           sequence: int, previous_digest: str) -> dict[str, Any]:
    """Derived only from independently recalculated source/model/proof results."""
    return {
        "schema_version": "1", "sequence": sequence, "previous_digest": previous_digest,
        "pdf_sha256": seal.pdf_sha256, "model_sha256": seal.model_sha256,
        "parameter_sha256": seal.parameter_sha256, "result_sha256": seal.result_sha256,
        "proof_sha256": seal.proof_sha256, "approval_digest": approval_digest,
        "draft_sha256": draft_sha256, "core_sha256": core_sha256,
        "citations_sha256": citations_sha256,
        "proposition_id": seal.proposition_id, "proof_version": seal.proof_version,
    }
