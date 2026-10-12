"""An end-to-end local PDF-to-matrix test; no external PDFs or online service."""

import json
from importlib.resources import files

from jsonschema import Draft202012Validator

from emr.adapters.pdf_extract import extract_pdf
from emr.core.papers import literature_matrix, paper_record
from emr.core.provenance import SourceAnchor, anchor_matches


def test_pdf_to_grounded_matrix(sample_pdf):
    doc = extract_pdf(sample_pdf)
    record = paper_record(doc)
    matrix = literature_matrix([record])
    assert record["file_sha256"] == matrix["rows"][0]["file_sha256"]
    for item in record["proposition_candidates"] + record["equation_candidates"]:
        assert anchor_matches(doc, SourceAnchor(**item["anchor"]))
    schema = json.loads(files("emr").joinpath("schemas/literature-matrix.schema.json").read_text())
    Draft202012Validator(schema).validate(matrix)
    assert matrix["rows"][0]["findings"] == []


def test_cli_paper_scan_and_matrix(sample_pdf, tmp_path, capsys):
    from emr.cli import main

    assert main(["paper", "scan", str(sample_pdf)]) == 0
    record = json.loads(capsys.readouterr().out)
    assert record["doi_candidates"] == ["10.1000/test.123"]
    record_path = tmp_path / "paper.json"
    record_path.write_text(json.dumps(record), encoding="utf-8")
    assert main(["paper", "matrix", str(record_path)]) == 0
    matrix = json.loads(capsys.readouterr().out)
    assert len(matrix["rows"]) == 1
    assert matrix["research_gap_status"] == "INSUFFICIENT_EVIDENCE"


def test_cli_matrix_invalid_record_rejected_without_stack_trace(tmp_path, capsys):
    from emr.cli import main

    bad = tmp_path / "bad.json"
    bad.write_text('{"file_sha256":"pretend"}', encoding="utf-8")
    assert main(["paper", "matrix", str(bad)]) == 2
    output = capsys.readouterr()
    assert not output.out
    assert "paper operation failed" in output.err
