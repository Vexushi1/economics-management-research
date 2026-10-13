"""Versioned proposition and strict-export state-machine regression tests."""

import copy

import pytest

from emr.domain.proof import (
    ProofAuditError,
    ProofLedger,
    audit_proof_step,
    certify_proof,
    register_obligation,
    render_proof_status,
    render_verification_report,
    validate_proposition,
)


def sample_proposition():
    return {
        "schema_version": "1",
        "id": "PropOne",
        "statement": "A formal mathematical conditional for testing only",
        "author": "First researcher",
        "proof_version": 1,
        "model_sha256": "a" * 64,
        "quantifiers": [{"kind": "forall", "symbol": "p"}],
        "parameter_domains": [{"symbol": "p", "lower": "0", "upper": "10",
                               "lower_closed": True, "upper_closed": True}],
        "assumptions": ["Synthetic model"],
        "lemma_refs": [],
        "source_refs": ["synthetic:source:1"],
    }


def test_sketch_never_automatically_proves_or_erases_marker():
    ledger = ProofLedger()
    ledger.register(sample_proposition())
    register_obligation(ledger, "PropOne", 1, "FOC", "Check derivative exactly")
    audit_proof_step(ledger, "PropOne", 1, "step1", "FOC", "OK", ("proof:check:1",))
    report = render_verification_report(ledger, "PropOne", 1)
    assert report["verdict"] == "SKETCH_ACCEPTED"
    assert report["open_obligations"] == []
    assert "\\unproven{" in render_proof_status(ledger, "PropOne", 1)
    with pytest.raises(ProofAuditError, match="strict proof export"):
        render_proof_status(ledger, "PropOne", 1, strict=True)
    with pytest.raises(ProofAuditError):
        certify_proof(ledger, "PropOne", 1, reviewer="First researcher",
                      evidence_refs=("review:1",),
                      attestation="INDEPENDENT_FULL_PROOF_REVIEW_COMPLETED")
    certify_proof(ledger, "PropOne", 1, reviewer="Independent scholar",
                  evidence_refs=("review:complete:1",),
                  attestation="INDEPENDENT_FULL_PROOF_REVIEW_COMPLETED")
    assert render_proof_status(ledger, "PropOne", 1, strict=True).startswith("\\paragraph{Proof")
    with pytest.raises(ProofAuditError):
        register_obligation(ledger, "PropOne", 1, "more", "Changing a final proof")


def test_unclosed_or_gap_cannot_be_certified():
    ledger = ProofLedger()
    ledger.register(sample_proposition())
    register_obligation(ledger, "PropOne", 1, "KKT", "Check boundary")
    audit_proof_step(ledger, "PropOne", 1, "gap", "KKT", "GAP")
    assert render_verification_report(ledger, "PropOne", 1)["verdict"] == "REVIEW_REQUIRED"
    with pytest.raises(ProofAuditError):
        certify_proof(ledger, "PropOne", 1, reviewer="Other",
                      evidence_refs=("source",),
                      attestation="INDEPENDENT_FULL_PROOF_REVIEW_COMPLETED")
    assert "\\unproven{" in render_proof_status(ledger, "PropOne", 1)


def test_narrowed_scope_creates_fresh_report_without_inheriting_proof():
    ledger = ProofLedger()
    ledger.register(sample_proposition())
    register_obligation(ledger, "PropOne", 1, "check", "Check argument")
    audit_proof_step(ledger, "PropOne", 1, "step", "check", "OK", ("proof:step",))
    certify_proof(ledger, "PropOne", 1, reviewer="Independent", evidence_refs=("full:proof",),
                  attestation="INDEPENDENT_FULL_PROOF_REVIEW_COMPLETED")
    narrowed = copy.deepcopy(sample_proposition()["parameter_domains"])
    narrowed[0].update(lower="2", upper="8")
    version = ledger.narrow_scope("PropOne", 1, narrowed)
    assert version == 2
    revised = render_verification_report(ledger, "PropOne", 2)
    assert revised["verdict"] == "OPEN" and revised["steps"] == []
    assert revised["prior_report_id"] == "PropOne@1"
    assert render_verification_report(ledger, "PropOne", 1)["verdict"] == "PROVED"
    with pytest.raises(ProofAuditError):
        render_proof_status(ledger, "PropOne", 2, strict=True)
    with pytest.raises(ProofAuditError, match="widen"):
        ledger.narrow_scope("PropOne", 2, sample_proposition()["parameter_domains"])


