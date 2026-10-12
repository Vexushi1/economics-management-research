---
name: economic-model-design
description: Specify economics and management game primitives as inert, independently reviewable structural facts.
---

# Economic Model Design — Phase 3

This Skill proposes **model facts**, not equilibria, proofs, calculations or executable code.

1. Obtain the actual research question and original source anchors. Mark unreadable PDF equations `NOT_VERIFIED`; do not infer symbols from damaged extraction.
2. Specify players, decision variables, domain and units, decision stages, exogenous states, information sets and when signals become available. Separate conditional forecasts from actual realizations.
3. Represent every payoff and constraint exclusively as **JSON AST nodes** defined in `schemas/model-spec.schema.json`; never paste Python expressions, SymPy parser syntax, shell commands or JavaScript into AST fields. Supported operations are `const`, `symbol`, `neg`, `add`, `mul`, `sub`, `div`, `pow`.
4. Run the local structural/domain/timing checks in `emr.domain.game.validate_game_spec`. Errors are **blockers**, not assumptions to silently repair. Declarations that pass are not mathematical verification.
5. Compare against a relevant **cited** baseline. Record the extra economic mechanism and a zero-mechanism limiting-case *question*; mathematical reduction must be checked in later stages, not asserted here.
6. Propose reverse-stage best-response tasks only through `build_best_response_tasks`, which emits `NOT_SOLVED`. Do not execute formulas or claim a unique equilibrium.

## Scientific limitations

- A syntactically valid utility does not guarantee demand nonnegativity over all parameters, stochastic distribution normalization, IR/IC satisfaction or a valid optimum.
- A `paper_anchor` record contains a file hash and page number, not verified source content; link exact quotes through Phase 2 provenance and human verification.
- The current discrete-stage DSL is deliberately unsuitable for continuous-time HJB or hidden-information Bayesian games without further specification and tests.
- The 2025 Omega random-supply example is **stochastic sequential**, not an HJB, but the included taxonomy test fixture is not a reconstruction of the published model.

## Safe local verification

```bash
emr model validate tests/fixtures/phase3/stackelberg_synthetic.json
emr model tasks tests/fixtures/phase3/stackelberg_synthetic.json
```

Input is inert local JSON. Reject unsupported syntax and oversized files. Never upload unpublished PDFs or data to a public repository.
