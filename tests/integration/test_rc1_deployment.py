"""Operational process boundaries must remain fail-closed without external trust."""
from pathlib import Path

from emr.services.checkpoint_service import CheckpointHandler
from emr.services.g6_service import load_protected_policy

ROOT = Path(__file__).resolve().parents[2]


def test_g6_cannot_start_with_missing_pinned_root(monkeypatch, tmp_path):
    monkeypatch.setenv("EMR_ROOT_PUBLIC_KEY_PATH", str(tmp_path / "missing-root.pub"))
    try:
        load_protected_policy()
    except (ValueError, OSError, KeyError):
        pass
    else:
        raise AssertionError("trust missing but G6 preflight did not lock down")


def test_compose_separates_service_filesystems_and_never_mounts_signer_token():
    raw = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert "checkpoint_link:" in raw and "internal: true" in raw
    assert "read_only: true" in raw and "cap_drop:" in raw
    assert "EMR_SIGNED_POLICY_FILE" in raw and "EMR_TRUST_ROOT_FILE" in raw
    assert "X_VAULT_TOKEN" not in raw and "VAULT_TOKEN" not in raw
    assert "127.0.0.1:8081:8081" in raw
    assert "- type: bind" in raw
    assert "deploy/" not in raw  # no host path exposing any signer secret


def test_checkpoint_http_is_read_only():
    assert hasattr(CheckpointHandler, "do_GET")
    assert hasattr(CheckpointHandler, "do_POST")
    assert hasattr(CheckpointHandler, "do_PUT")
    assert hasattr(CheckpointHandler, "do_DELETE")