@pytest.mark.parametrize("edit", [
    lambda p: p.update(parameter_domains=[]),
    lambda p: p["quantifiers"].append({"kind": "exists", "symbol": "missing"}),
    lambda p: p["parameter_domains"][0].update(lower="10", upper="1"),
    lambda p: p.update(model_sha256="not-a-sha"),
])
def test_invalid_proposition_rejected(edit):
    p = sample_proposition()
    edit(p)
    with pytest.raises(ProofAuditError):
        validate_proposition(p)


def test_proof_step_error_cannot_be_overwritten_by_ok():
    ledger = ProofLedger()
    ledger.register(sample_proposition())
    register_obligation(ledger, "PropOne", 1, "test", "Try the conjecture")
    audit_proof_step(ledger, "PropOne", 1, "counter", "test", "ERROR", ("source:error",))
    audit_proof_step(ledger, "PropOne", 1, "later", "test", "OK", ("source:new",))
    assert render_verification_report(ledger, "PropOne", 1)["verdict"] == "ERROR"


def test_external_entry_mutation_cannot_forge_proved_or_erase_debt():
    ledger = ProofLedger()
    ledger.register(sample_proposition())
    register_obligation(ledger, "PropOne", 1, "required", "Keep this debt")
    detached = ledger.entry("PropOne", 1)
    detached.verdict = "PROVED"
    detached.obligations.clear()
    assert render_verification_report(ledger, "PropOne", 1)["verdict"] == "OPEN"
    assert render_verification_report(ledger, "PropOne", 1)["open_obligations"] == ["required"]
    with pytest.raises(ProofAuditError):
        render_proof_status(ledger, "PropOne", 1, strict=True)


def test_schema_blocks_forged_proved_report_with_unfinished_obligations():
    import json
    from importlib.resources import files

    from jsonschema import Draft202012Validator, ValidationError

    ledger = ProofLedger()
    ledger.register(sample_proposition())
    register_obligation(ledger, "PropOne", 1, "missing", "Missing proof")
    report = render_verification_report(ledger, "PropOne", 1)
    report.update(verdict="PROVED", reviewer="Self-styled reviewer")
    schema = json.loads(files("emr").joinpath("schemas/verification-report.schema.json").read_text())
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(report)


def test_unverified_lemma_dependency_blocks_certification():
    p = sample_proposition()
    p["lemma_refs"] = ["MissingLemma@1"]
    ledger = ProofLedger()
    ledger.register(p)
    register_obligation(ledger, "PropOne", 1, "check", "Review step")
    audit_proof_step(ledger, "PropOne", 1, "step", "check", "OK", ("reviewed:proof",))
    with pytest.raises(ProofAuditError):
        certify_proof(ledger, "PropOne", 1, reviewer="Independent scholar",
                      evidence_refs=("review:complete",),
                      attestation="INDEPENDENT_FULL_PROOF_REVIEW_COMPLETED")


def test_error_persists_if_extra_obligation_is_added():
    ledger = ProofLedger()
    ledger.register(sample_proposition())
    register_obligation(ledger, "PropOne", 1, "original", "Check original")
    audit_proof_step(ledger, "PropOne", 1, "wrong", "original", "ERROR")
    register_obligation(ledger, "PropOne", 1, "extra", "Check another")
    assert render_verification_report(ledger, "PropOne", 1)["verdict"] == "ERROR"


def test_appendix_template_keeps_unproven_macro_and_numbered_proof():
    from pathlib import Path

    source = Path(__file__).resolve().parents[2] / "templates/theoretical-paper/proof-appendix.tex"
    text = source.read_text(encoding="utf-8")
    assert "\\providecommand{\\unproven}" in text
    assert "\\paragraph{Proof P1-v1}" in text
    assert "\\unproven{P1-v1:" in text
