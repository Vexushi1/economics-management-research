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
