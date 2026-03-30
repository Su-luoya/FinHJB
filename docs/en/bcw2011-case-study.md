# BCW2011 Case Study

This page is the hub for the repository BCW path.

Use it after [Getting Started](./getting-started.md) when you want the full map of the four worked BCW cases shipped in `src/example/`.

The repository examples now cover four paper-aligned cases:

- `src/example/BCW2011Liquidation.py`
- `src/example/BCW2011Refinancing.py`
- `src/example/BCW2011Hedging.py`
- `src/example/BCW2011CreditLine.py`

The shared paper transcript used for equation references is:

- `src/example/A_unified_theory_of_tobin's_q,_corporate_investment,_financing,_and_risk_management.md`

## What The BCW Path Is For

The BCW track is the shortest route from a continuous-time corporate finance paper to a runnable one-dimensional FinHJB implementation.

It teaches three things at the same time:

- how BCW reduces a two-state problem to one state by homogeneity,
- how that reduced problem is expressed in the FinHJB class interface,
- how endogenous boundaries become numerical search targets.

## Common Notation And Mapping

All four BCW examples use the same one-dimensional reduction:

$$
P(K, W) = K p(w), \qquad w = W/K.
$$

The paper's objects map to repository objects as follows:

| Paper object | Meaning | Repository object |
|---|---|---|
| `w` | cash-capital ratio | `grid.s` |
| `p(w)` | value-capital ratio | `grid.v` |
| `p'(w)` | marginal value of cash | `grid.dv` |
| `p''(w)` | curvature | `grid.d2v` |
| `q_a = p-w` | average q | derived series `qa` |
| `q_m = p-wp'` | marginal q | derived series `qm` |
| policy functions | `i(w)`, `\psi(w)` | `grid.policy[...]` |

The FinHJB interface mapping is equally stable across the four scripts:

| FinHJB class | BCW role |
|---|---|
| `Parameter` | Table I primitives and case-specific parameters |
| `Boundary` | left/right boundary values and state limits |
| `PolicyDict` | control variables stored on the grid |
| `Policy` | FOCs or explicit policy updates |
| `Model` | HJB residual and outer boundary targets |

## Four Cases, Four Modeling Patterns

| Case | Script | Paper figure | Main numerical idea | Main economic idea |
|---|---|---|---|---|
| Case I | `BCW2011Liquidation.py` | Figure 2 | one-target payout-boundary search | severe financing distress triggers disinvestment |
| Case II | `BCW2011Refinancing.py` | Figure 3 | two-target search over `s_max` and `v_left` | equity issuance softens the liquidation region |
| Case IV | `BCW2011Hedging.py` | Figure 6 | two-control HJB plus hedge-region diagnostics | hedging and liquidity management are complements |
| Case V | `BCW2011CreditLine.py` | Figure 7 | piecewise HJB over cash and debt regions | credit lines reduce the marginal value of liquidity |

## How Paper Boundary Conditions Become Numerical Targets

One of the main reasons to study the BCW examples is that they show how a paper's boundary language becomes runnable code.

The recurring pattern is:

1. a paper equation specifies a boundary value,
2. a paper optimality condition specifies a searched unknown,
3. the solver searches until the grid satisfies the target residual.

Examples:

- liquidation: search `\bar w` until `p''(\bar w)=0`,
- refinancing: search `p(0)` and `\bar w`, then infer `m` from `p'(m)=1+\gamma`,
- hedging: keep the refinancing boundary logic but solve a richer policy problem,
- credit line: keep issuance and payout logic while switching the HJB residual across regimes.

## Recommended Reading Order

If your goal is to understand the package through BCW rather than just run the scripts, use this order:

1. [Installation and Environment](./installation-and-environment.md)
2. [Getting Started](./getting-started.md)
3. [BCW2011 Liquidation Walkthrough](./bcw2011-liquidation-walkthrough.md)
4. [BCW2011 Refinancing Walkthrough](./bcw2011-refinancing-walkthrough.md)
5. [BCW2011 Hedging Walkthrough](./bcw2011-hedging-walkthrough.md)
6. [BCW2011 Credit Line Walkthrough](./bcw2011-credit-line-walkthrough.md)
7. [Results and Diagnostics](./results-and-diagnostics.md)
8. [Adapting BCW To Your Model](./adapting-bcw-to-your-model.md)

The walkthroughs are the derivation-and-code bridge. `Results and Diagnostics` is the solver-facing companion once you already understand the case logic.

## Stable Magnitudes To Cross-Check

Healthy runs in this repository usually look like this:

| Case | Stable magnitudes |
|---|---|
| Liquidation | `\bar w \approx 0.22`, `p'(0) \approx 30`, `i(\bar w) \approx 10.5%` |
| Refinancing | with `phi=1%`: `\bar w \approx 0.19`, `m \approx 0.06`; with `phi=0`: `\bar w \approx 0.14`, `m \approx 0` |
| Hedging | costly margin: `w_- \approx 0.07`, `w_+ \approx 0.11`, `\bar w \approx 0.14`, `\psi \in [-5, 0]` |
| Credit line | with `c=20%`: `\bar w \approx 0.08`, `c+m \approx 0.10`, `p'(0) \approx 1.01` |

These are the right first checks before you worry about small grid-to-grid differences.

## Which Walkthrough To Use As A Template

If you later adapt BCW to your own model, pick the closest structural example:

- liquidation for one control and one endogenous payout boundary,
- refinancing for issuance and smooth pasting at an interior target,
- hedging for multiple controls and control-dependent variance,
- credit line for regime-dependent residuals on one shared grid.

## Next Step

- Start with [BCW2011 Liquidation Walkthrough](./bcw2011-liquidation-walkthrough.md).
- Use [Results and Diagnostics](./results-and-diagnostics.md) once you want a solver-oriented view of the objects returned by `run_case()`.
