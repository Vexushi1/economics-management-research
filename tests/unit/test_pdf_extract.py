"""Offline PDF security and extraction regressions with self-generated documents."""

import hashlib

import pytest

from emr.adapters.pdf_extract import PdfExtractionError, extract_pdf


def test_extract_pdf_candidates_are_unverified(sample_pdf):
    document = extract_pdf(sample_pdf)
    assert document.page_count == 1
    assert document.sha256 == hashlib.sha256(sample_pdf.read_bytes()).hexdigest()
    page = document.pages[0]
    assert page.status == "NOT_VERIFIED"
    assert page.number == 1
    assert "READING_ORDER_NOT_VERIFIED" in page.warnings
    assert any("Proposition 1" in b.text for b in page.blocks)
    assert all(b.status == "NOT_VERIFIED" for b in page.blocks)
    for block in page.blocks:
        x0, top, x1, bottom = block.bbox
        assert 0 <= x0 < x1 <= page.width
        assert 0 <= top < bottom <= page.height


def test_columns_keep_spatial_coordinates_and_uncertain_order(two_column_pdf):
    result = extract_pdf(two_column_pdf)
    page = result.pages[0]
    assert any("Left column" in block.text for block in page.blocks)
    assert any("Right column" in block.text for block in page.blocks)
    left = next(b for b in page.blocks if "Left column" in b.text)
    right = next(b for b in page.blocks if "Right column" in b.text)
    assert left.bbox[0] < right.bbox[0]
    assert "READING_ORDER_NOT_VERIFIED" in page.warnings


def test_no_text_layer_is_explicit(blank_pdf):
    page = extract_pdf(blank_pdf).pages[0]
    assert page.status == "UNREADABLE"
    assert "NO_TEXT_LAYER_OCR_REQUIRED" in page.warnings


@pytest.mark.parametrize("data", [b"", b"%PDF-1.4\ngarbage", b"just text"])
def test_invalid_rejected_without_execution(tmp_path, data):
    path = tmp_path / "bad.pdf"
    path.write_bytes(data)
    with pytest.raises(PdfExtractionError):
        extract_pdf(path)


def test_bytes_budget_enforced_before_parsing(sample_pdf):
    with pytest.raises(PdfExtractionError, match="byte limit"):
        extract_pdf(sample_pdf, max_bytes=20)


def test_upper_budget_cannot_be_bypassed(sample_pdf):
    with pytest.raises(ValueError):
        extract_pdf(sample_pdf, max_pages=10**10)


def test_symlink_rejected(sample_pdf, tmp_path):
    shortcut = tmp_path / "shortcut.pdf"
    shortcut.symlink_to(sample_pdf)
    with pytest.raises(PdfExtractionError):
        extract_pdf(shortcut)


def test_nested_form_fallback_preserves_real_text(nested_figure_pdf):
    page = extract_pdf(nested_figure_pdf).pages[0]
    assert page.status == "NOT_VERIFIED"
    assert any("nested form" in block.text for block in page.blocks)
    assert "PDFMINER_NESTED_FIGURE_FALLBACK" in page.warnings


def test_grid_table_extraction_is_candidate(grid_table_pdf):
    page = extract_pdf(grid_table_pdf).pages[0]
    assert page.tables
    assert all(table.status == "NOT_VERIFIED" for table in page.tables)


def test_password_protected_pdf_rejected(sample_pdf, tmp_path):
    from pypdf import PdfReader, PdfWriter

    writer = PdfWriter()
    writer.append(PdfReader(sample_pdf))
    writer.encrypt("secret")
    path = tmp_path / "protected.pdf"
    with path.open("wb") as stream:
        writer.write(stream)
    with pytest.raises(PdfExtractionError, match="encrypted"):
        extract_pdf(path)
