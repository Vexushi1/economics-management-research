"""Two independent synthetic Stackelberg cases: exact conditions and numeric check."""

import json
from pathlib import Path

import pytest
import sympy as sp
from scipy.optimize import minimize_scalar

from emr.adapters.symbolic_sympy import compile_game, simplify_identity
from emr.domain.equilibrium import backward_induction_two_stage
from emr.domain.game import GameSpecValidationError, validate_game_spec

HERE = Path(__file__).resolve().parents[1] / "fixtures/stackelberg_linear"
PARAMS = {"A": "10", "a": "1", "b": "1", "c": "1", "gamma": "0.2", "w": "2"}


def model(name):
    return validate_game_spec(json.loads((HERE / name).read_text()))


def independent_numerical_crosscheck(source, outcome):
    compiled = compile_game(source)
    p = compiled.symbol("p")
    e = compiled.symbol("e")
    fixed = {compiled.symbol(k): sp.Rational(v) for k, v in PARAMS.items()}
    profit = sp.cancel(compiled.objectives["retailer"].subs(
        {e: outcome.follower_reaction, **fixed}, simultaneous=True))
    low, high = outcome.leader_report.interval.lower, outcome.leader_report.interval.upper
    optimizer = minimize_scalar(lambda value: -float(profit.subs(p, sp.Float(value))),
                                bounds=(float(low), float(high)), method="bounded",
                                options={"xatol": 1e-10})
    assert optimizer.success
    assert abs(optimizer.x - float(outcome.strategies["p"])) < 1e-5
    return compiled


def test_baseline_stackelberg_has_closed_form_verified_under_assumptions():
    result = backward_induction_two_stage(model("baseline.json"), PARAMS)
    assert result.status == "EQUILIBRIUM_CHECKED"
    assert result.strategies == {"p": sp.Integer(6), "e": sp.Integer(4)}
    assert result.follower_reaction == 10 - sp.Symbol("p", real=True)
    assert result.leader_report.kkt_checks == ("INTERIOR_FOC",)
    assert result.follower_report.kkt_checks == ("INTERIOR_FOC",)
    assert result.leader_report.second_derivative == -sp.Rational(12, 5)
    independent_numerical_crosscheck(model("baseline.json"), result)


def test_strategic_feedback_changes_leader_optimum_and_makes_gamma_relevant():
    source = model("strategic_feedback.json")
    result = backward_induction_two_stage(source, PARAMS)
    assert result.status == "EQUILIBRIUM_CHECKED"
    assert result.strategies == {"p": sp.Rational(29, 4), "e": sp.Rational(29, 4)}
    assert result.leader_report.second_derivative == -sp.Rational(8, 5)
    independent_numerical_crosscheck(source, result)
    absent = backward_induction_two_stage(source, {**PARAMS, "gamma": "0"})
    assert absent.status == "EQUILIBRIUM_CHECKED"
    assert absent.strategies["p"] == 6
    assert result.strategies["p"] != absent.strategies["p"]
    compiled = compile_game(source)
    p = compiled.symbol("p")
    e = compiled.symbol("e")
    # Algebraic identity is independently rebuilt from the *generic* objectives.
    reduced = compiled.objectives["retailer"].subs(e, compiled.symbol("a") * p / compiled.symbol("c"))
    explicit = (p - compiled.symbol("w")) * (
        compiled.symbol("A") - compiled.symbol("b") * p +
        compiled.symbol("gamma") * compiled.symbol("a") * p / compiled.symbol("c"))
    assert simplify_identity(reduced, explicit)


def test_solver_refuses_unproven_more_than_two_stages():
    source = model("baseline.json")
    source_dict = source.data
    source_dict["time"]["stages"] = 3
    # Changes are rejected by Phase 3 schema before reaching the engine.
    with pytest.raises(GameSpecValidationError):
        validate_game_spec(source_dict)


def test_feature_gate_preserves_default_unresolved_state():
    from emr.domain.equilibrium import solve_experimental
    source = model("strategic_feedback.json")
    assert solve_experimental(source, PARAMS).status == "UNRESOLVED"
    assert solve_experimental(source, PARAMS, experimental_solver=True).status == "EQUILIBRIUM_CHECKED"
