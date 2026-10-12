# Reproducible Python 3.12 CI dependencies

`ci.in` contains reviewed direct requirements and build tools. The final
`ci-py312-linux.lock` must be generated on GitHub's Python 3.12 runner with
hashes, committed, and consumed via `pip install --require-hashes`.

A direct-version pin without artifact SHA-256 verification is not considered a
complete CI supply-chain lock. The lock targets Ubuntu 24.04 x86_64 / CPython
3.12, not arbitrary OS/Python combinations. Avoid running `pip-compile` at CI
install time: it would cause silent solver changes between runs.

To install the project after the locked dependency install, use
`python -m pip install --no-deps --no-build-isolation -e .`.
