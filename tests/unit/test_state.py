"""Schema, persistence and integrity security regression tests."""

import hashlib
import json

import pytest

from emr.core.state import (
    MAX_STATE_BYTES,
    ResearchStateStore,
    StateValidationError,
    validate_research_state,
)


def base_state():
    return {"schema_version": "1", "research_type": "analytical_game", "artifacts": []}


def test_roundtrip_and_integrity(tmp_path):
    store = ResearchStateStore(tmp_path / "states")
    state = {**base_state(), "research_id": "demo-1", "revision": 0, "notes": ["Not a proof"]}
    snap = store.save("demo/0000.json", state)
    assert len(snap.sha256) == 64
    assert store.load(snap.name, expected_sha256=snap.sha256) == state
    assert hashlib.sha256((tmp_path / "states/demo/0000.json").read_bytes()).hexdigest() == snap.sha256


def test_write_once_creates_versions(tmp_path):
    store = ResearchStateStore(tmp_path)
    store.save("v0.json", base_state())
    with pytest.raises(FileExistsError):
        store.save("v0.json", base_state())
    second = {**base_state(), "revision": 1}
    store.save("v1.json", second)
    assert store.load("v1.json")["revision"] == 1


@pytest.mark.parametrize("name", ["", "../outside.json", "/tmp/a.json", ".", "a.txt"])
def test_path_restrictions(tmp_path, name):
    store = ResearchStateStore(tmp_path / "state")
    with pytest.raises(ValueError):
        store.save(name, base_state())


def test_symlink_escape_rejected(tmp_path):
    root, outside = tmp_path / "root", tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / "escape").symlink_to(outside, target_is_directory=True)
    store = ResearchStateStore(root)
    with pytest.raises(ValueError):
        store.save("escape/example.json", base_state())


def test_unknown_field_invalid(tmp_path):
    state = {**base_state(), "arbitrary": "no"}
    with pytest.raises(StateValidationError):
        ResearchStateStore(tmp_path).save("bad.json", state)
    assert not (tmp_path / "bad.json").exists()


def test_enum_and_format_rejected():
    with pytest.raises(StateValidationError):
        validate_research_state({**base_state(), "research_type": "bogus"})
    with pytest.raises(StateValidationError):
        validate_research_state({**base_state(), "updated_at": "tomorrow sometime"})


def test_duplicate_json_keys_and_nan_rejected(tmp_path):
    store = ResearchStateStore(tmp_path)
    (tmp_path / "duplicate.json").write_text(
        '{"schema_version":"1","schema_version":"1","research_type":"analytical_game","artifacts":[]}'
    )
    with pytest.raises(StateValidationError, match="duplicate"):
        store.load("duplicate.json")
    (tmp_path / "badnumber.json").write_text(
        '{"schema_version":"1","research_type":"analytical_game","artifacts":[],"revision":NaN}'
    )
    with pytest.raises(StateValidationError):
        store.load("badnumber.json")


def test_checksum_detects_tampering(tmp_path):
    store = ResearchStateStore(tmp_path)
    snap = store.save("valid.json", base_state())
    (tmp_path / "valid.json").write_text(json.dumps({**base_state(), "revision": 42}))
    with pytest.raises(StateValidationError, match="SHA-256 mismatch"):
        store.load("valid.json", expected_sha256=snap.sha256)


def test_oversize_rejected_without_disk_side_effect(tmp_path):
    store = ResearchStateStore(tmp_path)
    too_big = {**base_state(), "notes": ["x" * MAX_STATE_BYTES]}
    with pytest.raises(StateValidationError):
        store.save("oversize.json", too_big)
    assert not (tmp_path / "oversize.json").exists()


def test_malicious_text_is_inert(tmp_path):
    sentinel = tmp_path / "pwned"
    hostile = "__import__('pathlib').Path(%r).touch()" % str(sentinel)
    store = ResearchStateStore(tmp_path)
    store.save("safe.json", {**base_state(), "notes": [hostile]})
    assert not sentinel.exists()
    assert store.load("safe.json")["notes"] == [hostile]
