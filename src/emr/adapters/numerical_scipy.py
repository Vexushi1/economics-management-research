"""Reproducible multi-start local numerical checks, never a proof of globality.

The callable is derived only from a validated CompiledGame and evaluated via
symbolic replacement, not Python code generation or string interpretation.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import isfinite

import numpy as np
import sympy as sp
from scipy.optimize import brentq, minimize

from emr.adapters.symbolic_sympy import CompiledGame


@dataclass(frozen=True, slots=True)
class LocalCandidate:
    position: tuple[float, ...]
    objective: float
    gradient_residual: float
    success: bool
    message: str


@dataclass(frozen=True, slots=True)
class NumericalReport:
    status: str
    starts: tuple[tuple[float, ...], ...]
    candidates: tuple[LocalCandidate, ...]
    tolerance: float


def _real_float(expr: sp.Expr) -> float:
    value = complex(sp.N(expr, 18))
    if abs(value.imag) > 1e-10 or not np.isfinite(value.real):
        raise ValueError("non-real or non-finite model evaluation")
    return float(value.real)


def _safe_number(raw: object) -> float:
    """Reject strings/objects before any SymPy substitution or SciPy evaluation."""
    if isinstance(raw, bool) or not isinstance(raw, (int, float, sp.Rational, np.floating)):
        raise ValueError("numerical binding must be a number, never expression text")
    try:
        result = float(raw)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError("invalid numerical binding") from exc
    if not isfinite(result):
        raise ValueError("nonfinite numerical binding")
    return result


def optimize_constrained(compiled: CompiledGame, player: str,
                         controls: tuple[str, ...], fixed: Mapping[str, float],
                         bounds: tuple[tuple[float, float], ...], *,
                         starts: tuple[tuple[float, ...], ...] | None = None,
                         tolerance: float = 1e-9) -> NumericalReport:
    """Minimize negative objective over a box from several initial seeds.

    This intentionally does not silently treat cross-variable model constraints
    as simple bounds; callers needing them must use independently checked
    constraint handling. Every result is LOCAL_CANDIDATES_ONLY.
    """
    xs = [compiled.symbol(x) for x in controls]
    verified_bounds = tuple((_safe_number(lo), _safe_number(hi)) for lo, hi in bounds)
    verified_fixed = {name: _safe_number(value) for name, value in fixed.items()}
    tolerance = _safe_number(tolerance)
    if not 0 < tolerance < 1:
        raise ValueError("invalid optimizer tolerance")
    if len(xs) > 5 or not xs or len(xs) != len(verified_bounds) or any(lo >= hi
        for lo, hi in verified_bounds):
        raise ValueError("invalid variable bounds")
    if set(verified_fixed) - set(compiled.symbols) or set(controls) & set(verified_fixed):
        raise ValueError("unknown or overwritten fixed symbol")
    remaining = set(compiled.objectives[player].free_symbols) - set(xs) - {
        compiled.symbol(k) for k in verified_fixed}
    if remaining:
        raise ValueError("missing fixed parameter values")
    f = compiled.objectives[player].subs({compiled.symbol(k): sp.Float(v) for k, v in verified_fixed.items()})
    grad = [sp.diff(f, x) for x in xs]

    def values(point: np.ndarray) -> tuple[float, float]:
        replacement = dict(zip(xs, [sp.Float(float(v)) for v in point], strict=True))
        objective = _real_float(f.subs(replacement))
        g = float(np.linalg.norm([_real_float(d.subs(replacement)) for d in grad]))
        return objective, g

    if starts is None:
        middle = tuple((lo + hi) / 2 for lo, hi in verified_bounds)
        starts = (middle, tuple(lo + .1 * (hi-lo) for lo, hi in verified_bounds),
                  tuple(lo + .9 * (hi-lo) for lo, hi in bounds))
    if len(starts) > 10 or not starts:
        raise ValueError("multi-start budget exceeded")
    reports = []
    for start in starts:
        verified_start = tuple(_safe_number(v) for v in start)
        if len(verified_start) != len(xs) or any(
            not lo <= val <= hi for val, (lo, hi) in zip(verified_start, verified_bounds, strict=True)
        ):
            raise ValueError("invalid optimizer start")
        try:
            result = minimize(lambda p: -values(p)[0], np.asarray(verified_start, dtype=float),
                              bounds=verified_bounds, method="L-BFGS-B", options={"maxiter": 400, "ftol": tolerance})
            objective, g = values(result.x)
            reports.append(LocalCandidate(tuple(map(float, result.x)), objective, g,
                                          bool(result.success), str(result.message)))
        except (ValueError, TypeError, OverflowError) as exc:
            reports.append(LocalCandidate(verified_start, float("nan"),
                                          float("inf"), False, type(exc).__name__))
    return NumericalReport("LOCAL_CANDIDATES_ONLY", starts, tuple(reports), tolerance)


def evaluate_residuals(compiled: CompiledGame, player: str, control: str,
                       bindings: Mapping[str, float]) -> float:
    """FOC residual for a proposed point; boundary optimum may have nonzero FOC."""
    derivative = sp.diff(compiled.objectives[player], compiled.symbol(control))
    checked = {compiled.symbol(k): sp.Float(_safe_number(v)) for k, v in bindings.items()}
    return abs(_real_float(derivative.subs(checked)))


def find_roots(compiled: CompiledGame, player: str, control: str,
               bindings: Mapping[str, float], brackets: tuple[tuple[float, float], ...]) -> tuple[float, ...]:
    """Bracketed numeric FOC roots; they remain stationary candidates only."""
    if not brackets or len(brackets) > 20:
        raise ValueError("root bracket budget exceeded")
    x = compiled.symbol(control)
    checked = {compiled.symbol(k): sp.Float(_safe_number(v)) for k, v in bindings.items()}
    f = sp.diff(compiled.objectives[player], x).subs(checked)
    if f.free_symbols - {x}:
        raise ValueError("missing values for FOC")
    pairs = tuple((_safe_number(lo), _safe_number(hi)) for lo, hi in brackets)
    if any(lo >= hi for lo, hi in pairs):
        raise ValueError("invalid root bracket")
    return tuple(float(brentq(lambda v: _real_float(f.subs(x, sp.Float(v))), lo, hi))
                 for lo, hi in pairs)


def parameter_grid(base: Mapping[str, float], sweeps: Mapping[str, tuple[float, ...]]):
    """Deterministic finite Cartesian grid; caller must validate domain membership."""
    from itertools import product
    if len(sweeps) > 5 or any(not v or len(v) > 20 for v in sweeps.values()):
        raise ValueError("parameter grid exceeds budget")
    length = 1
    for values in sweeps.values():
        length *= len(values)
        if length > 5000:
            raise ValueError("parameter grid output exceeds budget")
    checked_base = {k: _safe_number(v) for k, v in base.items()}
    checked_sweeps = {k: tuple(_safe_number(v) for v in vals) for k, vals in sweeps.items()}
    names = list(checked_sweeps)
    return tuple({**checked_base, **dict(zip(names, values, strict=True))}
                 for values in product(*(checked_sweeps[k] for k in names)))
