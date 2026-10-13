"""Falsification tests: boundary, unattained maximum, set-valued and infeasible."""

import json
from pathlib import Path

import sympy as sp

from emr.adapters.symbolic_sympy import compile_game
from emr.domain.equilibrium import best_response
from emr.domain.game import validate_game_spec

FILE = Path(__file__).resolve().parents[1] / "fixtures/stackelberg_linear/baseline.json"
PARAMS = {"A": "10", "a": "1", "b": "1", "c": "1", "gamma": "0.2", "w": "2"}


def test_boundary_beats_infeasible_interior_stationary():
    model = json.loads(FILE.read_text())
    # f(e)=-(e+1)^2 -> stationary e=-1 is infeasible; maximizer e=0.
    e = {"op": "symbol", "name": "e"}
    model["players"][1]["objective"] = {"op": "neg", "arg": {"op": "pow",
        "base": {"op": "add", "args": [e, {"op": "const", "value": "1"}]}, "exponent": 2}}
    result = best_response(compile_game(validate_game_spec(model)), "influencer", "e",
                           parameters=PARAMS, fixed_controls={"p": "6"})
    assert result.status == "GLOBAL_OPTIMUM_CHECKED"
    assert result.maximizers == (0,)
    assert result.foc_candidates == (-1,)
    assert result.kkt_checks == ("LOWER_BOUND_KKT",)


def test_set_valued_best_response_is_not_reported_unique():
    model = json.loads(FILE.read_text())
    model["players"][1]["objective"] = {"op": "const", "value": "1"}
    report = best_response(compile_game(validate_game_spec(model)), "influencer", "e",
                           parameters=PARAMS, fixed_controls={"p": "6"})
    assert report.status == "SET_VALUED_BEST_RESPONSE"
    assert not report.maximizers


def test_upper_boundary_kkt():
    model = json.loads(FILE.read_text())
    model["symbols"][-1]["domain"]["upper"] = "8"
    model["symbols"][-1]["domain"]["upper_closed"] = True
    model["players"][1]["objective"] = {"op": "symbol", "name": "e"}
    report = best_response(compile_game(validate_game_spec(model)), "influencer", "e",
                           parameters=PARAMS, fixed_controls={"p": "6"})
    assert report.maximizers == (8,)
    assert report.kkt_checks == ("UPPER_BOUND_KKT",)


def test_open_upper_bound_supremum_not_attained():
    model = json.loads(FILE.read_text())
    model["symbols"][-1]["domain"]["upper"] = "8"
    model["symbols"][-1]["domain"]["upper_closed"] = False
    model["players"][1]["objective"] = {"op": "symbol", "name": "e"}
    report = best_response(compile_game(validate_game_spec(model)), "influencer", "e",
                           parameters=PARAMS, fixed_controls={"p": "6"})
    assert report.status == "SUPREMUM_NOT_ATTAINED"
    assert report.maximizers == ()


def test_infeasible_conflicting_constraints():
    model = json.loads(FILE.read_text())
    e = {"op": "symbol", "name": "e"}
    for relation, amount in (("ge", "5"), ("le", "3")):
        model["constraints"].append({"id": "extra"+relation, "lhs": e,
            "relation": relation, "rhs": {"op": "const", "value": amount}})
    report = best_response(compile_game(validate_game_spec(model)), "influencer", "e",
                           parameters=PARAMS, fixed_controls={"p": "6"})
    assert report.status == "INFEASIBLE"


def test_nonlinear_objective_fails_closed_without_global_label():
    model = json.loads(FILE.read_text())
    model["players"][1]["objective"] = {"op": "pow", "base": {"op": "symbol", "name": "e"}, "exponent": 3}
    result = best_response(compile_game(validate_game_spec(model)), "influencer", "e",
                           parameters=PARAMS, fixed_controls={"p": "6"})
    assert result.status == "CANDIDATE_STATIONARY_POINT"
    assert result.maximizers == ()


def test_two_equal_boundary_maxima_report_multiple_not_unique():
    model = json.loads(FILE.read_text())
    model["symbols"][-1]["domain"].update({"upper": "8", "upper_closed": True})
    e = {"op": "symbol", "name": "e"}
    model["players"][1]["objective"] = {"op": "pow", "base": {
        "op": "sub", "left": e, "right": {"op": "const", "value": "4"}}, "exponent": 2}
    result = best_response(compile_game(validate_game_spec(model)), "influencer", "e",
                           parameters=PARAMS, fixed_controls={"p": "6"})
    assert result.status == "MULTIPLE_MAXIMIZERS"
    assert result.maximizers == (sp.Integer(0), sp.Integer(8)) or result.maximizers == (sp.Integer(8), sp.Integer(0))
    assert set(result.kkt_checks) == {"LOWER_BOUND_KKT", "UPPER_BOUND_KKT"}
