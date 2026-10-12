# Economic model library — evidence-linked reference index

These documents are **conceptual references**, not executable model code, copied third-party Skills, mathematical proof, or a representation that all cited publications share the same assumptions.

| Reference | Suitable for | Unresolved checks |
|---|---|---|
| [Stackelberg](stackelberg.md) | sequential leader–follower pricing, effort, channel decisions | follower feasible best-response sets, timing, existence, multiple equilibria |
| [Platform/Hotelling](platform-hotelling.md) | differentiated sellers/platforms, participation and multi-sided interaction | consumer indifference, segment bounds, cross-side network feedback, corner cases |
| [Principal–agent](principal-agent.md) | hidden type/action, platform/influencer contract design | IR/IC, outside options, observability, transfers and timing |

## Sources and provenance

- Upstream framework considered **as a reference**: [pAI-Econ-codex](https://github.com/Cavaradossi/pAI-Econ-codex/tree/84385fb1b4e093b22acae7fd7a8a5381762fb638) (model-library taxonomy and economic research workflow). This project did not copy its files. See `third_party/SOURCES.md`.
- Classical references: H. von Stackelberg, *Marktform und Gleichgewicht* (1934); H. Hotelling, “Stability in Competition,” *Economic Journal* (1929); B. Holmström, “Moral Hazard and Observability,” *Bell Journal of Economics* (1979); J. Mirrlees, “An Exploration in the Theory of Optimum Income Taxation,” *Review of Economic Studies* (1971).
- Applied taxonomy anchor: Q. Li, S. Zhu, T.-M. Choi and B. Shen, “Maintaining E-commerce Supply Chain Viability: Addressing Supply Risks with a Strategic Live-Streaming Channel,” *Omega*, DOI [10.1016/j.omega.2025.103276](https://doi.org/10.1016/j.omega.2025.103276). The associated synthetic taxonomy fixture is **not** their exact payoff function or decision ordering.

For each actual use, cite and audit the source's explicit model primitives; never invent its assumptions, numerical values or proposition proofs.
