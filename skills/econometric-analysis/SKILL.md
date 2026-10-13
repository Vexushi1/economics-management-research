# Econometric design and causal identification (Phase 7, optional)

## Purpose

Use only for empirical or mixed research. Theory-only model design and proof audit must not require empirical data. This version checks **identification designs**, not causal effects or regression coefficients; there is no statistical estimator.

## Required process

1. Define target population, units, time, treatment, outcome, treatment timing and the **estimand** first.
2. Separate association, prediction and causal inference. Statistical significance or predictive performance is not a causal identification argument.
3. DID: document parallel trends, no anticipation, no spillovers and common support. Account for heterogeneous/staggered adoption and pre-trend uncertainty before choosing an estimator; two-way fixed effects are not always a valid staggered DID estimand.
4. IV: document relevance, exclusion restriction, instrument exogeneity/as-if-random and monotonicity for LATE. Weak instruments and exclusion failures cannot be repaired by a significant 2SLS coefficient.
5. Panel FE: document strict exogeneity, stable unit mapping and no perfect collinearity; unobserved time-varying confounding is not automatically controlled.
6. Each asserted assumption requires a source reference, but a reference is not independent verification. Missing assumptions: CRITICAL. Complete declarations: ASSUMPTIONS_DOCUMENTED_NOT_VERIFIED.
7. Without independently checked data and identification review, emit only DEFINED_NOT_ESTIMATED or the appropriate not-verified design state. The Phase 7 causal claim renderer always blocks publication of causal effect claims.
8. No external transmission of private datasets. A separately approved future phase may implement estimation with standard errors, identification diagnostics, sensitivity tests and validated result schemas.

## Limits

Synthetic test panels are not real-world causal evidence. This skill must not weaken Phase 5's proof-status and Phase 1-6 provenance requirements.
