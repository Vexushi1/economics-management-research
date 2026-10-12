"""Multiple local starts and residual evidence do NOT certify global optimality."""

import json
from pathlib import Path

import pytest

from emr.adapters.numerical_scipy import (
    evaluate_residuals,
    find_roots,
    optimize_constrained,
    parameter_grid,
)
from emr.adapters.symbolic_sympy import compile_game
from emr.domain.game import validate_game_spec

FILE = Path(__file__).resolve().parents[1] / "fixtures/stackelberg_linear/baseline.json"
VALUES = {"A": 10.0, "a": 1.0, "b": 1.0, "c": 1.0, "gamma": .2, "w": 2.0}


def test_multistart_numerical_returns_local_only_even_for_quadratic():
    game = compile_game(validate_game_spec(json.loads(FILE.read_text())))
    report = optimize_constrained(game, "influencer", ("e",), {**VALUES, "p": 6.0}, ((0.0, 20.0),))
    assert report.status == "LOCAL_CANDIDATES_ONLY"
    assert len(report.starts) >= 3
    assert len(report.candidates) == len(report.starts)
    assert any(c.success and abs(c.position[0] - 4.0) < 1e-4 for c in report.candidates)
    assert evaluate_residuals(game, "influencer", "e", {**VALUES, "p": 6, "e": 4}) < 1e-10
    assert abs(find_roots(game, "influencer", "e", {**VALUES, "p": 6}, ((1.0, 9.0),))[0] - 4) < 1e-10


def test_parameter_grid_is_bounded_and_deterministic():
    grid = parameter_grid({"a": 1}, {"gamma": (0.0, 0.2), "b": (1.0, 2.0)})
    assert len(grid) == 4 and grid[0] == {"a": 1, "gamma": 0.0, "b": 1.0}
    with pytest.raises(ValueError):
        parameter_grid({}, {"x": tuple(range(21))})


def test_numeric_work_limits_reject_unbounded_batch_sizes():
    import pytest
    compiled = compile_game(validate_game_spec(json.loads(FILE.read_text())))
    with pytest.raises(ValueError, match="multi-start budget"):
        optimize_constrained(compiled, "influencer", ("e",), {**VALUES,"p":6},
                             ((0.0, 20.0),), starts=((4.0,),)*11)
    with pytest.raises(ValueError, match="output exceeds budget"):
        parameter_grid({}, {"a": tuple(range(20)), "b": tuple(range(20)), "c": tuple(range(20))})
