# Reproducible Python 3.12 CI dependencies

`ci.in` contains reviewed direct requirements and build tools. The committed
`ci-py312-linux.lock` was generated on GitHub's Python 3.12 runner with
SHA-256 hashes. CI consumes it via `pip install --require-hashes --only-binary=:all:`
without resolving dependencies.

A direct-version pin without artifact SHA-256 verification is not considered a
complete CI supply-chain lock. The lock targets Ubuntu 24.04 x86_64 / CPython
3.12, not arbitrary OS/Python combinations. Avoid running `pip-compile` at CI
install time: it would cause silent solver changes between runs.

For a reproducible installation matching CI (Ubuntu 24.04 x86_64 / Python 3.12):

```bash
python -m pip install --require-hashes --only-binary=:all: -r requirements/ci-py312-linux.lock
python -m pip install --no-deps --no-build-isolation -e .
```

Versions and hashes restrict the selected distributions but do not replace
package provenance, advisory monitoring, or a complete transitive-license audit.

## Phase 2 PDF optional profile

`requirements/pdf.in` records the three exact direct PDF package versions.
The Phase 2 PR first generates a **temporary hash-locked combined candidate**
from `ci.in` and `pdf.in` in a GitHub runner. Once independently checked, the
resolved lock must be committed and CI switched back to installing the
committed lock only. The final workflow must not regenerate dependencies.
The PDF transitive closure includes Pillow, pypdfium2, charset-normalizer,
cryptography and any of their dependencies. Builds target Ubuntu 24.04 x86_64
and Python 3.12, not arbitrary OS/platform combinations.
Use sandbox process limits for untrusted PDFs.

## Phase 4 SciPy addition

SciPy 1.17.0 is an opt-in `[math]` extra, not needed for offline PDF or
static research planning. `ci-py312-linux.lock` includes SciPy and all
transitive wheels at exact SHA-256 hashes and is used with
`pip install --require-hashes --only-binary=:all:`. The lock is limited to
CPython 3.12 / Ubuntu x86_64; it is not an all-platform SBOM or a guarantee
that upstream releases have no future vulnerabilities. The PR bootstrap
resolution workflow is removed before merge.
