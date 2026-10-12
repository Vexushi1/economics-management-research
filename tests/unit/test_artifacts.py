"""Tests local artifact immutability, path safety, and dependency invalidation."""

import hashlib

import pytest

from emr.core.artifacts import ArtifactStore
from emr.core.contracts import ArtifactStatus


def test_write_once_and_digest(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "data")
    artifact = store.write("safe/a.txt", b"research", created_by="unit-test")
    assert artifact.sha256 == hashlib.sha256(b"research").hexdigest()
    assert (tmp_path / "data/safe/a.txt").read_bytes() == b"research"
    with pytest.raises(FileExistsError):
        store.write("safe/a.txt", b"changed", created_by="unit-test")
    assert (tmp_path / "data/safe/a.txt").read_bytes() == b"research"


@pytest.mark.parametrize("relative", ["", "../secret", "safe/../../secret", "/tmp/secret", "."])
def test_traversal_rejected(tmp_path, relative: str) -> None:
    store = ArtifactStore(tmp_path / "data")
    with pytest.raises(ValueError):
        store.write(relative, b"bad", created_by="test")


def test_symlink_escape_rejected(tmp_path) -> None:
    root = tmp_path / "data"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "escape").symlink_to(outside, target_is_directory=True)
    store = ArtifactStore(root)
    with pytest.raises(ValueError):
        store.write("escape/secret", b"bad", created_by="test")
    assert not (outside / "secret").exists()


def test_invalidation_propagates_and_preserves_files(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "repo")
    for name in ("source", "model", "proof", "unrelated"):
        store.write(name, b"data", created_by="test")
    store.add_dependency("source", "model")
    store.add_dependency("model", "proof")
    changed = store.invalidate("source", revoke=True)
    assert changed == frozenset({"source", "model", "proof"})
    assert store.status("source") == ArtifactStatus.REVOKED
    assert store.status("model") == ArtifactStatus.STALE
    assert store.status("proof") == ArtifactStatus.STALE
    assert store.status("unrelated") == ArtifactStatus.VALID
    assert (tmp_path / "repo/source").exists()


def test_dependency_requires_known_endpoints(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "repo")
    with pytest.raises(KeyError):
        store.add_dependency("nonexistent", "other")


def test_dependency_cycle_rejected(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "repo")
    store.write("a", b"a", created_by="test")
    store.write("b", b"b", created_by="test")
    store.add_dependency("a", "b")
    with pytest.raises(ValueError, match="cyclic"):
        store.add_dependency("b", "a")
