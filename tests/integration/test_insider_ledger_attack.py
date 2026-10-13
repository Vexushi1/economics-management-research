"""Real file I/O insider tampering bypasses Python mutation APIs entirely.

Issuer/reviewer private keys and checkpoint live outside the attacker-writable
ledger directory. Their separation is the central security assumption.
"""

import copy
import json
from dataclasses import asdict

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from emr.core.evidence_chain import anchor_ref
from emr.core.security import (
    TrustPolicy,
    canonical_json,
    digest,
    parse_json_record,
    prepare_ledger_payload,
)
from emr.domain.citation_audit import CitationRecord
from emr.domain.manuscript import assemble_manuscript
from emr.domain.proof import certify_proof
from emr.domain.submission import audit_submission, render_g6_report


def _pub(key):
    return key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)


def _fixture(phase8_context, tmp_path):
    doc, anchor, model, params, ledger, prose = phase8_context
    certify_proof(ledger, 'PropBound', 1, reviewer='OutsideHumanReviewer',
                  evidence_refs=('synthetic:complete-independent-proof',),
                  attestation='INDEPENDENT_FULL_PROOF_REVIEW_COMPLETED')
    refs = (CitationRecord('ref', 'claimA', '10.1038/nature14236',
                           'Synthetic bibliographic context test', 'Fixture only', 2015,
                           'Fixture journal', 'VERIFIED', 'CLAIM_SUPPORTED',
                           'synth:paper', 'synth:explicit-claim-review', 'CLEAR'),)
    draft = assemble_manuscript(doc, anchor, model, params, ledger, 'PropBound', 1,
                                prose, refs)
    reviewer_key = Ed25519PrivateKey.generate()  # test-only external human signer
    issuer_key = Ed25519PrivateKey.generate()    # test-only protected ledger signer
    approval_data = {
        'version': '1', 'action': 'APPROVE', 'reviewer_id': 'OutsideHumanReviewer',
        'signer_key_id': 'scholar1', 'approved_at': '2026-10-13T10:00:00Z',
        'pdf_sha256': doc.sha256, 'source_anchor': anchor_ref(anchor),
        'model_sha256': draft.evidence_seal.model_sha256,
        'review_refs': ['synth:original-pdf-to-model-validation'],
        'review_digest': '9' * 64, 'semantic_scope': 'PDF_TO_MODELSPEC_MAPPING',
    }
    approval = {'payload': approval_data, 'signature': reviewer_key.sign(
        b'EMR:SEMANTIC:V1\0' + canonical_json(approval_data)).hex()}
    payload = prepare_ledger_payload(
        seal=draft.evidence_seal, draft_sha256=draft.sha256,
        core_sha256=draft.core_sha256,
        citations_sha256=digest({'records': [asdict(r) for r in refs]}),
        approval_digest=digest(approval), sequence=5, previous_digest='0'*64)
    envelope = {
        'payload': payload, 'key_id': 'ledger-issuer', 'self_sha256': digest(payload),
        'signature': issuer_key.sign(b'EMR:LEDGER:V1\0' + canonical_json(payload)).hex(),
    }
    # The trust policy and private keys are held out-of-band from ledger files.
    protected_policy = TrustPolicy({'scholar1': _pub(reviewer_key)}, 'ledger-issuer',
                                   _pub(issuer_key), 5, digest(envelope))
    path = tmp_path / 'attacker_writable_ledger.json'
    path.write_text(json.dumps(envelope), encoding='utf-8')
    args = {'draft': draft, 'final_tex': draft.tex, 'document': doc, 'anchor': anchor,
            'model': model, 'parameters': params, 'ledger': ledger, 'prose': prose,
            'citations': refs, 'semantic_approval': approval,
            'trust': protected_policy}
    return args, path


def _audit(args, ledger_path):
    return audit_submission(**args, signed_ledger=parse_json_record(ledger_path.read_bytes()))


def test_signed_human_approval_with_protected_ledger_allows_synthetic_g6(phase8_context, tmp_path):
    args, path = _fixture(phase8_context, tmp_path)
    report = _audit(args, path)
    assert report.status == 'READY_FOR_SUBMISSION', [x.code for x in report.findings]
    assert report.upstream_status == 'CURRENT'
    assert render_g6_report(report)['findings'] == []


def test_insider_physical_hash_rewrite_triggers_critical_lockdown(phase8_context, tmp_path):
    args, path = _fixture(phase8_context, tmp_path)
    assert _audit(args, path).status == 'READY_FOR_SUBMISSION'
    # Direct filesystem write: bypass every API and recompute self-hash to match forged payload.
    forged = json.loads(path.read_text(encoding='utf-8'))
    forged['payload']['model_sha256'] = 'e' * 64
    forged['self_sha256'] = digest(forged['payload'])
    path.write_text(json.dumps(forged), encoding='utf-8')
    report = _audit(args, path)
    assert report.status == 'BLOCKED'
    severe = next(x for x in report.findings if x.code == 'CRITICAL_LEDGER_CORRUPTION')
    assert severe.severity == 'CRITICAL'
    assert any(term in severe.message for term in ('checkpoint', 'signature', 'dependencies'))


def test_signed_old_snapshot_replay_rejected_by_trusted_sequence(phase8_context, tmp_path):
    args, path = _fixture(phase8_context, tmp_path)
    policy = args['trust']
    args = {**args, 'trust': TrustPolicy(policy.reviewers, policy.ledger_key_id,
                                       policy.ledger_public_key, 6, policy.expected_envelope_digest)}
    report = _audit(args, path)
    assert 'CRITICAL_LEDGER_CORRUPTION' in {x.code for x in report.findings}


def test_forged_approval_is_not_a_semantic_review(phase8_context, tmp_path):
    args, path = _fixture(phase8_context, tmp_path)
    forged = copy.deepcopy(args['semantic_approval'])
    forged['payload']['reviewer_id'] = 'Attacker'
    report = _audit({**args, 'semantic_approval': forged}, path)
    assert report.status == 'BLOCKED'
    assert 'SEMANTIC_APPROVAL_INVALID' in {x.code for x in report.findings}


def test_no_external_trust_is_never_submission_ready(phase8_context, tmp_path):
    args, path = _fixture(phase8_context, tmp_path)
    report = audit_submission(**{**args, 'trust': None},
                              signed_ledger=parse_json_record(path.read_bytes()))
    assert report.status == 'BLOCKED'
    assert 'TRUST_ANCHOR_MISSING' in {x.code for x in report.findings}
