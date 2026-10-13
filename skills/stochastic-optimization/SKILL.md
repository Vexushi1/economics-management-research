---
name: stochastic-optimization
description: Audit finite uncertainty, conditioning, action information and expected decisions without assuming unavailable distributions.
---

# Stochastic Optimization — Phase 6

1. Record the random **joint** support, state probabilities, source anchors, truncation event and whether the decision occurs **before** or **after** revelation. Do not assume independence from marginal distributions.
2. For a finite distribution, verify all joint masses are in [0,1] and sum **exactly to one**; require each state/action payoff. Finite bounded payoff tables are integrable. Continuous/unbounded support requires a separately specified distribution, tail/integrability proof and future reviewed backend; Phase 6 rejects it.
3. `before_observation`: `max_a sum_s p_s u(s,a)` with a **single nonanticipative** action; `after_observation`: `sum_s p_s max_a u(s,a)` with a state-contingent strategy. This is information value, not a proof of any model's economic assumptions.
4. For truncation, explicitly condition the **original** full finite distribution on a positive-probability event and divide by the retained mass. Unknown tails or absent probabilities are not silently truncated.
5. Exact calculations are only global over the **supplied finite** action list, not continuous production/order optimization or generic Nash equilibrium.
6. For Monte Carlo in later phases, record exact PRNG algorithm/seed/sample size/error bars; do not promote random runs to mathematical proofs. No Monte Carlo sampling exists in this version.
