"""Phase 1-6 crucible: PDF provenance -> inert AST -> solver -> proof ledger."""

import copy
import json
from dataclasses import replace
from pathlib import Path

import pytest

from emr.adapters.pdf_extract import extract_pdf
from emr.adapters.symbolic_sympy import compile_game
from emr.core.evidence_chain import (
    EvidenceChainError,
    anchor_ref,
    audit_evidence_seal,
    build_evidence_seal,
)
from emr.core.provenance import make_anchor
from emr.domain.game import validate_game_spec
from emr.domain.proof import (
    ProofLedger,
    audit_proof_step,
    certify_proof,
    model_fingerprint,
    register_obligation,
    render_proof_status,
)

BASE = Path(__file__).resolve().parents[1] / "fixtures/stackelberg_linear/baseline.json"
PARAMS = {"A": "10", "a": "1", "b": "1", "c": "1", "gamma": "0.2", "w": "2"}


def make_chain(sample_pdf):
    doc = extract_pdf(sample_pdf)
    # This synthetic PDF's text is NOT automatically interpreted as a model.
    a = make_anchor(doc, 1, 0, 0, 8)
    raw = json.loads(BASE.read_text(encoding="utf-8"))
    raw["source"] = {
        "kind": "paper_anchor", "note": "Synthetic integrity fixture; semantic mapping NOT VERIFIED.",
        "file_sha256": doc.sha256, "page": 1,
    }
    model = validate_game_spec(raw)
    ledger = ProofLedger()
    ledger.register({
        "schema_version": "1", "id": "ConditionalClaim",
        "statement": "Synthetic Stackelberg claim requiring independent proof",
        "author": "Synthetic author", "proof_version": 1,
        "model_sha256": model_fingerprint(compile_game(model)),
        "quantifiers": [{"kind": "forall", "symbol": "p"}],
        "parameter_domains": [{"symbol": "p", "lower": "2", "upper": "10",
                               "lower_closed": True, "upper_closed": True}],
        "assumptions": ["Synthetic conditional calculation; no automatic source interpretation"],
        "lemma_refs": [], "source_refs": [anchor_ref(a)],
    })
    register_obligation(ledger, "ConditionalClaim", 1, "math", "Independently audit general proof")
    audit_proof_step(ledger, "ConditionalClaim", 1, "s1", "math", "OK", ("synth:checked",))
    return doc, a, raw, model, ledger


def test_full_chain_preserves_unverified_origin_even_if_math_is_checked(sample_pdf):
    doc, anchor, _raw, model, ledger = make_chain(sample_pdf)
    seal = build_evidence_seal(doc, anchor, model, PARAMS, ledger, "ConditionalClaim", 1)
    assert seal.pdf_sha256 == doc.sha256 == seal.anchor.file_sha256
    assert seal.model_sha256 == model_fingerprint(compile_game(model))
    assert seal.mathematical_status == "EQUILIBRIUM_CHECKED"
    assert seal.source_status == seal.semantic_bridge_status == "NOT_VERIFIED"
    assert seal.status == "BOUND_NOT_PROVED"
    assert audit_evidence_seal(seal, doc, model, PARAMS, ledger) == "CURRENT"
    assert "\\unproven{" in render_proof_status(ledger, "ConditionalClaim", 1)
    with pytest.raises(ValueError, match="strict proof export"):
        render_proof_status(ledger, "ConditionalClaim", 1, strict=True)


def test_parameter_or_model_change_invalidates_previous_proof_chain(sample_pdf):
    doc, anchor, raw, model, ledger = make_chain(sample_pdf)
    seal = build_evidence_seal(doc, anchor, model, PARAMS, ledger, "ConditionalClaim", 1)
    assert audit_evidence_seal(seal, doc, model, {**PARAMS, "gamma": "0.3"}, ledger) == "STALE"
    changed = copy.deepcopy(raw)
    next(s for s in changed["symbols"] if s["name"] == "gamma")["domain"]["upper"] = "1"
    altered = validate_game_spec(changed)
    assert audit_evidence_seal(seal, doc, altered, PARAMS, ledger) == "STALE"
    with pytest.raises(EvidenceChainError, match="proof lacks exact model"):
        build_evidence_seal(doc, anchor, altered, PARAMS, ledger, "ConditionalClaim", 1)


def test_bad_pdf_binding_and_unsupported_model_cannot_be_promoted(sample_pdf):
    doc, anchor, raw, model, ledger = make_chain(sample_pdf)
    seal = build_evidence_seal(doc, anchor, model, PARAMS, ledger, "ConditionalClaim", 1)
    raw["source"]["file_sha256"] = "f" * 64
    with pytest.raises(EvidenceChainError, match="source differs"):
        build_evidence_seal(doc, anchor, validate_game_spec(raw), PARAMS, ledger, "ConditionalClaim", 1)
    raw["source"]["file_sha256"] = doc.sha256
    raw["players"][1]["objective"] = {
        "op": "pow", "base": {"op": "symbol", "name": "e"}, "exponent": 3,
    }
    assert audit_evidence_seal(seal, doc, validate_game_spec(raw), PARAMS, ledger) == "STALE"


def test_synthetically_attested_old_proof_is_stale_after_parameter_revision(sample_pdf):
    doc, anchor, raw, model, ledger = make_chain(sample_pdf)
    # Artificial reviewer fixture; NOT an actual independent scholarly review.
    certify_proof(ledger, "ConditionalClaim", 1, reviewer="Synthetic independent reviewer",
                  evidence_refs=("synthetic:full-audit",),
                  attestation="INDEPENDENT_FULL_PROOF_REVIEW_COMPLETED")
    assert render_proof_status(ledger, "ConditionalClaim", 1, strict=True).startswith("\\paragraph")
    seal = build_evidence_seal(doc, anchor, model, PARAMS, ledger, "ConditionalClaim", 1)
    changed = copy.deepcopy(raw)
    changed["symbols"][0]["domain"]["lower"] = "0.01"
    assert audit_evidence_seal(seal, doc, validate_game_spec(changed), PARAMS, ledger) == "STALE"
    assert audit_evidence_seal(seal, doc, model, {**PARAMS, "gamma": "0.4"}, ledger) == "STALE"


def test_anchor_and_proof_ledger_mutation_invalidates_seal(sample_pdf):
    doc, anchor, _, model, ledger = make_chain(sample_pdf)
    seal = build_evidence_seal(doc, anchor, model, PARAMS, ledger, "ConditionalClaim", 1)
    assert audit_evidence_seal(replace(seal, anchor=replace(anchor, quote="forged")),
                               doc, model, PARAMS, ledger) == "STALE"
    register_obligation(ledger, "ConditionalClaim", 1, "new_debt", "Review additional condition")
    assert audit_evidence_seal(seal, doc, model, PARAMS, ledger) == "STALE"
