"""IR/IC and centralized efficiency must be evaluated separately."""

import json
from pathlib import Path

import pytest

from emr.domain import contract

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures/contract_coordination/ir_violation.json"


def test_violated_ir_blocks_claim_of_mutual_gain():
    data = json.loads(FIXTURE.read_text())
    ir = contract.verify_individual_rationality(data["payoffs"], data["reservations"])
    assert ir.status == "IR_VIOLATED"
    assert ir.evidence == ("influencer",)
    report = contract.test_coordination(data["decentralized"], data["centralized"],
        realized_total=data["system_total"], centralized_total=data["centralized_total"],
        individual_payoffs=data["payoffs"], reservation_payoffs=data["reservations"])
    assert report["decision_match"] and report["system_profit_match"]
    assert report["coordination"] == "COORDINATED"
    assert report["ir"] == "IR_VIOLATED"
    assert not report["pareto_improvement"]


def test_ir_ic_checks_are_independent_of_efficiency():
    ic = contract.verify_incentive_compatibility({"agent": {"work": "1", "shirk": "3"}},
                                        {"agent": "work"})
    assert ic.status == "IC_VIOLATED"
    result = contract.test_coordination({"price": "6"}, {"price": "7"}, realized_total="10",
                                 centralized_total="11", ic=ic)
    assert not result["decision_match"]
    assert not result["system_profit_match"]
    assert result["ic"] == "IC_VIOLATED"
    assert result["ir"] == "NOT_CHECKED"


def test_ir_satisfied_without_strict_improvement_is_not_pareto_improvement():
    v = contract.test_coordination({"price": "6"}, {"price": "6"}, realized_total="10",
                            centralized_total="10", individual_payoffs={"a": "0", "b": "0"},
                            reservation_payoffs={"a": "0", "b": "0"})
    assert v["ir"] == "IR_SATISFIED" and not v["pareto_improvement"]


def test_contract_rejects_untrusted_formula_text():
    with pytest.raises(ValueError):
        contract.verify_individual_rationality({"a": '__import__("os")'}, {"a": "0"})


def test_internal_transfer_conservation():
    assert contract.verify_transfer_balance({"retailer": "-3.5", "influencer": "3.5"}).status == "TRANSFER_BALANCED"
    assert contract.verify_transfer_balance({"retailer": "-3.5", "influencer": "3"}).status == "TRANSFER_IMBALANCED"
