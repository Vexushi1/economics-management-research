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
    with pytest.raises(StateValidationError):
        validate_research_state({**base_state(), "updated_at": "2026-02-30T12:00:00Z"})
    assert validate_research_state({**base_state(), "updated_at": "2026-10-12T15:00:00Z"})[
        "updated_at"
    ] == "2026-10-12T15:00:00Z"


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
    hostile = f"__import__('pathlib').Path({str(sentinel)!r}).touch()"
    store = ResearchStateStore(tmp_path)
    store.save("safe.json", {**base_state(), "notes": [hostile]})
    assert not sentinel.exists()
    assert store.load("safe.json")["notes"] == [hostile]


def _artifact(name: str) -> dict[str, str]:
    """Build a valid inert artifact record for dependency tests."""
    return {
        "uri": name,
        "sha256": "a" * 64,
        "schema_version": "1",
        "created_by": "self-review",
        "created_at": "2026-10-12T12:00:00Z",
        "status": "VALID",
    }


def test_valid_dependency_dag_roundtrip(tmp_path):
    state = {
        **base_state(),
        "artifacts": [_artifact(name) for name in ("source", "model", "proof")],
        "artifact_dependencies": [
            {"parent": "source", "child": "model"},
            {"parent": "model", "child": "proof"},
        ],
        "workflow_nodes": [{"id": "read", "skill_name": "paper-reading", "status": "PENDING"}],
    }
    store = ResearchStateStore(tmp_path)
    result = store.save("valid-dag.json", state)
    assert store.load("valid-dag.json", expected_sha256=result.sha256) == state


@pytest.mark.parametrize(
    ("artifacts", "edges", "message"),
    [
        ([], [{"parent": "missing", "child": "orphan"}], "unknown artifact"),
        (["a"], [{"parent": "a", "child": "a"}], "self-referential"),
        (["a", "b"], [{"parent": "a", "child": "b"}, {"parent": "b", "child": "a"}], "cyclic"),
        (["a", "b", "c"], [{"parent": "a", "child": "b"}, {"parent": "b", "child": "c"}, {"parent": "c", "child": "a"}], "cyclic"),
        (["a", "b"], [{"parent": "a", "child": "b"}, {"parent": "a", "child": "b"}], "duplicate artifact dependency"),
    ],
)
def test_invalid_dependency_graph_rejected_before_write(tmp_path, artifacts, edges, message):
    store = ResearchStateStore(tmp_path)
    invalid = {
        **base_state(),
        "artifacts": [_artifact(name) for name in artifacts],
        "artifact_dependencies": edges,
    }
    with pytest.raises(StateValidationError, match=message):
        store.save("invalid.json", invalid)
    assert not (tmp_path / "invalid.json").exists()


def test_duplicate_artifact_id_rejected():
    with pytest.raises(StateValidationError, match="duplicate artifact uri"):
        validate_research_state({**base_state(), "artifacts": [_artifact("a"), _artifact("a")]})


def test_duplicate_workflow_node_id_rejected():
    with pytest.raises(StateValidationError, match="duplicate workflow node id"):
        validate_research_state(
            {
                **base_state(),
                "workflow_nodes": [
                    {"id": "prepare", "skill_name": "planner", "status": "PENDING"},
                    {"id": "prepare", "skill_name": "planner", "status": "READY"},
                ],
            }
        )


def test_tampered_dependency_graph_rejected_during_load(tmp_path):
    store = ResearchStateStore(tmp_path)
    (tmp_path / "bad-graph.json").write_text(
        json.dumps(
            {
                **base_state(),
                "artifacts": [_artifact("a"), _artifact("b")],
                "artifact_dependencies": [
                    {"parent": "a", "child": "b"},
                    {"parent": "b", "child": "a"},
                ],
            }
        )
    )
    with pytest.raises(StateValidationError, match="cyclic"):
        store.load("bad-graph.json")
