"""Offline citation identities and *separate* semantic-claim support adjudication.

A DOI-shaped identifier, or even verified bibliographic metadata, does not
establish that a particular paragraph is supported. This module never queries
DOI services or uses a language model as an evidence judge.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from emr.adapters.bibliography import normalize_doi

_KEY = re.compile(r"[A-Za-z][A-Za-z0-9_:-]{0,63}\Z")
_SHA = re.compile(r"[a-f0-9]{64}\Z")


class CitationAuditError(ValueError):
    """Citation metadata, attribution, or an evidence link is inconsistent."""


@dataclass(frozen=True, slots=True)
class CitationRecord:
    """An externally reviewed claim-to-paper *assertion*, not auto verification.

    `metadata_status=VERIFIED` is an imported assertion, not proof of DOI lookup.
    A missing/not authenticated external review must not be inferred from it.
    """

    key: str
    claim_id: str
    doi: str
    title: str
    authors: str
    year: int
    journal: str
    metadata_status: Literal["VERIFIED", "NOT_VERIFIED"]
    support_status: Literal["CLAIM_SUPPORTED", "CLAIM_UNSUPPORTED", "NOT_VERIFIED"]
    source_ref: str
    support_review_ref: str | None = None
    retraction_status: Literal["CLEAR", "RETRACTED", "UNKNOWN"] = "UNKNOWN"


def validate_citations(records: tuple[CitationRecord, ...]) -> tuple[CitationRecord, ...]:
    """Validate bounded literal data without treating any status as true evidence."""
    if not isinstance(records, tuple) or len(records) > 100:
        raise CitationAuditError("bounded tuple of citation records required")
    keys: set[str] = set()
    dois: dict[str, str] = {}
    claims: set[str] = set()
    for row in records:
        if not isinstance(row, CitationRecord):
            raise CitationAuditError("record must be a typed citation")
        if not _KEY.fullmatch(row.key) or not _KEY.fullmatch(row.claim_id):
            raise CitationAuditError("invalid citation key or claim identifier")
        doi = normalize_doi(row.doi)
        if doi is None or doi != row.doi:
            raise CitationAuditError("DOI must be canonical, but existence is not inferred")
        if row.key in keys or row.claim_id in claims:
            raise CitationAuditError("duplicate reference key or claim identifier")
        if doi in dois:
            raise CitationAuditError("duplicate DOI across reference keys")
        keys.add(row.key)
        claims.add(row.claim_id)
        dois[doi] = row.key
        if (not 1900 <= row.year <= 2100 or
            any(not isinstance(s, str) or not s.strip() or len(s) > 300
                for s in (row.title, row.authors, row.journal, row.source_ref)) or
            row.metadata_status not in ("VERIFIED", "NOT_VERIFIED") or
            row.support_status not in ("CLAIM_SUPPORTED", "CLAIM_UNSUPPORTED", "NOT_VERIFIED") or
            row.retraction_status not in ("CLEAR", "RETRACTED", "UNKNOWN")):
            raise CitationAuditError("invalid bibliographic or status fields")
        if row.support_review_ref is not None and (
            not isinstance(row.support_review_ref, str) or
            not row.support_review_ref.strip() or len(row.support_review_ref) > 300
        ):
            raise CitationAuditError("invalid claim support reviewer reference")
        if row.support_status != "NOT_VERIFIED" and not row.support_review_ref:
            raise CitationAuditError("semantic support verdict needs external review reference")
    return records
