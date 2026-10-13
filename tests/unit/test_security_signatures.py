"""Real Ed25519 verification, not hashes that a writer may recompute."""

from dataclasses import replace

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from emr.core.security import (
    SecurityBoundaryError, TrustPolicy, canonical_json, digest, parse_json_record,
    verify_semantic_approval, verify_signed_ledger,
)


def pub(private):
    return private.public_key().public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)


def issuer_fixture():
    user = Ed25519PrivateKey.generate()
    ledger_key = Ed25519PrivateKey.generate()
    payload = {
        'version': '1', 'action': 'APPROVE', 'reviewer_id': 'ExternalScholar',
        'signer_key_id': 'reviewer1', 'approved_at': '2026-10-13T10:00:00Z',
        'pdf_sha256': 'a' * 64, 'model_sha256': 'b' * 64,
        'source_anchor': 'pdf:' + 'a' * 64 + ':p1:b0:s0-8',
        'review_refs': ['approved:review-document-1'],
        'review_digest': 'c' * 64, 'semantic_scope': 'PDF_TO_MODELSPEC_MAPPING',
    }
    approved = {'payload': payload,
                'signature': user.sign(b'EMR:SEMANTIC:V1\0' + canonical_json(payload)).hex()}
    return user, ledger_key, approved


def test_semantic_approval_cannot_be_self_issued_by_json_edit():
    user, ledger_key, approved = issuer_fixture()
    policy = TrustPolicy({'reviewer1': pub(user)}, 'issuer', pub(ledger_key), 1, '0' * 64)
    args = {'pdf_sha256': 'a' * 64, 'source_anchor': approved['payload']['source_anchor'],
            'model_sha256': 'b' * 64}
    assert verify_semantic_approval(approved, policy, **args) == 'SEMANTIC_BRIDGE_VERIFIED'
    forged = {'payload': {**approved['payload'], 'reviewer_id': 'Intruder'},
              'signature': approved['signature']}
    with pytest.raises(SecurityBoundaryError, match='signature'):
        verify_semantic_approval(forged, policy, **args)
    with pytest.raises(SecurityBoundaryError, match='scope'):
        verify_semantic_approval(approved, policy, **{**args, 'model_sha256': 'e' * 64})
    with pytest.raises(SecurityBoundaryError):
        verify_semantic_approval({'payload': approved['payload'], 'signature': '0' * 128}, policy, **args)


def test_ledger_hash_rewrite_signature_and_freshness_protected():
    reviewer, issuer, _ = issuer_fixture()
    payload = {
        'schema_version': '1', 'sequence': 5, 'previous_digest': '0' * 64,
        'pdf_sha256': 'a' * 64, 'model_sha256': 'b' * 64,
        'parameter_sha256': '1' * 64, 'result_sha256': '2' * 64,
        'proof_sha256': '3' * 64, 'approval_digest': '4' * 64,
        'draft_sha256': '5' * 64, 'core_sha256': '6' * 64,
        'citations_sha256': '7' * 64, 'proposition_id': 'Theorem1', 'proof_version': 1,
    }
    envelope = {
        'payload': payload, 'key_id': 'issuer', 'self_sha256': digest(payload),
        'signature': issuer.sign(b'EMR:LEDGER:V1\0' + canonical_json(payload)).hex(),
    }
    policy = TrustPolicy({'reviewer1': pub(reviewer)}, 'issuer', pub(issuer), 5,
                         digest(envelope))
    verify_signed_ledger(envelope, policy, payload)
    forged_payload = {**payload, 'model_sha256': 'f' * 64}
    forged = {**envelope, 'payload': forged_payload,
              'self_sha256': digest(forged_payload)}
    with pytest.raises(SecurityBoundaryError, match='checkpoint'):
        verify_signed_ledger(forged, policy, forged_payload)
    with pytest.raises(SecurityBoundaryError):
        verify_signed_ledger(envelope, policy, forged_payload)
    with pytest.raises(SecurityBoundaryError, match='rollback'):
        verify_signed_ledger(envelope, replace(policy, expected_sequence=6), payload)


def test_json_duplicate_fields_and_nan_are_refused():
    for raw in (b'{"payload":1,"payload":2}', b'{"p":NaN}', b'[]', b'\xff'):
        with pytest.raises(SecurityBoundaryError):
            parse_json_record(raw)
