---
name: paper-replication
description: Check source-anchored model parameters before comparing computations with reported paper outputs.
---

# Paper Replication — Phase 6

1. Retain private source PDFs outside Git; record a SHA-256 identity, page/section/formula anchors and exact version of the reference.
2. Distinguish assumptions, original symbolic formulas, reproduced numerical values, tables/figures and mathematical proof. Never present matching numerical tables as theorem verification.
3. Enumerate all **required** exogenous parameters and their true source coordinates. The absence of cost coefficients, distribution parameters, standard deviations, or original formula anchors is `UNREPRODUCIBLE_INPUT` and blocks computation. Do **not** insert a convenient benchmark value, zero, sample estimate or inferred parameter.
4. Report side-by-side exact numeric differences with a predeclared tolerance. Missing published or computed target is `UNREPRODUCIBLE_INPUT`. An observed difference is not automatically a mistake in the publication; its cause remains unknown until independently investigated.
5. Keep partial reproductions scoped: never infer untested results from a successful formula/table. For stochastic simulation, record algorithm, seed, sample count, and confidence uncertainty before meaningful comparisons.
6. Do not send private manuscripts to external APIs or publish copyrighted papers as test fixtures; use original synthetic fixtures.
