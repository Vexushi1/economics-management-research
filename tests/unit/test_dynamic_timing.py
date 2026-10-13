"""Two identical joint stochastic payoffs, differing *only* in observation time."""

import copy
import json
from fractions import Fraction
from pathlib import Path

import pytest

from emr.domain.stochastic import (
    StochasticInputError,
    check_distribution_support,
    expected_objective,
)

FILE = Path(__file__).resolve().parents[1] / "fixtures/stochastic_supply/two_state.json"


def test_max_expectation_is_not_expectation_of_max():
    raw = json.loads(FILE.read_text())
    first = expected_objective(check_distribution_support(raw))
    moved = copy.deepcopy(raw)
    moved["decision_timing"] = "after_observation"
    second = expected_objective(check_distribution_support(moved))
    # State payoffs and probabilities are identical in both tests.
    assert first.objective_order == "MAX_EXPECTATION"
    assert second.objective_order == "EXPECTATION_OF_MAX"
    # E[aggressive] = .25*(-4) + .75*12 = 8; E[conservative] = 2 + .75 = 2.75
    assert first.optimal_value == Fraction(8)
    assert first.ex_ante_maximizers == ("aggressive",)
    # .25*max(8,-4) + .75*max(1,12) = 11
    assert second.optimal_value == Fraction(11)
    assert second.contingent_policy == (
        ("low_supply", ("conservative",)), ("high_supply", ("aggressive",)))
    assert second.optimal_value > first.optimal_value


def test_explicit_conditioning_on_positive_mass():
    raw = json.loads((FILE.parent / "conditioned.json").read_text())
    validated = check_distribution_support(raw)
    assert validated.scenarios == ("s1", "s2")
    assert validated.probabilities == (Fraction(2, 5), Fraction(3, 5))
    assert expected_objective(validated).optimal_value == Fraction(6)


@pytest.mark.parametrize("change", [
    lambda x: x["scenarios"].pop(),
    lambda x: x["scenarios"][0].update(probability="1.1"),
    lambda x: x["scenarios"][0].update(probability="1/4"),
    lambda x: x["payoffs"][0].pop(),
    lambda x: x.update(decision_timing="predict_as_if_known"),
    lambda x: x.update(distribution_type="normal_unknown_tails"),
    lambda x: x.update(independent=True),
    lambda x: x["payoffs"][0].__setitem__(0,"NaN"),
])
def test_incomplete_or_unproven_probability_assumption_fails(change):
    raw = json.loads(FILE.read_text())
    change(raw)
    with pytest.raises(StochasticInputError):
        check_distribution_support(raw)


def test_zero_probability_conditioning_rejected():
    raw = json.loads(FILE.read_text())
    raw["scenarios"][0]["probability"] = "0"
    raw["scenarios"][1]["probability"] = "1"
    raw["truncation_event"] = ["low_supply"]
    with pytest.raises(StochasticInputError, match="zero probability"):
        check_distribution_support(raw)


def test_malformed_truncation_identifier_fails_with_domain_error():
    raw = json.loads(FILE.read_text())
    raw["truncation_event"] = [{"untrusted": "object"}]
    with pytest.raises(StochasticInputError):
        check_distribution_support(raw)
