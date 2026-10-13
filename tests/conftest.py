"""Small synthetic PDFs with deterministic core PDF syntax; no extra fixture deps."""

from __future__ import annotations

from pathlib import Path

import pytest


def _pdf(
    lines: list[tuple[int, int, str]], *, page_count: int = 1, nested_figure: bool = False,
    grid: bool = False,
) -> bytes:
    """Generate minimal one- or multi-page Helvetica PDF using ASCII PDF syntax."""
    objects: list[bytes] = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    kids = " ".join(f"{4 + i * 2} 0 R" for i in range(page_count))
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {page_count} >>".encode())
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    for i in range(page_count):
        page_no = 4 + i * 2
        contents_no = page_no + 1
        xobject = " /XObject << /Fx 6 0 R >>" if nested_figure else ""
        objects.append(
            (f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
             f"/Resources << /Font << /F1 3 0 R >>{xobject} >> "
             f"/Contents {contents_no} 0 R >>").encode()
        )
        commands = []
        for x, y, text in lines:
            text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            commands.append(f"BT /F1 12 Tf 1 0 0 1 {x} {y} Tm ({text}) Tj ET")
        if grid:
            commands.extend([
                "60 600 m 340 600 l S", "60 620 m 340 620 l S",
                "60 640 m 340 640 l S", "60 600 m 60 640 l S",
                "200 600 m 200 640 l S", "340 600 m 340 640 l S",
            ])
        stream = ("\n".join(commands) + "\n").encode("ascii")
        if nested_figure:
            call = b"q /Fx Do Q\n"
            objects.append(f"<< /Length {len(call)} >>\nstream\n".encode() + call + b"endstream")
            objects.append(
                (f"<< /Type /XObject /Subtype /Form /FormType 1 /BBox [0 0 612 792] "
                 f"/Resources << /Font << /F1 3 0 R >> >> /Length {len(stream)} >>\nstream\n").encode()
                + stream + b"endstream"
            )
        else:
            objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"endstream")
    result = b"%PDF-1.4\n"
    offsets = [0]
    for i, obj in enumerate(objects, 1):
        offsets.append(len(result))
        result += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    start = len(result)
    result += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for offset in offsets[1:]:
        result += f"{offset:010d} 00000 n \n".encode()
    result += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{start}\n%%EOF\n"
    ).encode()
    return result


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    path = tmp_path / "study.pdf"
    path.write_bytes(
        _pdf([
            (70, 752, "Live Commerce Strategic Decisions"),
            (70, 719, "1 Introduction"),
            (70, 692, "DOI: 10.1000/TEST.123"),
            (70, 665, "Proposition 1: Profit increases under conditions."),
            (70, 640, "P = a - bQ"),
            (70, 585, "2 Model Setup"),
        ])
    )
    return path


@pytest.fixture
def two_column_pdf(tmp_path: Path) -> Path:
    path = tmp_path / "columns.pdf"
    path.write_bytes(_pdf([(55, 720, "Left column paragraph"), (335, 720, "Right column paragraph"), (55, 690, "3 Equilibrium Analysis")]))
    return path


@pytest.fixture
def blank_pdf(tmp_path: Path) -> Path:
    path = tmp_path / "blank.pdf"
    path.write_bytes(_pdf([]))
    return path


@pytest.fixture
def nested_figure_pdf(tmp_path: Path) -> Path:
    path = tmp_path / "nested.pdf"
    path.write_bytes(_pdf([(60, 720, "Content within nested form"), (60, 680, "Proposition 7")], nested_figure=True))
    return path


@pytest.fixture
def grid_table_pdf(tmp_path: Path) -> Path:
    path = tmp_path / "grid.pdf"
    path.write_bytes(_pdf([(80, 624, "A"), (230, 624, "B"), (80, 603, "1"), (230, 603, "2")], grid=True))
    return path

@pytest.fixture
def phase8_context(sample_pdf):
    """Entirely synthetic source->model->conditional solution->proof ledger."""
    import json

    from emr.adapters.pdf_extract import extract_pdf
    from emr.adapters.symbolic_sympy import compile_game
    from emr.core.evidence_chain import anchor_ref
    from emr.core.provenance import make_anchor
    from emr.domain.game import validate_game_spec
    from emr.domain.proof import (
        ProofLedger,
        audit_proof_step,
        model_fingerprint,
        register_obligation,
    )

    doc = extract_pdf(sample_pdf)
    anchor = make_anchor(doc, 1, 0, 0, 8)
    base = Path(__file__).resolve().parent / 'fixtures/stackelberg_linear/baseline.json'
    raw = json.loads(base.read_text(encoding='utf-8'))
    raw['source'] = {'kind': 'paper_anchor', 'file_sha256': doc.sha256, 'page': 1,
                     'note': 'Synthetic only: semantic correspondence not verified'}
    model = validate_game_spec(raw)
    ledger = ProofLedger()
    ledger.register({
        'schema_version': '1', 'id': 'PropBound', 'statement': 'Conditional follower optimum',
        'author': 'Synthetic author', 'proof_version': 1,
        'model_sha256': model_fingerprint(compile_game(model)),
        'quantifiers': [{'kind': 'forall', 'symbol': 'p'}],
        'parameter_domains': [{'symbol': 'p', 'lower': '2', 'upper': '10',
                               'lower_closed': True, 'upper_closed': True}],
        'assumptions': ['Synthesized fixture, not a verified source theorem'],
        'lemma_refs': [], 'source_refs': [anchor_ref(anchor)],
    })
    register_obligation(ledger, 'PropBound', 1, 'FOC', 'Review complete best-response argument')
    audit_proof_step(ledger, 'PropBound', 1, 's1', 'FOC', 'OK', ('synth:FOC',))
    params = {'A': '10', 'a': '1', 'b': '1', 'c': '1', 'gamma': '0.2', 'w': '2'}
    prose = {'introduction': 'We introduce a synthetic setting.',
             'literature_review': 'An external paper is discussed [CITE:claimA].',
             'conclusion': 'No external economic theorem is claimed.'}
    return doc, anchor, model, params, ledger, prose
