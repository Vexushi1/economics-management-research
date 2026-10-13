"""Dynamic model preflight and Pontryagin necessary conditions, NOT solving."""

import json
from pathlib import Path

import pytest

from emr.domain.dynamic import (
    DynamicInputError,
    build_optimal_control_tasks,
    check_transversality_requirements,
    validate_state_system,
)

DIR = Path(__file__).resolve().parents[1] / "fixtures/differential_state"


def example():
    return json.loads((DIR / "linear_finite_horizon.json").read_text())


def test_linear_dynamic_generates_valid_costate_necessary_conditions():
    model = validate_state_system(example())
    report = build_optimal_control_tasks(model)
    assert report.status == "NECESSARY_CONDITIONS_ONLY"
    terms = dict(report.conditions)
    # No text is re-interpreted as an expression; trusted construction is checked exactly.
    assert terms["state_derivative"] == "2*u - x/10 + 1"
    assert terms["terminal_costate"] == "3"
    assert "BOX_MAXIMUM_CONDITION_REQUIRED" == terms["control_optimality"]
    assert "NOT_SOLVED" in report.diagnostics


def test_hjb_and_stochastic_differential_game_unsupported_cleanly():
    model = json.loads((DIR / "unsupported_nonlinear_hjb.json").read_text())
    result = build_optimal_control_tasks(validate_state_system(model))
    assert result.status == "UNSUPPORTED"
    assert not result.conditions
    assert "NOT_SOLVED" not in result.diagnostics


def test_missing_initial_and_terminal_data_blocked_not_imputed():
    for key in ("initial_state", "terminal", "running_reward"):
        model = example()
        del model[key]
        assert validate_state_system(model).status == "INCOMPLETE_INPUT"


def test_fixed_terminal_state_needs_target():
    model = example()
    model["terminal"] = {"type": "fixed", "value": "10"}
    result = check_transversality_requirements(validate_state_system(model))
    assert "FIXED_TERMINAL_STATE_COSTATE_NOT_PRESCRIBED" in result.diagnostics
    model["terminal"] = {"type": "fixed"}
    with pytest.raises(DynamicInputError):
        validate_state_system(model)


def test_nonfinite_or_missing_coefficient_rejected():
    for raw in ("__import__('os').system('x')", "1/2", "NaN", "1e9999999"):
        model = example()
        model["drift"]["a"] = raw
        with pytest.raises(DynamicInputError):
            validate_state_system(model)


def test_no_horizon_or_negative_horizon_rejected():
    model = example()
    model["horizon"]["end"] = "-2"
    with pytest.raises(DynamicInputError):
        validate_state_system(model)


def test_fixed_terminal_target_is_preserved_in_necessary_conditions():
    original = example()
    original["terminal"] = {"type": "fixed", "value": "7.5"}
    first = validate_state_system(original)
    first_conditions = dict(build_optimal_control_tasks(first).conditions)
    assert first.terminal_target == 15 / 2
    assert first_conditions["terminal_state"] == "x(end) = 15/2; costate terminal free"
    original["terminal"]["value"] = "8"
    other_conditions = dict(build_optimal_control_tasks(validate_state_system(original)).conditions)
    assert other_conditions["terminal_state"] == "x(end) = 8; costate terminal free"
    assert other_conditions != first_conditions
