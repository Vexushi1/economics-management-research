"""Incomplete original-paper inputs must fail BEFORE any numerical comparison."""

from copy import deepcopy

import pytest

from emr.domain.replication import (
    ReplicationInputError,
    build_replication_manifest,
    classify_discrepancy,
    compare_results,
)


def manifest_request():
    return {"paper_sha256": "a"*64, "model_id": "synthetic_supply_1",
            "required_parameters": ["cost", "demand_std"],
            "parameters": {"cost": {"value": "3.5", "source_ref": "source:page:2"},
                           "demand_std": {"value": "2", "source_ref": "source:page:3"}},
            "formula_anchors": ["source:page:4:eq2"],
            "targets": [{"id": "table2", "kind": "TABLE", "source_ref": "source:page:8"}]}


def test_missing_parameter_returns_unreproducible_input_and_never_substitutes():
    request = manifest_request()
    del request["parameters"]["demand_std"]
    output = build_replication_manifest(request)
    assert output["status"] == "UNREPRODUCIBLE_INPUT"
    assert output["missing_requirements"] == ["demand_std"]
    assert not any(p["name"] == "demand_std" for p in output["parameter_provenance"])
    assert classify_discrepancy(output) == "MISSING_SOURCE_FACTS"
    refused = compare_results(output, {"table2": "5"}, {"table2": "5"})
    assert refused["status"] == "UNREPRODUCIBLE_INPUT"
    assert refused["targets"][0]["computed_value"] is None


def test_missing_original_formula_or_parameter_source_blocks():
    request = manifest_request()
    request["formula_anchors"] = []
    output = build_replication_manifest(request)
    assert "ORIGINAL_FORMULA_ANCHORS" in output["missing_requirements"]
    request = manifest_request()
    request["parameters"]["cost"]["source_ref"] = ""
    assert "cost" in build_replication_manifest(request)["missing_requirements"]


def test_one_missing_published_result_blocks_even_when_other_target_matches():
    request = manifest_request()
    request["targets"].append({"id": "figure3", "kind": "FIGURE", "source_ref": "p9"})
    output = compare_results(build_replication_manifest(request), {"table2": "5"},
                             {"table2": "5", "figure3": "1"})
    assert output["status"] == "UNREPRODUCIBLE_INPUT"
    assert output["missing_requirements"] == ["NUMERIC_TARGET:figure3"]


def test_numerical_agreement_is_not_mathematical_proof():
    request = manifest_request()
    ready = build_replication_manifest(request)
    assert ready["status"] == "READY_FOR_REPLICATION"
    report = compare_results(ready, {"table2": "1.2"}, {"table2": "1.2000003"},
                             tolerance="0.000001")
    assert report["status"] == "NUMERIC_COMPARISON_COMPLETE"
    assert classify_discrepancy(report) == "WITHIN_ABSOLUTE_TOLERANCE"
    assert "NUMERIC_AGREEMENT_IS_NOT_THEOREM_PROOF" in report["diagnostics"]
    difference = compare_results(ready, {"table2": "1.2"}, {"table2": "1.1"})
    assert difference["status"] == "COMPARISON_MISMATCH"
    assert classify_discrepancy(difference) == "OBSERVED_NUMERIC_DISCREPANCY_CAUSE_UNKNOWN"
    assert ready["targets"][0]["computed_value"] is None  # immutable input


def test_missing_parameter_from_paper_does_not_become_default():
    original = manifest_request()
    expected = deepcopy(original)
    for value in (None, "", "NaN", "0.5+0.1", 0.5):
        data = deepcopy(original)
        data["parameters"]["demand_std"]["value"] = value
        assert build_replication_manifest(data)["status"] == "UNREPRODUCIBLE_INPUT"
    assert original == expected


def test_duplicate_or_undocumented_target_rejected():
    request = manifest_request()
    request["targets"].append(request["targets"][0])
    with pytest.raises(ReplicationInputError):
        build_replication_manifest(request)


def test_forged_ready_report_without_required_parameter_rejected():
    ready = build_replication_manifest(manifest_request())
    forged = deepcopy(ready)
    forged["parameter_provenance"].pop()
    with pytest.raises(ReplicationInputError, match="complete parameter"):
        compare_results(forged, {"table2": "4"}, {"table2": "4"})


def test_numeric_comparison_rejects_expression_instead_of_original_value():
    ready = build_replication_manifest(manifest_request())
    result = compare_results(ready, {"table2": "a+3"}, {"table2": "5"})
    assert result["status"] == "UNREPRODUCIBLE_INPUT"
    assert "NUMERIC_TARGET:table2" in result["missing_requirements"]


def test_forged_completed_report_with_unchecked_targets_is_rejected():
    ready = build_replication_manifest(manifest_request())
    forged = deepcopy(ready)
    forged["status"] = "NUMERIC_COMPARISON_COMPLETE"
    with pytest.raises(ReplicationInputError, match="unverified numerical"):
        classify_discrepancy(forged)


def test_comparison_result_cannot_be_reused_as_an_approved_new_manifest():
    ready = build_replication_manifest(manifest_request())
    compared = compare_results(ready, {"table2": "1"}, {"table2": "1"})
    with pytest.raises(ReplicationInputError, match="uncompared ready manifest"):
        compare_results(compared, {"table2": "1"}, {"table2": "2"})


def test_forged_numeric_status_or_difference_is_rejected():
    ready = build_replication_manifest(manifest_request())
    genuine = compare_results(ready, {"table2": "5"}, {"table2": "4"}, tolerance="0.000001")
    assert genuine["status"] == "COMPARISON_MISMATCH"
    for field, replacement in (("status", "NUMERIC_MATCH"), ("absolute_error", "0"),
                               ("published_value", "4")):
        forged = deepcopy(genuine)
        forged["targets"][0][field] = replacement
        if field == "status":
            forged["status"] = "NUMERIC_COMPARISON_COMPLETE"
        with pytest.raises(ReplicationInputError, match="forged or inconsistent"):
            classify_discrepancy(forged)
    forged = deepcopy(genuine)
    forged["comparison_tolerance"] = None
    with pytest.raises(ReplicationInputError, match="requires its exact tolerance"):
        classify_discrepancy(forged)


def test_valid_saved_numeric_report_revalidates_exact_arithmetic():
    ready = build_replication_manifest(manifest_request())
    actual = compare_results(ready, {"table2": "5"}, {"table2": "5.0000002"},
                             tolerance="0.000001")
    assert actual["status"] == "NUMERIC_COMPARISON_COMPLETE"
    assert classify_discrepancy(actual) == "WITHIN_ABSOLUTE_TOLERANCE"
