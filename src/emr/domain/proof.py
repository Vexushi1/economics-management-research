"""Phase 5 evidence ledger; checked math evidence is not a complete proof.

No free-form mathematical text is evaluated. Numeric witnesses are rechecked
with exact rationals and Phase 3 validated ASTs. An unchecked or unsuccessful
optimizer result is *never* a counterexample. All versions remain immutable.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from importlib.resources import files
from typing import Any

import sympy as sp
from jsonschema import Draft202012Validator

from emr.adapters.symbolic_sympy import CompiledGame, compile_game
from emr.domain.equilibrium import _number, best_response, feasible_interval
from emr.domain.game import validate_game_spec

MAX_PROPOSITION_BYTES = 32_768
_STEP_STATES = frozenset({"OK", "GAP", "ERROR", "UNCLEAR"})


class ProofAuditError(ValueError):
    """A proof claim, transition, source scope or purported witness is invalid."""


def _canonical(obj: object) -> str:
    try:
        result = json.dumps(obj, sort_keys=True, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError, RecursionError) as exc:
        raise ProofAuditError("invalid or unbounded JSON proof data") from exc
    if len(result.encode("utf-8")) > MAX_PROPOSITION_BYTES:
        raise ProofAuditError("proof data exceeds size budget")
    return result


def model_fingerprint(compiled: CompiledGame) -> str:
    """Content identity of the Phase 3 validated model snapshot."""
    return hashlib.sha256(_canonical(compiled.model.data).encode("utf-8")).hexdigest()


def _schema(name: str) -> Draft202012Validator:
    content = files("emr").joinpath("schemas", name).read_text(encoding="utf-8")
    data = json.loads(content)
    Draft202012Validator.check_schema(data)
    return Draft202012Validator(data)


def _domains(data: Mapping[str, Any]) -> None:
    rows = data["parameter_domains"]
    symbols = [row["symbol"] for row in rows]
    quants = [row["symbol"] for row in data["quantifiers"]]
    if len(set(symbols)) != len(symbols) or len(set(quants)) != len(quants):
        raise ProofAuditError("duplicate quantified symbol or parameter domain")
    if set(quants) != set(symbols):
        raise ProofAuditError("every quantified symbol requires exactly one domain")
    for item in rows:
        low = Decimal(item["lower"]) if item["lower"] is not None else None
        high = Decimal(item["upper"]) if item["upper"] is not None else None
        if low is not None and high is not None and (low > high or (low == high and not (item["lower_closed"] and item["upper_closed"]))):
            raise ProofAuditError("empty or reversed parameter domain")


def validate_proposition(document: Mapping[str, Any]) -> dict[str, Any]:
    """Require complete scope, quantifiers, evidence origins and proof version."""
    normalized = json.loads(_canonical(document))
    try:
        _schema("proposition.schema.json").validate(normalized)
        _domains(normalized)
    except Exception as exc:
        if isinstance(exc, ProofAuditError):
            raise
        raise ProofAuditError("invalid proposition contract") from exc
    return normalized


@dataclass(slots=True)
class _Entry:
    proposition: dict[str, Any]
    obligations: dict[str, str] = field(default_factory=dict)
    steps: list[dict[str, Any]] = field(default_factory=list)
    counterexamples: list[dict[str, Any]] = field(default_factory=list)
    verdict: str = "OPEN"
    frozen: bool = False
    reviewer: str | None = None
    review_refs: tuple[str, ...] = ()
    prior_report_id: str | None = None

    def open_obligations(self) -> list[str]:
        return [name for name in self.obligations if not any(
            step["obligation_id"] == name and step["status"] == "OK" and step["evidence_refs"]
            for step in self.steps
        )]


class ProofLedger:
    """Version-addressed ledger. Frozen/refuted versions cannot be reopened."""

    def __init__(self) -> None:
        self._entries: dict[tuple[str, int], _Entry] = {}

    def register(self, proposition: Mapping[str, Any]) -> None:
        data = validate_proposition(proposition)
        key = data["id"], data["proof_version"]
        if key in self._entries:
            raise ProofAuditError("proposition version already exists")
        self._entries[key] = _Entry(data)

    def _entry(self, proposition_id: str, version: int) -> _Entry:
        try:
            return self._entries[proposition_id, version]
        except KeyError as exc:
            raise ProofAuditError("unknown proposition version") from exc

    def entry(self, proposition_id: str, version: int) -> _Entry:
        """Return a detached snapshot; external mutations cannot forge PROVED."""
        return copy.deepcopy(self._entry(proposition_id, version))

    def narrow_scope(self, proposition_id: str, old_version: int,
                     narrower_domains: list[dict[str, Any]]) -> int:
        """Create new unproved version, never import the prior PROVED verdict."""
        old = self._entry(proposition_id, old_version)
        data = json.loads(_canonical(old.proposition))
        current = {row["symbol"]: row for row in data["parameter_domains"]}
        if {row.get("symbol") for row in narrower_domains} != set(current):
            raise ProofAuditError("all old domain symbols must remain")
        for new in narrower_domains:
            previous = current[new["symbol"]]
            for edge in ("lower", "upper"):
                before, after = previous[edge], new[edge]
                if before is not None and after is None:
                    raise ProofAuditError("cannot widen a proof scope")
                if before is not None and after is not None:
                    a, b = Decimal(before), Decimal(after)
                    if (edge == "lower" and b < a) or (edge == "upper" and b > a):
                        raise ProofAuditError("cannot widen a proof scope")
                    if a == b and (not previous[edge + "_closed"] and new[edge + "_closed"]):
                        raise ProofAuditError("cannot include excluded endpoint")
        next_version = max(v for (p, v) in self._entries if p == proposition_id) + 1
        data.update(proof_version=next_version, parameter_domains=narrower_domains)
        self.register(data)
        entry = self._entry(proposition_id, next_version)
        entry.prior_report_id = f"{proposition_id}@{old_version}"
        return next_version


def _editable(entry: _Entry) -> None:
    if entry.frozen or entry.verdict in ("PROVED", "REFUTED"):
        raise ProofAuditError("finalized or refuted proof version is immutable")


def register_obligation(ledger: ProofLedger, proposition_id: str, version: int,
                        obligation_id: str, description: str) -> None:
    """Register a named proof debt; no deletion interface is exposed."""
    entry = ledger._entry(proposition_id, version)
    _editable(entry)
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9._-]{0,79}", obligation_id):
        raise ProofAuditError("invalid obligation id")
    if not description.strip() or len(description) > 2048 or obligation_id in entry.obligations:
        raise ProofAuditError("invalid or duplicate obligation")
    if len(entry.obligations) >= 200:
        raise ProofAuditError("obligation limit exceeded")
    entry.obligations[obligation_id] = description
    if entry.verdict not in ("ERROR", "UNCLEAR", "REVIEW_REQUIRED"):
        entry.verdict = "OPEN"


def audit_proof_step(ledger: ProofLedger, proposition_id: str, version: int,
                     step_id: str, obligation_id: str, status: str,
                     evidence_refs: tuple[str, ...] = ()) -> None:
    """Audit one step. 'OK' never promotes a proof beyond SKETCH_ACCEPTED."""
    entry = ledger._entry(proposition_id, version)
    _editable(entry)
    if obligation_id not in entry.obligations or status not in _STEP_STATES:
        raise ProofAuditError("unknown obligation or invalid audit state")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9._-]{0,79}", step_id):
        raise ProofAuditError("invalid step identifier")
    if any(step["id"] == step_id for step in entry.steps):
        raise ProofAuditError("duplicate proof step")
    if status == "OK" and not evidence_refs:
        raise ProofAuditError("an OK step requires a traceable evidence reference")
    if len(evidence_refs) > 30 or any(not isinstance(ref, str) or not ref.strip() or len(ref) > 256 for ref in evidence_refs):
        raise ProofAuditError("invalid evidence reference")
    if len(entry.steps) >= 500:
        raise ProofAuditError("proof step budget exceeded")
    entry.steps.append({"id": step_id, "obligation_id": obligation_id,
                        "status": status, "evidence_refs": list(evidence_refs)})
    if status == "ERROR":
        entry.verdict = "ERROR"
    elif entry.verdict == "ERROR":
        pass  # A later OK may never erase an earlier mathematical error.
    elif status == "UNCLEAR":
        entry.verdict = "UNCLEAR"
    elif status == "GAP":
        entry.verdict = "REVIEW_REQUIRED"
    elif entry.open_obligations() == [] and entry.obligations and all(s["status"] == "OK" for s in entry.steps):
        entry.verdict = "SKETCH_ACCEPTED"


def _proved_lemma(ledger: ProofLedger, ref: str, proposition_id: str, version: int) -> bool:
    """A cited lemma must point to an earlier independently attested record."""
    matched = re.fullmatch(r"([A-Za-z][A-Za-z0-9._-]{0,79})@([1-9][0-9]{0,5})", ref)
    if matched is None:
        return False
    lemma_id, lemma_version = matched[1], int(matched[2])
    if (lemma_id, lemma_version) == (proposition_id, version):
        return False
    try:
        return ledger._entry(lemma_id, lemma_version).verdict == "PROVED"
    except ProofAuditError:
        return False

def certify_proof(ledger: ProofLedger, proposition_id: str, version: int, *,
                  reviewer: str, evidence_refs: tuple[str, ...], attestation: str) -> None:
    """Explicit independent *human* adjudication, never automated inference.

    Merely passing pytest/SymPy/numeric probes or sketch steps cannot call this
    API implicitly; the named external reviewer signs a complete proof record.
    """
    entry = ledger._entry(proposition_id, version)
    _editable(entry)
    if (attestation != "INDEPENDENT_FULL_PROOF_REVIEW_COMPLETED"
        or reviewer.strip() == entry.proposition["author"] or not reviewer.strip()
        or not evidence_refs or any(not ref.strip() for ref in evidence_refs)
        or not entry.obligations or entry.open_obligations()
        or entry.verdict != "SKETCH_ACCEPTED"
        or any(not _proved_lemma(ledger, ref, proposition_id, version)
               for ref in entry.proposition["lemma_refs"])):
        raise ProofAuditError("independent proof certification obligations unmet")
    entry.reviewer, entry.review_refs = reviewer, evidence_refs
    entry.verdict = "PROVED"


def _witness_subs(compiled: CompiledGame, values: Mapping[str, object]) -> dict[sp.Symbol, sp.Rational]:
    """Exact witness is complete, within declared domains, and model-feasible."""
    data = compiled.model.data
    declared = {row["name"]: row for row in data["symbols"]}
    if set(values) != set(declared) or len(values) > 64:
        raise ProofAuditError("witness must bind every model symbol")
    subs = {compiled.symbol(name): _number(value) for name, value in values.items()}
    for name, row in declared.items():
        dom, value = row["domain"], subs[compiled.symbol(name)]
        low = _number(dom["lower"]) if dom["lower"] is not None else None
        high = _number(dom["upper"]) if dom["upper"] is not None else None
        if ((low is not None and (value < low or (value == low and not dom["lower_closed"])))
            or (high is not None and (value > high or (value == high and not dom["upper_closed"])))):
            raise ProofAuditError("witness outside model symbol domain")
    for rel, expression in compiled.constraints:
        result = sp.cancel(expression.subs(subs, simultaneous=True))
        if not result.is_Rational:
            raise ProofAuditError("witness constraint not exactly decidable")
        valid = {"ge": result >= 0, "gt": result > 0, "le": result <= 0,
                 "lt": result < 0, "eq": result == 0}[rel]
        if not valid:
            raise ProofAuditError("witness violates a model constraint")
    return subs


def _check_claim_scope(entry: _Entry, values: Mapping[str, object]) -> None:
    """A point can refute a universal claim only inside its quantified scope."""
    if any(row["kind"] != "forall" for row in entry.proposition["quantifiers"]):
        raise ProofAuditError("one numeric witness cannot refute existential claims")
    for row in entry.proposition["parameter_domains"]:
        name = row["symbol"]
        if name not in values:
            raise ProofAuditError("witness missing quantified symbol")
        v = _number(values[name])
        lo = _number(row["lower"]) if row["lower"] is not None else None
        hi = _number(row["upper"]) if row["upper"] is not None else None
        if ((lo is not None and (v < lo or (v == lo and not row["lower_closed"])))
            or (hi is not None and (v > hi or (v == hi and not row["upper_closed"])))):
            raise ProofAuditError("witness outside proposition scope")

def record_counterexample(ledger: ProofLedger, proposition_id: str, version: int,
                          *, kind: str, compiled: CompiledGame, player: str,
                          control: str, witness: Mapping[str, object] | None = None,
                          claimed_derivative: CompiledGame | None = None,
                          parameters: Mapping[str, object] | None = None,
                          claimed_point: object | None = None,
                          fixed_controls: Mapping[str, object] | None = None) -> dict[str, Any]:
    """Recalculate a witness. A root-finder failure is NEVER a counterexample.

    DERIVATIVE_IDENTITY requires two independently Phase 3-validated ASTs,
    a fully feasible exact substitution, and a nonzero rational discrepancy.
    OPTIMALITY requires a Phase 4 checked global optimum and a strictly
    worse *feasible* asserted maximizer. No user-provided 'verified' flag.
    """
    entry = ledger._entry(proposition_id, version)
    _editable(entry)
    # Recompile both inputs from sealed Phase 3 snapshots. CompiledGame caches
    # are not authority; their public dicts might have been mutated by a caller.
    compiled = compile_game(compiled.model)
    if claimed_derivative is not None:
        claimed_derivative = compile_game(claimed_derivative.model)
    if entry.proposition["model_sha256"] != model_fingerprint(compiled):
        raise ProofAuditError("proof and mathematical model fingerprints disagree")
    if kind == "DERIVATIVE_IDENTITY":
        if claimed_derivative is None or witness is None or claimed_point is not None:
            raise ProofAuditError("missing derivative claim or witness")
        if set(compiled.symbols) != set(claimed_derivative.symbols):
            raise ProofAuditError("derivative claim symbols differ")
        original = compiled.model.data
        asserted = claimed_derivative.model.data
        expected = json.loads(_canonical(original))
        counterpart = next(x for x in expected["players"] if x["id"] == player)
        other = next(x for x in asserted["players"] if x["id"] == player)
        counterpart["objective"] = other["objective"]
        if expected != asserted:
            raise ProofAuditError("derivative claim altered model context")
        _check_claim_scope(entry, witness)
        substitutions = _witness_subs(compiled, witness)
        actual = sp.diff(compiled.objectives[player], compiled.symbol(control))
        expected_deriv = claimed_derivative.objectives[player]
        difference = sp.cancel((actual - expected_deriv).subs(substitutions, simultaneous=True))
        if not difference.is_Rational or difference == 0:
            raise ProofAuditError("no exactly checked derivative contradiction")
        record = {"kind": kind, "witness": {k: str(v) for k, v in witness.items()},
                  "difference": str(difference), "precision": "EXACT_RATIONAL",
                  "optimizer_status": "NOT_APPLICABLE", "model_sha256": model_fingerprint(compiled)}
    elif kind == "OPTIMALITY":
        if parameters is None or claimed_point is None or witness is not None:
            raise ProofAuditError("missing optimality parameters or alleged maximizer")
        fixed = fixed_controls or {}
        optimum = best_response(compiled, player, control, parameters=parameters,
                                fixed_controls=fixed)
        if optimum.status not in ("GLOBAL_OPTIMUM_CHECKED", "MULTIPLE_MAXIMIZERS") or not optimum.maximizers:
            raise ProofAuditError("optimizer failed to certify a global optimum")
        alleged = _number(claimed_point)
        if optimum.interval is None or not optimum.interval.contains(alleged):
            raise ProofAuditError("alleged point not feasible")
        values = {**parameters, **fixed, control: str(alleged)}
        _check_claim_scope(entry, values)
        subs = _witness_subs(compiled, values)
        alleged_profit = sp.cancel(compiled.objectives[player].subs(subs, simultaneous=True))
        gap = sp.cancel(optimum.objective_value - alleged_profit)
        if not gap.is_Rational or gap <= 0:
            raise ProofAuditError("no exact positive optimality gap")
        record = {"kind": kind,
                  "witness": {**{k: str(v) for k, v in values.items()},
                              "checked_better_point": str(optimum.maximizers[0]),
                              "checked_optimum": str(optimum.objective_value)},
                  "difference": str(gap), "precision": "EXACT_RATIONAL",
                  "optimizer_status": optimum.status, "model_sha256": model_fingerprint(compiled)}
    else:
        raise ProofAuditError("root-finding failure or unsupported evidence is not a counterexample")
    if len(entry.counterexamples) >= 100:
        raise ProofAuditError("counterexample budget exceeded")
    entry.counterexamples.append(record)
    entry.verdict, entry.frozen = "REFUTED", True
    return json.loads(_canonical(record))


def render_verification_report(ledger: ProofLedger, proposition_id: str,
                               version: int) -> dict[str, Any]:
    """Snapshot the exact scope, open debts, reviewer, evidence and verdict."""
    entry = ledger._entry(proposition_id, version)
    sources = {ref for step in entry.steps for ref in step["evidence_refs"]}
    sources.update(entry.review_refs)
    report = {
        "schema_version": "1", "proposition_id": proposition_id,
        "proof_version": version,
        "scope": {"model_sha256": entry.proposition["model_sha256"],
                  "parameter_domains": entry.proposition["parameter_domains"],
                  "quantifiers": entry.proposition["quantifiers"]},
        "verdict": entry.verdict, "frozen": entry.frozen,
        "open_obligations": entry.open_obligations(),
        "steps": entry.steps, "counterexamples": entry.counterexamples,
        "evidence_refs": sorted(sources),
        "severity": "CRITICAL" if entry.frozen else "ERROR" if entry.verdict == "ERROR" else
                    "INFO" if entry.verdict == "PROVED" else "WARNING",
        "reviewer": entry.reviewer, "prior_report_id": entry.prior_report_id,
    }
    normalized = json.loads(_canonical(report))
    _schema("verification-report.schema.json").validate(normalized)
    return normalized


def render_proof_status(ledger: ProofLedger, proposition_id: str, version: int,
                        *, format: str = "latex", strict: bool = False) -> str:
    """Fail closed: no strict export while any obligation remains unproved.

    Non-strict LaTeX *always* contains an explicit \\unproven{...} marker unless
    an independently attested PROVED status has been recorded. This cannot
    prevent arbitrary manual editing of a separately exported TeX file.
    """
    record = render_verification_report(ledger, proposition_id, version)
    verified = record["verdict"] == "PROVED" and not record["open_obligations"]
    if strict and not verified:
        raise ProofAuditError("strict proof export forbidden: unresolved proof obligations")
    if format == "latex":
        label = f"{proposition_id}-v{version}"
        if verified:
            return f"\\paragraph{{Proof {label}}} [INDEPENDENTLY REVIEWED; see evidence ledger]"
        return f"\\paragraph{{Proof {label}}} \\unproven{{{label}: {record['verdict']}}}"
    if format == "status":
        return "PROVED" if verified else f"UNPROVEN:{record['verdict']}"
    raise ValueError("unsupported proof rendering format")
