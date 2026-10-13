---
name: game-equilibrium
description: Audited low-dimensional analytical and numerical equilibrium checks from a previously validated economic ModelSpec.
---

# Phase 4 game equilibrium workflow

1. Accept only an explicitly reviewed `ValidatedGameSpec`. Reject raw PDF formula strings and untrusted Python code.
2. Verify timing, players, controls, information sets and constraints before any SymPy operation. Compile only AST whitelist nodes through the dedicated constructor, using exact rationals.
3. For two-stage games, differentiate the follower objective and report FOC roots as **candidates** only. Check concavity, feasibility, boundaries, fixed strategies and all leader options before reporting an equilibrium.
4. A limited exact certificate can be issued for strictly concave univariate quadratic follower and at-most-quadratic reduced leader with affine feasibility sets. Nonlinear/discontinuous constraints or non-interior follower policy changes cause `UNRESOLVED`, not a guessed closed form.
5. Record interval KKT signs: at an interior maximizer derivative is zero, at the lower bound derivative is nonpositive, at the upper bound derivative is nonnegative. KKT is necessary only under its qualification assumptions; it is not sufficient for nonconvex global optimality.
6. Numerical multi-start paths return `LOCAL_CANDIDATES_ONLY` with starting points, objective values and derivative residuals. They never certify global equilibrium.
7. On multiple best responses return `SET_VALUED_BEST_RESPONSE` or `MULTIPLE_MAXIMIZERS`, not a fabricated unique strategy. Unsupported classes explicitly fail closed.
8. The experiment flag `experimental_solver` remains disabled in project defaults. Never silently insert numerical estimates into paper claims.

**Do not confuse** a stationary point, constrained local optimum, globally optimal best response, Nash/subgame-perfect equilibrium, and a theorem valid for all parameters.
