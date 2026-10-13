"""Missing-evidence-first reproducibility manifests and conservative comparisons.

The system never invents parameters, publication values, distributions or source
citations. Numerical agreement is not mathematical equivalence or replication.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from decimal import Decimal, localcontext
from fractions import Fraction
from importlib.resources import files
from typing import Any

from jsonschema import Draft202012Validator

from emr.domain.stochastic import StochasticInputError, _fraction

MAX_REPLICATION_BYTES = 32_768


class ReplicationInputError(ValueError):
    """Malformed replication metadata must not be treated as research evidence."""


def _copy(obj: Mapping[str, Any]) -> dict[str, Any]:
    try:
        data = json.dumps(obj, allow_nan=False, sort_keys=True)
        if len(data.encode("utf-8")) > MAX_REPLICATION_BYTES:
            raise ReplicationInputError("replication manifest exceeds byte budget")
        parsed = json.loads(data)
        if not isinstance(parsed, dict):
            raise ReplicationInputError("replication request must be an object")
        return parsed
    except (ValueError, TypeError, OverflowError, RecursionError) as exc:
        raise ReplicationInputError("invalid replication JSON") from exc


def _report_check(data: dict[str, Any]) -> dict[str, Any]:
    schema = json.loads(files("emr").joinpath("schemas/replication-report.schema.json").read_text())
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(data)
    required = data["required_parameters"]
    supplied = [row["name"] for row in data["parameter_provenance"]]
    if len(set(required)) != len(required) or len(set(supplied)) != len(supplied):
        raise ReplicationInputError("duplicate parameter identities")
    if set(supplied) - set(required):
        raise ReplicationInputError("unrequested parameter provenance")
    if data["status"] != "UNREPRODUCIBLE_INPUT" and set(supplied) != set(required):
        raise ReplicationInputError("ready status without complete parameter provenance")
    if data["status"] != "UNREPRODUCIBLE_INPUT" and not data["formula_anchors"]:
        raise ReplicationInputError("missing original formula anchors")
    # Derived comparison statuses are checked against the recorded exact values.
    # A caller may supply a saved report, but cannot forge its arithmetic result.
    tol_raw = data["comparison_tolerance"]
    tol: Fraction | None = None
    if tol_raw is not None:
        try:
            tol = _fraction(tol_raw)
        except StochasticInputError as exc:
            raise ReplicationInputError("invalid persisted comparison tolerance") from exc
        if tol <= 0 or tol > Fraction(1, 10):
            raise ReplicationInputError("comparison tolerance outside supported range")
    if data["status"] == "READY_FOR_REPLICATION" and tol is not None:
        raise ReplicationInputError("uncompared report cannot have a comparison tolerance")
    if data["status"] in ("NUMERIC_COMPARISON_COMPLETE", "COMPARISON_MISMATCH"):
        if any(target["status"] == "NOT_VERIFIED" for target in data["targets"]):
            raise ReplicationInputError("completed comparison has unverified numerical targets")
        if tol is None:
            raise ReplicationInputError("completed comparison requires its exact tolerance")
    for target in data["targets"]:
        fields = ("published_value", "computed_value", "absolute_error")
        if target["status"] == "NOT_VERIFIED":
            if any(target[k] is not None for k in fields):
                raise ReplicationInputError("unverified target cannot contain computed values")
            continue
        if tol is None or any(target[k] is None for k in fields):
            raise ReplicationInputError("numerical status without complete computed evidence")
        try:
            published, computed, recorded_gap = (_fraction(target[k]) for k in fields)
        except StochasticInputError as exc:
            raise ReplicationInputError("invalid persisted numerical comparison") from exc
        actual_gap = abs(published - computed)
        expected_status = "NUMERIC_MATCH" if actual_gap <= tol else "NUMERIC_MISMATCH"
        if recorded_gap != actual_gap or target["status"] != expected_status:
            raise ReplicationInputError("forged or inconsistent numerical comparison")
    target_states = [target["status"] for target in data["targets"]]
    if data["status"] == "READY_FOR_REPLICATION" and any(
        value != "NOT_VERIFIED" for value in target_states
    ):
        raise ReplicationInputError("ready report cannot contain fabricated comparisons")
    if data["status"] in ("NUMERIC_COMPARISON_COMPLETE", "COMPARISON_MISMATCH"):
        if any(value == "NOT_VERIFIED" for value in target_states):
            raise ReplicationInputError("completed comparison has unverified numerical targets")
        if data["status"] == "NUMERIC_COMPARISON_COMPLETE" and any(
            value != "NUMERIC_MATCH" for value in target_states
        ):
            raise ReplicationInputError("claimed numeric agreement conflicts with target values")
        if data["status"] == "COMPARISON_MISMATCH" and "NUMERIC_MISMATCH" not in target_states:
            raise ReplicationInputError("claimed mismatch has no differing target")
    return data


def build_replication_manifest(request: Mapping[str, Any]) -> dict[str, Any]:
    """Stop before computation when any required original-paper fact is unknown.

    All values must have source refs; fields such as "assumed" and missing
    values are never converted to defaults. Artifacts remain UNVERIFIED.
    """
    obj = _copy(request)
    allowed = {"paper_sha256", "model_id", "required_parameters", "parameters",
               "formula_anchors", "targets"}
    if set(obj) - allowed:
        raise ReplicationInputError("unexpected replication request fields")
    sha, model = obj.get("paper_sha256"), obj.get("model_id")
    if (not isinstance(sha, str) or len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha)
        or not isinstance(model, str) or not 1 <= len(model) <= 80):
        raise ReplicationInputError("source PDF digest and model ID required")
    required, params, anchors, targets = (obj.get(k) for k in
                                          ("required_parameters", "parameters", "formula_anchors", "targets"))
    if (not isinstance(required, list) or not 1 <= len(required) <= 64
        or any(not isinstance(name, str) or not name.isidentifier() or len(name) > 48 for name in required)
        or len(set(required)) != len(required)
        or not isinstance(params, dict) or len(params) > 64 or set(params) - set(required)
        or not isinstance(anchors, list) or len(anchors) > 100
        or not isinstance(targets, list) or not 1 <= len(targets) <= 100):
        raise ReplicationInputError("invalid parameter, formula or target collection")
    missing = []
    provenance = []
    for name in required:
        record = params.get(name)
        if not isinstance(record, dict) or set(record) != {"value", "source_ref"}:
            missing.append(name)
            continue
        source = record["source_ref"]
        if not isinstance(source, str) or not source.strip() or len(source) > 256:
            missing.append(name)
            continue
        try:
            value = _fraction(record["value"])
        except StochasticInputError:
            missing.append(name)
            continue
        provenance.append({"name": name, "value": str(value), "source_ref": source})
    anchor_valid = bool(anchors) and all(isinstance(a, str) and a.strip() and len(a) <= 256 for a in anchors)
    if not anchor_valid:
        missing.append("ORIGINAL_FORMULA_ANCHORS")
    seen = set()
    out_targets = []
    for item in targets:
        if not isinstance(item, dict) or set(item) != {"id", "kind", "source_ref"}:
            raise ReplicationInputError("each target needs id, kind, source ref")
        identifier = item["id"]
        kind = item["kind"]
        ref = item["source_ref"]
        if (not isinstance(identifier, str) or not 1 <= len(identifier) <= 80
            or identifier in seen or kind not in ("FORMULA", "PROPOSITION", "TABLE", "FIGURE")
            or not isinstance(ref, str) or len(ref) > 256):
            raise ReplicationInputError("invalid target identity or kind")
        seen.add(identifier)
        if not ref.strip():
            missing.append(f"TARGET_ANCHOR:{identifier}")
        out_targets.append({"id": identifier, "kind": kind, "source_ref": ref,
                            "status": "NOT_VERIFIED", "published_value": None,
                            "computed_value": None, "absolute_error": None})
    report = {"schema_version": "1", "paper_sha256": sha, "model_id": model,
              "status": "UNREPRODUCIBLE_INPUT" if missing else "READY_FOR_REPLICATION",
              "required_parameters": required, "missing_requirements": missing, "parameter_provenance": provenance,
              "formula_anchors": anchors if anchor_valid else [], "targets": out_targets,
              "comparison_tolerance": None,
              "diagnostics": ["NO_UNVERIFIED_PARAMETERS_GUESSED"] if missing else
                             ["METADATA_COMPLETE_NOT_YET_REPRODUCED"]}
    return _report_check(report)


def _exact_decimal(value: Fraction) -> str:
    """Canonical terminating decimal for arithmetic derived from decimal inputs."""
    with localcontext() as context:
        context.prec = 60
        result = format(Decimal(value.numerator) / Decimal(value.denominator), "f")
    if Fraction(result) != value:
        raise ReplicationInputError("comparison result cannot be stored as a finite decimal")
    return result


def compare_results(manifest: Mapping[str, Any], published: Mapping[str, Any],
                    computed: Mapping[str, Any], *, tolerance: str = "0.000001") -> dict[str, Any]:
    """Compare user-supplied finite scalar results; cannot certify proof or figures.

    Requires every target to have explicit paper value and independent computed
    value; missing evidence yields UNREPRODUCIBLE_INPUT, never a substituted zero.
    """
    report = _copy(manifest)
    _report_check(report)
    if report["status"] == "UNREPRODUCIBLE_INPUT":
        return report  # missing input is a terminal safety gate, not a default value.
    if report["status"] != "READY_FOR_REPLICATION":
        raise ReplicationInputError("only an uncompared ready manifest may be compared")
    if not isinstance(published, Mapping) or not isinstance(computed, Mapping):
        raise ReplicationInputError("numerical data sources must be explicit mappings")
    try:
        tol = _fraction(tolerance)
    except StochasticInputError as exc:
        raise ReplicationInputError("invalid absolute comparison tolerance") from exc
    if tol <= 0 or tol > Fraction(1, 10):
        raise ReplicationInputError("tolerance must be positive and small")
    report["comparison_tolerance"] = _exact_decimal(tol)
    ids = {item["id"] for item in report["targets"]}
    if set(published) - ids or set(computed) - ids:
        raise ReplicationInputError("unexpected target result")
    missing = []
    for item in report["targets"]:
        name = item["id"]
        if name not in published or name not in computed:
            missing.append(f"NUMERIC_TARGET:{name}")
            continue
        try:
            source, value = _fraction(published[name]), _fraction(computed[name])
        except StochasticInputError:
            missing.append(f"NUMERIC_TARGET:{name}")
            continue
        difference = abs(source - value)
        item.update(published_value=_exact_decimal(source), computed_value=_exact_decimal(value),
                    absolute_error=_exact_decimal(difference),
                    status="NUMERIC_MATCH" if difference <= tol else "NUMERIC_MISMATCH")
    if missing:
        report["missing_requirements"] = missing
        report["status"] = "UNREPRODUCIBLE_INPUT"
        report["diagnostics"] = ["INCOMPLETE_REFERENCE_OR_COMPUTED_NUMERIC_RESULT"]
    else:
        report["status"] = ("COMPARISON_MISMATCH" if any(
            i["status"] == "NUMERIC_MISMATCH" for i in report["targets"]
        ) else "NUMERIC_COMPARISON_COMPLETE")
        report["diagnostics"] = ["NUMERIC_AGREEMENT_IS_NOT_THEOREM_PROOF"]
    return _report_check(report)


def classify_discrepancy(report: Mapping[str, Any]) -> str:
    """Classify what *was observed*, never guess why the paper and model differ."""
    obj = _copy(report)
    _report_check(obj)
    return {
        "UNREPRODUCIBLE_INPUT": "MISSING_SOURCE_FACTS",
        "READY_FOR_REPLICATION": "NOT_YET_COMPARED",
        "NUMERIC_COMPARISON_COMPLETE": "WITHIN_ABSOLUTE_TOLERANCE",
        "COMPARISON_MISMATCH": "OBSERVED_NUMERIC_DISCREPANCY_CAUSE_UNKNOWN",
    }[obj["status"]]
