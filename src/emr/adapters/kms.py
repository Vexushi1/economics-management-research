"""Actual remote Vault Transit Ed25519 signing adapter; never loads a private key.

This module runs ONLY in an authorized issuance process, not the G6 workload.
The token supplier must come from an external identity/secret-delivery system.
No signer credentials are stored in config, git, command lines or emitted logs.
"""
from __future__ import annotations

import base64
import json
import re
import ssl
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

from emr.core.security import canonical_json

_KEY_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,62}\Z")


class KmsError(ValueError):
    """No signature may be substituted on remote KMS or protocol failure."""


class ExternalSigner(Protocol):
    """Sign raw domain-separated bytes in external hardware/service custody."""

    def sign(self, message: bytes) -> bytes: ...


@dataclass(frozen=True, slots=True)
class VaultTransitSigner:
    """Vault Transit Ed25519 /v1/transit/sign API. Optional transport for tests.

    Uses the `input` base64 field as raw Ed25519 message bytes; Vault key type
    MUST be `ed25519`. The response contains vault:vN:base64_signature.
    Vault role/policy permits ONLY sign on the named key, never key export.
    """

    base_url: str
    key_name: str
    token_provider: Callable[[], str]
    timeout_seconds: float = 5.0
    namespace: str | None = None
    transport: Callable[..., object] = urlopen

    def __post_init__(self) -> None:
        url = urlsplit(self.base_url)
        if (url.scheme != "https" or not url.hostname or url.username or url.password
            or url.query or url.fragment or url.path not in ("", "/")
            or not _KEY_ID.fullmatch(self.key_name) or
            not 0 < self.timeout_seconds <= 30 or not callable(self.token_provider)):
            raise KmsError("Vault signer requires bounded HTTPS endpoint and safe key name")
        if self.namespace is not None and (not self.namespace or len(self.namespace) > 128
                                           or any(x in self.namespace for x in "\r\n")):
            raise KmsError("invalid Vault namespace")

    def sign(self, message: bytes) -> bytes:
        if not isinstance(message, bytes) or not 1 <= len(message) <= 65536:
            raise KmsError("signing message must be bounded raw bytes")
        token = self.token_provider()
        if not isinstance(token, str) or not token or "\n" in token or "\r" in token:
            raise KmsError("remote signer authorization unavailable")
        data = json.dumps({"input": base64.b64encode(message).decode("ascii")},
                          separators=(",", ":")).encode("ascii")
        headers = {"Content-Type": "application/json", "X-Vault-Token": token}
        if self.namespace is not None:
            headers["X-Vault-Namespace"] = self.namespace
        url = self.base_url.rstrip("/") + "/v1/transit/sign/" + quote(self.key_name, safe="")
        try:
            request = Request(url, data=data, headers=headers, method="POST")
            with self.transport(request, timeout=self.timeout_seconds,
                                context=ssl.create_default_context()) as response:
                content = response.read(8193)
            if len(content) > 8192:
                raise KmsError("oversized KMS response")
            answer = json.loads(content)
            formatted = answer["data"]["signature"]
            if not isinstance(formatted, str) or not re.fullmatch(
                    r"vault:v[1-9][0-9]{0,8}:[A-Za-z0-9+/=]{80,100}", formatted):
                raise KmsError("unsupported Vault transit signature format")
            result = base64.b64decode(formatted.split(":", 2)[2], validate=True)
            if len(result) != 64:
                raise KmsError("Vault did not return an Ed25519 signature")
            return result
        except (HTTPError, URLError, ValueError, KeyError, TypeError, OSError) as exc:
            # Do not echo server errors: they could embed the Vault token.
            raise KmsError("external Vault signing failed closed") from exc


def sign_record(signer: ExternalSigner, payload: dict, *, purpose: str) -> str:
    """Explicit domain-separated envelope signature; never sympify/eval input."""
    domains = {"semantic": b"EMR:SEMANTIC:V1\0", "ledger": b"EMR:LEDGER:V1\0",
               "checkpoint": b"EMR:CHECKPOINT:V1\0"}
    if purpose not in domains:
        raise KmsError("unknown signing purpose")
    signature = signer.sign(domains[purpose] + canonical_json(payload))
    if not isinstance(signature, bytes) or len(signature) != 64:
        raise KmsError("remote KMS returned invalid signature")
    return signature.hex()


def rotate_vault_transit_key(*, base_url: str, key_name: str,
                             rotation_token_provider: Callable[[], str],
                             transport: Callable[..., object] = urlopen,
                             timeout_seconds: float = 5.0) -> None:
    """Operator-only REAL Vault Transit key rotation endpoint, fail-closed.

    Requires a distinct Vault token authorized for `update` on
    transit/keys/<name>/rotate; the signing token should not have this right.
    Rotating DOES NOT auto-trust the new version: reviewer/checkpoint root
    allowlists must be reissued and independently pinned before publication.
    """
    signer = VaultTransitSigner(base_url, key_name, rotation_token_provider,
                                timeout_seconds=timeout_seconds, transport=transport)
    token = signer.token_provider()
    if not isinstance(token, str) or not token or any(c in token for c in "\r\n"):
        raise KmsError("operator rotation token unavailable")
    url = base_url.rstrip("/") + "/v1/transit/keys/" + quote(key_name, safe="") + "/rotate"
    try:
        request = Request(url, data=b"{}", headers={"X-Vault-Token": token,
                          "Content-Type": "application/json"}, method="POST")
        with transport(request, timeout=timeout_seconds, context=ssl.create_default_context()) as res:
            if not 200 <= res.status < 300:
                raise KmsError("Vault rotation rejected")
            if len(res.read(8193)) > 8192:
                raise KmsError("Vault rotation response too large")
    except (HTTPError, URLError, OSError, ValueError) as exc:
        raise KmsError("Vault key rotation failed closed") from exc


def sign_checkpoint_policy(signer: ExternalSigner, policy: dict) -> dict:
    """Issuer-side Ed25519 envelope. This capability never runs in G6.

    Policy creation and reviewer authority must be approved out of band.
    """
    return {"policy": policy, "signature": sign_record(signer, policy, purpose="checkpoint")}
