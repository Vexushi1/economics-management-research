"""Checked status requires explicit evidence flags in result contract."""

import json
from importlib.resources import files
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError


def test_equilibrium_schema_is_bundled_and_valid():
    root = Path(__file__).resolve().parents[2]
    disk = (root / "schemas/equilibrium-result.schema.json").read_text()
    bundled = files("emr").joinpath("schemas/equilibrium-result.schema.json").read_text()
    assert disk == bundled
    schema = json.loads(disk)
    Draft202012Validator.check_schema(schema)
    sample = {"schema_version": "1", "model_id": "x", "model_sha256": "a"*64,
              "status": "CANDIDATE_STATIONARY_POINT", "strategies": {},
              "evidence": ["FOC only"], "assumptions": [], "diagnostics": []}
    validator = Draft202012Validator(schema)
    validator.validate(sample)
    with pytest.raises(ValidationError):
        validator.validate({**sample, "status": "EQUILIBRIUM_CHECKED"})
    validator.validate({**sample, "status": "EQUILIBRIUM_CHECKED",
                        "feasibility_checked": True, "global_optimality_checked": True,
                        "verification_scope": "two-stage quadratic restricted class"})
