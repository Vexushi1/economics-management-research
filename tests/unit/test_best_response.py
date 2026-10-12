"""Generic symbolic FOC and *independent* exact constrained quadratic checks."""

import json
from pathlib import Path

import pytest
import sympy as sp

from emr.adapters.symbolic_sympy import compile_game, differentiate, hessian, solve_foc
from emr.domain.equilibrium import best_response
from emr.domain.game import GameSpecValidationError, ValidatedGameSpec, validate_game_spec

FILES = Path(__file__).resolve().parents[1] / "fixtures" / "stackelberg_linear"
VALUES = {"A": "10", "a": "1", "b": "1", "c": "1", "gamma": "0.2", "w": "2"}


def load(name="baseline.json"):
    return validate_game_spec(json.loads((FILES / name).read_text()))


def test_analytic_foc_is_only_candidate_until_global_check():
    compiled = compile_game(load())
    e, p, a, A, b, c = (compiled.symbol(n) for n in ("e", "p", "a", "A", "b", "c"))
    assert solve_foc(compiled, "influencer", "e") == (a * (A - b * p) / c,)
    assert sp.simplify(differentiate(compiled, "influencer", "e") - (a * (A - b*p) - c*e)) == 0
    assert hessian(compiled, "influencer", ("e",)) == sp.Matrix([[-c]])
    actual = best_response(compiled, "influencer", "e", parameters=VALUES, fixed_controls={"p": "6"})
    assert actual.status == "GLOBAL_OPTIMUM_CHECKED"
    assert actual.maximizers == (sp.Integer(4),)
    assert actual.kkt_checks == ("INTERIOR_FOC",)
    assert actual.second_derivative == -1


def test_phase3_data_always_revalidated_before_sympy_conversion():
    broken = load().data
    broken["players"][1]["objective"] = {"op": "call", "name": "__import__", "args": []}
    with pytest.raises(GameSpecValidationError):
        compile_game(ValidatedGameSpec(json.dumps(broken), "static_sequential_game", ()))


def test_strategic_feedback_follower_response_differs_from_baseline():
    compiled = compile_game(load("strategic_feedback.json"))
    a, c, p = (compiled.symbol(n) for n in ("a", "c", "p"))
    assert solve_foc(compiled, "influencer", "e") == (a * p / c,)
