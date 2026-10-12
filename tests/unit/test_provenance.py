"""Anchors have byte identity and require explicit scholarly adjudication."""

import pytest

from emr.adapters.pdf_extract import extract_pdf
from emr.core.provenance import ClaimEvidence, SourceAnchor, anchor_matches, make_anchor


def test_anchor_matches_exact_source_and_offsets(sample_pdf):
    pdf = extract_pdf(sample_pdf)
    index = next(i for i, b in enumerate(pdf.pages[0].blocks) if "Proposition 1" in b.text)
    block = pdf.pages[0].blocks[index]
    start = block.text.index("Proposition 1")
    anchor = make_anchor(pdf, 1, index, start, start + len("Proposition 1"))
    assert anchor_matches(pdf, anchor)
    assert not anchor_matches(pdf, SourceAnchor("a" * 64, 1, index, start, anchor.end, anchor.quote))
    assert not anchor_matches(pdf, SourceAnchor(pdf.sha256, 1, index, start, anchor.end, "Wrong"))


def test_supported_claim_requires_review(sample_pdf):
    pdf = extract_pdf(sample_pdf)
    anchor = make_anchor(pdf, 1, 0, 0, 5)
    with pytest.raises(ValueError):
        ClaimEvidence("Model is coordinated", status="CLAIM_SUPPORTED", anchor=anchor)
    with pytest.raises(ValueError):
        ClaimEvidence("Model is coordinated", status="CLAIM_SUPPORTED", reviewer="Scholar")
    candidate = ClaimEvidence("Model is coordinated", anchor=anchor)
    assert candidate.status == "NOT_VERIFIED"
    reviewed = ClaimEvidence("A human-reviewed claim", "CLAIM_SUPPORTED", anchor, "Scholar")
    assert reviewed.status == "CLAIM_SUPPORTED"


def test_invalid_quote_bounds_rejected(sample_pdf):
    pdf = extract_pdf(sample_pdf)
    with pytest.raises(ValueError):
        make_anchor(pdf, 1, 0, -1, 2)
    with pytest.raises(ValueError):
        make_anchor(pdf, 2, 0, 0, 1)
