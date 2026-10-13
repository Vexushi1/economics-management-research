---
name: dynamic-optimal-control
description: Validate deterministic scalar linear-state controls and issue necessary PMP obligations without claiming HJB solutions.
---

# Dynamic Optimal Control — Phase 6

1. Separate finite-horizon deterministic ODEs from stochastic supply scenarios, stochastic differential equations, differential games and HJB PDEs. Do not infer dynamic time from an exponent alone.
2. Supply state initial value, horizon, exact linear-affine drift `x'=a*x+b*u+c`, bounded control interval, quadratic running reward and explicit free/fixed terminal treatment. A fixed terminal state has an unknown terminal co-state multiplier; never set it to zero.
3. Construct Hamiltonian, costate derivative, switching derivative and boundary/transversality candidate conditions only. With box constraints, `dH/du=0` **alone is insufficient**; require the box maximum condition. This version does not solve the state-co-state BVP, does not establish sufficiency and never returns `SOLVED`.
4. Nonlinear dynamics, stochastic HJB and stochastic/differential games return `UNSUPPORTED` **before any symbolic construction**. Missing initial/terminal facts return `INCOMPLETE_INPUT`.
5. All drift/payoff coefficients must be bounded finite numeric literals. Never evaluate raw PDF/LLM mathematical strings or call dynamic string parsers.
