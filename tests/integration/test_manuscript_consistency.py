"""Poisoned draft: independent G6 ledger reconciliation cannot be fooled."""

import copy
from dataclasses import replace

from emr.domain.citation_audit import CitationRecord
from emr.domain.game import validate_game_spec
from emr.domain.manuscript import assemble_manuscript
from emr.domain.submission import audit_submission


def _refs():
    # The DOI has a valid identity, but its (synthetically audited) passage is
    # deliberately stipulated NOT to support the claim. No automatic semantics.
    return (CitationRecord('ref', 'claimA', '10.1038/nature14236',
                           'Synthetic bibliographic assertion', 'Auditor', 2015,
                           'Nature', 'VERIFIED', 'CLAIM_UNSUPPORTED',
                           'fixture:passage', 'fixture:semantic-review', 'CLEAR'),)


def _context(phase8_context):
    doc, anchor, model, params, ledger, prose = phase8_context
    draft = assemble_manuscript(doc, anchor, model, params, ledger,
                                'PropBound', 1, prose, _refs())
    return draft, doc, anchor, model, params, ledger, prose


def test_poisoned_theorem_and_unproven_erasure_trigger_detailed_g6_log(phase8_context):
    draft, doc, anchor, model, params, ledger, prose = _context(phase8_context)
    poison = draft.tex.replace('SKETCH\\_ACCEPTED', 'PROVED')
    poison = poison.replace(r'\unproven{PropBound-v1: SKETCH\_ACCEPTED}',
                            r'\paragraph{Proof PropBound-v1} [STRICTLY PROVED]')
    assert poison != draft.tex
    audit = audit_submission(draft, final_tex=poison, document=doc, anchor=anchor,
                             model=model, parameters=params, ledger=ledger,
                             prose=prose, citations=_refs())
    by_code = {f.code: f for f in audit.findings}
    assert audit.status == 'BLOCKED'
    assert {'TRUSTED_MACRO_TAMPERED', 'FINAL_TEX_DRIFT',
            'CANONICAL_REBUILD_MISMATCH', 'UNPROVEN_PROPOSITION',
            'CLAIM_UNSUPPORTED'}.issubset(by_code)
    assert len(by_code['TRUSTED_MACRO_TAMPERED'].expected_digest) == 64
    assert len(by_code['TRUSTED_MACRO_TAMPERED'].observed_digest) == 64
    assert by_code['TRUSTED_MACRO_TAMPERED'].expected_digest != by_code['TRUSTED_MACRO_TAMPERED'].observed_digest
    assert 'SKETCH_ACCEPTED' in by_code['UNPROVEN_PROPOSITION'].message


def test_stale_model_parameter_and_proof_debt_block_submission(phase8_context):
    draft, doc, anchor, model, params, ledger, prose = _context(phase8_context)
    modified = {**params, 'gamma': '0.3'}
    report = audit_submission(draft, final_tex=draft.tex, document=doc, anchor=anchor,
                              model=model, parameters=modified, ledger=ledger,
                              prose=prose, citations=_refs())
    assert report.upstream_status == 'STALE'
    assert 'UPSTREAM_STALE' in {f.code for f in report.findings}
    raw = copy.deepcopy(model.data)
    next(s for s in raw['symbols'] if s['name'] == 'gamma')['domain']['upper'] = '1'
    changed = validate_game_spec(raw)
    report2 = audit_submission(draft, final_tex=draft.tex, document=doc, anchor=anchor,
                               model=changed, parameters=params, ledger=ledger,
                               prose=prose, citations=_refs())
    assert 'UPSTREAM_STALE' in {f.code for f in report2.findings}


def test_citation_status_transplant_does_not_fix_corrupted_math(phase8_context):
    draft, doc, anchor, model, params, ledger, prose = _context(phase8_context)
    # Even a cited record imported as supported/metadata verified does not
    # authorize using an altered mathematical conclusion.
    refs = (replace(_refs()[0], support_status='CLAIM_SUPPORTED'),)
    tampered = draft.tex.replace('e=4', 'e=999')
    assert tampered != draft.tex
    report = audit_submission(draft, final_tex=tampered, document=doc, anchor=anchor,
                              model=model, parameters=params, ledger=ledger,
                              prose=prose, citations=refs)
    assert report.status == 'BLOCKED'
    assert 'TRUSTED_MACRO_TAMPERED' in {x.code for x in report.findings}


def test_g6_structured_log_schema_carries_real_reconciliation_digests(phase8_context):
    from emr.domain.submission import render_g6_report

    draft, doc, anchor, model, params, ledger, prose = _context(phase8_context)
    altered = draft.tex.replace('SKETCH\\_ACCEPTED', 'PROVED')
    report = audit_submission(draft, final_tex=altered, document=doc, anchor=anchor,
                              model=model, parameters=params, ledger=ledger,
                              prose=prose, citations=_refs())
    payload = render_g6_report(report)
    assert payload['status'] == 'BLOCKED'
    assert payload['upstream_status'] == 'CURRENT'
    finding = next(item for item in payload['findings']
                   if item['code'] == 'TRUSTED_MACRO_TAMPERED')
    assert finding['expected_digest'] != finding['observed_digest']
    assert payload['recalculated_tex_sha256'] is not None
