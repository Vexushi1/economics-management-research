"""TeX smoke check: absence of a system TeX compiler is SKIP, never PASS."""

import shutil
import subprocess

import pytest

from emr.domain.manuscript import assemble_manuscript


def test_minimal_generated_latex_when_compiler_is_available(phase8_context, tmp_path):
    binary = shutil.which('pdflatex')
    if binary is None:
        pytest.skip('pdflatex not installed; TeX compile not verified')
    doc, anchor, model, params, ledger, prose = phase8_context
    prose['literature_review'] = 'Synthetic placeholder with no bibliography.'
    draft = assemble_manuscript(doc, anchor, model, params, ledger, 'PropBound', 1,
                                prose, ())
    (tmp_path / 'main.tex').write_text(draft.tex, encoding='utf-8')
    completed = subprocess.run([binary, '-no-shell-escape', '-halt-on-error',
                                '-interaction=nonstopmode', 'main.tex'],
                               cwd=tmp_path, capture_output=True, text=True, timeout=20,
                               check=False)
    assert completed.returncode == 0, completed.stdout[-2500:]
    assert (tmp_path / 'main.pdf').is_file()
