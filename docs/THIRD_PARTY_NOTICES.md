# Third-party dependency notice inventory

The project uses distribution versions pinned in `pyproject.toml` and the
Linux CPython 3.12 hash-locked CI dependency file. Key upstream projects used
include jsonschema, pypdf, pdfplumber, pdfminer.six, SymPy, NumPy, SciPy,
cryptography, pytest and Ruff, and their pinned transitive dependencies.

Before a stable publication, collect and verify each installed wheel's current
`METADATA`, `LICENSE`, `NOTICE` and `RECORD` from the offline wheelhouse;
preserve any required full license texts in the distribution. This file is an
**inventory**, not an unsupported claim that all individual terms were audited.
No externally uploaded academic PDF may be committed as a test fixture.
