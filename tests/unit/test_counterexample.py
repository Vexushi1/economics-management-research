"""Exact feasible counterexample checks; numeric optimizer failures are not proofs."""

import json
from pathlib import Path

import pytest

from emr.adapters.symbolic_sympy import compile_game
from emr.domain.game import validate_game_spec
from emr.domain.proof import (
    ProofAuditError,
    ProofLedger,
    model_fingerprint,
    record_counterexample,
    register_obligation,
    render_verification_report,
)

FILE = Path(__file__).resolve().parents[1] / "fixtures/stackelberg_linear/baseline.json"
PARAMS = {"A": "10", "a": "1", "b": "1", "c": "1", "gamma": "0.2", "w": "2"}


def setup():
    compiled = compile_game(validate_game_spec(json.loads(FILE.read_text(encoding="utf-8"))))
    symbols = [{"kind": "forall", "symbol": "p"}]
    domains = [{"symbol": "p", "lower": "2", "upper": "10",
                "lower_closed": True, "upper_closed": True}]
    ledger = ProofLedger()
    ledger.register({
        "schema_version": "1", "id": "FalseFollowerOpt", "statement": "Follower e=0 is optimal at p=6",
        "author": "Synthetic", "proof_version": 1, "model_sha256": model_fingerprint(compiled),
        "quantifiers": symbols, "parameter_domains": domains,
        "assumptions": ["Synthetic parameters"], "lemma_refs": [], "source_refs": ["synthetic:case"]})
    register_obligation(ledger, "FalseFollowerOpt", 1, "optimality", "Check global response")
    return ledger, compiled


def test_optimality_counterexample_requires_global_optimum_and_freezes():
    ledger, compiled = setup()
    result = record_counterexample(ledger, "FalseFollowerOpt", 1, kind="OPTIMALITY",
                                   compiled=compiled, player="influencer", control="e",
                                   parameters=PARAMS, fixed_controls={"p": "6"}, claimed_point="0")
    assert result["precision"] == "EXACT_RATIONAL"
    assert result["optimizer_status"] == "GLOBAL_OPTIMUM_CHECKED"
    assert result["witness"]["checked_better_point"] == "4"
    assert result["difference"] == "8"
    report = render_verification_report(ledger, "FalseFollowerOpt", 1)
    assert report["verdict"] == "REFUTED" and report["frozen"]
    assert report["severity"] == "CRITICAL"
    with pytest.raises(ProofAuditError, match="immutable"):
        record_counterexample(ledger, "FalseFollowerOpt", 1, kind="OPTIMALITY",
                              compiled=compiled, player="influencer", control="e",
                              parameters=PARAMS, fixed_controls={"p": "6"}, claimed_point="1")


def test_true_optimal_point_and_infeasible_claim_not_recorded():
    ledger, compiled = setup()
    for alleged in ("4", "-1"):
        with pytest.raises(ProofAuditError):
            record_counterexample(ledger, "FalseFollowerOpt", 1, kind="OPTIMALITY",
                                  compiled=compiled, player="influencer", control="e",
                                  parameters=PARAMS, fixed_controls={"p": "6"}, claimed_point=alleged)
    assert render_verification_report(ledger, "FalseFollowerOpt", 1)["counterexamples"] == []


def test_noncertified_optimization_is_not_a_counterexample():
    ledger, compiled = setup()
    model = compiled.model.data
    model["players"][1]["objective"] = {"op": "pow", "base": {"op": "symbol", "name": "e"}, "exponent": 3}
    cubic = compile_game(validate_game_spec(model))
    new_claim = ledger.entry("FalseFollowerOpt", 1).proposition
    new_claim["id"] = "CubicConjecture"
    new_claim["model_sha256"] = model_fingerprint(cubic)
    ledger.register(new_claim)
    with pytest.raises(ProofAuditError, match="optimizer failed"):
        record_counterexample(ledger, "CubicConjecture", 1, kind="OPTIMALITY",
                              compiled=cubic, player="influencer", control="e",
                              parameters=PARAMS, fixed_controls={"p": "6"}, claimed_point="1")
    with pytest.raises(ProofAuditError, match="root-finding failure"):
        record_counterexample(ledger, "CubicConjecture", 1, kind="ROOT_FAILURE",
                              compiled=cubic, player="influencer", control="e")


def test_counterexample_must_satisfy_claim_scope_even_if_model_allows_point():
    ledger, compiled = setup()
    p = ledger.entry("FalseFollowerOpt", 1).proposition
    p["id"] = "RestrictedClaim"
    p["parameter_domains"][0].update(lower="7", upper="9")
    ledger.register(p)
    with pytest.raises(ProofAuditError, match="proposition scope"):
        record_counterexample(ledger, "RestrictedClaim", 1, kind="OPTIMALITY",
                              compiled=compiled, player="influencer", control="e",
                              parameters=PARAMS, fixed_controls={"p": "6"}, claimed_point="0")
    assert render_verification_report(ledger, "RestrictedClaim", 1)["verdict"] == "OPEN"


def test_existential_claim_cannot_be_refuted_with_single_point():
    ledger, compiled = setup()
    p = ledger.entry("FalseFollowerOpt", 1).proposition
    p["id"] = "ExistentialClaim"
    p["quantifiers"][0]["kind"] = "exists"
    ledger.register(p)
    with pytest.raises(ProofAuditError, match="existential"):
        record_counterexample(ledger, "ExistentialClaim", 1, kind="OPTIMALITY",
                              compiled=compiled, player="influencer", control="e",
                              parameters=PARAMS, fixed_controls={"p": "6"}, claimed_point="0")
