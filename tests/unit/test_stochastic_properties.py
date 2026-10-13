"""Generic exact-scenario adversarial invariants, independent of model symbols."""

from random import Random

import pytest

from emr.domain.stochastic import StochasticInputError, check_distribution_support, expected_objective


def test_many_unrelated_game_tables_respect_information_value():
    rng = Random(4121)
    for n in (2, 3, 7, 12):
        for _ in range(16):
            random_payoffs = [[rng.randint(-12, 15) for _ in range(4)] for _ in range(n)]
            # Use valid exact decimal probability distributions.
            cuts = sorted(rng.sample(range(1, 100), n - 1))
            weights = [b-a for a,b in zip([0,*cuts],[*cuts,100],strict=True)]
            raw = {"distribution_type": "finite_joint", "scenarios": [
                {"id": f"scenario_{j}", "probability": f"0.{w:02d}"}
                for j, w in enumerate(weights)
            ], "actions": [f"act_{j}" for j in range(4)],
                "payoffs": random_payoffs, "decision_timing": "before_observation"}
            before = expected_objective(check_distribution_support(raw))
            raw["decision_timing"] = "after_observation"
            after = expected_objective(check_distribution_support(raw))
            assert after.optimal_value >= before.optimal_value
            # Permute columns without changing economic result.
            raw["actions"].reverse()
            for row in raw["payoffs"]:
                row.reverse()
            assert expected_objective(check_distribution_support(raw)).optimal_value == after.optimal_value


def test_unbounded_or_unspecified_integration_not_fabricated():
    raw = {"distribution_type": "continuous", "distribution": "lognormal",
           "actions": ["order"], "decision_timing": "before_observation"}
    with pytest.raises(StochasticInputError):
        check_distribution_support(raw)


def test_invalid_nonfinite_float_rejected():
    raw = {"distribution_type": "finite_joint", "scenarios": [
        {"id": "one", "probability": "1"}], "actions": ["x"], "payoffs": [[float("nan")]],
        "decision_timing": "before_observation"}
    with pytest.raises(StochasticInputError):
        check_distribution_support(raw)
