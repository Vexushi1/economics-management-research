"""An untrusted writing model cannot author arbitrary trusted math macros."""

from dataclasses import replace

import pytest

from emr.domain.citation_audit import CitationRecord
from emr.domain.manuscript import (
    ManuscriptError,
    assemble_manuscript,
    render_section_outline,
    trusted_core,
)
from emr.domain.submission import audit_submission


def citations():
    return (CitationRecord('citeA', 'claimA', '10.1038/nature14236',
                           'Synthetic metadata title', 'Synthetic author', 2015,
                           'Nature', 'VERIFIED', 'CLAIM_UNSUPPORTED',
                           'fixture:source', 'fixture:review', 'CLEAR'),)


def make_draft(phase8_context):
    doc, anchor, model, params, ledger, prose = phase8_context
    draft = assemble_manuscript(doc, anchor, model, params, ledger,
                                'PropBound', 1, prose, citations())
    return draft, (doc, anchor, model, params, ledger, prose)


def test_prose_slots_escape_latex_commands(phase8_context):
    doc, anchor, model, params, ledger, prose = phase8_context
    prose['introduction'] = '\\renewcommand{\\EMRProofVerdict}{PROVED} $x$ %'  # inert text
    artifact = assemble_manuscript(doc, anchor, model, params, ledger,
                                   'PropBound', 1, prose, citations())
    core = trusted_core(artifact.tex)
    assert core and core.count(r'\newcommand{\EMRProofVerdict}') == 1
    assert r'\textbackslash{}renewcommand' in artifact.tex
    assert r'\$x\$' in artifact.tex
    assert r'\unproven{' in core
    assert render_section_outline() == ('introduction', 'literature_review', 'conclusion')


def test_reject_unpermitted_llm_sections_or_unknown_claim(phase8_context):
    doc, anchor, model, params, ledger, prose = phase8_context
    with pytest.raises(ManuscriptError, match='only three'):
        assemble_manuscript(doc, anchor, model, params, ledger, 'PropBound', 1,
                            {**prose, 'equilibrium': 'I assert x=999'}, citations())
    with pytest.raises(ManuscriptError, match='undeclared citation'):
        assemble_manuscript(doc, anchor, model, params, ledger, 'PropBound', 1,
                            {**prose, 'conclusion': 'Text [CITE:unknown]'}, citations())


def test_tampered_draft_and_self_updated_hash_still_fails(phase8_context):
    from hashlib import sha256

    draft, (doc, anchor, model, params, ledger, prose) = make_draft(phase8_context)
    altered = draft.tex.replace('SKETCH\\_ACCEPTED', 'PROVED')
    assert altered != draft.tex
    fake = replace(draft, tex=altered, sha256=sha256(altered.encode()).hexdigest())
    report = audit_submission(fake, final_tex=altered, document=doc, anchor=anchor,
                              model=model, parameters=params, ledger=ledger,
                              prose=prose, citations=citations())
    codes = {x.code for x in report.findings}
    assert 'CANONICAL_REBUILD_MISMATCH' in codes
    assert 'TRUSTED_MACRO_TAMPERED' in codes or 'FINAL_TEX_DRIFT' in codes
    assert report.status == 'BLOCKED'


def test_even_untampered_sketch_is_not_submission_ready(phase8_context):
    draft, (doc, anchor, model, params, ledger, prose) = make_draft(phase8_context)
    report = audit_submission(draft, final_tex=draft.tex, document=doc, anchor=anchor,
                              model=model, parameters=params, ledger=ledger,
                              prose=prose, citations=citations())
    codes = {f.code for f in report.findings}
    assert 'UNPROVEN_PROPOSITION' in codes
    assert 'SEMANTIC_BRIDGE_NOT_VERIFIED' in codes
    assert 'CLAIM_UNSUPPORTED' in codes
    assert report.upstream_status == 'CURRENT'
