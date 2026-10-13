"""Real signed-policy wire contracts and Vault request integration, no external network."""
from __future__ import annotations

import base64
import json
from datetime import UTC, datetime
from io import BytesIO

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from emr.adapters.checkpoint import ProtectedCheckpointClient, verify_checkpoint_envelope
from emr.adapters.kms import KmsError, VaultTransitSigner, rotate_vault_transit_key, sign_record
from emr.core.security import SecurityBoundaryError, canonical_json


class Response:
    def __init__(self, body: bytes, status: int = 200):
        self.stream = BytesIO(body)
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.stream.close()

    def read(self, length: int):
        return self.stream.read(length)


def pub(key):
    return key.public_key().public_bytes(encoding=serialization.Encoding.Raw,
                                          format=serialization.PublicFormat.Raw)


def checkpoint():
    root = Ed25519PrivateKey.generate()
    issuer = Ed25519PrivateKey.generate()
    reviewer = Ed25519PrivateKey.generate()
    policy = {
        "version": "1", "sequence": 8, "expires_at": "2099-01-01T00:00:00Z",
        "ledger_key_id": "ledger-issuer", "ledger_public_key": base64.b64encode(pub(issuer)).decode(),
        "reviewers": {"reviewer1": base64.b64encode(pub(reviewer)).decode()},
        "expected_envelope_digest": "c"*64,
    }
    env = {"policy": policy, "signature": root.sign(
        b"EMR:CHECKPOINT:V1\0" + canonical_json(policy)).hex()}
    return root, env


def test_signed_policy_over_untrusted_transport():
    root, env = checkpoint()
    def transport(request, **kwargs):
        return Response(json.dumps(env).encode())
    client = ProtectedCheckpointClient("https://trust.example.org/v1/trust-policy", pub(root),
                                       8, transport=transport)
    policy = client.fetch()
    assert policy.expected_sequence == 8 and "reviewer1" in policy.reviewers
    forged = json.loads(json.dumps(env))
    forged["policy"]["expected_envelope_digest"] = "d" * 64
    with pytest.raises(SecurityBoundaryError):
        verify_checkpoint_envelope(forged, pub(root), minimum_sequence=8)
    with pytest.raises(SecurityBoundaryError, match="rolled back"):
        verify_checkpoint_envelope(env, pub(root), minimum_sequence=9)
    env["policy"]["expires_at"] = "2000-01-01T00:00:00Z"
    with pytest.raises(SecurityBoundaryError):
        verify_checkpoint_envelope(env, pub(root), minimum_sequence=8)


def test_fail_closed_unavailable_network_and_malformed_trust_endpoint():
    root, _ = checkpoint()
    with pytest.raises(SecurityBoundaryError):
        ProtectedCheckpointClient("http://evil.example/v1/trust-policy", pub(root), 1)
    with pytest.raises(SecurityBoundaryError, match="unavailable"):
        ProtectedCheckpointClient("https://trust.example.org/v1/trust-policy", pub(root), 1,
                                  transport=lambda *a, **k: (_ for _ in ()).throw(OSError())).fetch()


def test_vault_transit_signs_exact_domain_bytes_without_local_private_key():
    key = Ed25519PrivateKey.generate()  # test remote simulator only
    calls = []

    def transport(request, **kwargs):
        body = json.loads(request.data)
        message = base64.b64decode(body["input"])
        calls.append((request.full_url, request.get_method(), message))
        signature = key.sign(message)
        return Response(json.dumps({"data": {"signature":
                         "vault:v3:" + base64.b64encode(signature).decode()}}).encode())

    signer = VaultTransitSigner("https://vault.example.org", "emr-issuer",
                                lambda: "separate-sign-only-token", transport=transport)
    claim = {"approved": True}
    signature = bytes.fromhex(sign_record(signer, claim, purpose="semantic"))
    key.public_key().verify(signature, b"EMR:SEMANTIC:V1\0" + canonical_json(claim))
    assert calls[0][0] == "https://vault.example.org/v1/transit/sign/emr-issuer"
    assert calls[0][1] == "POST"
    assert calls[0][2].startswith(b"EMR:SEMANTIC:V1\0")
    with pytest.raises(KmsError):
        VaultTransitSigner("http://vault.example.org", "issuer", lambda: "token")


def test_operator_rotation_cannot_be_claimed_without_real_remote_post():
    requests = []

    def transport(request, **kwargs):
        requests.append((request.full_url, request.get_method()))
        return Response(b"{}", 204)

    rotate_vault_transit_key(base_url="https://vault.example.org", key_name="emr-issuer",
                             rotation_token_provider=lambda: "operator-role-only",
                             transport=transport)
    assert requests == [("https://vault.example.org/v1/transit/keys/emr-issuer/rotate", "POST")]
    with pytest.raises(KmsError):
        rotate_vault_transit_key(base_url="https://vault.example.org", key_name="emr-issuer",
                                 rotation_token_provider=lambda: "bad\nheader", transport=transport)


def test_checkpoint_current_time_expiration_and_no_secret_fields():
    root, env = checkpoint()
    env["policy"]["signing_private_key"] = "disallowed"
    with pytest.raises(SecurityBoundaryError):
        verify_checkpoint_envelope(env, pub(root), minimum_sequence=8)
    root, env = checkpoint()
    with pytest.raises(SecurityBoundaryError):
        verify_checkpoint_envelope(env, pub(root), minimum_sequence=8,
                                   now=datetime(2100, 1, 1, tzinfo=UTC))


def test_external_checkpoint_issuer_signs_versioned_policy_and_verifies():
    from emr.adapters.kms import sign_checkpoint_policy

    root, envelope = checkpoint()

    class IssuerOutsideG6:
        def sign(self, msg):
            assert msg.startswith(b"EMR:CHECKPOINT:V1" + bytes([0]))
            return root.sign(msg)

    issued = sign_checkpoint_policy(IssuerOutsideG6(), envelope["policy"])
    assert issued == envelope
    assert verify_checkpoint_envelope(issued, pub(root), minimum_sequence=8).expected_sequence == 8
