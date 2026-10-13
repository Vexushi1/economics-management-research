"""Independent signed trust-policy retrieval with pinned Ed25519 root key.

A malicious HTTP endpoint or tampered checkpoint file cannot forge a policy.
Freshness depends on the independently provisioned minimum sequence and expiry.
The G6 process receives public keys only and never a KMS signing token.
"""
from __future__ import annotations

import base64
import json
import re
import ssl
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from emr.core.security import SecurityBoundaryError, TrustPolicy, canonical_json, parse_json_record

_ID = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}\Z")


@dataclass(frozen=True, slots=True)
class ProtectedCheckpointClient:
    url: str
    root_public_key: bytes
    minimum_sequence: int
    timeout_seconds: float = 5.0
    # Permitted only for a private single-host Compose integration test.
    allow_insecure_internal_http: bool = False
    transport: Callable[..., object] = urlopen

    def __post_init__(self) -> None:
        parts = urlsplit(self.url)
        is_https = parts.scheme == "https"
        private_dev = (parts.scheme == "http" and self.allow_insecure_internal_http
                       and parts.hostname == "checkpoint" and parts.port == 8080)
        if (not (is_https or private_dev) or not parts.hostname or
            parts.username or parts.password or parts.query or parts.fragment or
            parts.path != "/v1/trust-policy" or
            not isinstance(self.root_public_key, bytes) or len(self.root_public_key) != 32 or
            type(self.minimum_sequence) is not int or self.minimum_sequence < 1 or
            not 0 < self.timeout_seconds <= 30):
            raise SecurityBoundaryError("untrusted checkpoint endpoint or root key")

    def fetch(self, *, now: datetime | None = None) -> TrustPolicy:
        request = Request(self.url, headers={"Accept": "application/json"}, method="GET")
        try:
            if self.url.startswith("https://"):
                response = self.transport(request, timeout=self.timeout_seconds,
                                          context=ssl.create_default_context())
            else:
                response = self.transport(request, timeout=self.timeout_seconds)
            with response:
                body = response.read(65537)
            if len(body) > 65536:
                raise SecurityBoundaryError("checkpoint response exceeds budget")
            envelope = parse_json_record(body)
        except (HTTPError, URLError, OSError, ValueError) as exc:
            raise SecurityBoundaryError("protected checkpoint unavailable") from exc
        return verify_checkpoint_envelope(envelope, self.root_public_key,
                                          minimum_sequence=self.minimum_sequence, now=now)


def verify_checkpoint_envelope(envelope: dict, root_public_key: bytes, *,
                               minimum_sequence: int, now: datetime | None = None) -> TrustPolicy:
    """External policy root authenticates issuer, reviewer allowlist and head digest."""
    if not isinstance(envelope, dict) or set(envelope) != {"policy", "signature"}:
        raise SecurityBoundaryError("malformed checkpoint envelope")
    policy = envelope["policy"]
    fields = {"version", "sequence", "expires_at", "ledger_key_id",
              "ledger_public_key", "reviewers", "expected_envelope_digest"}
    if (not isinstance(policy, dict) or set(policy) != fields or policy["version"] != "1"
        or type(policy["sequence"]) is not int or policy["sequence"] < minimum_sequence
        or not isinstance(policy["reviewers"], dict) or not policy["reviewers"]
        or not isinstance(root_public_key, bytes) or len(root_public_key) != 32):
        raise SecurityBoundaryError("malformed or rolled back checkpoint policy")
    try:
        signature = bytes.fromhex(envelope["signature"])
        if len(signature) != 64:
            raise ValueError("invalid signature length")
        Ed25519PublicKey.from_public_bytes(root_public_key).verify(
            signature, b"EMR:CHECKPOINT:V1\0" + canonical_json(policy))
        expiry = datetime.fromisoformat(policy["expires_at"].replace("Z", "+00:00"))
        current = now or datetime.now(UTC)
        if expiry.tzinfo is None or current.tzinfo is None or expiry.astimezone(UTC) <= current.astimezone(UTC):
            raise SecurityBoundaryError("checkpoint expired")
        ledger_pub = base64.b64decode(policy["ledger_public_key"], validate=True)
        reviewers = {k: base64.b64decode(v, validate=True) for k, v in policy["reviewers"].items()}
        if any(not _ID.fullmatch(k) for k in reviewers):
            raise SecurityBoundaryError("invalid reviewer key")
    except (InvalidSignature, ValueError, TypeError, KeyError, OverflowError) as exc:
        raise SecurityBoundaryError("checkpoint signature or contents invalid") from exc
    return TrustPolicy(reviewers, policy["ledger_key_id"], ledger_pub,
                       policy["sequence"], policy["expected_envelope_digest"])
