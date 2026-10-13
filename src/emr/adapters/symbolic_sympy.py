"""Fail-closed bridge from Phase 3 validated JSON ASTs to exact SymPy objects.

No Python source evaluation, no sympify(str), no parse_expr, no lambdify,
no dynamic imports. Only finite reviewed node constructors are used.
The model is revalidated upon entry (ValidatedGameSpec is not cryptographic).
Symbolic manipulation is bounded to small polynomials in public solve helpers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import sympy as sp

from emr.domain.game import ValidatedGameSpec, validate_game_spec

MAX_POLYNOMIAL_DEGREE = 4


class SymbolicUnsupported(ValueError):
    """An exact expression falls outside the verified symbolic subset."""


@dataclass(frozen=True, slots=True)
class CompiledGame:
    """SymPy expressions *originating only from an audited ModelSpec AST*."""

    model: ValidatedGameSpec
    symbols: dict[str, sp.Symbol]
    objectives: dict[str, sp.Expr]
    constraints: tuple[tuple[str, sp.Expr], ...]

    def symbol(self, name: str) -> sp.Symbol:
        return self.symbols[name]


def _compile_node(node: dict[str, Any], symbols: dict[str, sp.Symbol]) -> sp.Expr:
    """The only AST-to-SymPy constructor; callers cannot supply arbitrary text."""
    op = node["op"]
    if op == "const":
        # Phase 3 already validated strict short decimal grammar and size.
        return sp.Rational(node["value"])
    if op == "symbol":
        return symbols[node["name"]]
    if op == "neg":
        return -_compile_node(node["arg"], symbols)
    if op == "add":
        return sp.Add(*(_compile_node(v, symbols) for v in node["args"]))
    if op == "mul":
        return sp.Mul(*(_compile_node(v, symbols) for v in node["args"]))
    if op == "sub":
        return _compile_node(node["left"], symbols) - _compile_node(node["right"], symbols)
    if op == "div":
        return _compile_node(node["left"], symbols) / _compile_node(node["right"], symbols)
    if op == "pow":
        return _compile_node(node["base"], symbols) ** node["exponent"]
    raise SymbolicUnsupported("operator not in closed DSL")


def compile_game(model: ValidatedGameSpec) -> CompiledGame:
    """Revalidate every model fact before constructing exact symbolic objects."""
    if not isinstance(model, ValidatedGameSpec):
        raise TypeError("only validated Phase 3 model snapshots are accepted")
    checked = validate_game_spec(model.data)
    data = checked.data
    symbols = {row["name"]: sp.Symbol(row["name"], real=True) for row in data["symbols"]}
    objectives = {row["id"]: _compile_node(row["objective"], symbols) for row in data["players"]}
    constraints = tuple((row["relation"], _compile_node(row["lhs"], symbols)
                         - _compile_node(row["rhs"], symbols)) for row in data["constraints"])
    return CompiledGame(checked, symbols, objectives, constraints)


def differentiate(compiled: CompiledGame, player: str, control: str) -> sp.Expr:
    """Differentiate a compiled objective; result is not a verified best response."""
    return sp.diff(compiled.objectives[player], compiled.symbol(control))


def hessian(compiled: CompiledGame, player: str, controls: tuple[str, ...]) -> sp.Matrix:
    """Exact Hessian; definiteness and global optimality require separate checks."""
    xs = [compiled.symbol(x) for x in controls]
    return sp.hessian(compiled.objectives[player], xs)


def solve_foc(compiled: CompiledGame, player: str, control: str) -> tuple[sp.Expr, ...]:
    """Low-degree polynomial stationary *candidates*; never equilibrium labels.

    High-degree and non-polynomial cases are reported as unsupported instead of
    launching unbounded general-purpose equation solvers.
    """
    x = compiled.symbol(control)
    derivative = differentiate(compiled, player, control)
    try:
        poly = sp.Poly(derivative, x)
    except sp.PolynomialError as exc:
        raise SymbolicUnsupported("FOC not a polynomial") from exc
    if poly.degree() > MAX_POLYNOMIAL_DEGREE:
        raise SymbolicUnsupported("FOC degree exceeds audited budget")
    if poly.is_zero:
        return ()  # whole domain stationary; not a unique point
    solutions = sp.solve(poly.as_expr(), x)
    return tuple(sol for sol in solutions if not sol.has(sp.I))


def simplify_identity(lhs: sp.Expr, rhs: sp.Expr) -> bool:
    """Algebraic identity check for expressions made from compiled objects.

    Callers must not convert untrusted strings into Expr via any other path.
    """
    return sp.cancel(lhs - rhs) == 0


def substitute(expr: sp.Expr, replacements: dict[sp.Symbol, sp.Expr]) -> sp.Expr:
    """Simultaneous exact substitution into previously compiled expressions."""
    if not isinstance(expr, sp.Expr) or any(not isinstance(k, sp.Symbol) or
        not isinstance(v, sp.Expr) for k, v in replacements.items()):
        raise TypeError("only internal SymPy expression objects are supported")
    return expr.subs(replacements, simultaneous=True)


def compare_statics(expr: sp.Expr, variable: sp.Symbol,
                    *, assumptions: dict[sp.Symbol, tuple[sp.Expr | None, sp.Expr | None]]
                    | None = None) -> dict[str, object]:
    """Return exact derivative, sign and an explicit *sufficient* domain.

    Never infer a sign from numerical samples. A constant derivative or SymPy
    assumption proof is accepted; otherwise SIGN_INDETERMINATE.
    """
    deriv = sp.factor(sp.diff(expr, variable))
    if deriv.is_zero:
        return {"status": "ZERO", "derivative": deriv, "domain": "declared model domain"}
    if deriv.is_positive is True:
        return {"status": "POSITIVE", "derivative": deriv, "domain": "all real values where defined"}
    if deriv.is_negative is True:
        return {"status": "NEGATIVE", "derivative": deriv, "domain": "all real values where defined"}
    return {"status": "SIGN_INDETERMINATE", "derivative": deriv,
            "domain": assumptions or {}, "proof": "NOT_VERIFIED"}
