"""Adversarial empirical claims: assertions and prediction do not prove causation."""

import json
from pathlib import Path

import pytest

from emr.domain.econometrics import (
    EmpiricalDesignError,
    check_identification_assumptions,
    collect_estimand,
    render_empirical_claim,
    validate_design,
)

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures/synthetic_panel/did_design.json"


def design():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_complete_did_assumptions_do_not_establish_causality():
    checked = validate_design(design())
    result = check_identification_assumptions(checked)
    assert result.status == "ASSUMPTIONS_DOCUMENTED_NOT_VERIFIED"
    assert result.causal_claim_allowed is False
    assert collect_estimand(checked).name == "ATT"
    assert collect_estimand(checked).status == "DEFINED_NOT_ESTIMATED"
    with pytest.raises(EmpiricalDesignError, match="causal effect forbidden"):
        render_empirical_claim(checked, claim_kind="causal")


@pytest.mark.parametrize("missing", (
    "parallel_trends", "common_support", "no_anticipation", "no_spillovers"
))
def test_did_missing_assumptions_are_critical(missing):
    raw = design()
    raw["assumptions"] = [row for row in raw["assumptions"] if row["name"] != missing]
    result = check_identification_assumptions(validate_design(raw))
    assert result.status == "IDENTIFICATION_INCOMPLETE"
    assert result.severity == "CRITICAL"
    assert missing in result.missing_assumptions


def test_iv_exclusion_relevance_and_trusted_evidence_refs():
    raw = design()
    raw.update(method="iv", estimand="LATE", data_structure="cross_section")
    raw["assumptions"] = [
        {"name": "relevance", "status": "ASSERTED_NOT_VERIFIED",
         "evidence_refs": ["synthetic:design"]},
    ]
    result = check_identification_assumptions(validate_design(raw))
    assert "exclusion_restriction" in result.missing_assumptions
    raw["assumptions"][0]["evidence_refs"] = ["undeclared:ref"]
    with pytest.raises(EmpiricalDesignError):
        validate_design(raw)


def test_prediction_and_association_never_become_causal_effects():
    for method, intent, estimand in (
        ("predictive", "prediction", "PREDICTION"),
        ("descriptive", "association", "ASSOCIATION"),
    ):
        raw = design()
        raw.update(method=method, intent=intent, estimand=estimand,
                   data_structure="cross_section", assumptions=[])
        checked = validate_design(raw)
        assert render_empirical_claim(checked, claim_kind=intent) .endswith("NOT_ESTIMATED")
        with pytest.raises(EmpiricalDesignError):
            render_empirical_claim(checked, claim_kind="causal")
        raw["intent"] = "causal"
        with pytest.raises(EmpiricalDesignError):
            validate_design(raw)


def test_method_estimand_and_panel_data_structure_consistency():
    raw = design()
    raw["estimand"] = "ATE"
    with pytest.raises(EmpiricalDesignError):
        validate_design(raw)
    raw = design()
    raw["data_structure"] = "cross_section"
    with pytest.raises(EmpiricalDesignError):
        validate_design(raw)


def test_unknown_objects_and_oversized_inputs_are_rejected():
    raw = design()
    raw["additional"] = object()
    with pytest.raises(EmpiricalDesignError):
        validate_design(raw)
    raw = design()
    raw["target_population"] = "z" * 50000
    with pytest.raises(EmpiricalDesignError):
        validate_design(raw)


def test_theory_only_requires_no_empirical_data_or_statistical_package():
    from emr.domain.game import validate_game_spec

    baseline = FIXTURE.parents[1] / "stackelberg_linear/baseline.json"
    assert validate_game_spec(json.loads(baseline.read_text(encoding="utf-8"))).classification == "static_sequential_game"
