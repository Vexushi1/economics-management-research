# Principal–agent contracts — reference

**Scope:** delegated effort and contract choice when actions are hidden, types are private, or agents have outside options. Do not treat moral hazard and adverse selection as interchangeable.

Audit these primitives before claiming a contract mechanism:

- **Information structure:** who observes the worker/influencer effort, type, sales and noisy outcome, and at which stage? A hidden type must not be entered in the principal's information set as a known realization.
- **Contracts:** definition and units of commission, fixed fee, revenue-sharing or transfer, and what is verifiable/contractible.
- **IR (individual rationality):** define agent's expected utility and outside option by type. Do not equate aggregate profit growth with individual participation.
- **IC (incentive compatibility):** model best-response or truthful-report requirements conditional on information partitions; IC cannot be asserted by a bare payoff expression.
- **Feasibility/budget:** transfer accounting, liability limits and timing; distinguish system coordination from a Pareto improvement.
- **Boundary checks:** binding IR/IC, pooling/separating regimes, and multiple optimal contracts.

**Sources:** B. Holmström, “Moral Hazard and Observability,” *Bell Journal of Economics* (1979); J. Mirrlees, “An Exploration in the Theory of Optimum Income Taxation,” *Review of Economic Studies* (1971); [pAI-Econ-codex](https://github.com/Cavaradossi/pAI-Econ-codex/tree/84385fb1b4e093b22acae7fd7a8a5381762fb638) as an index of theoretical workflows.

**Phase 3 limit:** the current model DSL covers public discrete stages and declared signal availability. Full Bayesian information partitions and expectation operators require a separately versioned extension, not silent automatic assumptions.
