"""Optional, inert empirical research design and identification preflight.

Methods and asserted assumptions are not causal identification certificates.
No data loading, estimating, code evaluation or automatic causal assertions.
The theoretical workflow can operate without this module or real data.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

MAX_DESIGN_BYTES = 32_768
_ID = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,63}\Z")
_REQUIRED = {
    "did": frozenset({"parallel_trends", "no_anticipation", "no_spillovers", "common_support"}),
    "iv": frozenset({"relevance", "exclusion_restriction", "as_if_random", "monotonicity"}),
    "panel_fe": frozenset({"strict_exogeneity", "stable_unit_mapping", "no_perfect_collinearity"}),
    "randomized": frozenset({"random_assignment", "no_interference", "consistency"}),
}
_ALLOWED_ESTIMANDS = {
    "did": {"ATT"}, "iv": {"LATE"}, "panel_fe": {"ATE", "ATT"},
    "randomized": {"ATE", "ITT"}, "descriptive": {"ASSOCIATION"},
    "predictive": {"PREDICTION"},
}


class EmpiricalDesignError(ValueError):
    """A requested empirical claim is unsupported or structurally incomplete."""


@dataclass(frozen=True, slots=True)
class ValidatedEmpiricalDesign:
    """Detached and bounded JSON snapshot, with no claims of identification."""

    _payload: str

    @property
    def data(self) -> dict[str, Any]:
        return json.loads(self._payload)


@dataclass(frozen=True, slots=True)
class EmpiricalAssessment:
    status: Literal["ASSOCIATION_ONLY", "PREDICTION_ONLY", "IDENTIFICATION_INCOMPLETE",
                    "ASSUMPTIONS_DOCUMENTED_NOT_VERIFIED"]
    severity: Literal["INFO", "WARNING", "CRITICAL"]
    missing_assumptions: tuple[str, ...]
    declared_assumptions: tuple[str, ...]
    causal_claim_allowed: Literal[False] = False


@dataclass(frozen=True, slots=True)
class EstimandRecord:
    name: str
    outcome: str
    treatment: str
    population: str
    status: Literal["DEFINED_NOT_ESTIMATED"] = "DEFINED_NOT_ESTIMATED"


def _snapshot(raw: Mapping[str, Any]) -> str:
    if not isinstance(raw, Mapping):
        raise EmpiricalDesignError("design must be structured JSON")
    try:
        result = json.dumps(raw, ensure_ascii=False, allow_nan=False, sort_keys=True)
    except (TypeError, ValueError, OverflowError, RecursionError) as exc:
        raise EmpiricalDesignError("invalid JSON design") from exc
    if len(result.encode("utf-8")) > MAX_DESIGN_BYTES:
        raise EmpiricalDesignError("empirical design exceeds size budget")
    return result


def _string(value: Any, *, identifier: bool = False) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= 256 and (
        not identifier or bool(_ID.fullmatch(value))
    )


def validate_design(raw: Mapping[str, Any]) -> ValidatedEmpiricalDesign:
    """Validate a data-free design contract, including chosen estimand and scope.

    Identification assumptions may be missing: their absence is carried as a
    critical downstream diagnostic, never filled in automatically.
    """
    payload = _snapshot(raw)
    obj = json.loads(payload)
    keys = {"design_version", "study_id", "method", "intent", "data_structure", "outcome",
            "treatment", "target_population", "estimand", "assumptions", "source_refs"}
    if set(obj) != keys or obj["design_version"] != "1":
        raise EmpiricalDesignError("design fields must be exact and versioned")
    method = obj["method"]
    if method not in _ALLOWED_ESTIMANDS or obj["estimand"] not in _ALLOWED_ESTIMANDS[method]:
        raise EmpiricalDesignError("method and estimand mismatch")
    if obj["intent"] not in ("causal", "association", "prediction"):
        raise EmpiricalDesignError("research intent must be explicit")
    if (method == "predictive" and obj["intent"] != "prediction" or
        method == "descriptive" and obj["intent"] != "association" or
        method in _REQUIRED and obj["intent"] != "causal"):
        raise EmpiricalDesignError("intent cannot be rebranded as a different method")
    if obj["data_structure"] not in ("cross_section", "panel", "experiment"):
        raise EmpiricalDesignError("unknown empirical data structure")
    if (method in ("did", "panel_fe") and obj["data_structure"] != "panel" or
        method == "randomized" and obj["data_structure"] != "experiment"):
        raise EmpiricalDesignError("empirical method incompatible with data structure")
    if not all(_string(obj[name], identifier=(name in ("study_id", "outcome", "treatment")))
               for name in ("study_id", "outcome", "treatment", "target_population")):
        raise EmpiricalDesignError("study scope or variable names invalid")
    assumptions, refs = obj["assumptions"], obj["source_refs"]
    if not isinstance(assumptions, list) or len(assumptions) > 32:
        raise EmpiricalDesignError("invalid assumption collection")
    if not isinstance(refs, list) or len(refs) > 64 or any(
        not _string(ref) for ref in refs
    ) or len(set(refs)) != len(refs):
        raise EmpiricalDesignError("invalid or duplicated source reference")
    names = set()
    for row in assumptions:
        if not isinstance(row, dict) or set(row) != {"name", "status", "evidence_refs"}:
            raise EmpiricalDesignError("assumption must have full evidence status")
        name, status, evidence = row["name"], row["status"], row["evidence_refs"]
        if (not _string(name, identifier=True) or name in names or
            status not in ("ASSERTED_NOT_VERIFIED", "UNSUPPORTED") or
            not isinstance(evidence, list) or len(evidence) > 16 or
            any(not _string(ref) or ref not in refs for ref in evidence) or
            (status == "ASSERTED_NOT_VERIFIED" and not evidence)):
            raise EmpiricalDesignError("invalid assumption evidence linkage")
        names.add(name)
    if method in _REQUIRED and names - _REQUIRED[method]:
        raise EmpiricalDesignError("unknown assumption does not substitute for method requirements")
    return ValidatedEmpiricalDesign(payload)


def check_identification_assumptions(design: ValidatedEmpiricalDesign) -> EmpiricalAssessment:
    """Never certify causality merely because assumptions were declared."""
    if not isinstance(design, ValidatedEmpiricalDesign):
        raise EmpiricalDesignError("validated design required")
    obj = validate_design(design.data).data  # revalidate detached snapshot
    if obj["intent"] == "association":
        return EmpiricalAssessment("ASSOCIATION_ONLY", "INFO", (), ())
    if obj["intent"] == "prediction":
        return EmpiricalAssessment("PREDICTION_ONLY", "INFO", (), ())
    received = {row["name"] for row in obj["assumptions"]
                if row["status"] == "ASSERTED_NOT_VERIFIED"}
    missing = tuple(sorted(_REQUIRED[obj["method"]] - received))
    return EmpiricalAssessment(
        "IDENTIFICATION_INCOMPLETE" if missing else "ASSUMPTIONS_DOCUMENTED_NOT_VERIFIED",
        "CRITICAL" if missing else "WARNING", missing, tuple(sorted(received)))


def collect_estimand(design: ValidatedEmpiricalDesign) -> EstimandRecord:
    """Collect an explicit estimand without inventing observations or estimates."""
    if not isinstance(design, ValidatedEmpiricalDesign):
        raise EmpiricalDesignError("validated design required")
    obj = validate_design(design.data).data
    return EstimandRecord(obj["estimand"], obj["outcome"], obj["treatment"],
                          obj["target_population"])


def render_empirical_claim(design: ValidatedEmpiricalDesign, *, claim_kind: str) -> str:
    """Fail closed on any causal efficacy statement absent independent ID audit.

    This first version has NO causal-identification verifier and thus never
    marks causal effects established, even with all hypotheses documented.
    """
    check = check_identification_assumptions(design)
    if claim_kind == "causal":
        raise EmpiricalDesignError(
            f"causal effect forbidden: {check.status}; identification not independently verified"
        )
    if claim_kind == "association" and check.status == "ASSOCIATION_ONLY":
        return "ASSOCIATION_DESIGN_ONLY_NOT_ESTIMATED"
    if claim_kind == "prediction" and check.status == "PREDICTION_ONLY":
        return "PREDICTIVE_DESIGN_ONLY_NOT_ESTIMATED"
    raise EmpiricalDesignError("claim kind mismatches design intent")
