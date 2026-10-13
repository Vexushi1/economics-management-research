"""Adversarial false symbolic derivative: exact valid witness must refute it."""

import json
from pathlib import Path

import pytest

from emr.adapters.symbolic_sympy import compile_game
from emr.domain.game import validate_game_spec
from emr.domain.proof import (
    ProofAuditError,
    ProofLedger,
    audit_proof_step,
    model_fingerprint,
    record_counterexample,
    register_obligation,
    render_proof_status,
    render_verification_report,
)

FILE = Path(__file__).resolve().parents[1] / "fixtures/stackelberg_linear/baseline.json"


def test_false_symbolic_derivative_is_error_with_exact_feasible_witness():
    original = json.loads(FILE.read_text(encoding="utf-8"))
    good = compile_game(validate_game_spec(original))
    asserted = json.loads(FILE.read_text(encoding="utf-8"))
    # Deliberately false: de [a(A-bp)e - c*e^2/2] = 0 for all e,p.
    next(row for row in asserted["players"] if row["id"] == "influencer")["objective"] = {
        "op": "const", "value": "0"
    }
    false_derivative = compile_game(validate_game_spec(asserted))
    ledger = ProofLedger()
    ledger.register({
        "schema_version": "1", "id": "FalseDerivative", "proof_version": 1,
        "statement": "The follower objective derivative is identically zero",
        "author": "Research author", "model_sha256": model_fingerprint(good),
        "quantifiers": [{"kind": "forall", "symbol": "e"}],
        "parameter_domains": [{"symbol": "e", "lower": "0", "upper": "10",
                               "lower_closed": True, "upper_closed": True}],
        "assumptions": ["A=10, a=b=c=1, w=2, gamma=0.2"],
        "lemma_refs": [], "source_refs": ["synthetic:stackelberg"]})
    register_obligation(ledger, "FalseDerivative", 1, "derivative", "Verify derivative identity")
    audit_proof_step(ledger, "FalseDerivative", 1, "step1", "derivative", "ERROR",
                     ("symbolic:checked-derivative",))
    assert render_verification_report(ledger, "FalseDerivative", 1)["verdict"] == "ERROR"
    witness = {"A": "10", "a": "1", "b": "1", "c": "1", "gamma": "0.2",
               "w": "2", "p": "6", "e": "2"}
    counter = record_counterexample(ledger, "FalseDerivative", 1,
                                    kind="DERIVATIVE_IDENTITY", compiled=good,
                                    claimed_derivative=false_derivative, player="influencer",
                                    control="e", witness=witness)
    assert counter["difference"] == "2"
    report = render_verification_report(ledger, "FalseDerivative", 1)
    assert report["verdict"] == "REFUTED"
    assert report["frozen"] is True
    assert report["counterexamples"][0]["witness"]["e"] == "2"
    assert "\\unproven{" in render_proof_status(ledger, "FalseDerivative", 1)
    with pytest.raises(ProofAuditError, match="strict proof export"):
        render_proof_status(ledger, "FalseDerivative", 1, strict=True)


def test_noncontradicting_derivative_witness_is_not_falsification():
    original = json.loads(FILE.read_text(encoding="utf-8"))
    compiled = compile_game(validate_game_spec(original))
    asserted = json.loads(FILE.read_text(encoding="utf-8"))
    next(row for row in asserted["players"] if row["id"] == "influencer")["objective"] = {
        "op": "const", "value": "0"
    }
    alleged = compile_game(validate_game_spec(asserted))
    ledger = ProofLedger()
    ledger.register({"schema_version": "1", "id": "AClaim", "proof_version": 1,
                     "statement": "Derivative zero", "author": "Research author",
                     "model_sha256": model_fingerprint(compiled),
                     "quantifiers": [{"kind": "forall", "symbol": "e"}],
                     "parameter_domains": [{"symbol": "e", "lower": "0", "upper": "10",
                                            "lower_closed": True, "upper_closed": True}],
                     "assumptions": [], "lemma_refs": [], "source_refs": ["synthetic:source"]})
    # At p=6, e=4 the real derivative happens to be zero: not a counterexample.
    witness = {"A": "10", "a": "1", "b": "1", "c": "1", "gamma": "0.2",
               "w": "2", "p": "6", "e": "4"}
    with pytest.raises(ProofAuditError, match="no exactly checked"):
        record_counterexample(ledger, "AClaim", 1, kind="DERIVATIVE_IDENTITY",
                              compiled=compiled, claimed_derivative=alleged,
                              player="influencer", control="e", witness=witness)
