# Phase 8 — Restricted academic writing

Purpose: produce text drafts without changing audited mathematics. Input source is the actual evidence ledger, not generative restatements.

Only three untrusted plain-text slots are accepted: `introduction`, `literature_review`, `conclusion`. All backslashes, braces, control symbols and TeX metacharacters are escaped; citations must use declared `[CITE:claim_id]` markers and are inserted deterministically. No LLM-authored raw LaTeX, Model Setup, Equilibrium Analysis, theorem, quantitative result, proof, tables or macros.

The assembly engine compiles checked conditional equilibria from a Phase 3 validated JSON AST and Phase 4 engine. Phase 5 proof status is injected directly from the ledger; `SKETCH_ACCEPTED` stays unproved. Core macro bytes are audited against freshly recomputed values. Do not send private model facts or whole manuscripts to external LLMs without explicit authorization. A sanitized writing slot alone does not make prose semantically true; human review remains required.

Claim citations must be separately reviewed: DOI validity/metadata and substantive claim support are different validations. No invented references, effects, quantitative generalizations, or universal statements from pointwise numerical runs.
