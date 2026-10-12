"""Installed-resource and CLI state-validation regression checks."""

import json

from emr.cli import main
from emr.core.state import ResearchStateStore


def test_cli_schema_validation_after_install(capsys):
    assert main(["validate"]) == 0
    assert json.loads(capsys.readouterr().out)["schema_document"] == "validated"


def test_cli_checks_supplied_state(tmp_path, capsys):
    store = ResearchStateStore(tmp_path)
    store.save("project.json", {"schema_version": "1", "research_type": "replication", "artifacts": []})
    assert main(["validate", "--state", str(tmp_path / "project.json")]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["state"] == "valid"
