"""Inert bibliographic normalization. Network lookups intentionally disabled."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping

_DOI = re.compile(r"^10\.\d{4,9}/[^\s]+$", re.IGNORECASE)


def normalize_doi(raw: str) -> str | None:
    """Normalize basic DOI URI/prefix; does not assert DOI existence."""
    cleaned = raw.strip()
    cleaned = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi\s*:\s*)", "", cleaned, flags=re.I)
    cleaned = cleaned.strip().rstrip(".,;)")
    return cleaned.lower() if _DOI.fullmatch(cleaned) else None


def deduplicate_by_doi(records: Iterable[Mapping[str, object]]) -> list[Mapping[str, object]]:
    """Keep first DOI entry; preserve DOI-less records instead of guessing duplicates."""
    seen: set[str] = set()
    out: list[Mapping[str, object]] = []
    for record in records:
        doi = normalize_doi(str(record.get("doi") or ""))
        if doi is not None and doi in seen:
            continue
        if doi is not None:
            seen.add(doi)
        out.append(record)
    return out


def lookup_doi(_doi: str) -> None:
    """Explicitly unavailable in offline profile. No implicit API requests."""
    raise NotImplementedError("DOI lookup requires a separately approved online adapter")


def resolve_bibtex(_record: Mapping[str, object]) -> None:
    """Do not fabricate bibliographic entries from unverified metadata."""
    raise NotImplementedError("BibTeX resolution requires source verification")
