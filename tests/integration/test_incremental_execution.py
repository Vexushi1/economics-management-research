"""Selective cache and persistent artifact invalidation across model edits."""

from emr.core.artifacts import ArtifactStore
from emr.core.cache import ExecutionCache, fingerprint
from emr.core.contracts import ArtifactStatus


def test_model_edit_invalidates_solver_proof_draft_but_not_source(tmp_path):
    store = ArtifactStore(tmp_path / "artifacts")
    for name in ("source", "model", "solver", "proof", "draft"):
        store.write(name, name.encode(), created_by="synthetic-phase9")
    for before, after in (("source", "model"), ("model", "solver"),
                          ("solver", "proof"), ("proof", "draft")):
        store.add_dependency(before, after)
    previous_source = (tmp_path / "artifacts/source").read_bytes()
    changed = store.invalidate("model")
    assert changed == frozenset({"model", "solver", "proof", "draft"})
    assert store.status("source") == ArtifactStatus.VALID
    assert (tmp_path / "artifacts/source").read_bytes() == previous_source
    for name in ("model", "solver", "proof", "draft"):
        assert store.status(name) == ArtifactStatus.STALE

    cache = ExecutionCache()
    pdf = fingerprint({"bytes": "unchanged synthetic pdf"})
    old = fingerprint({"parameter": "0.2"})
    new = fingerprint({"parameter": "0.3"})
    cache.put("pdf-extraction", "v1", {"page": 1}, {"pdf": pdf})
    cache.put("symbolic-solver", "v1", {"result": "checked"}, {"model": old})
    assert cache.get("pdf-extraction", "v1", {"pdf": pdf})[0] == "HIT"
    assert cache.get("symbolic-solver", "v1", {"model": new})[0] == "STALE"
