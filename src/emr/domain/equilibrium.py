"""Auditable bounded univariate quadratic optimization and two-stage games.

An optimizer is not a proof. Only finite closed/attained linear-feasibility
intervals and degree <=2 objectives can receive a global-optimum certificate.
The two-stage routine additionally checks the follower response for the full
leader strategy range. No hard-coded economic symbols or functional forms.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Mapping

import sympy as sp

from emr.adapters.symbolic_sympy import CompiledGame, compile_game
from emr.domain.game import ValidatedGameSpec


@dataclass(frozen=True, slots=True)
class Interval:
    lower: sp.Rational | None
    upper: sp.Rational | None
    lower_closed: bool = True
    upper_closed: bool = True

    def contains(self, value: sp.Expr) -> bool:
        if not value.is_Rational:
            return False
        if self.lower is not None and (value < self.lower or (value == self.lower and not self.lower_closed)):
            return False
        if self.upper is not None and (value > self.upper or (value == self.upper and not self.upper_closed)):
            return False
        return True

    def intersect(self, other: Interval) -> Interval:
        lo, lc = self.lower, self.lower_closed
        hi, hc = self.upper, self.upper_closed
        if other.lower is not None and (lo is None or other.lower > lo):
            lo, lc = other.lower, other.lower_closed
        elif other.lower is not None and other.lower == lo:
            lc = lc and other.lower_closed
        if other.upper is not None and (hi is None or other.upper < hi):
            hi, hc = other.upper, other.upper_closed
        elif other.upper is not None and other.upper == hi:
            hc = hc and other.upper_closed
        return Interval(lo, hi, lc, hc)

    @property
    def empty(self) -> bool:
        return self.lower is not None and self.upper is not None and (
            self.lower > self.upper or
            (self.lower == self.upper and not (self.lower_closed and self.upper_closed))
        )


@dataclass(frozen=True, slots=True)
class OptimumReport:
    status: str
    maximizers: tuple[sp.Expr, ...]
    interval: Interval | None
    objective_value: sp.Expr | None
    foc_candidates: tuple[sp.Expr, ...]
    kkt_checks: tuple[str, ...]
    second_derivative: sp.Expr | None
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SequentialEquilibrium:
    status: str
    strategies: dict[str, sp.Expr]
    follower_reaction: sp.Expr | None
    leader_report: OptimumReport | None
    follower_report: OptimumReport | None
    diagnostics: tuple[str, ...]


class OptimizationUnsupported(ValueError):
    """The case cannot be certified by the deliberately limited proof engine."""


def _number(value: object) -> sp.Rational:
    """Exact bounded rational number; rejects arbitrary formula strings."""
    if isinstance(value, bool) or not isinstance(value, (str, int, sp.Integer, sp.Rational)):
        raise ValueError("bindings must be exact decimal or rational values")
    if isinstance(value, str) and (len(value) > 32 or not re.fullmatch(r"-?\d{1,12}(?:\.\d{1,8})?", value)):
        raise ValueError("bindings must be bounded decimal literals")
    result = sp.Rational(value)
    if abs(result.p) > 10**14 or result.q > 10**12:
        raise ValueError("exact rational exceeds number budget")
    return result


def _bind_parameters(compiled: CompiledGame, params: Mapping[str, object]) -> dict[sp.Symbol, sp.Rational]:
    declared = {s["name"]: s for s in compiled.model.data["symbols"]}
    required = {k for k, v in declared.items() if v["role"] == "parameter"}
    if set(params) != required:
        raise ValueError("all and only model parameter values must be supplied")
    assignments = {compiled.symbol(k): _number(v) for k, v in params.items()}
    for name, v in declared.items():
        if v["role"] != "parameter":
            continue
        dom = v["domain"]
        lo = _number(dom["lower"]) if dom["lower"] is not None else None
        hi = _number(dom["upper"]) if dom["upper"] is not None else None
        point = assignments[compiled.symbol(name)]
        if not Interval(lo, hi, dom["lower_closed"], dom["upper_closed"]).contains(point):
            raise ValueError("parameter value outside declared domain")
    return assignments


def _control_domain(compiled: CompiledGame, name: str) -> Interval:
    sym = next((v for v in compiled.model.data["symbols"] if v["name"] == name), None)
    if sym is None or sym["role"] != "control":
        raise ValueError("unknown control symbol")
    domain = sym["domain"]
    return Interval(_number(domain["lower"]) if domain["lower"] is not None else None,
                    _number(domain["upper"]) if domain["upper"] is not None else None,
                    domain["lower_closed"], domain["upper_closed"])


def _bound_from_linear(expr: sp.Expr, rel: str, x: sp.Symbol) -> Interval | None:
    """Exact linear feasibility with strict/non-strict bounds; no floating guesses."""
    try:
        poly = sp.Poly(sp.cancel(expr), x)
        if poly.degree() > 1 or poly.free_symbols - {x}:
            raise OptimizationUnsupported("nonlinear or symbolic constraint")
        a = poly.coeff_monomial(x)
        b = poly.coeff_monomial(1)
        if not a.is_Rational or not b.is_Rational:
            raise OptimizationUnsupported("cannot prove constraint coefficient sign")
        if a == 0:
            satisfied = {"ge": b >= 0, "gt": b > 0, "le": b <= 0,
                         "lt": b < 0, "eq": b == 0}[rel]
            return None if satisfied else Interval(sp.Integer(1), sp.Integer(0))
        cutoff = -b / a
        if rel == "eq":
            return Interval(cutoff, cutoff)
        is_lower = (rel in ("ge", "gt")) == (a > 0)
        inclusive = rel in ("ge", "le")
        return Interval(cutoff, None, inclusive, True) if is_lower else Interval(None, cutoff, True, inclusive)
    except sp.PolynomialError as exc:
        raise OptimizationUnsupported("constraint not polynomial") from exc


def feasible_interval(compiled: CompiledGame, control: str,
                      fixed: Mapping[str, object], *,
                      response: tuple[str, sp.Expr] | None = None) -> Interval:
    """Intersect control domain and every affine constraint after substitutions.

    When response is given, restrict also to where another control's response
    stays within its declared domain. This is *not* a general KKT solver.
    """
    x = compiled.symbol(control)
    replacements = {compiled.symbol(k): _number(v) for k, v in fixed.items()}
    if response is not None:
        other, reaction = response
        replacements[compiled.symbol(other)] = reaction
    current = _control_domain(compiled, control)
    for rel, raw in compiled.constraints:
        expr = sp.cancel(raw.subs(replacements, simultaneous=True))
        extra = expr.free_symbols - {x}
        if extra:
            raise OptimizationUnsupported("constraint contains unbound control/parameter")
        bound = _bound_from_linear(expr, rel, x)
        if bound is not None:
            current = current.intersect(bound)
    if response is not None:
        other, reaction = response
        domain = _control_domain(compiled, other)
        if domain.lower is not None:
            interval = _bound_from_linear(reaction - domain.lower,
                "ge" if domain.lower_closed else "gt", x)
            if interval is not None:
                current = current.intersect(interval)
        if domain.upper is not None:
            interval = _bound_from_linear(reaction - domain.upper,
                "le" if domain.upper_closed else "lt", x)
            if interval is not None:
                current = current.intersect(interval)
    return current


def _optimise_polynomial(objective: sp.Expr, x: sp.Symbol, interval: Interval) -> OptimumReport:
    if interval.empty:
        return OptimumReport("INFEASIBLE", (), interval, None, (), (), None)
    try:
        poly = sp.Poly(sp.cancel(objective), x)
    except sp.PolynomialError:
        return OptimumReport("UNRESOLVED", (), interval, None, (), (), None,
                             ("NONPOLYNOMIAL_OBJECTIVE",))
    if poly.free_symbols - {x} or poly.degree() > 2:
        return OptimumReport("CANDIDATE_STATIONARY_POINT", (), interval, None, (), (), None,
                             ("GLOBAL_OPTIMALITY_NOT_ESTABLISHED",))
    first, second = sp.diff(poly.as_expr(), x), sp.diff(poly.as_expr(), x, 2)
    foc = ()
    if not first.is_zero:
        roots = sp.solve(first, x)
        foc = tuple(z for z in roots if z.is_Rational)
    if interval.lower is None or interval.upper is None:
        return OptimumReport("UNRESOLVED", (), interval, None, foc, (), second,
                             ("UNBOUNDED_DOMAIN_REQUIRES_SEPARATE_PROOF",))
    if poly.degree() == 0:
        return OptimumReport("SET_VALUED_BEST_RESPONSE", (), interval, poly.as_expr(), (),
                             ("ALL_FEASIBLE_POINTS_MAXIMIZE",), second)
    candidates = list(foc)
    candidates.extend((interval.lower, interval.upper))
    if not candidates:
        return OptimumReport("UNRESOLVED", (), interval, None, (), (), second)
    # Include open endpoints to detect unattained supremum; filter them from maximizers.
    scores = [(sp.cancel(poly.eval(z)), z) for z in dict.fromkeys(candidates)
              if interval.lower <= z <= interval.upper]
    supremum = max(score for score, _ in scores)
    best = tuple(z for score, z in scores if score == supremum and interval.contains(z))
    if not best:
        return OptimumReport("SUPREMUM_NOT_ATTAINED", (), interval, supremum, foc, (), second)
    kkt = []
    for point in best:
        derivative = sp.cancel(first.subs(x, point))
        if point == interval.lower and point == interval.upper:
            tag = "FIXED_DOMAIN_POINT"
        elif point == interval.lower:
            tag = "LOWER_BOUND_KKT" if derivative <= 0 else "KKT_FAILED"
        elif point == interval.upper:
            tag = "UPPER_BOUND_KKT" if derivative >= 0 else "KKT_FAILED"
        else:
            tag = "INTERIOR_FOC" if derivative == 0 else "FOC_FAILED"
        kkt.append(tag)
    if any(tag in ("KKT_FAILED", "FOC_FAILED") for tag in kkt):
        return OptimumReport("UNRESOLVED", best, interval, supremum, foc, tuple(kkt), second)
    return OptimumReport("GLOBAL_OPTIMUM_CHECKED" if len(best) == 1 else "MULTIPLE_MAXIMIZERS",
                         best, interval, supremum, foc, tuple(kkt), second,
                         ("EXACT_DEGREE_AT_MOST_TWO_ON_AFFINE_FEASIBLE_INTERVAL",))


def best_response(compiled: CompiledGame, player: str, control: str,
                  *, parameters: Mapping[str, object],
                  fixed_controls: Mapping[str, object] | None = None) -> OptimumReport:
    """Exact global report for a restricted 1D constrained optimization problem.

    Never declares a *game equilibrium* based on a single FOC.
    """
    fixed = fixed_controls or {}
    assignments = _bind_parameters(compiled, parameters)
    for key, val in fixed.items():
        if key not in compiled.symbols or key in parameters:
            raise ValueError("unknown fixed control")
        assignments[compiled.symbol(key)] = _number(val)
    expr = sp.cancel(compiled.objectives[player].subs(assignments, simultaneous=True))
    try:
        interval = feasible_interval(compiled, control, dict(parameters) | dict(fixed))
    except OptimizationUnsupported as exc:
        return OptimumReport("UNRESOLVED", (), None, None, (), (), None,
                             (str(exc),))
    if expr.free_symbols - {compiled.symbol(control)}:
        return OptimumReport("UNRESOLVED", (), interval, None, (), (), None,
                             ("UNBOUND_OBJECTIVE_SYMBOL",))
    return _optimise_polynomial(expr, compiled.symbol(control), interval)


def backward_induction_two_stage(model: ValidatedGameSpec,
                                 parameters: Mapping[str, object]) -> SequentialEquilibrium:
    """Verify a narrow but *general* sequential quadratic/affine game subclass.

    Requires one leader and one follower control, follower strictly concave
    quadratic with interior response valid for the *entire* leader feasible
    range; affine constraints and at-most-quadratic reduced leader payoff.
    Otherwise returns UNRESOLVED/SET_VALUED rather than invented equilibrium.
    """
    compiled = compile_game(model)
    data = compiled.model.data
    decisions = sorted(data["decisions"], key=lambda d: d["stage"])
    if len(decisions) != 2 or [d["stage"] for d in decisions] != [1, 2]:
        return SequentialEquilibrium("UNRESOLVED", {}, None, None, None,
                                     ("ONLY_TWO_SINGLE_CONTROL_STAGES_SUPPORTED",))
    first, second = decisions
    l, f = first["symbol"], second["symbol"]
    leader, follower = compiled.symbol(l), compiled.symbol(f)
    bindings = _bind_parameters(compiled, parameters)
    f_objective = sp.cancel(compiled.objectives[second["player"]].subs(bindings))
    try:
        fpoly = sp.Poly(f_objective, follower)
        if fpoly.degree() != 2 or sp.diff(f_objective, follower, 2).free_symbols:
            raise OptimizationUnsupported("follower curvature unverified")
        if sp.diff(f_objective, follower, 2) >= 0:
            raise OptimizationUnsupported("follower not strictly concave")
        sol = sp.solve(sp.diff(f_objective, follower), follower)
        if len(sol) != 1 or sol[0].free_symbols - {leader}:
            raise OptimizationUnsupported("follower stationary point not unique")
        reaction = sp.cancel(sol[0])
        # The leader's full originally feasible range must admit the interior
        # response; restricting to a favorable subrange would be unsound.
        params = {k: str(v) for k, v in parameters.items()}
        raw_interval = feasible_interval(compiled, l, params)
        response_interval = feasible_interval(compiled, l, params, response=(f, reaction))
        if raw_interval != response_interval:
            raise OptimizationUnsupported("follower interior response not valid on whole leader domain")
        reduced = compiled.objectives[first["player"]].subs(
            {follower: reaction, **bindings}, simultaneous=True)
        leader_report = _optimise_polynomial(sp.cancel(reduced), leader, raw_interval)
        if leader_report.status != "GLOBAL_OPTIMUM_CHECKED":
            return SequentialEquilibrium(leader_report.status, {}, reaction,
                                         leader_report, None, ("LEADER_NOT_UNIQUELY_CERTIFIED",))
        l_star = leader_report.maximizers[0]
        f_star = sp.cancel(reaction.subs(leader, l_star))
        follower_report = best_response(compiled, second["player"], f,
                                       parameters=parameters, fixed_controls={l: l_star})
        if (follower_report.status != "GLOBAL_OPTIMUM_CHECKED" or
            follower_report.maximizers != (f_star,)):
            return SequentialEquilibrium("UNRESOLVED", {}, reaction, leader_report,
                                         follower_report, ("FOLLOWER_OPTIMALITY_NOT_CERTIFIED",))
        return SequentialEquilibrium("EQUILIBRIUM_CHECKED", {l: l_star, f: f_star},
                                     reaction, leader_report, follower_report,
                                     ("TWO_STAGE_STRICT_CONCAVE_FOLLOWER_AND_QUADRATIC_LEADER",
                                      "FEASIBILITY_AND_KKT_CHECKED_ON_FULL_LEADER_INTERVAL"))
    except (OptimizationUnsupported, sp.PolynomialError, ValueError, TypeError) as exc:
        return SequentialEquilibrium("UNRESOLVED", {}, None, None, None, (str(exc),))


def solve_experimental(model: ValidatedGameSpec, parameters: Mapping[str, object], *,
                       experimental_solver: bool = False) -> SequentialEquilibrium:
    """Feature gate for the limited checked two-stage engine; default is disabled."""
    if not experimental_solver:
        return SequentialEquilibrium("UNRESOLVED", {}, None, None, None,
                                     ("EXPERIMENTAL_SOLVER_DISABLED",))
    return backward_induction_two_stage(model, parameters)
