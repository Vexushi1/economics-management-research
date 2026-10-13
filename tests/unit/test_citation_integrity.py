"""DOI validity does not imply substantive support for a particular claim."""

from dataclasses import replace

import pytest

from emr.domain.citation_audit import CitationAuditError, CitationRecord, validate_citations
from emr.domain.submission import check_claim_evidence


def citation():
    return CitationRecord(
        key='citeA', claim_id='claimA', doi='10.1038/nature14236',
        title='Human-level control through deep reinforcement learning',
        authors='Mnih, Kavukcuoglu, Silver, et al.', year=2015, journal='Nature',
        metadata_status='VERIFIED', support_status='CLAIM_UNSUPPORTED',
        source_ref='fixture:source:paragraph:1', support_review_ref='fixture:review:against-claim',
        retraction_status='CLEAR',
    )


def test_valid_doi_but_contradictory_claim_is_blocked():
    r = citation()
    assert validate_citations((r,)) == (r,)
    report = check_claim_evidence((r,), ('claimA',))
    assert 'CLAIM_UNSUPPORTED' in [issue.code for issue in report]
    assert 'DOI_METADATA_NOT_VERIFIED' not in [issue.code for issue in report]


def test_doi_dedup_and_unknown_citations_block():
    r = citation()
    with pytest.raises(CitationAuditError, match='duplicate DOI'):
        validate_citations((r, replace(r, key='citeB', claim_id='claimB')))
    assert 'CITATION_KEY_MISSING' in [x.code for x in check_claim_evidence((r,), ('different',))]


def test_unsupported_claim_cannot_masquerade_as_reviewed_without_review_reference():
    r = replace(citation(), support_review_ref=None)
    with pytest.raises(CitationAuditError):
        validate_citations((r,))


def test_unverified_and_retracted_metadata_are_blockers():
    r = replace(citation(), support_status='NOT_VERIFIED', support_review_ref=None,
                retraction_status='RETRACTED', metadata_status='NOT_VERIFIED')
    codes = [f.code for f in check_claim_evidence((r,), ('claimA',))]
    assert {'CLAIM_NOT_VERIFIED', 'RETRACTION_STATUS_UNCLEAR',
            'DOI_METADATA_NOT_VERIFIED'}.issubset(codes)
