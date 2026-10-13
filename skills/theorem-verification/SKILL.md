---
name: theorem-verification
description: Track mathematical proof obligations, independent adjudication and exact checked counterexamples without treating numeric agreement as proof.
---
# Theorem Verification — Phase 5

1. Record a precise proposition (quantifiers, assumptions, parameter domains, model/content digest, proof version, references).
2. Register explicit numbered proof obligations. A step can be `OK`, `GAP`, `ERROR`, or `UNCLEAR`. Each `OK` requires traceable evidence and **never** by itself proves a theorem.
3. `SKETCH_ACCEPTED` only acknowledges a complete-looking argument; strict labels require explicit independent full-proof review and zero open obligations. A separate version is required after scope revision.
4. Recheck any purported counterexample with exact feasible substitutions. Optimization counterexamples additionally need a *checked global* Phase 4 optimum; numerical root failure is not a counterexample.
5. A verified contradiction freezes that exact proposition version as `REFUTED`. Create a new restricted-domain version rather than altering a refuted record.
6. Appendices must retain `\\unproven{}` for all unresolved records. No writing tool can remove proof debts to improve prose appearance.
7. Do not send PDF mathematical text to `eval`, `exec`, dynamic SymPy parsers, shell or external paid services. Numerical cross-checks supplement but do not replace mathematical arguments.
