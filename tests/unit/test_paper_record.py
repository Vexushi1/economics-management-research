"""Paper records, DOI normalization, and no fabricated publication claims."""

import json
from importlib.resources import files

from jsonschema import Draft202012Validator

from emr.adapters.bibliography import deduplicate_by_doi, lookup_doi, normalize_doi
from emr.adapters.pdf_extract import extract_pdf
from emr.core.papers import literature_matrix, paper_record


def _schema(file: str):
    return json.loads(files("emr").joinpath("schemas", file).read_text(encoding="utf-8"))


def test_paper_record_is_source_anchored_and_schema_valid(sample_pdf):
    doc = extract_pdf(sample_pdf)
    record = paper_record(doc)
    Draft202012Validator(_schema("paper-record.schema.json")).validate(record)
    assert record["doi_candidates"] == ["10.1000/test.123"]
    assert record["evidence_status"] == "NOT_VERIFIED"
    assert record["metadata"]["journal"] is None
    assert record["metadata"]["first_online_year"] is None
    assert record["metadata"]["volume_year"] is None
    assert record["economic_mechanisms"] == []
    assert record["claims"] == []
    assert any("Proposition 1" in p["text"] for p in record["proposition_candidates"])
    assert any("=" in e["text"] for e in record["equation_candidates"])


def test_matrix_does_not_manufacture_findings(sample_pdf):
    record = paper_record(extract_pdf(sample_pdf))
    matrix = literature_matrix([record])
    Draft202012Validator(_schema("literature-matrix.schema.json")).validate(matrix)
    assert matrix["research_gap_status"] == "INSUFFICIENT_EVIDENCE"
    assert matrix["rows"][0]["methods"]["status"] == "UNKNOWN"
    assert matrix["rows"][0]["findings"] == []


def test_doi_dedup_only_when_identifier_exists():
    rows = [
        {"doi": "https://doi.org/10.1000/ABC", "title": "first"},
        {"doi": "doi:10.1000/abc", "title": "second"},
        {"doi": None, "title": "no DOI 1"},
        {"doi": None, "title": "no DOI 2"},
    ]
    assert [r["title"] for r in deduplicate_by_doi(rows)] == ["first", "no DOI 1", "no DOI 2"]
    assert normalize_doi("https://doi.org/10.1000/ABC") == "10.1000/abc"
    assert normalize_doi("none") is None


def test_online_doi_lookup_disabled():
    import pytest

    with pytest.raises(NotImplementedError):
        lookup_doi("10.1000/test")
