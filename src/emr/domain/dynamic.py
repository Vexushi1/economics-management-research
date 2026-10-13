"""Fail-closed finite-horizon linear dynamics and PMP *necessary conditions*.

No HJB solver, ODE integration of arbitrary expressions, or claims of optimality.
Only bounded numeric linear-affine coefficients enter reviewed constructors.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Literal

import sympy as sp

from emr.domain.stochastic import StochasticInputError, _fraction

MAX_DYNAMIC_BYTES = 16_384


class DynamicInputError(ValueError):
    """A necessary linear control input is missing or internally invalid."""


@dataclass(frozen=True, slots=True)
class DynamicAssessment:
    status: Literal["NECESSARY_CONDITIONS_ONLY", "UNSUPPORTED", "INCOMPLETE_INPUT"]
    classification: str
    conditions: tuple[tuple[str, str], ...] = ()
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class LinearStateSystem:
    horizon: tuple[Fraction, Fraction]
    x_initial: Fraction
    drift: tuple[Fraction, Fraction, Fraction]
    reward: tuple[Fraction, Fraction, Fraction, Fraction, Fraction, Fraction]
    terminal_type: Literal["free", "fixed"]
    terminal_reward: tuple[Fraction, Fraction] | None
    terminal_target: Fraction | None
    control_bounds: tuple[Fraction, Fraction]


def _copy(data: Mapping[str, Any]) -> dict[str, Any]:
    try:
        encoded = json.dumps(data, allow_nan=False, sort_keys=True)
        if len(encoded.encode()) > MAX_DYNAMIC_BYTES:
            raise DynamicInputError("dynamic model exceeds byte budget")
        result = json.loads(encoded)
        if not isinstance(result, dict):
            raise DynamicInputError("dynamic model must be a JSON object")
        return result
    except (TypeError, OverflowError, RecursionError, ValueError) as exc:
        raise DynamicInputError("invalid dynamic JSON data") from exc


def _required_numbers(data: dict[str, Any], keys: tuple[str, ...]) -> tuple[Fraction, ...]:
    if set(data) != set(keys):
        raise DynamicInputError("missing or extra coefficients")
    try:
        return tuple(_fraction(data[key]) for key in keys)
    except StochasticInputError as exc:
        raise DynamicInputError("invalid numeric coefficient") from exc


def validate_state_system(raw: Mapping[str, Any]) -> LinearStateSystem | DynamicAssessment:
    """Filter complexity *before* any symbolic construction.

    Supports deterministic, finite-horizon, scalar linear-affine state equation
    and quadratic running payoff only. Stochastic SDEs, nonlinear HJB, unknown
    transversality, dynamic games and infinite horizons return UNSUPPORTED.
    """
    obj = _copy(raw)
    kind = obj.get("kind")
    if kind is None:
        return DynamicAssessment("INCOMPLETE_INPUT", "unknown", diagnostics=("MISSING_MODEL_CLASSIFICATION",))
    if kind != "deterministic_linear_scalar_control":
        return DynamicAssessment("UNSUPPORTED", str(kind)[:80], diagnostics=(
            "ONLY_FINITE_HORIZON_DETERMINISTIC_LINEAR_SCALAR_SUPPORTED",))
    expected = {"kind", "horizon", "initial_state", "drift", "running_reward", "terminal", "control_bounds"}
    if set(obj) != expected:
        return DynamicAssessment("INCOMPLETE_INPUT", "linear_control", diagnostics=("REQUIRED_MODEL_FACTS_MISSING",))
    try:
        h = obj["horizon"]
        if not isinstance(h, dict):
            raise DynamicInputError("horizon must be a map")
        t0, t1 = _required_numbers(h, ("start", "end"))
        if t1 <= t0 or t1 - t0 > 10_000:
            raise DynamicInputError("finite, positive, bounded horizon required")
        x0 = _fraction(obj["initial_state"])
        drift = _required_numbers(obj["drift"], ("a", "b", "c"))
        reward = _required_numbers(obj["running_reward"],
                                   ("q_xx", "q_x", "q_uu", "q_u", "q_xu", "constant"))
        bounds = obj["control_bounds"]
        if not isinstance(bounds, dict):
            raise DynamicInputError("control bounds must be a map")
        lo, hi = _required_numbers(bounds, ("lower", "upper"))
        if lo >= hi:
            raise DynamicInputError("control interval must have interior")
        terminal = obj["terminal"]
        if not isinstance(terminal, dict) or terminal.get("type") not in ("free", "fixed"):
            raise DynamicInputError("terminal state boundary must be explicit")
        terminal_type = terminal["type"]
        if terminal_type == "fixed":
            if set(terminal) != {"type", "value"}:
                raise DynamicInputError("fixed terminal state requires target")
            terminal_target = _fraction(terminal["value"])
            terminal_reward = None
        else:
            if set(terminal) != {"type", "terminal_reward"} or not isinstance(terminal["terminal_reward"], dict):
                raise DynamicInputError("free endpoint requires terminal reward coefficients")
            terminal_target = None
            terminal_reward = _required_numbers(terminal["terminal_reward"], ("linear", "quadratic"))
        return LinearStateSystem((t0, t1), x0, drift, reward, terminal_type, terminal_reward,
                                 terminal_target, (lo, hi))
    except (StochasticInputError, TypeError, KeyError) as exc:
        raise DynamicInputError("invalid or missing linear control input") from exc


def check_transversality_requirements(model: LinearStateSystem | DynamicAssessment) -> DynamicAssessment:
    """Flag endpoint requirements without fabricating missing co-state values."""
    if isinstance(model, DynamicAssessment):
        return model
    if model.terminal_type == "fixed":
        return DynamicAssessment("NECESSARY_CONDITIONS_ONLY", "linear_control", diagnostics=(
            "FIXED_TERMINAL_STATE_COSTATE_NOT_PRESCRIBED", "NO_OPTIMUM_CERTIFICATE"))
    if model.terminal_reward is None:
        return DynamicAssessment("INCOMPLETE_INPUT", "linear_control", diagnostics=("MISSING_TERMINAL_REWARD",))
    return DynamicAssessment("NECESSARY_CONDITIONS_ONLY", "linear_control", diagnostics=(
        "FREE_ENDPOINT_COSTATE_EQUALS_TERMINAL_REWARD_GRADIENT", "NO_OPTIMUM_CERTIFICATE"))


def build_optimal_control_tasks(model: LinearStateSystem | DynamicAssessment) -> DynamicAssessment:
    """Construct necessary PMP relationships without integrating or optimizing.

    Hamiltonian H = running_reward + lambda*(a*x+b*u+c),
    costate derivative = -dH/dx. Box-constrained controls additionally need
    variational inequality; unconstrained stationarity cannot prove optimality.
    """
    preflight = check_transversality_requirements(model)
    if not isinstance(model, LinearStateSystem) or preflight.status != "NECESSARY_CONDITIONS_ONLY":
        return preflight
    x, u, co = sp.symbols("x u costate", real=True)
    a, b, c = (sp.Rational(z.numerator, z.denominator) for z in model.drift)
    qxx, qx, quu, qu, qxu, constant = (
        sp.Rational(z.numerator, z.denominator) for z in model.reward
    )
    h = qxx*x**2 + qx*x + quu*u**2 + qu*u + qxu*x*u + constant + co*(a*x+b*u+c)
    state = a*x+b*u+c
    conditions = [("state_derivative", str(state)), ("hamiltonian", str(h)),
                  ("costate_derivative", str(-sp.diff(h, x))),
                  ("switching_derivative", str(sp.diff(h, u)))]
    if model.terminal_type == "free":
        linear, quadratic = model.terminal_reward  # type: ignore[misc]
        phi_prime = sp.Rational(linear.numerator, linear.denominator) + (
            2*sp.Rational(quadratic.numerator, quadratic.denominator)*x
        )
        conditions.append(("terminal_costate", str(phi_prime)))
    else:
        if model.terminal_target is None:
            return DynamicAssessment("INCOMPLETE_INPUT", "linear_control", diagnostics=("MISSING_TERMINAL_TARGET",))
        target = sp.Rational(model.terminal_target.numerator, model.terminal_target.denominator)
        conditions.append(("terminal_state", f"x(end) = {target}; costate terminal free"))
    conditions.append(("control_optimality", "BOX_MAXIMUM_CONDITION_REQUIRED"))
    return DynamicAssessment("NECESSARY_CONDITIONS_ONLY", "linear_control",
                             tuple(conditions), preflight.diagnostics + ("NOT_SOLVED",))
