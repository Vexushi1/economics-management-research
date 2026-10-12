"""Bounded, offline PDF text/layout extraction with conservative evidence status.

The extractors are not security sandboxes: untrusted PDFs should additionally be
handled in an OS-level process sandbox with CPU/RAM/time limits. No embedded PDF
scripts or extracted text are executed. All extracted text is unverified.
"""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass
from pathlib import Path

MAX_PDF_BYTES = 25 * 1024 * 1024
MAX_PAGES = 80
MAX_PAGE_CHARS = 60_000
MAX_DOCUMENT_CHARS = 700_000
MAX_TABLE_CELLS = 2_000


class PdfExtractionError(ValueError):
    """A PDF could not be safely or faithfully extracted."""


@dataclass(frozen=True, slots=True)
class TextBlock:
    """Candidate PDF text, bbox in top-left-origin PDF points; NOT_VERIFIED."""

    page: int
    text: str
    bbox: tuple[float, float, float, float]
    method: str = "pdfminer.six"
    status: str = "NOT_VERIFIED"


@dataclass(frozen=True, slots=True)
class TableCandidate:
    """Heuristically extracted table, never a confirmed data table."""

    page: int
    rows: tuple[tuple[str, ...], ...]
    status: str = "NOT_VERIFIED"


@dataclass(frozen=True, slots=True)
class PdfPage:
    """One-based page with blocks, detected tables, and extraction diagnostics."""

    number: int
    width: float
    height: float
    blocks: tuple[TextBlock, ...]
    tables: tuple[TableCandidate, ...]
    status: str
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PdfDocument:
    """Immutable in-memory extraction. Content is untrusted and unverified."""

    sha256: str
    file_bytes: int
    page_count: int
    pages: tuple[PdfPage, ...]
    title_metadata: str | None = None
    author_metadata: str | None = None


