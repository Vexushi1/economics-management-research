"""Offline adversarial limits, including paths, PDF bytes and manuscript injection."""

import pytest

from emr.adapters.pdf_extract import PdfExtractionError, extract_pdf
from emr.core.artifacts import ArtifactStore
from emr.domain.manuscript import tex_escape


def test_path_escape_and_symlink_cannot_write_outside_artifact_root(tmp_path):
    root = tmp_path / "approved"
    store = ArtifactStore(root)
    outside = tmp_path / "external"
    outside.mkdir()
    (root / "redirect").symlink_to(outside, target_is_directory=True)
    for name in ("../external/private", "redirect/private", "/tmp/private"):
        with pytest.raises(ValueError):
            store.write(name, b"could-be-sensitive", created_by="adversarial-test")
    assert list(outside.iterdir()) == []


def test_pdf_embedded_script_bytes_remain_untrusted_and_invalid_input_stops(tmp_path):
    suspect = tmp_path / "attack.pdf"
    suspect.write_bytes(b'%PDF-1.4\n<< /JavaScript (os.system("exit")) >>')
    with pytest.raises(PdfExtractionError):
        extract_pdf(suspect)
    assert suspect.read_bytes().startswith(b"%PDF-1.4")


def test_llm_prose_with_latex_shell_or_file_input_is_inert_text():
    payload = r"\input{/private/secret} \write18{curl example.invalid} \renewcommand{\EMREquilibrium}{forged}"
    escaped = tex_escape(payload)
    assert r"\input{" not in escaped
    assert r"\write18{" not in escaped
    assert r"\renewcommand{" not in escaped
    assert escaped.count(r"\textbackslash{}") >= 3
