"""Immutable data contracts for the research workflow.

The types are intentionally lightweight. Formal JSON validation and mathematical
semantics are future phases; typed records are *not* evidence of correctness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal


class ResearchType(StrEnum):
    """Supported planning branches, not claims of implemented research engines."""

    ANALYTICAL_GAME = "analytical_game"
    STOCHASTIC_OPERATIONS = "stochastic_operations"
    EMPIRICAL_ECONOMETRICS = "empirical_econometrics"
    HYBRID = "hybrid"
    REPLICATION = "replication"


class SolveStatus(StrEnum):
    """Declared mathematical computation state (separate from proof status)."""

    UNRESOLVED = "UNRESOLVED"
    SOLVED_ANALYTICALLY = "SOLVED_ANALYTICALLY"
    SOLVED_NUMERICALLY = "SOLVED_NUMERICALLY"
    MULTIPLE_EQUILIBRIA = "MULTIPLE_EQUILIBRIA"
    INFEASIBLE = "INFEASIBLE"
    RESOURCE_LIMIT = "RESOURCE_LIMIT"


class VerificationStatus(StrEnum):
    """Independent claim verification status."""

    NOT_VERIFIED = "NOT_VERIFIED"
    VERIFIED = "VERIFIED"
    GAP = "GAP"
    ERROR = "ERROR"
    UNRESOLVED = "UNRESOLVED"


class ArtifactStatus(StrEnum):
    """Artifact lifecycle, not a scientific claim about its contents."""

    VALID = "VALID"
    STALE = "STALE"
    REVOKED = "REVOKED"


@dataclass(frozen=True, slots=True)
class ResearchRequest:
    """Untrusted human research request; planning does not execute its text."""

    research_type: ResearchType
    description: str

    def __post_init__(self) -> None:
        if not isinstance(self.research_type, ResearchType):
            raise ValueError("research_type must be a ResearchType")
        if not self.description.strip():
            raise ValueError("description must not be empty")


@dataclass(frozen=True, slots=True)
class ExecutionNode:
    """A *proposed* DAG node; no runner exists in Phase 1."""

    id: str
    skill_name: str
    input_refs: tuple[str, ...] = ()
    output_types: tuple[str, ...] = ()
    deps: tuple[str, ...] = ()
    approval_required: bool = False
    estimated_cost_class: Literal["low", "medium", "high"] = "low"


@dataclass(frozen=True, slots=True)
class ExecutionPlan:
    """Static plan that contains no shell command or executable callback."""

    research_type: ResearchType
    nodes: tuple[ExecutionNode, ...]


@dataclass(frozen=True, slots=True)
class ArtifactRef:
    """Provenance for a single local immutable artifact."""

    uri: str
    sha256: str
    schema_version: str
    created_by: str
    created_at: str


@dataclass(frozen=True, slots=True)
class SolveResult:
    """Candidate solver output; a successful status still needs verification."""

    status: SolveStatus = SolveStatus.UNRESOLVED
    candidate_equilibria: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class VerificationReport:
    """Status and evidence of an independent mathematical review."""

    status: VerificationStatus = VerificationStatus.NOT_VERIFIED
    evidence_refs: tuple[str, ...] = ()
    unverified_obligations: tuple[str, ...] = field(default_factory=tuple)