def extract_pdf(path: Path, *, max_bytes: int = MAX_PDF_BYTES, max_pages: int = MAX_PAGES) -> PdfDocument:
    """Extract local PDF only; reject oversize/encrypted/damaged and unsupported PDFs.

    No URLs, shell commands, OCR, arbitrary formula parsers, or external APIs.
    One-based pages and bbox coordinates are consistent with pdfplumber's top-left
    origin. Text order of complex/multi-column layouts remains NOT_VERIFIED.

    Security note: size/page/text budgets limit normal use, NOT PDF parser CPU/
    memory denial-of-service. The caller must provide a process sandbox for
    adversarial PDFs; this adapter makes no claim of hard resource isolation.
    """
    if not (1 <= max_bytes <= MAX_PDF_BYTES and 1 <= max_pages <= MAX_PAGES):
        raise ValueError("extraction budgets cannot exceed audited maximums")
    source = Path(path)
    if source.is_symlink() or not source.is_file():
        raise PdfExtractionError("PDF must be a regular non-symlink local file")
    if source.stat().st_size > max_bytes:
        raise PdfExtractionError("PDF exceeds input byte limit")
    with source.open("rb") as stream:
        data = stream.read(max_bytes + 1)
    if len(data) > max_bytes or not data.startswith(b"%PDF-"):
        raise PdfExtractionError("invalid PDF signature or byte limit")

    # Lazy imports: regular offline research planning doesn't require PDF packages.
    try:
        import pdfplumber
        from pdfminer.high_level import extract_pages
        from pdfminer.layout import LTTextContainer
        from pypdf import PdfReader
    except ImportError as exc:
        raise PdfExtractionError("install the optional pdf extraction dependencies") from exc

    pages: list[PdfPage] = []
    seen_chars = 0
    try:
        reader = PdfReader(io.BytesIO(data), strict=True)
        if reader.is_encrypted:
            raise PdfExtractionError("encrypted PDFs require a separate approved workflow")
        count = len(reader.pages)
        if count == 0 or count > max_pages:
            raise PdfExtractionError("PDF page count outside allowed range")
        title = str(reader.metadata.title) if reader.metadata and reader.metadata.title else None
        author = str(reader.metadata.author) if reader.metadata and reader.metadata.author else None
        # Parse the layout stream once. pdfminer produces PDF bottom-left boxes.
        with pdfplumber.open(io.BytesIO(data)) as document:
            if len(document.pages) != count:
                raise PdfExtractionError("PDF parsers disagree on page count")
            layouts = extract_pages(io.BytesIO(data), maxpages=max_pages)
            for number, (plumber_page, layout) in enumerate(zip(document.pages, layouts, strict=True), 1):
                height = float(layout.height)
                width = float(layout.width)
                blocks: list[TextBlock] = []
                page_chars = 0
                for element in layout:
                    if not isinstance(element, LTTextContainer):
                        continue
                    text = element.get_text().strip()
                    if not text:
                        continue
                    page_chars += len(text)
                    seen_chars += len(text)
                    if page_chars > MAX_PAGE_CHARS or seen_chars > MAX_DOCUMENT_CHARS:
                        raise PdfExtractionError("PDF extracted text exceeds character budget")
                    x0, y0, x1, y1 = element.bbox
                    bbox = (
                        round(float(x0), 2),
                        round(height - float(y1), 2),
                        round(float(x1), 2),
                        round(height - float(y0), 2),
                    )
                    blocks.append(TextBlock(number, text, bbox))
                # Publisher preprints sometimes put all glyphs in nested LTFigure
                # objects. pdfminer returns no LTTextContainer although the page
                # has a text layer. Recover via pdfplumber's character geometry.
                method_warning: list[str] = []
                if not blocks and plumber_page.chars:
                    method_warning.append("PDFMINER_NESTED_FIGURE_FALLBACK")
                    for item in plumber_page.extract_text_lines(return_chars=False):
                        text = str(item.get("text", "")).strip()
                        if not text:
                            continue
                        page_chars += len(text)
                        seen_chars += len(text)
                        if page_chars > MAX_PAGE_CHARS or seen_chars > MAX_DOCUMENT_CHARS:
                            raise PdfExtractionError("PDF extracted text exceeds character budget")
                        bbox = tuple(round(float(item[key]), 2) for key in ("x0", "top", "x1", "bottom"))
                        blocks.append(TextBlock(number, text, bbox, method="pdfplumber"))
                # Sort is for reproducibility, not a promise of accurate multi-column order.
                blocks.sort(key=lambda b: (b.bbox[1], b.bbox[0], b.text))
                candidate_tables: list[TableCandidate] = []
                total_cells = 0
                for table in plumber_page.extract_tables():
                    safe_rows = tuple(tuple("" if v is None else str(v) for v in row) for row in table)
                    total_cells += sum(len(row) for row in safe_rows)
                    if total_cells > MAX_TABLE_CELLS:
                        raise PdfExtractionError("table cell budget exceeded")
                    if safe_rows:
                        candidate_tables.append(TableCandidate(number, safe_rows))
                warnings: list[str] = ["READING_ORDER_NOT_VERIFIED", *method_warning]
                if not blocks:
                    warnings.append("NO_TEXT_LAYER_OCR_REQUIRED")
                pages.append(
                    PdfPage(
                        number=number,
                        width=width,
                        height=height,
                        blocks=tuple(blocks),
                        tables=tuple(candidate_tables),
                        status="UNREADABLE" if not blocks else "NOT_VERIFIED",
                        warnings=tuple(warnings),
                    )
                )
        if len(pages) != count:
            raise PdfExtractionError("PDF layout extraction returned fewer pages")
    except PdfExtractionError:
        raise
    except Exception as exc:
        # Deliberately don't leak source text/path in user-facing errors.
        raise PdfExtractionError("PDF parser failed; damaged or unsupported file") from exc

    return PdfDocument(
        sha256=hashlib.sha256(data).hexdigest(),
        file_bytes=len(data),
        page_count=len(pages),
        pages=tuple(pages),
        title_metadata=title,
        author_metadata=author,
    )
