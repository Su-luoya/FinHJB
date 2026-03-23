# BCW2011 Case Study

This page is the hub for learning FinHJB through the BCW examples.

The repository includes two worked examples based on Bolton, Chen, and Wang (2011):

- `src/example/BCW2011Liquidation.py`
- `src/example/BCW2011Hedging.py`

The original equation transcript used by the repository is:

- `src/example/A_unified_theory_of_tobin's_q,_corporate_investment,_financing,_and_risk_management.md`

## What You Learn From BCW

The BCW examples teach nearly every important FinHJB concept in one coherent setting:

- how to encode parameters and boundaries,
- how to express a policy either explicitly or implicitly,
- how to search for an endogenous boundary,
- how to interpret `v`, `dv`, and `d2v`,
- how financing frictions change policies in low-cash states,
- how a hedging extension adds a second control and a margin-account mechanism.

## Recommended Reading Order

If you are new to the project, use this sequence:

1. [Installation and Environment](./installation-and-environment.md)
2. [Getting Started](./getting-started.md)
3. [BCW Liquidation Walkthrough](./bcw2011-liquidation-walkthrough.md)
4. [Results and Diagnostics](./results-and-diagnostics.md)
5. [BCW Hedging Walkthrough](./bcw2011-hedging-walkthrough.md)
6. [Adapting BCW to Your Model](./adapting-bcw-to-your-model.md)

## Two Cases, Two Learning Goals

| Case | Script | Main numerical idea | Main economic idea |
|---|---|---|---|
| Liquidation | `BCW2011Liquidation.py` | right-boundary search with super-contact condition | low cash sharply depresses investment |
| Hedging | `BCW2011Hedging.py` | policy with two controls and refinancing-aware boundaries | hedge demand binds in distressed states and fades with internal liquidity |

## Stable Result Patterns To Expect

You do not need to reproduce every printed line. What matters is the pattern.

### Liquidation

Healthy runs in this repository show:

- `v_left` at `0.9`,
- solved `s_max` around `0.22`,
- `d2v[-1]` near zero,
- investment negative in distressed states and positive near the right boundary.

### Hedging

Healthy runs in this repository show:

- left boundary value above the pure liquidation value,
- solved `s_max` around `0.14`,
- `psi` between `-5` and `0`,
- a three-region hedge pattern: fully binding, then interior, then zero hedge.

## How The Case Study Pages Split Responsibilities

Use the other BCW pages intentionally:

- [BCW Liquidation Walkthrough](./bcw2011-liquidation-walkthrough.md):
  line-by-line interpretation of the liquidation script, the boundary-search target, and the expected solution shape.
- [BCW Hedging Walkthrough](./bcw2011-hedging-walkthrough.md):
  how `psi`, `kappa`, refinancing, and the three hedge regions are encoded.
- [Results and Diagnostics](./results-and-diagnostics.md):
  how to inspect `state`, `grid`, `history`, and continuation outputs without guessing.

## Equation-to-Code Landmarks

The repository already uses BCW as a structured mapping exercise. Some of the most important landmarks are:

| Equation idea | Where it appears in code |
|---|---|
| first-best investment rule | `Policy.initialize` in the liquidation case |
| liquidation value boundary | `Boundary.compute_v_left` |
| payout-side contact condition | `boundary_condition()` with `grid.d2v[-1]` |
| hedge FOC and clipping | `Policy.cal_policy` in the hedging case |
| margin-account share | `kappa = min(|psi| / pi, 1)` inside the hedging model |

## When To Leave The BCW Track

Stay on the BCW track until you can answer these questions from your own run:

1. Why is `d2v[-1]` the key right-boundary diagnostic?
2. Why can investment become strongly negative at low cash?
3. Why does `psi` saturate at `-pi` in the hedging case?
4. What changes between fixed-boundary solving, boundary search, and boundary update?

Once you can answer them, move to:

- [Modeling Guide](./modeling-guide.md)
- [Adapting BCW to Your Model](./adapting-bcw-to-your-model.md)
