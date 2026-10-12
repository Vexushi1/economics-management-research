"""Source-grounding contracts: presence of a quote is not proof of its meaning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from emr.adapters.pdf_extract import PdfDocument

EvidenceStatus = Literal["NOT_VERIFIED", "CLAIM_SUPPORTED", "CLAIM_UNSUPPORTED"]


@dataclass(frozen=True, slots=True)
class SourceAnchor:
    """An exact snippet located inside an immutable PDF text block.

    Offsets are zero-based Python string character offsets, end exclusive; page
    numbering and block indexing are 1-based and 0-based, respectively.
    """

    file_sha256: str
    page: int
    block: int
    start: int
    end: int
    quote: str


def make_anchor(document: PdfDocument, page: int, block: int, start: int, end: int) -> SourceAnchor:
    """Create an anchor only when its quote exists at the specified block span."""
    if not (1 <= page <= document.page_count):
        raise ValueError("page out of range")
    blocks = document.pages[page - 1].blocks
    if not (0 <= block < len(blocks)):
        raise ValueError("block index out of range")
    text = blocks[block].text
    if not (0 <= start < end <= len(text)):
        raise ValueError("invalid quote span")
    return SourceAnchor(document.sha256, page, block, start, end, text[start:end])


def anchor_matches(document: PdfDocument, anchor: SourceAnchor) -> bool:
    """Check byte-identified source and exact extracted snippet; no semantic claim."""
    try:
        expected = make_anchor(document, anchor.page, anchor.block, anchor.start, anchor.end)
    except (ValueError, IndexError):
        return False
    return anchor == expected


@dataclass(frozen=True, slots=True)
class ClaimEvidence:
    """A scholarly assertion and independently reviewed support state.

    Even a perfect textual anchor does not imply the source supports an economic
    proposition. Only explicit reviewer adjudication may set SUPPORTED.
    """

    statement: str
    status: EvidenceStatus = "NOT_VERIFIED"
    anchor: SourceAnchor | None = None
    reviewer: str | None = None

    def __post_init__(self) -> None:
        if not self.statement.strip():
            raise ValueError("claim statement cannot be empty")
        if self.status not in ("NOT_VERIFIED", "CLAIM_SUPPORTED", "CLAIM_UNSUPPORTED"):
            raise ValueError("invalid evidence status")
        if self.status != "NOT_VERIFIED" and (self.anchor is None or not self.reviewer):
            raise ValueError("adjudication requires source anchor and named reviewer")
