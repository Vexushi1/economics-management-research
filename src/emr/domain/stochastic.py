"""Finite-scenario, exact stochastic decisions. Timing determines quantifier order.

This is not a generic stochastic program or a continuous-distribution solver.
Every probability, action and payoff must be supplied; missing facts fail closed.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Literal

MAX_INPUT_BYTES = 32_768
MAX_SCENARIOS = 32
MAX_ACTIONS = 32
_DECIMAL = re.compile(r"-?(?:0|[1-9][0-9]{0,9})(?:\.[0-9]{1,9})?\Z")


class StochasticInputError(ValueError):
    """Missing, invalid, or mathematically unsupported finite uncertainty data."""


def _fraction(raw: object) -> Fraction:
    if isinstance(raw, bool) or not isinstance(raw, (str, int)):
        raise StochasticInputError("values must be bounded integer/decimal data, not expressions")
    text = str(raw)
    if not _DECIMAL.fullmatch(text):
        raise StochasticInputError("values must be short finite decimal literals")
    return Fraction(text)


def _bounded_copy(problem: Mapping[str, Any]) -> dict[str, Any]:
    try:
        serialized = json.dumps(problem, allow_nan=False, sort_keys=True)
        if len(serialized.encode("utf-8")) > MAX_INPUT_BYTES:
            raise StochasticInputError("stochastic input exceeds byte budget")
        result = json.loads(serialized)
    except (ValueError, TypeError, OverflowError, RecursionError) as exc:
        raise StochasticInputError("invalid stochastic JSON input") from exc
    if not isinstance(result, dict):
        raise StochasticInputError("stochastic problem must be an object")
    return result


@dataclass(frozen=True, slots=True)
class FiniteProblem:
    """Only exact, fully specified finite support and common action set."""

    scenarios: tuple[str, ...]
    probabilities: tuple[Fraction, ...]
    actions: tuple[str, ...]
    payoffs: tuple[tuple[Fraction, ...], ...]
    decision_timing: Literal["before_observation", "after_observation"]
    truncation_event: tuple[str, ...] | None = None


@dataclass(frozen=True, slots=True)
class ExpectationResult:
    """Exact optimum for a finite table, not an equilibrium or general theorem."""

    status: Literal["FINITE_EXACT_OPTIMUM"]
    objective_order: Literal["MAX_EXPECTATION", "EXPECTATION_OF_MAX"]
    expected_payoff_by_action: tuple[tuple[str, Fraction], ...]
    optimal_value: Fraction
    ex_ante_maximizers: tuple[str, ...]
    contingent_policy: tuple[tuple[str, tuple[str, ...]], ...]
    information_warnings: tuple[str, ...] = ()


def check_distribution_support(data: Mapping[str, Any]) -> FiniteProblem:
    """Validate exact finite support, probabilities, rewards and truncation.

    `truncation_event` conditions a supplied ORIGINAL finite distribution.
    It never guesses an unknown tail. Renormalization is exact and explicit.
    Multiple random sources must be supplied as a *joint* scenario table;
    no independence is silently assumed.
    """
    obj = _bounded_copy(data)
    allowed = {"distribution_type", "scenarios", "actions", "payoffs", "decision_timing", "truncation_event"}
    if set(obj) - allowed or obj.get("distribution_type") != "finite_joint":
        raise StochasticInputError("only explicit finite joint distributions are supported")
    scenarios = obj.get("scenarios")
    actions = obj.get("actions")
    payoffs = obj.get("payoffs")
    timing = obj.get("decision_timing")
    if (not isinstance(scenarios, list) or not 1 <= len(scenarios) <= MAX_SCENARIOS
        or not isinstance(actions, list) or not 1 <= len(actions) <= MAX_ACTIONS):
        raise StochasticInputError("missing or excessive scenarios/actions")
    if any(not isinstance(a, str) or not a or len(a) > 80 for a in actions) or len(set(actions)) != len(actions):
        raise StochasticInputError("invalid or repeated actions")
    names: list[str] = []
    weights: list[Fraction] = []
    for item in scenarios:
        if not isinstance(item, dict) or set(item) != {"id", "probability"}:
            raise StochasticInputError("each joint scenario needs id and explicit probability")
        name = item["id"]
        if not isinstance(name, str) or not name or len(name) > 80:
            raise StochasticInputError("invalid scenario name")
        names.append(name)
        weight = _fraction(item["probability"])
        if not 0 <= weight <= 1:
            raise StochasticInputError("scenario probability outside [0,1]")
        weights.append(weight)
    if len(set(names)) != len(names) or sum(weights, Fraction()) != 1:
        raise StochasticInputError("joint scenarios must be unique and sum exactly to one")
    if not isinstance(payoffs, list) or len(payoffs) != len(scenarios):
        raise StochasticInputError("a payoff row is required for every scenario")
    matrix: list[tuple[Fraction, ...]] = []
    for row in payoffs:
        if not isinstance(row, list) or len(row) != len(actions):
            raise StochasticInputError("every state/action payoff must be supplied")
        matrix.append(tuple(_fraction(value) for value in row))
    if timing not in ("before_observation", "after_observation"):
        raise StochasticInputError("decision time relative to revelation is required")
    event = obj.get("truncation_event")
    if event is not None:
        if (not isinstance(event, list) or not event
            or any(not isinstance(name, str) or name not in names for name in event)
            or len(set(event)) != len(event)):
            raise StochasticInputError("truncation event must name existing joint states")
        selected = [i for i, name in enumerate(names) if name in event]
        mass = sum((weights[i] for i in selected), Fraction())
        if mass <= 0:
            raise StochasticInputError("conditioning event has zero probability")
        names = [names[i] for i in selected]
        matrix = [matrix[i] for i in selected]
        weights = [weights[i] / mass for i in selected]
    return FiniteProblem(tuple(names), tuple(weights), tuple(actions), tuple(matrix), timing,
                         None if event is None else tuple(event))


def validate_information_timing(problem: FiniteProblem) -> None:
    """Reject impossible declarations rather than reinterpreting revelation."""
    if not isinstance(problem, FiniteProblem):
        raise StochasticInputError("validated finite decision problem required")
    if problem.decision_timing not in ("before_observation", "after_observation"):
        raise StochasticInputError("unknown decision timing")
    if (not problem.scenarios or len(problem.probabilities) != len(problem.scenarios)
        or len(set(problem.scenarios)) != len(problem.scenarios)
        or not problem.actions or len(set(problem.actions)) != len(problem.actions)):
        raise StochasticInputError("invalid probability or action support")
    if any(not isinstance(p, Fraction) or p < 0 or p > 1 for p in problem.probabilities):
        raise StochasticInputError("invalid exact probability")
    if any(not isinstance(v, Fraction) for row in problem.payoffs for v in row):
        raise StochasticInputError("non-integrable or inexact finite payoff")
    if sum(problem.probabilities, Fraction()) != 1:
        raise StochasticInputError("probabilities must sum to one")
    if len(problem.payoffs) != len(problem.scenarios) or any(
        len(row) != len(problem.actions) for row in problem.payoffs
    ):
        raise StochasticInputError("incomplete contingent payoff table")


def expected_objective(problem: FiniteProblem) -> ExpectationResult:
    """Place `max` outside or inside expectation per declared information set.

    BEFORE: max_a sum_s p(s)*u(s,a) (one nonanticipative action).
    AFTER: sum_s p(s)*max_a u(s,a) (one action per observed state).
    Both are exact for the *finite* declared action set only.
    """
    validate_information_timing(problem)
    per_action = tuple((action, sum((weight * row[j]
                             for weight, row in zip(problem.probabilities, problem.payoffs, strict=True)),
                            Fraction())) for j, action in enumerate(problem.actions))
    if problem.decision_timing == "before_observation":
        optimal = max(value for _, value in per_action)
        return ExpectationResult("FINITE_EXACT_OPTIMUM", "MAX_EXPECTATION", per_action,
                                 optimal, tuple(a for a, v in per_action if v == optimal), ())
    policy = []
    total = Fraction()
    for name, weight, row in zip(problem.scenarios, problem.probabilities, problem.payoffs, strict=True):
        best = max(row)
        total += weight * best
        policy.append((name, tuple(a for a, v in zip(problem.actions, row, strict=True) if v == best)))
    return ExpectationResult("FINITE_EXACT_OPTIMUM", "EXPECTATION_OF_MAX", per_action,
                             total, (), tuple(policy))
