"""End-to-end static CLI smoke tests; do not invoke any network services."""

import json

from emr.cli import main


def test_cli_inspection_and_validation(capsys) -> None:
    assert main(["inspect"]) == 0
    assert json.loads(capsys.readouterr().out)["mode"] == "phase2-offline-pdf"
    assert main(["validate"]) == 0
    assert json.loads(capsys.readouterr().out)["registry"] == "valid"


def test_cli_plan_prints_static_dag(capsys) -> None:
    assert main(["plan", "--type", "analytical_game", "--description", "A sample problem"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["research_type"] == "analytical_game"
    assert [node["id"] for node in data["nodes"]] == ["intake", "plan"]
