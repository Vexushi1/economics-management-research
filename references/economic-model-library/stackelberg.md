# Stackelberg: sequential best responses (reference, not a solver)

**Baseline concept.** A leader commits to an observable action; one or more followers observe signals according to declared information sets and choose their own strategies. Equilibrium requires followers to choose feasible best responses and the leader to optimize anticipating the specified response correspondence. Multiple follower best responses require an explicit selection rule or a set-valued answer.

## Minimal model facts

- Players, timing and observability: identify the leader's stage, follower's stage, and exactly when the action becomes public. An earlier actor cannot observe a future realization.
- Strategy sets: every leader/follower action needs its own declared domain (boundaries and strictness included).
- Payoffs: record the exact objective AST and any participation/feasibility constraints, with units and signed parameter domains.
- Verification *later*: follower FOC is **not** sufficient for global optimality, and the leader's FOC alone does not establish an equilibrium. Analyze corners, multiple responses, and whether the demand/supply assumptions are feasible.

## Synthetic regression model (not an original paper quote)

Use the manually authored fixture `tests/fixtures/phase3/stackelberg_synthetic.json`, following the test problem in `MODIFICATION_PLAN.md` §6.2:

\[
\Pi_F(e\mid p)=a(A-bp)e-\frac{c}{2}e^2,\qquad
\Pi_L(p,e)=(p-w)(A-bp+\gamma e).
\]

The fixture encodes these expressions as an inert, bounded JSON AST with normalized dimensionless symbols, declares `p` at stage 1 and `e` at stage 2, and records the effort decision's visibility of the earlier price. **Only structural validation is performed in Phase 3**, with `NOT_SOLVED` reverse-stage task descriptors. The illustrative finite strategy bounds and demand constraints are not a claim that all parameter combinations satisfy the economically preferred closed-form solution.

**Origins:** Stackelberg (1934); [pAI-Econ-codex model workflow](https://github.com/Cavaradossi/pAI-Econ-codex/tree/84385fb1b4e093b22acae7fd7a8a5381762fb638); synthetic test formulation in `MODIFICATION_PLAN.md` §6.2.
