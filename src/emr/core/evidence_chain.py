"""Fail-closed cross-phase provenance bindings, never a semantic proof of source text.

PDF snippets remain unverified. Equation interpretation is a separately reviewed
operation; a checked conditional game optimum does not prove a claim about a PDF.
No PDF/LLM text is evaluated as a Python or SymPy expression.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

from emr.adapters.pdf_extract import PdfDocument
from emr.adapters.symbolic_sympy import compile_game
from emr.core.provenance import SourceAnchor, anchor_matches
from emr.domain.equilibrium import backward_induction_two_stage
from emr.domain.game import ValidatedGameSpec
from emr.domain.proof import ProofLedger, model_fingerprint, render_verification_report


class EvidenceChainError(ValueError):
    """Unverified or inconsistent cross-phase evidence cannot be certified."""


@dataclass(frozen=True, slots=True)
class EvidenceSeal:
    """Immutable, content-bound evidence summary; not cryptographic reviewer identity."""

    pdf_sha256: str
    anchor: SourceAnchor
    model_sha256: str
    parameter_sha256: str
    result_sha256: str
    proof_sha256: str
    proposition_id: str
    proof_version: int
    source_status: Literal["NOT_VERIFIED"] = "NOT_VERIFIED"
    mathematical_status: Literal["EQUILIBRIUM_CHECKED"] = "EQUILIBRIUM_CHECKED"
    semantic_bridge_status: Literal["NOT_VERIFIED"] = "NOT_VERIFIED"

    @property
    def status(self) -> str:
        return "BOUND_NOT_PROVED"


def _digest(value: Any) -> str:
    try:
        raw = json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    except (ValueError, TypeError, OverflowError, RecursionError) as exc:
        raise EvidenceChainError("unserializable evidence binding") from exc
    if len(raw) > 65536:
        raise EvidenceChainError("evidence binding budget exceeded")
    return hashlib.sha256(raw).hexdigest()


def anchor_ref(anchor: SourceAnchor) -> str:
    """Canonical exact source locator, not an unverified citation URL."""
    return (f"pdf:{anchor.file_sha256}:p{anchor.page}:b{anchor.block}"
            f":s{anchor.start}-{anchor.end}")


def build_evidence_seal(document: PdfDocument, anchor: SourceAnchor,
                        model: ValidatedGameSpec, parameters: Mapping[str, object],
                        ledger: ProofLedger, proposition_id: str, proof_version: int,
                        *, require_checked: bool = True) -> EvidenceSeal:
    """Recompute all math and proof links from currently supplied source snapshots.

    ModelSpec-to-PDF interpretation remains NOT_VERIFIED even if the game has a
    conditional checked optimum and the provenance anchor is exact.
    """
    if not isinstance(model, ValidatedGameSpec) or not anchor_matches(document, anchor):
        raise EvidenceChainError("source document or validated model is missing/mismatched")
    source = model.data["source"]
    if (source["kind"] != "paper_anchor" or source["file_sha256"] != document.sha256
        or source["page"] != anchor.page):
        raise EvidenceChainError("model source differs from source anchor")
    compiled = compile_game(model)
    fingerprint = model_fingerprint(compiled)
    proposition = ledger.entry(proposition_id, proof_version).proposition
    if proposition["model_sha256"] != fingerprint or anchor_ref(anchor) not in proposition["source_refs"]:
        raise EvidenceChainError("proof lacks exact model/source binding")
    report = render_verification_report(ledger, proposition_id, proof_version)
    if report["scope"]["model_sha256"] != fingerprint:
        raise EvidenceChainError("proof scope no longer matches ModelSpec")
    result = backward_induction_two_stage(model, parameters)
    if require_checked and result.status != "EQUILIBRIUM_CHECKED":
        raise EvidenceChainError("unchecked solver result cannot be promoted downstream")
    if result.status != "EQUILIBRIUM_CHECKED":
        raise EvidenceChainError("this seal supports only checked conditional optima")
    strategies = {name: str(value) for name, value in result.strategies.items()}
    return EvidenceSeal(
        pdf_sha256=document.sha256, anchor=anchor, model_sha256=fingerprint,
        parameter_sha256=_digest(dict(parameters)),
        result_sha256=_digest({"status": result.status, "strategies": strategies,
                               "follower_reaction": str(result.follower_reaction),
                               "leader_status": result.leader_report.status if result.leader_report else None,
                               "follower_status": result.follower_report.status if result.follower_report else None}),
        proof_sha256=_digest(report), proposition_id=proposition_id, proof_version=proof_version,
    )


def audit_evidence_seal(seal: EvidenceSeal, document: PdfDocument,
                        model: ValidatedGameSpec, parameters: Mapping[str, object],
                        ledger: ProofLedger) -> Literal["CURRENT", "STALE"]:
    """Recompute a chain; changed model/parameters/source/proof invalidate the seal."""
    if not isinstance(seal, EvidenceSeal):
        raise EvidenceChainError("expected a recorded evidence seal")
    try:
        current = build_evidence_seal(document, seal.anchor, model, parameters, ledger,
                                      seal.proposition_id, seal.proof_version)
    except (EvidenceChainError, KeyError, ValueError, TypeError):
        return "STALE"
    return "CURRENT" if current == seal else "STALE"
