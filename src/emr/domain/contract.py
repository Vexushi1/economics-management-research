"""Contract feasibility is separate from system efficiency and coordination.

All amounts are exact bounded decimal/rational inputs; no formula evaluation or
paper-text interpretation. Checking IR/IC never implies game equilibrium.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from fractions import Fraction
from typing import Mapping


@dataclass(frozen=True, slots=True)
class ContractCheck:
    status: str
    evidence: tuple[str, ...]


def _value(raw: str | int | Fraction) -> Fraction:
    if isinstance(raw, bool) or not isinstance(raw, (str, int, Fraction)):
        raise ValueError("contract payment must be an exact rational/decimal")
    if isinstance(raw, str) and (len(raw) > 24 or not re.fullmatch(r"-?\d{1,10}(?:\.\d{1,8})?", raw)):
        raise ValueError("untrusted contract expression rejected")
    value = Fraction(raw)
    if abs(value.numerator) > 10**15 or value.denominator > 10**12:
        raise ValueError("contract amount exceeds budget")
    return value


def verify_individual_rationality(payoffs: Mapping[str, str | int | Fraction],
                                  reservations: Mapping[str, str | int | Fraction]) -> ContractCheck:
    """Both/all participants must weakly prefer the contract to not joining."""
    if not payoffs or set(payoffs) != set(reservations):
        return ContractCheck("INVALID_INPUT", ("participant sets differ",))
    rejected = tuple(name for name in sorted(payoffs)
                     if _value(payoffs[name]) < _value(reservations[name]))
    return ContractCheck("IR_VIOLATED" if rejected else "IR_SATISFIED", rejected)


def verify_incentive_compatibility(utilities: Mapping[str, Mapping[str, str | int | Fraction]],
                                   prescribed: Mapping[str, str]) -> ContractCheck:
    """For each type/agent, the prescribed report maximizes reported utility.

    Checks a *finite enumerated* deviation table only. No universal IC proof.
    """
    if not utilities or set(utilities) != set(prescribed):
        return ContractCheck("INVALID_INPUT", ("missing reported type",))
    failures = []
    for agent, payoffs in utilities.items():
        selected = prescribed[agent]
        if selected not in payoffs or not payoffs:
            return ContractCheck("INVALID_INPUT", ("missing prescribed action",))
        if any(_value(v) > _value(payoffs[selected]) for v in payoffs.values()):
            failures.append(agent)
    return ContractCheck("IC_VIOLATED" if failures else "ENUMERATED_IC_SATISFIED",
                         tuple(sorted(failures)))


def test_coordination(decentralized: Mapping[str, str | int | Fraction],
                      centralized: Mapping[str, str | int | Fraction], *,
                      realized_total: str | int | Fraction,
                      centralized_total: str | int | Fraction,
                      individual_payoffs: Mapping[str, str | int | Fraction] | None = None,
                      reservation_payoffs: Mapping[str, str | int | Fraction] | None = None,
                      ic: ContractCheck | None = None) -> dict[str, object]:
    """Decision match, system optimality, IR and IC are distinct checks."""
    same_decisions = set(decentralized) == set(centralized) and all(
        _value(decentralized[k]) == _value(centralized[k]) for k in decentralized)
    efficient = _value(realized_total) == _value(centralized_total)
    ir = (verify_individual_rationality(individual_payoffs, reservation_payoffs)
          if individual_payoffs is not None and reservation_payoffs is not None else None)
    pareto = bool(ir and ir.status == "IR_SATISFIED" and any(
        _value(individual_payoffs[k]) > _value(reservation_payoffs[k])
        for k in individual_payoffs))
    return {"decision_match": same_decisions, "system_profit_match": efficient,
            "ir": ir.status if ir else "NOT_CHECKED",
            "ic": ic.status if ic else "NOT_CHECKED",
            "coordination": "COORDINATED" if same_decisions and efficient else "NOT_COORDINATED",
            "pareto_improvement": pareto}


def verify_transfer_balance(transfers: Mapping[str, str | int | Fraction]) -> ContractCheck:
    """A closed, internal transfer ledger must sum exactly to zero."""
    if not transfers:
        return ContractCheck("INVALID_INPUT", ("empty transfer ledger",))
    net = sum((_value(amount) for amount in transfers.values()), Fraction(0))
    return ContractCheck("TRANSFER_BALANCED" if net == 0 else "TRANSFER_IMBALANCED",
                         ("net=" + str(net),))
