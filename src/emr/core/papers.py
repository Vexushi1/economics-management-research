"""Conservative, evidence-traceable records for analytical research papers.

Regex rules identify candidates only, never validated mathematical propositions,
real DOI registry entries, publication dates or causal/economic conclusions.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from importlib.resources import files

from jsonschema import Draft202012Validator

from emr.adapters.bibliography import normalize_doi
from emr.adapters.pdf_extract import PdfDocument
from emr.core.provenance import make_anchor

_DOI_FIND = re.compile(r"10\.\d{4,9}/[^\s<>\[\]{}]+", re.I)
_HEADING = re.compile(r"^(?:\d+(?:\.\d+){0,3}[. ]+|(?:ABSTRACT|INTRODUCTION|CONCLUSIONS?|REFERENCES|APPENDIX)\b)", re.I)
_PROPOSITION = re.compile(r"\b(?:Proposition|Theorem|Lemma|Corollary)\s+\d+[A-Za-z]?\b", re.I)


def paper_record(document: PdfDocument) -> dict[str, object]:
    """Derive a candidate record with exact anchors and no inferred findings."""
    doi_candidates: list[str] = []
    sections: list[dict[str, object]] = []
    propositions: list[dict[str, object]] = []
    equations: list[dict[str, object]] = []
    title = document.title_metadata if document.title_metadata else None
    for page in document.pages:
        for index, block in enumerate(page.blocks):
            for match in _DOI_FIND.finditer(block.text):
                doi = normalize_doi(match.group().rstrip(".,;:"))
                if doi and doi not in doi_candidates:
                    doi_candidates.append(doi)
            # Work with original offsets: repeated lines must not point to their
            # first occurrence in the same text block.
            offset = 0
            for raw_line in block.text.splitlines(keepends=True):
                line = raw_line.rstrip("\r\n")
                heading = line.strip()
                if len(heading) < 150 and _HEADING.match(heading):
                    sections.append({
                        "text": heading,
                        "anchor": _anchor_dict(document, page.number, index, offset, offset + len(line)),
                        "status": "NOT_VERIFIED",
                    })
                # '=' also occurs outside mathematics; never evaluate these strings.
                if "=" in line and len(line) <= 280 and len(equations) < 300:
                    equations.append({
                        "text": line.strip(),
                        "anchor": _anchor_dict(document, page.number, index, offset, offset + len(line)),
                        "bbox": list(block.bbox),
                        "bbox_scope": "text_block",
                        "status": "NOT_VERIFIED",
                    })
                offset += len(raw_line)
            for match in _PROPOSITION.finditer(block.text):
                propositions.append({
                    "text": match.group(),
                    "anchor": _anchor_dict(
                        document, page.number, index, match.start(), match.end()
                    ),
                    "status": "NOT_VERIFIED",
                })
    if title is None and document.pages:
        for block in document.pages[0].blocks:
            candidate = block.text.splitlines()[0].strip()
            if 12 <= len(candidate) <= 180:
                title = candidate
                break
    return {
        "schema_version": "1",
        "file_sha256": document.sha256,
        "pages": document.page_count,
        "title": {"value": title, "status": "NOT_VERIFIED"},
        "doi_candidates": doi_candidates,
        "sections": sections,
        "proposition_candidates": propositions,
        "equation_candidates": equations,
        "metadata": {"author": document.author_metadata, "journal": None, "first_online_year": None, "volume_year": None},
        "research_questions": [],
        "players": [],
        "decision_variables": [],
        "economic_mechanisms": [],
        "claims": [],
        "evidence_status": "NOT_VERIFIED",
    }


def _anchor_dict(document: PdfDocument, page: int, block: int, start: int, end: int) -> dict[str, object]:
    anchor = make_anchor(document, page, block, start, end)
    return {"file_sha256": anchor.file_sha256, "page": anchor.page, "block": anchor.block, "start": anchor.start, "end": anchor.end, "quote": anchor.quote}


def literature_matrix(records: list[Mapping[str, object]]) -> dict[str, object]:
    """Make an auditable comparison matrix without fabricating economic mechanisms."""
    rows = []
    seen_sources: set[str] = set()
    for record in records:
        file_sha = str(record["file_sha256"])
        if file_sha in seen_sources:
            continue  # Exact same PDF bytes are one source; keep distinct revisions.
        seen_sources.add(file_sha)
        title_obj = record.get("title")
        title = title_obj.get("value") if isinstance(title_obj, Mapping) else None
        rows.append({"file_sha256": record["file_sha256"], "title": title, "title_status": "NOT_VERIFIED", "doi_candidates": list(record.get("doi_candidates", [])), "methods": {"value": None, "status": "UNKNOWN"}, "mechanisms": {"value": None, "status": "UNKNOWN"}, "findings": []})
    return {"schema_version": "1", "rows": rows, "research_gap_status": "INSUFFICIENT_EVIDENCE"}


def validate_paper_record(record: Mapping[str, object]) -> None:
    """Validate candidate record shape against locally bundled reviewed Schema.

    Schema validity is not source integrity or substantive claim verification.
    """
    import json

    schema = json.loads(files("emr").joinpath("schemas/paper-record.schema.json").read_text())
    Draft202012Validator(schema).validate(record)
    # JSON Schema checks shape but cannot express cross-field evidence linkage.
    for field in ("sections", "proposition_candidates", "equation_candidates"):
        for item in record[field]:
            anchor = item["anchor"]
            if anchor["file_sha256"] != record["file_sha256"]:
                raise ValueError("source anchor SHA mismatches paper record")
            if anchor["page"] > record["pages"] or anchor["end"] <= anchor["start"]:
                raise ValueError("source anchor span or page is invalid")
            if anchor["quote"].strip() != item["text"].strip():
                raise ValueError("candidate text differs from quoted evidence")
            if field == "equation_candidates":
                # These are *block* coordinates, not precise glyph bounds. They
                # locate untrusted raw text without claiming formula recognition.
                x0, top, x1, bottom = item["bbox"]
                if not all(math.isfinite(x) for x in (x0, top, x1, bottom)):
                    raise ValueError("candidate coordinates must be finite")
                if not (x0 < x1 and top < bottom):
                    raise ValueError("candidate text-block coordinates are invalid")


def validate_literature_matrix(matrix: Mapping[str, object]) -> None:
    """Validate matrix structure; rows intentionally have no auto-inferred claims."""
    import json

    schema = json.loads(files("emr").joinpath("schemas/literature-matrix.schema.json").read_text())
    Draft202012Validator(schema).validate(matrix)
