"""Deterministic LaTeX assembly from trusted phase-specific computations.

The only LLM-controlled slots are intro, literature review, and conclusion
plain-text paragraphs. There is no free-form TeX input to the mathematical
portion. The caller must not pass an LLM a trusted proof ledger/solver snapshot
or the full generated manuscript for editing; G6 rechecks the final bytes.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass

import sympy as sp

from emr.adapters.pdf_extract import PdfDocument
from emr.core.evidence_chain import EvidenceSeal, anchor_ref, build_evidence_seal
from emr.core.provenance import SourceAnchor
from emr.domain.citation_audit import CitationRecord, validate_citations
from emr.domain.equilibrium import backward_induction_two_stage
from emr.domain.game import ValidatedGameSpec
from emr.domain.proof import ProofLedger, render_proof_status, render_verification_report

_ALLOWED = ("introduction", "literature_review", "conclusion")
_CITE = re.compile(r"\[CITE:([A-Za-z][A-Za-z0-9_:-]{0,63})\]")
_ESC = {"\\": r"\textbackslash{}", "{": r"\{", "}": r"\}", "%": r"\%",
        "&": r"\&", "#": r"\#", "_": r"\_", "$": r"\$", "^": r"\textasciicircum{}",
        "~": r"\textasciitilde{}"}
_BEGIN = "% EMR-TRUSTED-BEGIN\n"
_END = "% EMR-TRUSTED-END\n"


class ManuscriptError(ValueError):
    """Untrusted text attempted to bypass immutable core assembly constraints."""


@dataclass(frozen=True, slots=True)
class DraftArtifact:
    tex: str
    sha256: str
    core_sha256: str
    evidence_seal: EvidenceSeal
    proposition_id: str
    proof_version: int
    used_claims: tuple[str, ...]


def tex_escape(value: str) -> str:
    """Treat any outside prose as *text*, not an executable LaTeX control layer."""
    if not isinstance(value, str) or any(ord(c) < 32 and c not in "\n\t" for c in value):
        raise ManuscriptError("invalid or control-character-containing prose")
    return "".join(_ESC.get(char, char) for char in value)


def _prose(prose: Mapping[str, str], refs: tuple[CitationRecord, ...]) -> tuple[dict[str, str], tuple[str, ...]]:
    if not isinstance(prose, Mapping) or set(prose) != set(_ALLOWED):
        raise ManuscriptError("only three LLM prose slots are permitted")
    by_claim = {ref.claim_id: ref.key for ref in refs}
    sections: dict[str, str] = {}
    used: list[str] = []
    for key in _ALLOWED:
        s = prose[key]
        if not isinstance(s, str) or not s.strip() or len(s.encode("utf-8")) > 12000:
            raise ManuscriptError("empty or oversized prose slot")
        positions: list[str] = []
        cursor = 0
        for match in _CITE.finditer(s):
            claim = match.group(1)
            if claim not in by_claim:
                raise ManuscriptError("undeclared citation claim reference")
            positions.append(tex_escape(s[cursor:match.start()]))
            positions.append(r"\cite{" + by_claim[claim] + "}")
            cursor = match.end()
            used.append(claim)
        positions.append(tex_escape(s[cursor:]))
        sections[key] = "".join(positions)
    return sections, tuple(dict.fromkeys(used))


def _trusted_math(model: ValidatedGameSpec, parameters: Mapping[str, object],
                  ledger: ProofLedger, proposition_id: str, proof_version: int,
                  seal: EvidenceSeal) -> str:
    result = backward_induction_two_stage(model, parameters)
    if result.status != "EQUILIBRIUM_CHECKED":
        raise ManuscriptError("no checked conditional optimum available for trusted macro")
    report = render_verification_report(ledger, proposition_id, proof_version)
    prop = ledger.entry(proposition_id, proof_version).proposition
    math = r",\;".join(
        sp.latex(sp.Symbol(name, real=True)) + "=" + sp.latex(value)
        for name, value in sorted(result.strategies.items())
    )
    # Phase 5 renders the unproven marker; assembly must not hand this section to an LLM.
    # Phase 5 controls strict-vs-unproven semantics. Render the marker with
    # escaped text; Phase 5's raw status renderer is not itself TeX-escaped.
    proof_state = render_proof_status(ledger, proposition_id, proof_version, format="status")
    label = tex_escape(f"{proposition_id}-v{proof_version}")
    if proof_state == "PROVED":
        proof = r"\paragraph{Proof " + label + "} [INDEPENDENTLY REVIEWED; see evidence ledger]"
    else:
        proof = (r"\paragraph{Proof " + label + r"} \unproven{" +
                 tex_escape(f"{proposition_id}-v{proof_version}: {report['verdict']}") + "}")
    lines = (
        r"\newcommand{\EMRModelHash}{" + seal.model_sha256 + "}",
        r"\newcommand{\EMRParameterHash}{" + seal.parameter_sha256 + "}",
        r"\newcommand{\EMREquilibrium}{\ensuremath{" + math + "}}",
        r"\newcommand{\EMRPropositionText}{" + tex_escape(prop["statement"]) + "}",
        r"\newcommand{\EMRProofVerdict}{\texttt{" + tex_escape(report["verdict"]) + "}}",
        r"\newcommand{\EMRSourceAnchor}{\texttt{" + tex_escape(anchor_ref(seal.anchor)) + "}}",
        r"\newcommand{\EMRProofAppendix}{" + proof + "}",
    )
    return _BEGIN + "\n".join(lines) + "\n" + _END


def trusted_core(text: str) -> str | None:
    """Return the unique delimited, deterministic core, or signal tampering."""
    if not isinstance(text, str) or text.count(_BEGIN) != 1 or text.count(_END) != 1:
        return None
    start = text.find(_BEGIN)
    end = text.find(_END, start)
    if end < start:
        return None
    return text[start:end + len(_END)]


def assemble_manuscript(document: PdfDocument, anchor: SourceAnchor,
                        model: ValidatedGameSpec, parameters: Mapping[str, object],
                        ledger: ProofLedger, proposition_id: str, proof_version: int,
                        prose: Mapping[str, str], citations: tuple[CitationRecord, ...]) -> DraftArtifact:
    """Rebuild from authoritative inputs; do not accept user-authored math sections."""
    refs = validate_citations(citations)
    sections, used = _prose(prose, refs)
    seal = build_evidence_seal(document, anchor, model, parameters, ledger,
                               proposition_id, proof_version)
    core = _trusted_math(model, parameters, ledger, proposition_id, proof_version, seal)
    # Only audited keys are emitted as cite commands. All outside prose is escaped.
    tex = (
        r"\documentclass{article}" + "\n" +
        r"\usepackage[T1]{fontenc}" + "\n" +
        r"\providecommand{\unproven}[1]{\textbf{[UNPROVEN: #1]}}" + "\n" +
        core +
        r"\begin{document}" + "\n" +
        r"\section{Introduction}" + "\n" + sections["introduction"] + "\n" +
        r"\section{Literature Review}" + "\n" + sections["literature_review"] + "\n" +
        r"\section{Model and Equilibrium}" + "\n" +
        r"Conditional checked equilibrium: \EMREquilibrium{}." + "\n" +
        r"\section{Proposition}" + "\n" +
        r"\EMRPropositionText{} \EMRProofVerdict{}." + "\n" +
        r"\section{Conclusions}" + "\n" + sections["conclusion"] + "\n" +
        r"\appendix" + "\n" + r"\EMRProofAppendix{}" + "\n" +
        r"\end{document}" + "\n"
    )
    return DraftArtifact(tex=tex, sha256=hashlib.sha256(tex.encode("utf-8")).hexdigest(),
                         core_sha256=hashlib.sha256(core.encode("utf-8")).hexdigest(),
                         evidence_seal=seal, proposition_id=proposition_id,
                         proof_version=proof_version, used_claims=used)


def collect_verified_results(model: ValidatedGameSpec, parameters: Mapping[str, object]) -> dict[str, object]:
    """Read-only checked conditional strategies; never infer theorem proof status."""
    r = backward_induction_two_stage(model, parameters)
    if r.status != "EQUILIBRIUM_CHECKED":
        raise ManuscriptError("solver does not certify this case")
    return {"status": r.status, "strategies": {k: str(v) for k, v in r.strategies.items()}}


def render_section_outline() -> tuple[str, ...]:
    """Only the designated prose slots are editable by a writing model."""
    return _ALLOWED
