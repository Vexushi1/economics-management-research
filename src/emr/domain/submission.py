"""G6: replay the trusted source, math, proof and citation ledgers.

Never trust a manuscript's own hash/status or a DOI to assert scholarly truth.
A newly edited .tex is untrusted input; compare it with independently rebuilt
content, not the hash stored in that same .tex file or its adjacent metadata.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Literal

from emr.adapters.pdf_extract import PdfDocument
from emr.core.evidence_chain import audit_evidence_seal
from emr.core.provenance import SourceAnchor
from emr.domain.citation_audit import CitationAuditError, CitationRecord, validate_citations
from emr.domain.game import ValidatedGameSpec
from emr.domain.manuscript import DraftArtifact, ManuscriptError, assemble_manuscript, trusted_core
from emr.domain.proof import ProofAuditError, ProofLedger, render_verification_report


@dataclass(frozen=True, slots=True)
class GateFinding:
    code: str
    severity: Literal["BLOCKER", "WARNING"]
    message: str
    expected_digest: str | None = None
    observed_digest: str | None = None


@dataclass(frozen=True, slots=True)
class G6Report:
    status: Literal["BLOCKED", "READY_FOR_SUBMISSION"]
    findings: tuple[GateFinding, ...]
    recalculated_tex_sha256: str | None
    upstream_status: Literal["CURRENT", "STALE"]


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def check_claim_evidence(citations: tuple[CitationRecord, ...],
                         used_claims: tuple[str, ...]) -> tuple[GateFinding, ...]:
    """A real/canonical DOI is not evidence of claim support.

    This cannot infer semantic contradiction by reading the DOI alone. Evidence
    verdicts must originate in an external documented source-content review.
    """
    findings: list[GateFinding] = []
    try:
        rows = validate_citations(citations)
    except (CitationAuditError, ValueError, TypeError) as exc:
        return (GateFinding("CITATION_CONTRACT_INVALID", "BLOCKER", str(exc)),)
    indexed = {r.claim_id: r for r in rows}
    for claim in used_claims:
        if claim not in indexed:
            findings.append(GateFinding("CITATION_KEY_MISSING", "BLOCKER", f"claim={claim}"))
    for row in rows:
        if row.support_status == "CLAIM_UNSUPPORTED":
            findings.append(GateFinding("CLAIM_UNSUPPORTED", "BLOCKER",
                                        f"key={row.key}; doi={row.doi}; review={row.support_review_ref}"))
        elif row.support_status != "CLAIM_SUPPORTED":
            findings.append(GateFinding("CLAIM_NOT_VERIFIED", "BLOCKER",
                                        f"key={row.key}; doi={row.doi}"))
        if row.metadata_status != "VERIFIED":
            findings.append(GateFinding("DOI_METADATA_NOT_VERIFIED", "BLOCKER",
                                        f"key={row.key}; DOI existence and attribution not verified"))
        if row.retraction_status != "CLEAR":
            findings.append(GateFinding("RETRACTION_STATUS_UNCLEAR", "BLOCKER",
                                        f"key={row.key}; status={row.retraction_status}"))
    return tuple(findings)


def audit_submission(draft: DraftArtifact, *, final_tex: str, document: PdfDocument,
                     anchor: SourceAnchor, model: ValidatedGameSpec,
                     parameters: Mapping[str, object], ledger: ProofLedger,
                     prose: Mapping[str, str], citations: tuple[CitationRecord, ...]) -> G6Report:
    """Fail closed with *multi-cause* audit log, not premature short circuit.

    Phase 7 provenance facts are recalculated from independent references;
    Phase 5 proof state must be PROVED. Source semantic correspondence is
    unverified by the present pipeline, so default release is BLOCKED.
    """
    if not isinstance(draft, DraftArtifact):
        raise TypeError("a recorded deterministic draft artifact is required")
    issues: list[GateFinding] = []
    def fail(code: str, message: str, *, expected: str | None = None,
             observed: str | None = None) -> None:
        issues.append(GateFinding(code, "BLOCKER", message, expected, observed))

    observed_tex_digest = _hash(final_tex) if isinstance(final_tex, str) and len(final_tex) <= 256000 else None
    if observed_tex_digest is None:
        fail("DRAFT_INPUT_INVALID", "unreadable or oversized final LaTeX source")
        final_tex = ""
    if _hash(draft.tex) != draft.sha256:
        fail("DRAFT_LEDGER_SHA_MISMATCH", "recorded draft hash does not match its stored contents",
             expected=draft.sha256, observed=_hash(draft.tex))
    final_core = trusted_core(final_tex)
    if final_core is None:
        fail("TRUSTED_MACRO_MISSING_OR_DUPLICATED", "exactly one immutable math block required")
    elif _hash(final_core) != draft.core_sha256:
        fail("TRUSTED_MACRO_TAMPERED", "math/proof macro block differs from immutable draft",
             expected=draft.core_sha256, observed=_hash(final_core))
    if final_tex != draft.tex:
        fail("FINAL_TEX_DRIFT", "final .tex differs from recorded deterministic assembly",
             expected=draft.sha256, observed=observed_tex_digest)

    if audit_evidence_seal(draft.evidence_seal, document, model, parameters, ledger) != "CURRENT":
        fail("UPSTREAM_STALE", "PDF/model/parameters/solver/proof ledger fingerprint changed")
        upstream = "STALE"
    else:
        upstream = "CURRENT"
    if draft.evidence_seal.source_status != "NOT_VERIFIED" or draft.evidence_seal.semantic_bridge_status != "NOT_VERIFIED":
        fail("EVIDENCE_STATUS_FORGED", "source/semantic bridge status is not the established contract")
    # There is no authenticated Phase 8 semantic bridge reviewer yet. Do not
    # pretend a PDF locator demonstrates source meaning or claim support.
    fail("SEMANTIC_BRIDGE_NOT_VERIFIED", "paper-to-model interpretation needs independent source review")

    try:
        report = render_verification_report(ledger, draft.proposition_id, draft.proof_version)
        if report["verdict"] != "PROVED" or report["open_obligations"]:
            fail("UNPROVEN_PROPOSITION", "proposition proof is not independently certified; "
                 f"status={report['verdict']}; open={report['open_obligations']}")
    except (ProofAuditError, KeyError, ValueError) as exc:
        fail("PROOF_LEDGER_UNAVAILABLE", f"recompute proof failed: {type(exc).__name__}")

    # Independent regeneration catches a forged draft+hash pair, and untrusted
    # math snippets inserted outside the delimited core (not only macros).
    try:
        expected = assemble_manuscript(document, anchor, model, parameters, ledger,
                                       draft.proposition_id, draft.proof_version,
                                       prose, citations)
        if expected.tex != final_tex:
            fail("CANONICAL_REBUILD_MISMATCH",
                 "reassembled trusted inputs do not match submitted bytes",
                 expected=expected.sha256, observed=observed_tex_digest)
        if expected.evidence_seal != draft.evidence_seal:
            fail("SNAPSHOT_BINDING_MISMATCH", "draft seal differs from independently rebuilt seal")
        if expected.used_claims != draft.used_claims:
            fail("CITATION_USAGE_TAMPERED", "recorded cited claim IDs were changed")
        used_claims = expected.used_claims
    except (ManuscriptError, ValueError, KeyError, TypeError) as exc:
        fail("CANONICAL_REBUILD_FAILED", f"independent assembly failed: {type(exc).__name__}")
        used_claims = draft.used_claims

    issues.extend(check_claim_evidence(citations, used_claims))
    return G6Report("BLOCKED" if issues else "READY_FOR_SUBMISSION", tuple(issues),
                    observed_tex_digest, upstream)


def render_g6_report(report: G6Report) -> dict[str, object]:
    """Structured submission audit log, checked against packaged JSON Schema."""
    import json
    from importlib.resources import files

    from jsonschema import Draft202012Validator

    if not isinstance(report, G6Report):
        raise TypeError("G6Report required")
    content = {"schema_version": "1", **asdict(report)}
    content["findings"] = list(content["findings"])
    schema = json.loads(files("emr").joinpath("schemas/g6-audit.schema.json")
                        .read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(content)
    return content
