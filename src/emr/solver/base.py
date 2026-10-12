"""Clean-room mathematical solver *interfaces*, not numerical implementations.

The model is a structured statement of players/timing. Formula strings are
inert and must never be passed to eval/exec/unguarded sympify/parse_expr.
Future implementations require an audited AST/DSL parser, feasibility checks,
backward-induction semantics and independent residual/proof verification.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from emr.core.contracts import SolveResult, VerificationReport


@dataclass(frozen=True, slots=True)
class ModelSpec:
    """Minimal safe, inert model descriptor; not a mathematical expression parser.

    Players and decision timing are deliberately explicit. A future model
    schema will add typed objective functions, domains, information sets,
    constraints and model versions before any mathematical solver is enabled.
    """

    model_id: str
    players: tuple[str, ...]
    decision_sequence: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.model_id.strip():
            raise ValueError("model_id is required")
        if not self.players or not all(player.strip() for player in self.players):
            raise ValueError("at least one nonempty player is required")
        if not self.decision_sequence or not all(self.decision_sequence):
            raise ValueError("decision_sequence is required")


class BaseEquilibriumSolver(ABC):
    """Contract for future analytical, numerical or hybrid game solvers.

    `solve` must respect decision sequence, strategy sets and constraints.
    An FOC alone does not establish a best response or valid equilibrium.
    `verify` must assess feasibility, objective optimality, boundary cases,
    and the appropriate equilibrium concept. Proof is a separate obligation.
    """

    @abstractmethod
    def solve(self, model: ModelSpec) -> SolveResult:
        """Return candidate equilibria, assumptions and diagnostics."""

    @abstractmethod
    def verify(self, model: ModelSpec, result: SolveResult) -> VerificationReport:
        """Independently validate a proposed result; never silently infer proof."""


class PendingEquilibriumSolver(BaseEquilibriumSolver):
    """Explicit placeholder that refuses to fabricate equilibrium results."""

    def solve(self, model: ModelSpec) -> SolveResult:
        """Not implemented in Phase 1; no expression is evaluated."""
        raise NotImplementedError("Equilibrium solving belongs to a later phase")

    def verify(self, model: ModelSpec, result: SolveResult) -> VerificationReport:
        """Not implemented in Phase 1; verification is not inferred."""
        raise NotImplementedError("Independent verification belongs to a later phase")
